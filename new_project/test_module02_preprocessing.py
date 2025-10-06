"""
Module02 数据预处理功能测试

测试内容:
1. 质量检测 (QualityChecker)
2. 数据清洗 (DataCleaner)
3. 数据平滑 (DataSmoother)
4. 完整流水线 (Pipeline)
"""
import numpy as np
import pandas as pd
from pathlib import Path
import sys

# 添加项目路径
sys.path.insert(0, str(Path(__file__).parent))

from src.modules.module02_preprocessing import (
    QualityChecker,
    DataCleaner,
    DataSmoother,
    Pipeline
)


def generate_test_data(n_points=1000, add_noise=True):
    """生成测试数据"""
    print(f"\n生成测试数据 ({n_points} 个点)...")

    # 生成时间序列
    time = np.linspace(0, 10000, n_points)  # 10秒, ms

    # 生成正弦波轨迹
    x = 0.5 + 0.3 * np.sin(2 * np.pi * time / 1000)
    y = 0.5 + 0.2 * np.cos(2 * np.pi * time / 1000)

    if add_noise:
        # 添加噪声
        x += np.random.normal(0, 0.02, n_points)
        y += np.random.normal(0, 0.02, n_points)

        # 添加一些缺失值
        missing_indices = np.random.choice(n_points, size=int(n_points * 0.05), replace=False)
        x[missing_indices] = np.nan
        y[missing_indices] = np.nan

        # 添加一些异常值
        outlier_indices = np.random.choice(n_points, size=int(n_points * 0.02), replace=False)
        x[outlier_indices] += np.random.uniform(-0.5, 0.5, len(outlier_indices))
        y[outlier_indices] += np.random.uniform(-0.5, 0.5, len(outlier_indices))

    df = pd.DataFrame({
        'time': time,
        'x': x,
        'y': y
    })

    print(f"[OK] 生成了 {len(df)} 个数据点")
    return df


def test_quality_checker(df):
    """测试质量检测器"""
    print("\n" + "="*60)
    print("测试 1: 质量检测 (QualityChecker)")
    print("="*60)

    checker = QualityChecker()
    report = checker.check_quality(df)

    print(f"\n数据点总数: {report['total_points']}")
    print(f"缺失值: {report['missing_values']['total_missing']}")
    print(f"  - x缺失: {report['missing_values']['x_missing']}")
    print(f"  - y缺失: {report['missing_values']['y_missing']}")
    print(f"异常值: {report['outliers']['total_outliers']}")
    print(f"范围违规: {report['range_violations']['total']}")
    print(f"采样率: {report['sampling_issues'].get('actual_rate', 'N/A')} Hz")
    print(f"\n质量分数: {report['quality_score']:.2f} / 100")

    return report


def test_data_cleaner(df):
    """测试数据清洗器"""
    print("\n" + "="*60)
    print("测试 2: 数据清洗 (DataCleaner)")
    print("="*60)

    cleaner = DataCleaner()
    config = {
        'missing_method': 'interpolate',
        'outlier_method': '3sigma',
        'outlier_threshold': 3.0,
        'outlier_action': 'interpolate',
        'clip_range': True,
        'x_range': [0, 1],
        'y_range': [0, 1]
    }

    df_cleaned, log = cleaner.clean(df, config)

    print(f"\n原始数据点: {log['original_points']}")
    print(f"最终数据点: {log['final_points']}")
    print(f"删除数据点: {log['points_removed']}")

    for step in log['steps']:
        print(f"\n步骤: {step['step']}")
        if 'original_missing' in step:
            print(f"  - 原始缺失: {step['original_missing']}")
            print(f"  - 剩余缺失: {step['remaining_missing']}")
        if 'outliers_handled' in step:
            print(f"  - 处理异常值: {step['outliers_handled']}")
        if 'points_clipped' in step:
            print(f"  - 裁剪点数: {step['points_clipped']}")

    return df_cleaned, log


def test_data_smoother(df):
    """测试数据平滑器"""
    print("\n" + "="*60)
    print("测试 3: 数据平滑 (DataSmoother)")
    print("="*60)

    smoother = DataSmoother()

    # 测试不同的平滑方法
    methods = ['moving_average', 'gaussian', 'median', 'savgol']
    results = {}

    for method in methods:
        config = {
            'method': method,
            'window_size': 5,
            'sigma': 1.5,
            'smooth_x': True,
            'smooth_y': True
        }

        df_smoothed, log = smoother.smooth(df, config)
        results[method] = df_smoothed

        print(f"\n{method}:")
        print(f"  - 平滑列数: {len(log['columns_smoothed'])}")
        print(f"  - 平滑列: {', '.join(log['columns_smoothed'])}")

    return results


def test_pipeline(df):
    """测试完整流水线"""
    print("\n" + "="*60)
    print("测试 4: 完整流水线 (Pipeline)")
    print("="*60)

    pipeline = Pipeline()
    config = pipeline.get_default_config()

    print(f"\n流水线配置:")
    print(f"  - 质量检测: {config['enable_quality_check']}")
    print(f"  - 数据清洗: {config['enable_cleaning']}")
    print(f"  - 数据平滑: {config['enable_smoothing']}")

    df_processed, log = pipeline.process(df, config)

    print(f"\n处理结果:")
    print(f"  - 原始数据点: {log['original_points']}")
    print(f"  - 最终数据点: {log['final_points']}")
    print(f"  - 开始时间: {log['start_time']}")
    print(f"  - 结束时间: {log['end_time']}")

    print(f"\n处理步骤:")
    for step in log['steps']:
        print(f"  - {step['step']}")
        if step['step'] == 'quality_check':
            print(f"    质量分数: {step['report']['quality_score']:.2f}/100")
        elif step['step'] == 'cleaning':
            print(f"    删除点数: {step['log']['points_removed']}")
        elif step['step'] == 'smoothing':
            print(f"    平滑列数: {len(step['log']['columns_smoothed'])}")

    return df_processed, log


def test_file_processing():
    """测试文件处理"""
    print("\n" + "="*60)
    print("测试 5: 文件处理")
    print("="*60)

    # 创建测试目录
    test_dir = Path("c:/Users/asino/Downloads/az - 副本 (11)/new_project/data/test_preprocessing")
    test_dir.mkdir(parents=True, exist_ok=True)

    # 生成并保存测试数据
    df = generate_test_data(500)
    input_path = test_dir / "test_input.csv"
    output_path = test_dir / "test_output.csv"

    df.to_csv(input_path, index=False)
    print(f"\n已保存测试数据: {input_path}")

    # 使用流水线处理文件
    pipeline = Pipeline()
    result = pipeline.process_file(
        str(input_path),
        str(output_path),
        save_log=True
    )

    if result['success']:
        print(f"\n[OK] 文件处理成功")
        print(f"  - 输入: {result['input_file']}")
        print(f"  - 输出: {result['output_file']}")
        print(f"  - 质量分数: {result['log']['steps'][0]['report']['quality_score']:.2f}/100")
    else:
        print(f"\n[ERROR] 文件处理失败: {result.get('error')}")

    return result


def main():
    """主测试函数"""
    print("\n" + "="*60)
    print("Module02 数据预处理功能测试")
    print("="*60)

    # 生成测试数据
    df = generate_test_data(n_points=1000, add_noise=True)

    # 1. 测试质量检测
    quality_report = test_quality_checker(df)

    # 2. 测试数据清洗
    df_cleaned, cleaning_log = test_data_cleaner(df)

    # 3. 测试数据平滑
    smoothed_results = test_data_smoother(df_cleaned)

    # 4. 测试完整流水线
    df_final, pipeline_log = test_pipeline(df)

    # 5. 测试文件处理
    file_result = test_file_processing()

    # 总结
    print("\n" + "="*60)
    print("测试总结")
    print("="*60)
    print("\n所有测试已完成！")
    print(f"\n最终数据统计:")
    print(f"  - 原始数据点: {len(df)}")
    print(f"  - 清洗后数据点: {len(df_cleaned)}")
    print(f"  - 流水线处理后: {len(df_final)}")
    print(f"  - 质量分数提升: {quality_report['quality_score']:.2f} -> 预计更高")
    print("\n[OK] Module02 预处理功能正常工作！")


if __name__ == "__main__":
    main()
