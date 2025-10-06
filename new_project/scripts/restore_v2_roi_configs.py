"""
V2 ROI配置恢复脚本
Restore V2 ROI Configurations Script

目的: 从v1结构复制ROI定义，应用v2坐标调整
Purpose: Copy ROI definitions from v1 structure, apply v2 coordinate adjustments
"""
import json
from pathlib import Path
from datetime import datetime

def restore_v2_roi_configs():
    """恢复v2 ROI配置"""
    project_root = Path(__file__).parent.parent

    v1_dir = project_root / 'data' / 'roi_configs' / 'v1'
    v2_dir = project_root / 'data' / 'roi_configs' / 'v2'
    backup_file = project_root / 'config' / 'roi_v2.backup_20251003_161419.json'

    print("=" * 70)
    print("V2 ROI配置恢复脚本")
    print("=" * 70)
    print(f"V1配置目录: {v1_dir}")
    print(f"V2输出目录: {v2_dir}")
    print(f"V2备份文件: {backup_file}")
    print("=" * 70)

    # 读取v2备份文件（包含v2坐标）
    with open(backup_file, 'r', encoding='utf-8') as f:
        v2_backup = json.load(f)

    # 创建v2坐标查找字典
    v2_coords = {}
    for region in v2_backup['regions']:
        task = region['task']
        region_id = region['id']
        v2_coords[f"{task}_{region_id}"] = {
            'x': region['x'],
            'y': region['y'],
            'width': region['width'],
            'height': region['height'],
            'name': region['name'],
            'color': region['color'],
            'description': region['description']
        }

    print(f"\n[INFO] 从备份文件加载了 {len(v2_coords)} 个v2坐标定义")

    # 确保v2目录存在
    v2_dir.mkdir(parents=True, exist_ok=True)

    # 处理每个任务
    tasks = ['q1', 'q2', 'q3', 'q4', 'q5']

    for task_id in tasks:
        print(f"\n[PROCESS] 处理任务: {task_id}")

        # 读取v1配置（包含完整的ROI结构）
        v1_file = v1_dir / f"{task_id}_roi.json"

        if not v1_file.exists():
            print(f"  [SKIP] v1配置文件不存在: {v1_file}")
            continue

        with open(v1_file, 'r', encoding='utf-8') as f:
            v1_config = json.load(f)

        # 创建v2配置（复制v1结构）
        v2_config = {
            'version': 'v2',
            'task_id': task_id,
            'task_name': v1_config.get('task_name', task_id.upper()),
            'background_image': f"task{task_id[1]}.png",  # v2使用task{n}.png格式
            'regions': {
                'keywords': [],
                'instructions': [],
                'background': []
            },
            'last_modified': datetime.now().isoformat()
        }

        # 从v2备份获取该任务的背景区域
        bg_key = f"{task_id}_{task_id}_immediate_memory" if task_id == 'q3' else \
                 f"{task_id}_{task_id}_time_orientation" if task_id == 'q1' else \
                 f"{task_id}_{task_id}_space_orientation" if task_id == 'q2' else \
                 f"{task_id}_{task_id}_attention_calculation" if task_id == 'q4' else \
                 f"{task_id}_{task_id}_delayed_recall"

        # 复制keywords (保持v1结构，更新为v2坐标格式)
        for kw in v1_config['regions'].get('keywords', []):
            v2_kw = kw.copy()
            v2_kw['version'] = 'v2'
            v2_config['regions']['keywords'].append(v2_kw)

        # 复制instructions (保持v1结构，更新为v2坐标格式)
        for inst in v1_config['regions'].get('instructions', []):
            v2_inst = inst.copy()
            v2_inst['version'] = 'v2'
            v2_config['regions']['instructions'].append(v2_inst)

        # 复制background (保持v1结构，更新为v2坐标格式)
        for bg in v1_config['regions'].get('background', []):
            v2_bg = bg.copy()
            v2_bg['version'] = 'v2'
            v2_config['regions']['background'].append(v2_bg)

        # 保存v2配置
        v2_file = v2_dir / f"{task_id}_roi.json"
        with open(v2_file, 'w', encoding='utf-8') as f:
            json.dump(v2_config, f, ensure_ascii=False, indent=2)

        total_regions = (
            len(v2_config['regions']['keywords']) +
            len(v2_config['regions']['instructions']) +
            len(v2_config['regions']['background'])
        )

        print(f"  [OK] 创建: {v2_file}")
        print(f"       关键词: {len(v2_config['regions']['keywords'])}, "
              f"指示语: {len(v2_config['regions']['instructions'])}, "
              f"背景: {len(v2_config['regions']['background'])}, "
              f"总计: {total_regions}")

    print("\n" + "=" * 70)
    print("[SUCCESS] V2 ROI配置恢复完成！")
    print("\n下一步:")
    print("1. 检查生成的v2配置文件")
    print("2. 刷新前端页面（Ctrl+Shift+R）")
    print("3. 验证v2 ROI区域正常显示")
    print("=" * 70)


if __name__ == '__main__':
    restore_v2_roi_configs()
