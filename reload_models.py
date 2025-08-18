#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
重新加载模型
===========

清理缓存并重新加载更新后的模型。
"""

import requests
import json

BASE_URL = "http://127.0.0.1:8080/api/m10"

def clear_cache():
    """清理模型缓存"""
    print("🗑️ 清理模型缓存...")
    
    try:
        response = requests.post(f"{BASE_URL}/cache/clear")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 缓存清理成功，清理了 {data.get('cleared_count')} 个模型")
            return True
        else:
            print(f"❌ 缓存清理失败: {response.status_code}")
            print(f"   响应: {response.text}")
            return False
            
    except Exception as e:
        print(f"❌ 缓存清理异常: {e}")
        return False

def activate_models():
    """重新激活所有模型"""
    print("🔄 重新激活所有模型...")
    
    for q_tag in ["Q1", "Q2", "Q3", "Q4", "Q5"]:
        try:
            payload = {
                "q_tag": q_tag,
                "version": "best"
            }
            
            response = requests.post(
                f"{BASE_URL}/activate",
                headers={'Content-Type': 'application/json'},
                data=json.dumps(payload)
            )
            
            if response.status_code == 200:
                print(f"   ✅ {q_tag} 已重新激活")
            else:
                print(f"   ❌ {q_tag} 激活失败: {response.status_code}")
                
        except Exception as e:
            print(f"   ❌ {q_tag} 激活异常: {e}")

def test_new_prediction():
    """测试新模型的预测"""
    print("🧪 测试新模型预测...")
    
    payload = {
        "q_tag": "Q1",
        "features": [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0]
    }
    
    try:
        response = requests.post(
            f"{BASE_URL}/predict",
            headers={'Content-Type': 'application/json'},
            data=json.dumps(payload)
        )
        
        if response.status_code == 200:
            data = response.json()
            score = data.get('score')
            print(f"✅ 新模型预测成功: {score}")
            
            if score != 0.0:
                print(f"🎉 模型现在输出有意义的值!")
                return True
            else:
                print(f"⚠️  模型仍然输出0.0")
                return False
        else:
            print(f"❌ 预测失败: {response.status_code}")
            return False
            
    except Exception as e:
        print(f"❌ 预测异常: {e}")
        return False

if __name__ == "__main__":
    print("🚀 开始重新加载模型...")
    
    # 1. 清理缓存
    cache_cleared = clear_cache()
    
    # 2. 重新激活模型
    if cache_cleared:
        activate_models()
        
        # 3. 测试新模型
        test_new_prediction()
    
    print("\n✅ 模型重新加载完成!")