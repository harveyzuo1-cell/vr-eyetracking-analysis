"""
从真实的Python代码中提取ROI信息并转换为v2格式
Extract real ROI information from Python code and convert to v2 format

用户提供的ROI坐标是正确的,但需要:
1. 转换坐标格式: tuple(name, xmin, ymin, xmax, ymax) -> normalized_coords: [x, y, w, h]
2. 解决Y轴上下颠倒问题 (代码中已经处理了Y轴翻转)
"""
import json
from pathlib import Path
from datetime import datetime

# 从用户代码中提取的真实ROI定义
USER_DEFINED_ROI = {
    "n2q1": {
        "keywords": [
            ("KW_n2q1_1", 0.01, 0.5886, 0.39, 0.4164),
            ("KW_n2q1_2", 0.39, 0.5886, 0.668, 0.4164),
            ("KW_n2q1_3", 0.01, 0.3494, 0.49, 0.1716),
            ("KW_n2q1_4", 0.49, 0.3494, 0.915, 0.1716),
        ],
        "instructions": [
            ("INST_n2q1_1", 0.01, 0.8250, 0.355, 0.6500)
        ],
        "background": [
            ("BG_n2q1", 0, 0, 1, 1)
        ]
    },
    "n2q2": {
        "keywords": [
            ("KW_n2q2_1", 0.01, 0.5896, 0.466, 0.4104),
            ("KW_n2q2_2", 0.466, 0.5886, 0.95, 0.4164),
            ("KW_n2q2_3", 0.01, 0.3494, 0.49, 0.1716),
            ("KW_n2q2_4", 0.49, 0.3494, 0.999, 0.1716),
        ],
        "instructions": [
            ("INST_n2q2_1", 0.01, 0.8250, 0.754, 0.6500)
        ],
        "background": [
            ("BG_n2q2", 0, 0, 1, 1)
        ]
    },
    "n2q3": {
        "keywords": [
            ("KW_n2q3_1", 0.01, 0.5688, 0.18, 0.4152),
            ("KW_n2q3_2", 0.18, 0.5688, 0.34, 0.4152),
            ("KW_n2q3_3", 0.34, 0.5688, 0.51, 0.4152),
        ],
        "instructions": [
            ("INST_n2q3_1", 0.01, 0.8373, 0.788, 0.6757),
            ("INST_n2q3_2", 0.01, 0.3050, 0.999, 0.1450),
        ],
        "background": [
            ("BG_n2q3", 0, 0, 1, 1)
        ]
    },
    "n2q4": {
        "keywords": [
            ("KW_n2q4_1", 0.42, 0.9273, 0.76, 0.5757),
        ],
        "instructions": [
            ("INST_n2q4_1", 0.01, 0.8373, 0.42, 0.6757),
            ("INST_n2q4_2a", 0.01, 0.54, 0.999, 0.38),
            ("INST_n2q4_2b", 0.01, 0.2525, 0.788, 0.0845),
        ],
        "background": [
            ("BG_n2q4", 0, 0, 1, 1)
        ]
    },
    "n2q5": {
        "keywords": [],
        "instructions": [
            ("INST_n2q5_1a", 0.01, 0.8250, 0.428, 0.6500),
            ("INST_n2q5_1b", 0.01, 0.5886, 0.523, 0.4164),
            ("INST_n2q5_1c", 0.01, 0.3494, 0.77, 0.1716)
        ],
        "background": [
            ("BG_n2q5", 0, 0, 1, 1)
        ]
    }
}


def convert_tuple_to_normalized_coords(roi_tuple):
    """
    转换ROI坐标格式并修复Y轴翻转

    输入: (name, xmin, ymin, xmax, ymax)
    输出: [x, y, width, height]

    注意: V1的ROI在ModuleEX中显示倒置,需要Y轴翻转
    公式: y_new = 1 - y_old - height
    """
    name, xmin, ymin, xmax, ymax = roi_tuple

    # 确保 min < max
    if xmin > xmax:
        xmin, xmax = xmax, xmin
    if ymin > ymax:
        ymin, ymax = ymax, ymin

    # 计算宽高
    width = xmax - xmin
    height = ymax - ymin

    # Y轴翻转: 将原始的Y坐标翻转到正确位置
    # 原始: ymin在下方 (小值), ymax在上方 (大值)
    # 翻转后: 新的Y从顶部开始
    y_flipped = 1 - ymax  # 使用ymax作为翻转后的顶部位置

    return {
        "id": name,
        "name": name,
        "normalized_coords": [xmin, y_flipped, width, height]
    }


def convert_real_roi_to_v2():
    """执行转换"""
    project_root = Path(__file__).parent.parent
    output_dir = project_root / "data" / "roi_configs" / "v1"
    output_dir.mkdir(parents=True, exist_ok=True)

    print("=" * 70)
    print("真实ROI数据转换工具")
    print("从用户提供的Python代码中提取ROI信息并转换为v2格式")
    print("=" * 70)

    # 处理每个任务
    for task_key, roi_def in USER_DEFINED_ROI.items():
        # n2q1 -> q1
        task_id = task_key.replace("n2", "")
        q_num = task_id[1]  # 提取数字

        print(f"\n[INFO] 处理 {task_key} -> {task_id}")

        # 创建v2格式配置
        v2_config = {
            "version": "v1",
            "task_id": task_id,
            "task_name": f"Q{q_num}_{['时间定向', '空间定向', 'MMSE第三题', 'MMSE第四题', 'MMSE第五题'][int(q_num)-1]}",
            "background_image": f"Q{q_num}.jpg",
            "regions": {
                "keywords": [],
                "instructions": [],
                "background": []
            },
            "last_modified": datetime.now().isoformat()
        }

        # 转换keywords
        for roi_tuple in roi_def.get("keywords", []):
            region = convert_tuple_to_normalized_coords(roi_tuple)
            region["task_id"] = task_id
            region["version"] = "v1"
            region["color"] = "#1890ff"  # 蓝色
            region["description"] = "关键区域"
            v2_config["regions"]["keywords"].append(region)

        # 转换instructions
        for roi_tuple in roi_def.get("instructions", []):
            region = convert_tuple_to_normalized_coords(roi_tuple)
            region["task_id"] = task_id
            region["version"] = "v1"
            region["color"] = "#52c41a"  # 绿色
            region["description"] = "指令区域"
            v2_config["regions"]["instructions"].append(region)

        # 转换background
        for roi_tuple in roi_def.get("background", []):
            region = convert_tuple_to_normalized_coords(roi_tuple)
            region["task_id"] = task_id
            region["version"] = "v1"
            region["color"] = "#faad14"  # 橙色
            region["description"] = "背景区域"
            v2_config["regions"]["background"].append(region)

        # 保存文件
        output_file = output_dir / f"{task_id}_roi.json"
        with open(output_file, 'w', encoding='utf-8') as f:
            json.dump(v2_config, f, ensure_ascii=False, indent=2)

        kw_count = len(v2_config['regions']['keywords'])
        inst_count = len(v2_config['regions']['instructions'])
        bg_count = len(v2_config['regions']['background'])

        print(f"[OK] {task_id}: {kw_count} keywords, {inst_count} instructions, {bg_count} background -> {output_file.name}")

        # 显示第一个关键区域的坐标示例
        if v2_config['regions']['keywords']:
            sample = v2_config['regions']['keywords'][0]
            print(f"     示例: {sample['id']} -> {sample['normalized_coords']}")

    print(f"\n{'=' * 70}")
    print(f"[SUCCESS] 转换完成！共处理 {len(USER_DEFINED_ROI)} 个任务")
    print(f"[INFO] 输出目录: {output_dir}")
    print(f"{'=' * 70}")

    return True


if __name__ == '__main__':
    success = convert_real_roi_to_v2()

    if success:
        print("\n✓ 转换成功!")
        print("真实的v1 ROI数据已转换为v2格式")
        print("坐标格式: [x, y, width, height]")
        print("现在可以在ModuleEX和Module1中正确显示ROI了")
    else:
        print("\n✗ 转换失败!")
