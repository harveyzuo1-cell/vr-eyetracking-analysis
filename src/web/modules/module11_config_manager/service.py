"""
Module11 配置管理服务
提供ROI配置的业务逻辑层
"""
import json
import os
from pathlib import Path
from typing import Dict, List, Optional, Tuple
from datetime import datetime
from PIL import Image

from .validators import ROIValidator


class ROIConfigService:
    """ROI配置服务"""
    
    def __init__(self, base_dir: str = None):
        """
        初始化服务
        
        Args:
            base_dir: 项目根目录，默认为当前工作目录
        """
        self.base_dir = Path(base_dir) if base_dir else Path.cwd()
        self.validator = ROIValidator()
        
        # 定义数据目录
        self.background_images_dir = self.base_dir / 'data' / 'background_images'
        self.roi_configs_dir = self.base_dir / 'data' / 'roi_configs'
        
        # 确保目录存在
        self._ensure_directories()
    
    def _ensure_directories(self):
        """确保所需目录存在"""
        for version in ['v1', 'v2']:
            (self.background_images_dir / version).mkdir(parents=True, exist_ok=True)
            (self.roi_configs_dir / version).mkdir(parents=True, exist_ok=True)
    
    # ==================== 背景图片管理 ====================
    
    def list_background_images(self, version: str = 'v2') -> Dict:
        """
        获取背景图片列表
        
        Args:
            version: 数据版本 (v1/v2)
            
        Returns:
            {
                'success': bool,
                'data': [
                    {
                        'filename': str,
                        'task_id': str,
                        'path': str,
                        'size': int,
                        'dimensions': {'width': int, 'height': int},
                        'modified_time': str
                    }
                ],
                'message': str
            }
        """
        try:
            image_dir = self.background_images_dir / version
            if not image_dir.exists():
                return {'success': False, 'message': f'目录不存在: {version}'}
            
            images = []
            for img_file in sorted(image_dir.glob('*.png')) + sorted(image_dir.glob('*.jpg')):
                try:
                    # 获取图片信息
                    stat = img_file.stat()
                    with Image.open(img_file) as img:
                        width, height = img.size
                    
                    # 解析task_id（假设文件名格式为 task1.png, task2.png, ...）
                    task_id = img_file.stem  # 去掉扩展名
                    
                    images.append({
                        'filename': img_file.name,
                        'task_id': task_id,
                        'path': str(img_file.relative_to(self.base_dir)),
                        'size': stat.st_size,
                        'dimensions': {'width': width, 'height': height},
                        'modified_time': datetime.fromtimestamp(stat.st_mtime).isoformat()
                    })
                except Exception as e:
                    print(f"Error processing image {img_file}: {e}")
                    continue
            
            return {
                'success': True,
                'data': images,
                'message': f'找到 {len(images)} 个背景图片'
            }
        except Exception as e:
            return {'success': False, 'message': f'获取背景图片列表失败: {str(e)}'}
    
    def get_background_image_info(self, version: str, task_id: str) -> Dict:
        """
        获取指定背景图片信息
        
        Args:
            version: 数据版本
            task_id: 任务ID (如 task1, task2)
            
        Returns:
            {
                'success': bool,
                'data': {...},
                'message': str
            }
        """
        try:
            image_dir = self.background_images_dir / version
            
            # 尝试查找图片文件（支持png和jpg）
            img_path = None
            for ext in ['.png', '.jpg', '.jpeg']:
                candidate = image_dir / f"{task_id}{ext}"
                if candidate.exists():
                    img_path = candidate
                    break
            
            if not img_path:
                return {'success': False, 'message': f'未找到图片: {task_id}'}
            
            # 获取图片信息
            stat = img_path.stat()
            with Image.open(img_path) as img:
                width, height = img.size
            
            return {
                'success': True,
                'data': {
                    'filename': img_path.name,
                    'task_id': task_id,
                    'path': str(img_path.relative_to(self.base_dir)),
                    'absolute_path': str(img_path),
                    'size': stat.st_size,
                    'dimensions': {'width': width, 'height': height},
                    'modified_time': datetime.fromtimestamp(stat.st_mtime).isoformat()
                },
                'message': '获取成功'
            }
        except Exception as e:
            return {'success': False, 'message': f'获取背景图片信息失败: {str(e)}'}
    
    def save_background_image(self, file_data, version: str, task_id: str, 
                             filename: str = None) -> Dict:
        """
        保存上传的背景图片
        
        Args:
            file_data: 文件数据（FileStorage对象或二进制数据）
            version: 数据版本
            task_id: 任务ID
            filename: 原始文件名（可选）
            
        Returns:
            {
                'success': bool,
                'data': {...},
                'message': str
            }
        """
        try:
            image_dir = self.background_images_dir / version
            image_dir.mkdir(parents=True, exist_ok=True)
            
            # 确定文件扩展名
            if filename:
                ext = Path(filename).suffix
            else:
                ext = '.png'
            
            # 保存文件
            save_path = image_dir / f"{task_id}{ext}"
            
            if hasattr(file_data, 'save'):  # FileStorage对象
                file_data.save(str(save_path))
            else:  # 二进制数据
                with open(save_path, 'wb') as f:
                    f.write(file_data)
            
            # 验证是否为有效图片
            with Image.open(save_path) as img:
                width, height = img.size
            
            return {
                'success': True,
                'data': {
                    'task_id': task_id,
                    'path': str(save_path.relative_to(self.base_dir)),
                    'dimensions': {'width': width, 'height': height}
                },
                'message': '背景图片保存成功'
            }
        except Exception as e:
            return {'success': False, 'message': f'保存背景图片失败: {str(e)}'}
    
    # ==================== ROI配置管理 ====================
    
    def load_roi_config(self, version: str, task_id: str) -> Dict:
        """
        加载ROI配置
        
        Args:
            version: 数据版本
            task_id: 任务ID
            
        Returns:
            {
                'success': bool,
                'data': {...},  # ROI配置JSON
                'message': str
            }
        """
        try:
            config_path = self.roi_configs_dir / version / f"{task_id}_roi.json"
            
            if not config_path.exists():
                # 返回默认空配置
                default_config = self._create_default_config(version, task_id)
                return {
                    'success': True,
                    'data': default_config,
                    'message': '未找到配置，返回默认配置'
                }
            
            with open(config_path, 'r', encoding='utf-8') as f:
                config = json.load(f)
            
            return {
                'success': True,
                'data': config,
                'message': '加载成功'
            }
        except Exception as e:
            return {'success': False, 'message': f'加载ROI配置失败: {str(e)}'}
    
    def save_roi_config(self, version: str, task_id: str, config: Dict) -> Dict:
        """
        保存ROI配置
        
        Args:
            version: 数据版本
            task_id: 任务ID
            config: ROI配置字典
            
        Returns:
            {
                'success': bool,
                'data': {...},
                'message': str
            }
        """
        try:
            # 验证配置
            validation_result = self.validate_config(config)
            if not validation_result['valid']:
                return {
                    'success': False,
                    'message': f"配置验证失败: {', '.join(validation_result['errors'])}"
                }
            
            # 确保配置包含必要字段
            config['version'] = version
            config['task_id'] = task_id
            config['last_modified'] = datetime.now().isoformat()
            
            # 保存配置
            config_dir = self.roi_configs_dir / version
            config_dir.mkdir(parents=True, exist_ok=True)
            config_path = config_dir / f"{task_id}_roi.json"
            
            with open(config_path, 'w', encoding='utf-8') as f:
                json.dump(config, f, ensure_ascii=False, indent=2)
            
            return {
                'success': True,
                'data': {
                    'path': str(config_path.relative_to(self.base_dir)),
                    'task_id': task_id,
                    'version': version
                },
                'message': 'ROI配置保存成功'
            }
        except Exception as e:
            return {'success': False, 'message': f'保存ROI配置失败: {str(e)}'}
    
    def validate_config(self, config: Dict) -> Dict:
        """
        验证ROI配置完整性和正确性
        
        Args:
            config: ROI配置字典
            
        Returns:
            {
                'valid': bool,
                'errors': List[str],
                'warnings': List[str]
            }
        """
        errors = []
        warnings = []
        
        try:
            # 检查必需字段
            required_fields = ['version', 'task_id', 'background_image', 'regions']
            for field in required_fields:
                if field not in config:
                    errors.append(f'缺少必需字段: {field}')
            
            if 'regions' in config:
                regions = config['regions']
                
                # 检查regions结构
                expected_types = ['keywords', 'instructions', 'background']
                for region_type in expected_types:
                    if region_type not in regions:
                        warnings.append(f'缺少ROI类型: {region_type}')
                
                # 验证每个ROI
                task_id = config.get('task_id', '')
                for region_type, roi_list in regions.items():
                    if not isinstance(roi_list, list):
                        errors.append(f'{region_type} 应该是列表类型')
                        continue
                    
                    for roi in roi_list:
                        # 检查ROI必需字段
                        roi_required = ['id', 'x', 'y', 'width', 'height']
                        for field in roi_required:
                            if field not in roi:
                                errors.append(f'ROI {roi.get("id", "unknown")} 缺少字段: {field}')
                        
                        # 验证ROI ID格式
                        if 'id' in roi:
                            roi_id = roi['id']
                            type_map = {
                                'keywords': 'KW',
                                'instructions': 'INST',
                                'background': 'BG'
                            }
                            expected_type = type_map.get(region_type)
                            
                            if expected_type:
                                validation = self.validator.validate_roi_id(
                                    roi_id, expected_type, task_id
                                )
                                if not validation['valid']:
                                    errors.append(f"ROI ID验证失败: {roi_id} - {validation.get('error', 'unknown error')}")
                        
                        # 验证坐标范围（归一化坐标应在0-1之间）
                        for coord in ['x', 'y', 'width', 'height']:
                            if coord in roi:
                                value = roi[coord]
                                if not (0 <= value <= 1):
                                    warnings.append(
                                        f"ROI {roi.get('id', 'unknown')} 的 {coord} 值 {value} 超出范围 [0, 1]"
                                    )
            
            return {
                'valid': len(errors) == 0,
                'errors': errors,
                'warnings': warnings
            }
        except Exception as e:
            return {
                'valid': False,
                'errors': [f'验证过程出错: {str(e)}'],
                'warnings': []
            }
    
    def _create_default_config(self, version: str, task_id: str) -> Dict:
        """创建默认ROI配置"""
        # 尝试获取背景图片信息
        bg_result = self.get_background_image_info(version, task_id)
        background_image = bg_result['data']['filename'] if bg_result['success'] else f"{task_id}.png"
        
        return {
            'version': version,
            'task_id': task_id,
            'task_name': task_id,
            'background_image': background_image,
            'regions': {
                'keywords': [],
                'instructions': [],
                'background': []
            },
            'created_time': datetime.now().isoformat(),
            'last_modified': datetime.now().isoformat()
        }
    
    # ==================== ROI ID管理 ====================
    
    def validate_roi_id(self, roi_id: str, roi_type: str, task_id: str) -> Dict:
        """
        验证ROI ID
        
        Args:
            roi_id: ROI标识符
            roi_type: ROI类型 (KW/INST/BG)
            task_id: 任务ID
            
        Returns:
            验证结果字典
        """
        return self.validator.validate_roi_id(roi_id, roi_type, task_id)
    
    def generate_roi_id(self, roi_type: str, task_id: str, version: str = 'v2') -> Dict:
        """
        生成下一个可用的ROI ID
        
        Args:
            roi_type: ROI类型 (KW/INST/BG)
            task_id: 任务ID
            version: 数据版本
            
        Returns:
            {
                'success': bool,
                'data': {'roi_id': str},
                'message': str
            }
        """
        try:
            # 加载现有配置获取已使用的ID
            config_result = self.load_roi_config(version, task_id)
            existing_ids = []
            
            if config_result['success']:
                config = config_result['data']
                type_map = {
                    'KW': 'keywords',
                    'INST': 'instructions',
                    'BG': 'background'
                }
                region_type = type_map.get(roi_type)
                
                if region_type and region_type in config.get('regions', {}):
                    existing_ids = [roi['id'] for roi in config['regions'][region_type]]
            
            # 生成新ID
            result = self.validator.generate_roi_id(roi_type, task_id, existing_ids)

            if not result['success']:
                return {'success': False, 'message': result.get('error', '生成失败')}

            return {
                'success': True,
                'data': {'roi_id': result['roi_id']},
                'message': '生成成功'
            }
        except Exception as e:
            return {'success': False, 'message': f'生成ROI ID失败: {str(e)}'}


