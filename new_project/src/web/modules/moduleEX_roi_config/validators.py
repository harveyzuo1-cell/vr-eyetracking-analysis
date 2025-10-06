"""
ROI命名验证器
ROI Naming Validator

功能:
- 验证ROI ID格式
- 生成新ROI ID
- 检查ID冲突
"""

import re
from typing import Dict, List, Optional, Tuple


class ROIValidator:
    """ROI配置验证器"""

    # ROI命名规则: {TYPE}_{TASK}_{INDEX}
    # TYPE: KW (keywords), INST (instructions), BG (background)
    # TASK: task1-5 (v2) 或 q1-5 (v1 legacy)
    # INDEX: 数字索引 (BG类型不需要索引)
    ROI_PATTERN = r'^(KW|INST|BG)_(task\d+|q\d+)(_\d+)?$'

    # ROI类型定义
    ROI_TYPES = {
        'KW': {
            'name': 'keywords',
            'priority': 2,
            'requires_index': True,
            'description': '关键词区域'
        },
        'INST': {
            'name': 'instructions',
            'priority': 1,
            'requires_index': True,
            'description': '指令区域'
        },
        'BG': {
            'name': 'background',
            'priority': 0,
            'requires_index': False,
            'description': '背景区域'
        }
    }

    # 任务ID验证规则
    TASK_PATTERN_V2 = r'^task[1-5]$'
    TASK_PATTERN_V1 = r'^q[1-5]$'

    def __init__(self):
        self.roi_regex = re.compile(self.ROI_PATTERN)
        self.task_regex_v2 = re.compile(self.TASK_PATTERN_V2)
        self.task_regex_v1 = re.compile(self.TASK_PATTERN_V1)

    def validate_roi_id(self, roi_id: str, expected_type: Optional[str] = None,
                        expected_task: Optional[str] = None) -> Dict:
        """
        验证ROI ID格式

        Args:
            roi_id: ROI ID字符串
            expected_type: 期望的ROI类型 (可选)
            expected_task: 期望的任务ID (可选)

        Returns:
            {
                'valid': bool,
                'type': str,
                'task': str,
                'index': int,
                'error': str
            }
        """
        result = {
            'valid': False,
            'type': None,
            'task': None,
            'index': None,
            'error': None
        }

        # 检查格式
        match = self.roi_regex.match(roi_id)
        if not match:
            result['error'] = f'ROI ID格式错误: {roi_id}. 期望格式: {{TYPE}}_{{TASK}}_{{INDEX}}'
            return result

        # 提取组件
        roi_type = match.group(1)
        task_id = match.group(2)
        index_part = match.group(3)

        # 验证ROI类型
        if roi_type not in self.ROI_TYPES:
            result['error'] = f'未知的ROI类型: {roi_type}. 允许的类型: {list(self.ROI_TYPES.keys())}'
            return result

        # 验证任务ID
        if not (self.task_regex_v2.match(task_id) or self.task_regex_v1.match(task_id)):
            result['error'] = f'任务ID格式错误: {task_id}. 期望格式: task1-5 或 q1-5'
            return result

        # 验证索引
        type_config = self.ROI_TYPES[roi_type]
        if type_config['requires_index']:
            if not index_part:
                result['error'] = f'{roi_type}类型的ROI需要索引号'
                return result
            try:
                index = int(index_part[1:])  # 去掉前导下划线
                if index < 1:
                    result['error'] = f'索引必须大于0: {index}'
                    return result
            except ValueError:
                result['error'] = f'索引格式错误: {index_part}'
                return result
        else:
            # BG类型不应该有索引
            if index_part:
                result['error'] = f'{roi_type}类型的ROI不应该有索引号'
                return result
            index = None

        # 检查期望值
        if expected_type and roi_type != expected_type:
            result['error'] = f'ROI类型不匹配: 期望{expected_type}, 实际{roi_type}'
            return result

        if expected_task and task_id != expected_task:
            result['error'] = f'任务ID不匹配: 期望{expected_task}, 实际{task_id}'
            return result

        # 验证通过
        result['valid'] = True
        result['type'] = roi_type
        result['task'] = task_id
        result['index'] = index

        return result

    def generate_roi_id(self, roi_type: str, task_id: str,
                        existing_ids: Optional[List[str]] = None) -> str:
        """
        生成新的ROI ID

        Args:
            roi_type: ROI类型 (KW, INST, BG)
            task_id: 任务ID
            existing_ids: 已存在的ROI ID列表

        Returns:
            新生成的ROI ID字符串
        """
        # 验证ROI类型
        if roi_type not in self.ROI_TYPES:
            raise ValueError(f'未知的ROI类型: {roi_type}')

        # 验证任务ID
        if not (self.task_regex_v2.match(task_id) or self.task_regex_v1.match(task_id)):
            raise ValueError(f'任务ID格式错误: {task_id}')

        type_config = self.ROI_TYPES[roi_type]

        # BG类型不需要索引
        if not type_config['requires_index']:
            roi_id = f'{roi_type}_{task_id}'

            # 检查是否已存在
            if existing_ids and roi_id in existing_ids:
                raise ValueError(f'背景ROI已存在: {roi_id}')

            return roi_id

        # KW/INST类型需要找到下一个可用索引
        existing_ids = existing_ids or []
        prefix = f'{roi_type}_{task_id}_'

        # 提取已存在的索引
        existing_indices = []
        for existing_id in existing_ids:
            if existing_id.startswith(prefix):
                try:
                    index = int(existing_id[len(prefix):])
                    existing_indices.append(index)
                except ValueError:
                    continue

        # 找到下一个可用索引
        next_index = 1
        while next_index in existing_indices:
            next_index += 1

        roi_id = f'{roi_type}_{task_id}_{next_index}'
        return roi_id

    def check_roi_conflicts(self, roi_id: str, existing_ids: List[str]) -> Dict:
        """
        检查ROI ID冲突

        Args:
            roi_id: 要检查的ROI ID
            existing_ids: 已存在的ROI ID列表

        Returns:
            {
                'has_conflict': bool,
                'message': str
            }
        """
        result = {
            'has_conflict': False,
            'message': None
        }

        if roi_id in existing_ids:
            result['has_conflict'] = True
            result['message'] = f'ROI ID已存在: {roi_id}'

        return result

    def parse_roi_id(self, roi_id: str) -> Dict:
        """
        解析ROI ID

        Args:
            roi_id: ROI ID字符串

        Returns:
            {
                'type': str,
                'type_name': str,
                'priority': int,
                'task': str,
                'index': int,
                'description': str
            }
        """
        validation = self.validate_roi_id(roi_id)
        if not validation['valid']:
            return None

        roi_type = validation['type']
        type_config = self.ROI_TYPES[roi_type]

        return {
            'type': roi_type,
            'type_name': type_config['name'],
            'priority': type_config['priority'],
            'task': validation['task'],
            'index': validation['index'],
            'description': type_config['description']
        }

    def get_roi_category(self, roi_id: str) -> Optional[str]:
        """
        获取ROI的分类 (keywords/instructions/background)

        Args:
            roi_id: ROI ID

        Returns:
            分类名称 (keywords/instructions/background) 或 None
        """
        parsed = self.parse_roi_id(roi_id)
        if parsed:
            return parsed['type_name']
        return None


