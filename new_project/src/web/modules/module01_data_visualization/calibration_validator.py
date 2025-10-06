"""
校正参数验证器
Calibration Parameter Validator

验证眼动数据校正的请求参数
"""
from typing import Tuple, List, Dict, Any


class CalibrationValidator:
    """校正参数验证器"""

    # 位置偏移范围限制
    MAX_OFFSET = 0.4
    MIN_OFFSET = -0.4

    # 时间裁剪范围限制（秒）
    MAX_TRIM_TIME = 60.0
    MIN_TRIM_TIME = 0.0

    # 有效的组别
    VALID_GROUPS = ['control', 'mci', 'ad']

    @classmethod
    def validate_calibration_request(cls, data: Dict[str, Any]) -> Tuple[bool, List[str]]:
        """
        验证校正请求

        Args:
            data: 请求数据字典

        Returns:
            (is_valid, error_messages)

        Example:
            >>> validator = CalibrationValidator()
            >>> is_valid, errors = validator.validate_calibration_request({
            ...     'group': 'control',
            ...     'subject_id': 'S001',
            ...     'task': 'q1',
            ...     'params': {
            ...         'offsetX': 0.01,
            ...         'offsetY': -0.02
            ...     }
            ... })
            >>> is_valid
            True
        """
        errors = []

        # 1. 验证必需字段
        required_fields = ['group', 'subject_id', 'task', 'params']
        for field in required_fields:
            if field not in data or data[field] is None:
                errors.append(f"Missing required field: {field}")

        if errors:
            return False, errors

        # 2. 验证group
        group = data.get('group', '').lower()
        if group not in cls.VALID_GROUPS:
            errors.append(
                f"Invalid group: '{group}'. Must be one of: {', '.join(cls.VALID_GROUPS)}"
            )

        # 3. 验证subject_id
        subject_id = data.get('subject_id', '')
        if not subject_id or not isinstance(subject_id, str):
            errors.append("subject_id must be a non-empty string")
        elif len(subject_id) > 50:
            errors.append("subject_id is too long (max 50 characters)")

        # 4. 验证task
        task = data.get('task', '')
        if not task or not isinstance(task, str):
            errors.append("task must be a non-empty string")
        elif len(task) > 20:
            errors.append("task is too long (max 20 characters)")

        # 5. 验证params
        params = data.get('params')
        if not isinstance(params, dict):
            errors.append("params must be a dictionary")
            return False, errors

        # 验证具体参数
        param_errors = cls._validate_params(params)
        errors.extend(param_errors)

        return len(errors) == 0, errors

    @classmethod
    def _validate_params(cls, params: Dict[str, Any]) -> List[str]:
        """
        验证校正参数

        Args:
            params: 校正参数字典

        Returns:
            错误消息列表
        """
        errors = []

        # 验证offsetX
        if 'offsetX' in params:
            offset_x = params['offsetX']
            if not isinstance(offset_x, (int, float)):
                errors.append("offsetX must be a number")
            elif not (cls.MIN_OFFSET <= offset_x <= cls.MAX_OFFSET):
                errors.append(
                    f"offsetX must be between {cls.MIN_OFFSET} and {cls.MAX_OFFSET}, "
                    f"got {offset_x}"
                )

        # 验证offsetY
        if 'offsetY' in params:
            offset_y = params['offsetY']
            if not isinstance(offset_y, (int, float)):
                errors.append("offsetY must be a number")
            elif not (cls.MIN_OFFSET <= offset_y <= cls.MAX_OFFSET):
                errors.append(
                    f"offsetY must be between {cls.MIN_OFFSET} and {cls.MAX_OFFSET}, "
                    f"got {offset_y}"
                )

        # 验证trimStart
        if 'trimStart' in params:
            trim_start = params['trimStart']
            if not isinstance(trim_start, (int, float)):
                errors.append("trimStart must be a number")
            elif not (cls.MIN_TRIM_TIME <= trim_start <= cls.MAX_TRIM_TIME):
                errors.append(
                    f"trimStart must be between {cls.MIN_TRIM_TIME} and {cls.MAX_TRIM_TIME}, "
                    f"got {trim_start}"
                )
            elif trim_start < 0:
                errors.append("trimStart cannot be negative")

        # 验证trimEnd
        if 'trimEnd' in params:
            trim_end = params['trimEnd']
            if not isinstance(trim_end, (int, float)):
                errors.append("trimEnd must be a number")
            elif not (cls.MIN_TRIM_TIME <= trim_end <= cls.MAX_TRIM_TIME):
                errors.append(
                    f"trimEnd must be between {cls.MIN_TRIM_TIME} and {cls.MAX_TRIM_TIME}, "
                    f"got {trim_end}"
                )
            elif trim_end < 0:
                errors.append("trimEnd cannot be negative")

        # 验证trimStart和trimEnd的组合
        if 'trimStart' in params and 'trimEnd' in params:
            trim_start = params.get('trimStart', 0)
            trim_end = params.get('trimEnd', 0)
            if isinstance(trim_start, (int, float)) and isinstance(trim_end, (int, float)):
                if trim_start + trim_end > cls.MAX_TRIM_TIME:
                    errors.append(
                        f"Combined trim (start + end) cannot exceed {cls.MAX_TRIM_TIME} seconds, "
                        f"got {trim_start + trim_end}"
                    )

        return errors

    @classmethod
    def validate_get_params_request(cls, group: str, subject_id: str, task: str) -> Tuple[bool, List[str]]:
        """
        验证获取参数请求

        Args:
            group: 组别
            subject_id: 受试者ID
            task: 任务ID

        Returns:
            (is_valid, error_messages)
        """
        errors = []

        if not group:
            errors.append("group is required")
        elif group.lower() not in cls.VALID_GROUPS:
            errors.append(f"Invalid group: '{group}'")

        if not subject_id:
            errors.append("subject_id is required")

        if not task:
            errors.append("task is required")

        return len(errors) == 0, errors
