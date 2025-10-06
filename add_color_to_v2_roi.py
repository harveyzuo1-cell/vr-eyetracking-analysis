"""
为v2的ROI配置文件添加color字段
按照v1的颜色规范：
- Keywords: #1890ff (蓝色)
- Instructions: #52c41a (绿色)
- Background: #faad14 (橙色)
"""
import json
from pathlib import Path

# 颜色配置（与v1一致）
COLOR_MAP = {
    'KW': '#1890ff',      # Keywords - 蓝色
    'INST': '#52c41a',    # Instructions - 绿色
    'BG': '#faad14'       # Background - 橙色
}

def add_colors_to_roi_file(file_path):
    """为单个ROI文件添加color字段"""
    print(f"\n处理文件: {file_path.name}")

    with open(file_path, 'r', encoding='utf-8') as f:
        data = json.load(f)

    modified = False

    # 遍历所有region类型
    for region_type in ['keywords', 'instructions', 'background']:
        if region_type not in data.get('regions', {}):
            continue

        for region in data['regions'][region_type]:
            # 获取region的type字段
            region_type_abbr = region.get('type', '')

            # 如果没有color字段，添加它
            if 'color' not in region:
                color = COLOR_MAP.get(region_type_abbr, '#808080')  # 默认灰色
                region['color'] = color
                print(f"  添加 {region['id']}: {color}")
                modified = True

            # 添加描述字段（如果没有）
            if 'description' not in region:
                desc_map = {
                    'KW': '关键区域',
                    'INST': '指令区域',
                    'BG': '背景区域'
                }
                region['description'] = desc_map.get(region_type_abbr, '区域')
                modified = True

            # 添加name字段（如果没有）
            if 'name' not in region:
                region['name'] = region['id']
                modified = True

    if modified:
        # 保存修改后的文件
        with open(file_path, 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        print(f"  ✓ 已保存")
        return True
    else:
        print(f"  - 无需修改")
        return False

def main():
    # v2 ROI配置目录
    roi_dir = Path("new_project/data/roi_configs/v2")

    if not roi_dir.exists():
        print(f"错误: 目录不存在 - {roi_dir}")
        return

    print("=" * 60)
    print("为v2 ROI配置添加颜色字段")
    print("=" * 60)

    # 处理所有task*.json文件
    task_files = sorted(roi_dir.glob("task*_roi.json"))

    if not task_files:
        print("未找到task*_roi.json文件")
        return

    modified_count = 0
    for task_file in task_files:
        if add_colors_to_roi_file(task_file):
            modified_count += 1

    print("\n" + "=" * 60)
    print(f"完成！共处理 {len(task_files)} 个文件，修改了 {modified_count} 个文件")
    print("=" * 60)

if __name__ == "__main__":
    main()
