#!/usr/bin/env python3
"""
模块10-B: CLI训练入口
====================================

命令行界面，用于启动单个Q任务的模型训练。

使用示例:
    python -m m10_training.run_train --rqa_config m2_tau1_eps0.055_lmin2 --q_tag Q1
    python -m m10_training.run_train --rqa_config m2_tau1_eps0.055_lmin2 --q_tag Q3 --override '{"training":{"epochs":600}}'
"""

import argparse
import json
import sys
import logging
from pathlib import Path
from typing import Dict, Any, Optional

# 添加项目根目录到路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from backend.m10_training.trainer import create_trainer_from_config, deep_update


def setup_logging(verbose: bool = False):
    """
    设置日志配置
    
    Args:
        verbose: 是否显示详细日志
    """
    level = logging.DEBUG if verbose else logging.INFO
    
    logging.basicConfig(
        level=level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S'
    )
    
    # 设置第三方库的日志级别
    logging.getLogger('matplotlib').setLevel(logging.WARNING)
    logging.getLogger('PIL').setLevel(logging.WARNING)


def parse_arguments() -> argparse.Namespace:
    """
    解析命令行参数
    
    Returns:
        解析后的参数命名空间
    """
    parser = argparse.ArgumentParser(
        description="模块10-B: PyTorch MLP训练器",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
使用示例:
  # 基础训练
  python -m m10_training.run_train --rqa_config m2_tau1_eps0.055_lmin2 --q_tag Q1
  
  # 自定义参数
  python -m m10_training.run_train \\
    --rqa_config m2_tau1_eps0.055_lmin2 \\
    --q_tag Q3 \\
    --override '{"training":{"epochs":600,"lr":0.001},"arch":{"h1":64}}'
  
  # 指定GPU
  python -m m10_training.run_train \\
    --rqa_config m2_tau1_eps0.055_lmin2 \\
    --q_tag Q1 \\
    --device cuda:0
  
  # 详细输出
  python -m m10_training.run_train \\
    --rqa_config m2_tau1_eps0.055_lmin2 \\
    --q_tag Q1 \\
    --verbose
        """
    )
    
    # 必需参数
    parser.add_argument(
        "--rqa_config",
        type=str,
        required=True,
        help="RQA配置签名，如 m2_tau1_eps0.055_lmin2"
    )
    
    parser.add_argument(
        "--q_tag",
        type=str,
        required=True,
        choices=["Q1", "Q2", "Q3", "Q4", "Q5"],
        help="MMSE子任务标签"
    )
    
    # 可选参数
    parser.add_argument(
        "--config",
        type=str,
        default=None,
        help="配置文件路径 (默认: backend/m10_training/config.yaml)"
    )
    
    parser.add_argument(
        "--override",
        type=str,
        default=None,
        help="JSON字符串，用于覆盖配置文件中的参数"
    )
    
    parser.add_argument(
        "--device",
        type=str,
        default=None,
        help="计算设备 (cpu, cuda, cuda:0 等)"
    )
    
    parser.add_argument(
        "--data_root",
        type=str,
        default="data/module10_datasets",
        help="数据集根目录"
    )
    
    parser.add_argument(
        "--output_dir",
        type=str,
        default=None,
        help="输出目录 (默认使用配置文件中的设置)"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="显示详细日志"
    )
    
    parser.add_argument(
        "--dry_run",
        action="store_true",
        help="仅验证配置，不实际训练"
    )
    
    return parser.parse_args()


def validate_arguments(args: argparse.Namespace) -> bool:
    """
    验证命令行参数
    
    Args:
        args: 解析后的参数
        
    Returns:
        是否验证通过
    """
    errors = []
    
    # 检查数据集文件是否存在
    data_path = Path(args.data_root) / args.rqa_config / f"{args.q_tag}.npz"
    if not data_path.exists():
        errors.append(f"数据集文件不存在: {data_path}")
    
    # 检查配置文件是否存在
    if args.config:
        config_path = Path(args.config)
        if not config_path.exists():
            errors.append(f"配置文件不存在: {config_path}")
    
    # 验证override JSON格式
    if args.override:
        try:
            json.loads(args.override)
        except json.JSONDecodeError as e:
            errors.append(f"override参数JSON格式错误: {str(e)}")
    
    # 检查设备格式
    if args.device and not args.device.startswith(("cpu", "cuda")):
        errors.append(f"无效的设备格式: {args.device}")
    
    if errors:
        for error in errors:
            print(f"❌ 错误: {error}", file=sys.stderr)
        return False
    
    return True


def load_and_merge_config(args: argparse.Namespace) -> Dict[str, Any]:
    """
    加载并合并配置
    
    Args:
        args: 命令行参数
        
    Returns:
        最终配置字典
    """
    # 确定配置文件路径
    if args.config:
        config_path = Path(args.config)
    else:
        config_path = Path(__file__).parent / "config.yaml"
    
    if not config_path.exists():
        raise FileNotFoundError(f"配置文件不存在: {config_path}")
    
    # 加载基础配置
    import yaml
    with open(config_path, 'r', encoding='utf-8') as f:
        config = yaml.safe_load(f)
    
    # 应用命令行参数覆盖
    overrides = {}
    
    if args.device:
        overrides["device"] = args.device
    
    if args.output_dir:
        overrides["save_root"] = args.output_dir
        overrides["log_root"] = str(Path(args.output_dir) / "logs")
    
    # 应用JSON覆盖
    if args.override:
        json_overrides = json.loads(args.override)
        overrides = deep_update(overrides, json_overrides)
    
    # 合并配置
    if overrides:
        config = deep_update(config, overrides)
    
    return config


def print_config_summary(config: Dict[str, Any], args: argparse.Namespace):
    """
    打印配置摘要
    
    Args:
        config: 配置字典
        args: 命令行参数
    """
    print("=" * 60)
    print("🚀 模块10-B: PyTorch MLP训练器")
    print("=" * 60)
    print(f"📋 任务信息:")
    print(f"   RQA配置: {args.rqa_config}")
    print(f"   Q任务: {args.q_tag}")
    print(f"   数据集: {Path(args.data_root) / args.rqa_config / f'{args.q_tag}.npz'}")
    print()
    
    print(f"⚙️  训练配置:")
    training = config.get("training", {})
    print(f"   设备: {config.get('device', 'cpu')}")
    print(f"   批大小: {training.get('batch_size', 16)}")
    print(f"   轮数: {training.get('epochs', 100)}")
    print(f"   学习率: {training.get('lr', 1e-3)}")
    print(f"   验证集比例: {training.get('val_split', 0.2)}")
    print()
    
    print(f"🏗️  模型架构:")
    arch = config.get("arch", {})
    print(f"   输入维度: {arch.get('input_dim', 10)}")
    print(f"   隐藏层1: {arch.get('h1', 32)}")
    print(f"   隐藏层2: {arch.get('h2', 16)}")
    print(f"   Dropout: {arch.get('dropout', 0.25)}")
    print()
    
    print(f"📁 输出路径:")
    print(f"   模型保存: {config.get('save_root', 'models')}")
    print(f"   日志保存: {config.get('log_root', 'logs')}")
    print("=" * 60)


def main():
    """主函数"""
    # 解析参数
    args = parse_arguments()
    
    # 设置日志
    setup_logging(args.verbose)
    logger = logging.getLogger(__name__)
    
    try:
        # 验证参数
        if not validate_arguments(args):
            sys.exit(1)
        
        # 加载配置
        config = load_and_merge_config(args)
        
        # 打印配置摘要
        print_config_summary(config, args)
        
        # 确定数据集路径
        npz_path = Path(args.data_root) / args.rqa_config / f"{args.q_tag}.npz"
        
        if args.dry_run:
            print("✅ 配置验证通过 (dry-run模式)")
            return
        
        # 创建训练器
        logger.info("创建训练器...")
        trainer = create_trainer_from_config(
            config_path=Path(__file__).parent / "config.yaml",
            q_tag=args.q_tag,
            rqa_sig=args.rqa_config,
            override_config=config
        )
        
        # 开始训练
        logger.info("开始训练...")
        result = trainer.fit(npz_path)
        
        # 打印结果
        if result["success"]:
            print()
            print("🎉 训练成功完成!")
            print(f"   训练轮数: {result['epochs_trained']}")
            print(f"   最佳轮数: {result['best_epoch']}")
            print(f"   最佳验证损失: {result['best_val_loss']:.6f}")
            print(f"   总用时: {result['total_time']:.2f}秒")
            print(f"   模型路径: {result['model_path']}")
            
            # 打印最终指标
            final_metrics = result["final_metrics"]
            print()
            print("📊 最终评估指标:")
            for name, value in final_metrics.items():
                print(f"   {name}: {value:.6f}")
            
            print()
            print("✅ 可以使用TensorBoard查看训练过程:")
            print(f"   tensorboard --logdir {config.get('log_root', 'logs')}/{args.rqa_config}/{args.q_tag}")
        else:
            print("❌ 训练失败")
            sys.exit(1)
    
    except KeyboardInterrupt:
        print("\n⚠️ 训练被用户中断")
        sys.exit(1)
    except Exception as e:
        logger.error(f"训练过程出错: {str(e)}")
        if args.verbose:
            import traceback
            traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()