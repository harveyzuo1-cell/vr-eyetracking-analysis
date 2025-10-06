"""
将老项目的ROI配置转换为新架构JSON格式

老代码坐标格式: (name, x_min, y_max, x_max, y_min) - OpenCV坐标系 (Y轴倒置)
新架构格式: {x, y, width, height} - Plotly坐标系 (Y轴正向)
"""
import json
from pathlib import Path

# 老代码的完整ROI定义 (从提供的代码中提取)
OLD_ROI_CONFIG = {
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

# 任务名称映射
TASK_NAMES = {
    "q1": "时间定向",
    "q2": "空间定向",
    "q3": "即刻记忆",
    "q4": "注意力与计算",
    "q5": "延迟回忆"
}

# 颜色方案
COLORS = {
    "keyword": "#FF6B6B",      # 红色 - 关键词
    "instruction": "#FFA500",  # 橙色 - 指令
    "background": "#87CEEB"    # 浅蓝 - 背景
}


def convert_opencv_to_plotly(x_min, y_max, x_max, y_min):
    """
    OpenCV坐标 -> Plotly坐标

    老代码 (OpenCV):
        原点在左上角, Y轴向下
        格式: (x_min, y_max, x_max, y_min)

    新架构 (Plotly):
        原点在左下角, Y轴向上
        格式: (x, y, width, height)

    Args:
        x_min: OpenCV的x最小值
        y_max: OpenCV的y最大值 (屏幕坐标越往下越大)
        x_max: OpenCV的x最大值
        y_min: OpenCV的y最小值

    Returns:
        (x, y, width, height): Plotly坐标
    """
    # X轴保持不变
    x = x_min
    width = x_max - x_min

    # Y轴需要翻转: Plotly的y是从底部开始的
    # OpenCV的y_max是屏幕上方，对应Plotly的较小值
    # OpenCV的y_min是屏幕下方，对应Plotly的较大值
    y = 1 - y_max  # Plotly的y_min
    height = y_max - y_min  # 高度保持正值

    return round(x, 4), round(y, 4), round(width, 4), round(height, 4)


def convert_region_list(region_list, region_type):
    """
    转换一组ROI区域

    Args:
        region_list: [(name, x_min, y_max, x_max, y_min), ...]
        region_type: "keyword" | "instruction" | "background"

    Returns:
        List of region dicts
    """
    converted = []
    priority_map = {"keyword": 2, "instruction": 1, "background": 0}

    for i, (name, x_min, y_max, x_max, y_min) in enumerate(region_list):
        x, y, width, height = convert_opencv_to_plotly(x_min, y_max, x_max, y_min)

        # 提取ID (移除前缀 "KW_n2q1_1" -> "KW_q1_1")
        roi_id = name.replace("n2", "")

        converted.append({
            "id": roi_id,
            "name": name,
            "type": region_type,
            "x": x,
            "y": y,
            "width": width,
            "height": height,
            "color": COLORS[region_type],
            "priority": priority_map[region_type]
        })

    return converted


def convert_roi_config(old_config, version="v1"):
    """
    主转换函数

    Args:
        old_config: 老代码的ROI配置字典
        version: 目标版本 (v1/v2)

    Returns:
        新架构的ROI配置字典
    """
    new_config = {
        "version": version,
        "layout": "legacy" if version == "v1" else "new",
        "coordinate_system": "plotly",
        "description": f"从老项目ROI配置转换 (版本{version})",
        "created_date": "2025-10-02",
        "conversion_notes": [
            "坐标系已从OpenCV (Y轴倒置) 转换为Plotly (Y轴正向)",
            "优先级: keywords(2) > instructions(1) > background(0)",
            "匹配规则: 先匹配高优先级区域"
        ],
        "tasks": {}
    }

    # 转换每个任务
    for task_key, roi_def in old_config.items():
        # task_key = "n2q1" => qid = "q1"
        qid = task_key.replace("n2", "")

        task_config = {
            "task_id": qid,
            "task_name": TASK_NAMES.get(qid, f"任务{qid}"),
            "background_image": f"{qid.upper()}.jpg",
            "regions": {
                "keywords": convert_region_list(roi_def["keywords"], "keyword"),
                "instructions": convert_region_list(roi_def["instructions"], "instruction"),
                "background": convert_region_list(roi_def["background"], "background")
            }
        }

        new_config["tasks"][qid] = task_config

    # 添加元数据统计
    new_config["metadata"] = {
        "total_tasks": len(new_config["tasks"]),
        "total_subjects": 65 if version == "v1" else 94,
        "groups": {
            "control": 22 if version == "v1" else 31,
            "mci": 22 if version == "v1" else 32,
            "ad": 21 if version == "v1" else 31
        },
        "data_period": "2025-01" if version == "v1" else "2025-02",
        "source": "old_roi_config.py"
    }

    return new_config


def validate_config(config):
    """
    验证转换后的配置

    Returns:
        (bool, List[str]): (是否有效, 错误信息列表)
    """
    errors = []

    if not config.get("tasks"):
        errors.append("配置中没有任务定义")
        return False, errors

    for task_id, task_config in config["tasks"].items():
        # 检查必需字段
        if not task_config.get("task_name"):
            errors.append(f"任务{task_id}缺少task_name")

        regions = task_config.get("regions", {})

        # 验证每个区域的坐标范围
        for region_type in ["keywords", "instructions", "background"]:
            for region in regions.get(region_type, []):
                x, y, w, h = region["x"], region["y"], region["width"], region["height"]

                # 坐标应在[0, 1]范围内
                if not (0 <= x <= 1 and 0 <= y <= 1):
                    errors.append(f"{task_id}/{region['id']}: 坐标超出范围 x={x}, y={y}")

                # 宽高应为正值
                if w <= 0 or h <= 0:
                    errors.append(f"{task_id}/{region['id']}: 宽高无效 w={w}, h={h}")

                # x+width 和 y+height 不应超过1
                if x + w > 1.001 or y + h > 1.001:  # 允许微小误差
                    errors.append(f"{task_id}/{region['id']}: 区域超出边界 x+w={x+w}, y+h={y+h}")

    return len(errors) == 0, errors


def main():
    """主函数"""
    print("=" * 60)
    print("ROI配置转换工具")
    print("=" * 60)

    # 转换配置
    print("\n[1/4] 转换ROI配置...")
    new_config = convert_roi_config(OLD_ROI_CONFIG, version="v1")
    print(f"  ✓ 成功转换 {len(new_config['tasks'])} 个任务")

    # 统计信息
    total_regions = sum(
        len(task["regions"]["keywords"]) +
        len(task["regions"]["instructions"]) +
        len(task["regions"]["background"])
        for task in new_config["tasks"].values()
    )
    print(f"  ✓ 总共 {total_regions} 个ROI区域")

    # 验证配置
    print("\n[2/4] 验证配置完整性...")
    is_valid, errors = validate_config(new_config)

    if not is_valid:
        print("  ✗ 配置验证失败:")
        for error in errors:
            print(f"    - {error}")
        return
    else:
        print("  ✓ 配置验证通过")

    # 保存配置
    print("\n[3/4] 保存配置文件...")
    project_root = Path(__file__).parent.parent
    output_path = project_root / "config" / "roi_v1_enhanced.json"

    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(new_config, f, ensure_ascii=False, indent=2)

    print(f"  ✓ 已保存到: {output_path}")

    # 输出示例
    print("\n[4/4] 配置预览 (Q1任务):")
    q1_config = new_config["tasks"]["q1"]
    print(f"  任务名称: {q1_config['task_name']}")
    print(f"  背景图片: {q1_config['background_image']}")
    print(f"  关键词区域: {len(q1_config['regions']['keywords'])} 个")
    print(f"  指令区域: {len(q1_config['regions']['instructions'])} 个")

    print("\n  第一个关键词区域:")
    if q1_config['regions']['keywords']:
        kw1 = q1_config['regions']['keywords'][0]
        print(f"    ID: {kw1['id']}")
        print(f"    名称: {kw1['name']}")
        print(f"    坐标: x={kw1['x']}, y={kw1['y']}, w={kw1['width']}, h={kw1['height']}")
        print(f"    颜色: {kw1['color']}")
        print(f"    优先级: {kw1['priority']}")

    print("\n" + "=" * 60)
    print("✅ ROI配置转换完成!")
    print("=" * 60)

    print("\n下一步:")
    print("  1. 检查生成的 config/roi_v1_enhanced.json")
    print("  2. 运行后端服务测试新API")
    print("  3. 前端集成新配置")


if __name__ == "__main__":
    main()
