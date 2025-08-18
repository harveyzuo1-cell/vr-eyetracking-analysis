"""
模块10 Eye-Index 综合评估 - Flask API Blueprint
提供S_eye计算、数据获取、报告生成的后端接口
包含子模块10-A: 数据准备构建器
"""

import os
import json
import pandas as pd
import sys
from pathlib import Path
from flask import Blueprint, request, jsonify, send_file

# 添加backend目录到Python路径
backend_path = Path(__file__).parent.parent.parent / "backend"
if str(backend_path) not in sys.path:
    sys.path.insert(0, str(backend_path))
try:
    from .utils import (
        compute_s_eye, 
        eye_index_report, 
        save_dataset_with_s_eye, 
        save_report,
        EYE_FEATURES,
        MMSE_FEATURES
    )
except ImportError:
    # 尝试绝对导入
    from visualization.module10_eye_index.utils import (
        compute_s_eye, 
        eye_index_report, 
        save_dataset_with_s_eye, 
        save_report,
        EYE_FEATURES,
        MMSE_FEATURES
    )

# 创建Blueprint
bp = Blueprint("eye_index", __name__, url_prefix="/api/eye-index")

@bp.route("/run", methods=["POST"])
def run_eye_index():
    """
    执行Eye-Index综合评估计算
    
    Request JSON:
    {
        "config_name": "m2_tau1_eps0.05_lmin2",
        "mode": "equal|pca|custom", 
        "weights": [0.1, 0.1, ...] (可选，仅mode=custom时使用)
    }
    """
    try:
        data = request.get_json()
        
        # 获取参数
        config_name = data.get("config_name")
        mode = data.get("mode", "equal")
        weights = data.get("weights")
        
        if not config_name:
            return jsonify({
                "success": False,
                "error": "缺少必要参数: config_name"
            }), 400
        
        print(f"🚀 开始Eye-Index计算: {config_name}, 模式: {mode}")
        
        # 读取模块9.1的数据
        source_file = os.path.join("data", "module9_ml_results", config_name, "train_dataset_latest.csv")
        
        # 如果最新文件不存在，尝试查找其他train_dataset文件
        if not os.path.exists(source_file):
            data_dir = os.path.join("data", "module9_ml_results", config_name)
            if os.path.exists(data_dir):
                csv_files = [f for f in os.listdir(data_dir) if f.startswith("train_dataset") and f.endswith(".csv")]
                if csv_files:
                    source_file = os.path.join(data_dir, sorted(csv_files)[-1])  # 取最新的
                    print(f"📁 使用文件: {sorted(csv_files)[-1]}")
        
        if not os.path.exists(source_file):
            return jsonify({
                "success": False,
                "error": f"数据源文件不存在: {source_file}。请先运行模块9.1数据预处理。"
            }), 404
        
        # 读取数据
        df = pd.read_csv(source_file)
        print(f"📊 加载数据: {len(df)} 行, {len(df.columns)} 列")
        
        # 检查必要特征
        available_eye_features = [feat for feat in EYE_FEATURES if feat in df.columns]
        available_mmse_features = [feat for feat in MMSE_FEATURES if feat in df.columns]
        
        print(f"👁️ 可用眼动特征: {len(available_eye_features)}/{len(EYE_FEATURES)}")
        print(f"🧠 可用MMSE特征: {len(available_mmse_features)}/{len(MMSE_FEATURES)}")
        
        if len(available_eye_features) == 0:
            return jsonify({
                "success": False,
                "error": "数据中不包含任何眼动特征，请检查数据源"
            }), 400
        
        # 计算S_eye
        df_with_s_eye = compute_s_eye(df, mode=mode, weights=weights)
        
        # 创建输出目录
        output_dir = os.path.join("data", "module10_eye_index", config_name)
        os.makedirs(output_dir, exist_ok=True)
        
        # 保存数据集
        dataset_path = os.path.join(output_dir, "eye_index_dataset.csv")
        save_dataset_with_s_eye(df_with_s_eye, dataset_path)
        
        # 生成报告
        report = eye_index_report(df_with_s_eye)
        report_path = os.path.join(output_dir, "eye_index_report.json")
        save_report(report, report_path)
        
        # 返回成功结果
        return jsonify({
            "success": True,
            "message": f"Eye-Index计算完成",
            "stats": report["overall"]["stats"],
            "correlations": report["overall"]["correlations"],
            "metadata": {
                "total_subjects": len(df_with_s_eye),
                "eye_features_count": len(available_eye_features),
                "mmse_features_count": len(available_mmse_features),
                "mode": mode,
                "output_dir": output_dir
            }
        })
        
    except Exception as e:
        print(f"❌ Eye-Index计算失败: {str(e)}")
        import traceback
        traceback.print_exc()
        
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@bp.route("/dataset", methods=["GET"])
def get_dataset():
    """
    获取Eye-Index数据集CSV文件
    
    Query Parameters:
        config: RQA配置名称
    """
    try:
        config_name = request.args.get("config")
        if not config_name:
            return jsonify({"error": "缺少参数: config"}), 400
        
        file_path = os.path.join("data", "module10_eye_index", config_name, "eye_index_dataset.csv")
        
        if not os.path.exists(file_path):
            return jsonify({"error": f"数据集文件不存在: {file_path}"}), 404
        
        return send_file(file_path, as_attachment=True, download_name=f"eye_index_dataset_{config_name}.csv")
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route("/report", methods=["GET"])
def get_report():
    """
    获取Eye-Index分析报告JSON
    
    Query Parameters:
        config: RQA配置名称
    """
    try:
        config_name = request.args.get("config")
        if not config_name:
            return jsonify({"error": "缺少参数: config"}), 400
        
        file_path = os.path.join("data", "module10_eye_index", config_name, "eye_index_report.json")
        
        if not os.path.exists(file_path):
            return jsonify({"error": f"报告文件不存在: {file_path}"}), 404
        
        with open(file_path, 'r', encoding='utf-8') as f:
            report = json.load(f)
        
        return jsonify(report)
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500

@bp.route("/data", methods=["GET"])
def get_data():
    """
    获取Eye-Index数据用于前端图表展示
    
    Query Parameters:
        config: RQA配置名称
    """
    try:
        config_name = request.args.get("config")
        if not config_name:
            return jsonify({"error": "缺少参数: config"}), 400
        
        # 读取数据集
        file_path = os.path.join("data", "module10_eye_index", config_name, "eye_index_dataset.csv")
        
        if not os.path.exists(file_path):
            return jsonify({"error": f"数据集文件不存在: {file_path}"}), 404
        
        df = pd.read_csv(file_path)
        
        # 准备前端展示数据
        chart_data = {
            "subjects": df["Subject_ID"].tolist() if "Subject_ID" in df.columns else [],
            "s_eye": df["S_eye"].tolist() if "S_eye" in df.columns else [],
            "s_eye_z": df["S_eye_z"].tolist() if "S_eye_z" in df.columns else [],
            "groups": df["Group_Type"].tolist() if "Group_Type" in df.columns else [],
            "mmse_scores": {}
        }
        
        # 添加MMSE子分数数据
        for mmse_feat in MMSE_FEATURES:
            if mmse_feat in df.columns:
                chart_data["mmse_scores"][mmse_feat] = df[mmse_feat].tolist()
        
        # 添加组别统计
        group_stats = {}
        if "Group_Type" in df.columns and "S_eye" in df.columns:
            for group in ["control", "mci", "ad"]:
                group_data = df[df["Group_Type"] == group]["S_eye"]
                if len(group_data) > 0:
                    group_stats[group] = {
                        "values": group_data.tolist(),
                        "mean": float(group_data.mean()),
                        "std": float(group_data.std()),
                        "median": float(group_data.median()),
                        "q1": float(group_data.quantile(0.25)),
                        "q3": float(group_data.quantile(0.75)),
                        "count": int(len(group_data))
                    }
        
        chart_data["group_stats"] = group_stats
        
        return jsonify({
            "success": True,
            "data": chart_data
        })
        
    except Exception as e:
        print(f"❌ 获取图表数据失败: {str(e)}")
        return jsonify({"error": str(e)}), 500

@bp.route("/available-configs", methods=["GET"])
def get_available_configs():
    """获取可用的Eye-Index配置列表"""
    try:
        base_dir = os.path.join("data", "module10_eye_index")
        configs = []
        
        if os.path.exists(base_dir):
            for item in os.listdir(base_dir):
                item_path = os.path.join(base_dir, item)
                if os.path.isdir(item_path):
                    # 检查是否包含必要文件
                    dataset_file = os.path.join(item_path, "eye_index_dataset.csv")
                    report_file = os.path.join(item_path, "eye_index_report.json")
                    
                    config_info = {
                        "name": item,
                        "has_dataset": os.path.exists(dataset_file),
                        "has_report": os.path.exists(report_file)
                    }
                    
                    if config_info["has_dataset"]:
                        # 读取基本信息
                        try:
                            df = pd.read_csv(dataset_file)
                            config_info["subject_count"] = len(df)
                            config_info["has_s_eye"] = "S_eye" in df.columns
                        except:
                            config_info["subject_count"] = 0
                            config_info["has_s_eye"] = False
                    
                    configs.append(config_info)
        
        return jsonify({
            "success": True,
            "configs": configs
        })
        
    except Exception as e:
        return jsonify({"error": str(e)}), 500


# ================= 子模块10-A: 数据准备构建器API =================

@bp.route("/build-dataset", methods=["POST"])
def build_dataset():
    """
    构建特征数据集 (子模块10-A)
    
    Request JSON:
    {
        "rqa_config": "m2_tau1_eps0.06_lmin2",
        "val_split": 0.2,
        "random_state": 42
    }
    """
    try:
        data = request.get_json()
        rqa_config = data.get("rqa_config")
        val_split = data.get("val_split", 0.2)
        random_state = data.get("random_state", 42)
        
        if not rqa_config:
            return jsonify({"error": "缺少rqa_config参数"}), 400
        
        # 导入构建器
        try:
            from m10_data_prep import FeatureBuilder
        except ImportError as e:
            return jsonify({"error": f"无法导入FeatureBuilder: {str(e)}"}), 500
        
        # 创建构建器实例
        builder = FeatureBuilder(
            rqa_sig=rqa_config,
            val_split=val_split,
            random_state=random_state
        )
        
        # 执行构建
        meta = builder.run_all()
        
        return jsonify({
            "success": True,
            "message": "数据集构建完成",
            "meta": meta,
            "output_dir": str(builder.output_dir)
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@bp.route("/check-prerequisites", methods=["POST"])
def check_prerequisites():
    """
    检查构建数据集的前置条件
    
    Request JSON:
    {
        "rqa_config": "m2_tau1_eps0.06_lmin2"
    }
    """
    try:
        data = request.get_json()
        rqa_config = data.get("rqa_config")
        
        if not rqa_config:
            return jsonify({"error": "缺少rqa_config参数"}), 400
        
        # 导入构建器
        try:
            from m10_data_prep import FeatureBuilder
        except ImportError as e:
            return jsonify({"error": f"无法导入FeatureBuilder: {str(e)}"}), 500
        
        # 创建构建器实例并检查前置条件
        builder = FeatureBuilder(rqa_sig=rqa_config)
        prereq_report = builder.check_prerequisites()
        
        return jsonify({
            "success": True,
            "report": prereq_report
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


@bp.route("/dataset-status", methods=["GET"])
def dataset_status():
    """
    获取已构建数据集的状态信息
    """
    try:
        # 导入设置
        try:
            from m10_data_prep.settings import MODULE10_ROOT, FILE_PATTERNS
        except ImportError as e:
            return jsonify({"error": f"无法导入设置: {str(e)}"}), 500
        
        datasets = []
        
        # 扫描模块10输出目录
        if MODULE10_ROOT.exists():
            for config_dir in MODULE10_ROOT.iterdir():
                if config_dir.is_dir():
                    meta_file = config_dir / FILE_PATTERNS["module10_meta"]
                    
                    if meta_file.exists():
                        try:
                            with open(meta_file, 'r', encoding='utf-8') as f:
                                meta = json.load(f)
                            
                            # 检查数据文件是否存在
                            task_files = {}
                            for task_id in ["Q1", "Q2", "Q3", "Q4", "Q5"]:
                                task_file = config_dir / FILE_PATTERNS["module10_task"].format(task_id=task_id)
                                task_files[task_id] = task_file.exists()
                            
                            dataset_info = {
                                "rqa_sig": meta.get("rqa_sig", config_dir.name),
                                "generated_at": meta.get("generated_at"),
                                "samples": meta.get("samples", {}),
                                "val_split": meta.get("val_split", 0.2),
                                "task_files": task_files,
                                "output_dir": str(config_dir),
                                "total_samples": sum(meta.get("samples", {}).values())
                            }
                            
                            datasets.append(dataset_info)
                            
                        except Exception as e:
                            # 跳过有问题的配置
                            continue
        
        return jsonify({
            "success": True,
            "datasets": datasets
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500


# 注册Blueprint的函数
def register_eye_index_routes(app):
    """注册Eye-Index相关的API路由"""
    app.register_blueprint(bp)
    print("✅ 模块10 Eye-Index API路由已注册")