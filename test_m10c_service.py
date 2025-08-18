#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
模块10-C 服务测试脚本
==================

测试模型服务API的各项功能：
- 模型列表查询
- 模型激活
- 预测接口
- 指标查询
"""

import requests
import json
import time
import numpy as np
from typing import Dict, List

# API基础URL
BASE_URL = "http://127.0.0.1:8080/api/m10"

class M10ServiceTester:
    """模块10-C服务测试器"""
    
    def __init__(self, base_url: str = BASE_URL):
        self.base_url = base_url
        self.session = requests.Session()
        self.session.headers.update({'Content-Type': 'application/json'})
    
    def test_health(self) -> bool:
        """测试健康检查接口"""
        print("\n" + "="*50)
        print("🔍 测试健康检查接口")
        print("="*50)
        
        try:
            response = self.session.get(f"{self.base_url}/predict/health")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 健康检查通过")
                print(f"   状态: {data.get('status')}")
                print(f"   激活模型数: {data.get('active_models_count')}")
                print(f"   时间戳: {data.get('timestamp')}")
                return True
            else:
                print(f"❌ 健康检查失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 健康检查异常: {e}")
            return False
    
    def test_list_models(self) -> bool:
        """测试模型列表查询"""
        print("\n" + "="*50)
        print("📋 测试模型列表查询")
        print("="*50)
        
        try:
            response = self.session.get(f"{self.base_url}/models")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 模型列表查询成功")
                print(f"   发现 {data.get('count', 0)} 个任务")
                
                for model in data.get('models', []):
                    print(f"   📁 {model['q']}: {len(model['versions'])} 个版本")
                    print(f"      签名: {model['sig']}")
                    print(f"      版本: {model['versions']}")
                    print(f"      激活: {model.get('active', 'None')}")
                
                return True
            else:
                print(f"❌ 模型列表查询失败: {response.status_code}")
                print(f"   响应: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 模型列表查询异常: {e}")
            return False
    
    def test_activate_model(self, q_tag: str = "Q1", version: str = "best") -> bool:
        """测试模型激活"""
        print("\n" + "="*50)
        print(f"🔄 测试模型激活: {q_tag} -> {version}")
        print("="*50)
        
        try:
            payload = {
                "q_tag": q_tag,
                "version": version
            }
            
            response = self.session.post(
                f"{self.base_url}/activate",
                data=json.dumps(payload)
            )
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 模型激活成功")
                print(f"   任务: {data.get('q_tag')}")
                print(f"   版本: {data.get('version')}")
                print(f"   签名: {data.get('sig')}")
                return True
            else:
                print(f"❌ 模型激活失败: {response.status_code}")
                print(f"   响应: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 模型激活异常: {e}")
            return False
    
    def test_predict(self, q_tag: str = "Q1") -> bool:
        """测试预测接口"""
        print("\n" + "="*50)
        print(f"🎯 测试预测接口: {q_tag}")
        print("="*50)
        
        try:
            # 生成随机测试特征
            features = np.random.rand(10).tolist()
            
            payload = {
                "q_tag": q_tag,
                "features": features
            }
            
            print(f"📊 输入特征: {[f'{x:.3f}' for x in features[:5]]}...")
            
            start_time = time.time()
            response = self.session.post(
                f"{self.base_url}/predict",
                data=json.dumps(payload)
            )
            end_time = time.time()
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 预测成功")
                print(f"   任务: {data.get('q_tag')}")
                print(f"   分数: {data.get('score'):.4f}")
                print(f"   模型: {data.get('model_info', {}).get('version', 'Unknown')}")
                print(f"   耗时: {(end_time - start_time)*1000:.1f}ms")
                return True
            else:
                print(f"❌ 预测失败: {response.status_code}")
                print(f"   响应: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 预测异常: {e}")
            return False
    
    def test_batch_predict(self, q_tag: str = "Q1", batch_size: int = 3) -> bool:
        """测试批量预测"""
        print("\n" + "="*50)
        print(f"📦 测试批量预测: {q_tag} (批量大小: {batch_size})")
        print("="*50)
        
        try:
            # 生成批量测试数据
            samples = [np.random.rand(10).tolist() for _ in range(batch_size)]
            
            payload = {
                "q_tag": q_tag,
                "samples": samples
            }
            
            print(f"📊 批量大小: {len(samples)}")
            
            start_time = time.time()
            response = self.session.post(
                f"{self.base_url}/predict/batch",
                data=json.dumps(payload)
            )
            end_time = time.time()
            
            if response.status_code == 200:
                data = response.json()
                results = data.get('results', [])
                print(f"✅ 批量预测成功")
                print(f"   任务: {data.get('q_tag')}")
                print(f"   样本数: {data.get('count')}")
                print(f"   成功数: {data.get('success_count')}")
                print(f"   结果: {[f'{r:.3f}' if r else 'None' for r in results]}")
                print(f"   耗时: {(end_time - start_time)*1000:.1f}ms")
                return True
            else:
                print(f"❌ 批量预测失败: {response.status_code}")
                print(f"   响应: {response.text}")
                return False
                
        except Exception as e:
            print(f"❌ 批量预测异常: {e}")
            return False
    
    def test_get_status(self) -> bool:
        """测试状态查询"""
        print("\n" + "="*50)
        print("📊 测试状态查询")
        print("="*50)
        
        try:
            response = self.session.get(f"{self.base_url}/predict/status")
            
            if response.status_code == 200:
                data = response.json()
                print(f"✅ 状态查询成功")
                print(f"   缓存大小: {data.get('cache_size')}")
                print(f"   可用任务: {data.get('available_tasks')}")
                
                active_models = data.get('active_models', {})
                print(f"   激活模型:")
                for q, info in active_models.items():
                    print(f"     {q}: {info.get('version')} ({info.get('sig', 'unknown')})")
                
                return True
            else:
                print(f"❌ 状态查询失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 状态查询异常: {e}")
            return False
    
    def test_metrics(self, q_tag: str = "Q1") -> bool:
        """测试指标查询"""
        print("\n" + "="*50)
        print(f"📈 测试指标查询: {q_tag}")
        print("="*50)
        
        try:
            # 测试指标摘要
            response = self.session.get(f"{self.base_url}/metrics/summary")
            
            if response.status_code == 200:
                data = response.json()
                summary = data.get('summary', {})
                
                print(f"✅ 指标摘要查询成功")
                print(f"   签名: {data.get('sig')}")
                print(f"   版本: {data.get('version')}")
                
                for q, metrics in summary.items():
                    if metrics:
                        print(f"   {q}: RMSE={metrics.get('rmse', 0):.3f}, "
                              f"R²={metrics.get('r2', 0):.3f}, "
                              f"MAE={metrics.get('mae', 0):.3f}")
                    else:
                        print(f"   {q}: 无指标数据")
                
                return True
            else:
                print(f"❌ 指标查询失败: {response.status_code}")
                return False
                
        except Exception as e:
            print(f"❌ 指标查询异常: {e}")
            return False
    
    def run_all_tests(self) -> Dict[str, bool]:
        """运行所有测试"""
        print("🚀 开始模块10-C服务测试")
        print("="*70)
        
        results = {}
        
        # 基础测试
        results['health'] = self.test_health()
        results['list_models'] = self.test_list_models()
        results['status'] = self.test_get_status()
        
        # 如果基础测试通过，进行高级测试
        if results['health'] and results['list_models']:
            results['activate'] = self.test_activate_model()
            
            if results['activate']:
                results['predict'] = self.test_predict()
                results['batch_predict'] = self.test_batch_predict()
            else:
                results['predict'] = False
                results['batch_predict'] = False
        else:
            results['activate'] = False
            results['predict'] = False
            results['batch_predict'] = False
        
        # 指标测试（独立）
        results['metrics'] = self.test_metrics()
        
        # 测试结果汇总
        print("\n" + "="*70)
        print("📋 测试结果汇总")
        print("="*70)
        
        passed_count = sum(results.values())
        total = len(results)
        
        for test_name, test_passed in results.items():
            status = "✅ 通过" if test_passed else "❌ 失败"
            print(f"   {test_name:15}: {status}")
        
        print(f"\n🎯 总体结果: {passed_count}/{total} 项测试通过")
        
        if passed_count == total:
            print("🎉 所有测试通过！模块10-C服务运行正常")
        else:
            print("⚠️  部分测试失败，请检查服务状态")
        
        return results

def main():
    """主函数"""
    import argparse
    
    parser = argparse.ArgumentParser(description="模块10-C服务测试")
    parser.add_argument('--url', default=BASE_URL, help='API基础URL')
    parser.add_argument('--test', choices=['all', 'health', 'predict', 'models'], 
                       default='all', help='运行特定测试')
    
    args = parser.parse_args()
    
    tester = M10ServiceTester(args.url)
    
    if args.test == 'all':
        tester.run_all_tests()
    elif args.test == 'health':
        tester.test_health()
    elif args.test == 'predict':
        tester.test_activate_model()
        tester.test_predict()
    elif args.test == 'models':
        tester.test_list_models()

if __name__ == "__main__":
    main()