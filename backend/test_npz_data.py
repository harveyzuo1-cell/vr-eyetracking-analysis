"""
直接测试NPZ数据表格化功能
"""

import sys
import json
from pathlib import Path

# 添加当前目录到Python路径
sys.path.append('.')

def test_npz_data_functionality():
    """测试NPZ数据表格化功能"""
    print("🚀 测试NPZ数据表格化功能...")
    
    try:
        # 导入数据表格服务
        from m10_service.data_table import DataTableService
        print("✅ DataTableService导入成功")
        
        # 检查数据集目录
        data_root = Path("../data/module10_datasets")
        print(f"📁 数据集根目录: {data_root.absolute()}")
        
        if not data_root.exists():
            print("❌ 数据集目录不存在")
            # 检查expert_demo目录中的数据
            demo_data_root = Path("expert_demo/data")
            if demo_data_root.exists():
                print(f"📁 找到演示数据目录: {demo_data_root.absolute()}")
                # 列出可用的RQA配置
                for rqa_dir in demo_data_root.iterdir():
                    if rqa_dir.is_dir():
                        print(f"  RQA配置: {rqa_dir.name}")
                        # 列出NPZ文件
                        for npz_file in rqa_dir.glob("*.npz"):
                            print(f"    NPZ文件: {npz_file.name}")
                            
                            # 测试数据转换
                            try:
                                result = DataTableService.npz_to_dataframe(str(npz_file), include_predictions=False)
                                print(f"    ✅ 转换成功: {result['total_samples']}个样本, {len(result['feature_names'])}个特征")
                                
                                # 显示摘要统计
                                stats = result['summary_stats']
                                print(f"    📊 MMSE均值: {stats['mmse_stats']['mean']:.4f}")
                                print(f"    📊 数据质量分布: {stats['quality_distribution']}")
                                
                            except Exception as e:
                                print(f"    ❌ 转换失败: {e}")
            else:
                print("❌ 没有找到任何数据目录")
            return
        
        # 测试主数据集目录
        print("📋 搜索可用的数据集...")
        found_data = False
        
        for rqa_dir in data_root.iterdir():
            if not rqa_dir.is_dir():
                continue
                
            print(f"🔍 检查RQA配置: {rqa_dir.name}")
            
            for q_tag in ["Q1", "Q2", "Q3", "Q4", "Q5"]:
                npz_file = rqa_dir / f"{q_tag}.npz"
                if npz_file.exists():
                    found_data = True
                    print(f"  ✅ 找到数据文件: {npz_file}")
                    
                    # 测试数据转换
                    try:
                        result = DataTableService.npz_to_dataframe(str(npz_file), include_predictions=False)
                        print(f"    ✅ 转换成功: {result['total_samples']}个样本")
                        
                        # 测试分页
                        paginated = DataTableService.paginate_data(result, page=1, page_size=10)
                        print(f"    ✅ 分页测试成功: 第1页显示{len(paginated['table_data'])}条记录")
                        
                        # 测试CSV转换
                        csv_data = DataTableService.to_csv(result)
                        print(f"    ✅ CSV转换成功: {len(csv_data)}字符")
                        
                        # 只测试第一个文件就够了
                        break
                        
                    except Exception as e:
                        print(f"    ❌ 转换失败: {e}")
                        
        if not found_data:
            print("❌ 没有找到可用的NPZ数据文件")
            return
            
        print("\n🎉 NPZ数据表格化功能测试完成！")
        
    except Exception as e:
        print(f"❌ 测试失败: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_npz_data_functionality()

