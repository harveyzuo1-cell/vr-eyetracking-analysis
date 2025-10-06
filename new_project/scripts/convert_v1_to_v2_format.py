"""
一次性转换v1 ROI格式到v2格式
Convert v1 ROI format (x/y/width/height) to v2 format (normalized_coords array)

这个脚本会：
1. 读取备份的真实v1 ROI数据
2. 将 {x, y, width, height} 转换为 normalized_coords: [x, y, w, h]
3. 保存为v2兼容格式到 data/roi_configs/v1/
"""
import json
from pathlib import Path
from datetime import datetime

def convert_v1_roi_to_v2_format():
    """执行转换"""
    project_root = Path(__file__).parent.parent

    # 读取真实的v1 ROI备份数据
    backup_file = project_root / "config" / "roi_v1.backup_20251003_161419.json"

    if not backup_file.exists():
        print(f"[ERROR] 备份文件不存在: {backup_file}")
        return False

    print(f"[INFO] 读取真实v1 ROI数据: {backup_file}")

    with open(backup_file, 'r', encoding='utf-8') as f:
        v1_data = json.load(f)

    # 按task分组
    tasks_data = {}
    for region in v1_data['regions']:
        task = region['task']
        if task not in tasks_data:
            tasks_data[task] = []
        tasks_data[task].append(region)

    print(f"[INFO] 找到 {len(tasks_data)} 个任务: {list(tasks_data.keys())}")

    # 为每个任务创建v2格式配置
    output_dir = project_root / "data" / "roi_configs" / "v1"
    output_dir.mkdir(parents=True, exist_ok=True)

    for task_id, regions in tasks_data.items():
        # 转换为v2格式
        v2_config = {
            "version": "v1",
            "task_id": task_id,
            "task_name": regions[0]['name'] if regions else task_id.upper(),
            "background_image": f"Q{task_id[1]}.jpg",  # Q1.jpg, Q2.jpg, etc.
            "regions": {
                "keywords": [],
                "instructions": [],
                "background": []
            },
            "last_modified": datetime.now().isoformat()
        }

        # 转换每个region
        for region in regions:
            # 转换坐标格式: {x, y, width, height} -> normalized_coords: [x, y, w, h]
            converted_region = {
                "id": region['id'],
                "name": region.get('name', region['id']),
                "normalized_coords": [
                    region['x'],
                    region['y'],
                    region['width'],
                    region['height']
                ],
                "task_id": task_id,
                "version": "v1",
                "color": region.get('color', '#999'),
                "description": region.get('description', '')
            }

            # 根据ID判断类型
            if 'time' in region['id'] or 'space' in region['id']:
                # 时间定向、空间定向 -> keywords
                v2_config['regions']['keywords'].append(converted_region)
            elif 'memory' in region['id'] or 'recall' in region['id']:
                # 记忆、回忆 -> keywords
                v2_config['regions']['keywords'].append(converted_region)
            elif 'attention' in region['id'] or 'calculation' in region['id']:
                # 注意力、计算 -> keywords
                v2_config['regions']['keywords'].append(converted_region)
            else:
                # 其他归为background
                v2_config['regions']['background'].append(converted_region)

        # 如果没有background，添加一个全屏背景
        if not v2_config['regions']['background']:
            v2_config['regions']['background'].append({
                "id": f"BG_{task_id}",
                "name": f"{task_id.upper()}_背景",
                "normalized_coords": [0, 0, 1, 1],
                "task_id": task_id,
                "version": "v1",
                "color": "#f0f0f0",
                "description": "全屏背景区域"
            })

        # 保存文件
        output_file = output_dir / f"{task_id}_roi.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(v2_config, f, ensure_ascii=False, indent=2)

        kw_count = len(v2_config['regions']['keywords'])
        inst_count = len(v2_config['regions']['instructions'])
        bg_count = len(v2_config['regions']['background'])

        print(f"[OK] {task_id}: {kw_count} keywords, {inst_count} instructions, {bg_count} background -> {output_file.name}")

    print(f"\n[SUCCESS] 转换完成！共处理 {len(tasks_data)} 个任务")
    print(f"[INFO] 输出目录: {output_dir}")

    # 也更新当前的roi_v1.json
    current_v1 = project_root / "config" / "roi_v1.json"
    with open(current_v1, 'w', encoding='utf-8') as f:
        json.dump(v1_data, f, ensure_ascii=False, indent=2)
    print(f"[INFO] 已恢复 config/roi_v1.json 为真实数据")

    return True

if __name__ == '__main__':
    print("=" * 60)
    print("V1 ROI 格式转换工具")
    print("将 {x, y, width, height} 转换为 normalized_coords: [x, y, w, h]")
    print("=" * 60)

    success = convert_v1_roi_to_v2_format()

    if success:
        print("\n" + "=" * 60)
        print("转换成功！")
        print("现在可以：")
        print("1. 在ModuleEX中加载v1 ROI（自动使用新格式）")
        print("2. Module1可视化v1 ROI（坐标已翻转）")
        print("3. 移除前端的格式兼容代码")
        print("=" * 60)
    else:
        print("\n[ERROR] 转换失败！")
