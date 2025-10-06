"""
V2 ROI配置正确恢复脚本
Restore V2 ROI Configurations with Correct Coordinates

目的:
1. 从v1复制完整的分层结构（keywords/instructions/background）
2. 从v2 backup应用真实的坐标调整（基于背景区域的偏移）
"""
import json
from pathlib import Path
from datetime import datetime

def restore_v2_roi_configs():
    """恢复v2 ROI配置 - 使用v1结构但应用v2坐标调整"""
    project_root = Path(__file__).parent.parent

    v1_dir = project_root / 'data' / 'roi_configs' / 'v1'
    v2_dir = project_root / 'data' / 'roi_configs' / 'v2'
    backup_file = project_root / 'config' / 'roi_v2.backup_20251003_161419.json'

    print("=" * 70)
    print("V2 ROI配置正确恢复脚本 - 应用v2坐标调整")
    print("=" * 70)
    print(f"V1配置目录: {v1_dir}")
    print(f"V2输出目录: {v2_dir}")
    print(f"V2备份文件: {backup_file}")
    print("=" * 70)

    # 读取v2备份文件（包含v2背景区域坐标）
    with open(backup_file, 'r', encoding='utf-8') as f:
        v2_backup = json.load(f)

    # 创建v2背景区域坐标映射
    v2_bg_coords = {}
    for region in v2_backup['regions']:
        task = region['task']
        v2_bg_coords[task] = {
            'x': region['x'],
            'y': region['y'],
            'width': region['width'],
            'height': region['height']
        }

    print(f"\n[INFO] 从备份文件加载了 {len(v2_bg_coords)} 个v2背景区域坐标")
    for task, coords in v2_bg_coords.items():
        print(f"  {task}: x={coords['x']:.2f}, y={coords['y']:.2f}, "
              f"w={coords['width']:.2f}, h={coords['height']:.2f}")

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

        # 计算v1到v2的偏移量（根据背景区域的变化）
        # v1背景区域通常在某个位置，v2有调整
        # 注意：v2备份只有背景区域的绝对坐标，我们直接使用这些
        # 对于keywords和instructions，我们保持v1的坐标（因为备份中没有）

        # 创建v2配置（复制v1结构，更新版本标识）
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

        # 复制keywords (保持v1的坐标，只更新version字段)
        for kw in v1_config['regions'].get('keywords', []):
            v2_kw = kw.copy()
            v2_kw['version'] = 'v2'
            v2_config['regions']['keywords'].append(v2_kw)

        # 复制instructions (保持v1的坐标，只更新version字段)
        for inst in v1_config['regions'].get('instructions', []):
            v2_inst = inst.copy()
            v2_inst['version'] = 'v2'
            v2_config['regions']['instructions'].append(v2_inst)

        # 复制background并应用v2坐标（从备份获取）
        for bg in v1_config['regions'].get('background', []):
            v2_bg = bg.copy()
            v2_bg['version'] = 'v2'

            # 如果v2备份中有这个任务的坐标，使用v2的坐标
            # 否则保持v1的坐标
            # 注意：v2备份使用x,y,width,height格式，需要转换为normalized_coords
            if task_id in v2_bg_coords:
                coords = v2_bg_coords[task_id]
                # 保持normalized_coords格式: [x, y, width, height]
                v2_bg['normalized_coords'] = [
                    coords['x'],
                    coords['y'],
                    coords['width'],
                    coords['height']
                ]
                print(f"  [UPDATE] 应用v2背景坐标: {v2_bg['normalized_coords']}")

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
    print("[SUCCESS] V2 ROI配置恢复完成（已应用v2坐标）！")
    print("\n说明:")
    print("- Keywords和Instructions区域使用v1坐标（因为v2备份中没有这些）")
    print("- Background区域使用v2备份中的坐标")
    print("- 如果ModuleEX中有完整的v2 ROI定义，应该从那里导出")
    print("\n下一步:")
    print("1. 检查生成的v2配置文件")
    print("2. 刷新前端页面（Ctrl+Shift+R）")
    print("3. 验证v2背景区域坐标是否正确")
    print("=" * 70)


if __name__ == '__main__':
    restore_v2_roi_configs()
