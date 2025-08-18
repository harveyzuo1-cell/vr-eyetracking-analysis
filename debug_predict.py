#!/usr/bin/env python
# -*- coding: utf-8 -*-
"""
调试预测API问题
===============

测试单个和批量预测，找出返回None的原因。
"""

import requests
import json
import numpy as np

BASE_URL = "http://127.0.0.1:8080/api/m10"

def test_single_predict():
    """测试单个预测"""
    print("🔍 测试单个预测...")
    
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
        
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ 单个预测成功: {data.get('score')}")
            return True
        else:
            print(f"❌ 单个预测失败")
            return False
            
    except Exception as e:
        print(f"❌ 单个预测异常: {e}")
        return False

def test_batch_predict():
    """测试批量预测"""
    print("\n🔍 测试批量预测...")
    
    # 创建3个样本，都是10维
    samples = [
        [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],
        [0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 0.1],
        [0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 0.1, 0.2]
    ]
    
    payload = {
        "q_tag": "Q1",
        "samples": samples
    }
    
    print(f"发送样本数: {len(samples)}")
    for i, sample in enumerate(samples):
        print(f"  样本 {i}: 长度={len(sample)}, 前3个值={sample[:3]}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/predict/batch",
            headers={'Content-Type': 'application/json'},
            data=json.dumps(payload)
        )
        
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        
        if response.status_code == 200:
            data = response.json()
            results = data.get('results', [])
            print(f"✅ 批量预测完成")
            print(f"   结果: {results}")
            print(f"   成功数: {data.get('success_count')}")
            
            # 检查是否有None
            none_count = sum(1 for r in results if r is None)
            if none_count > 0:
                print(f"⚠️  发现 {none_count} 个None结果")
                return False
            else:
                print(f"✅ 所有结果都是数值")
                return True
        else:
            print(f"❌ 批量预测失败")
            return False
            
    except Exception as e:
        print(f"❌ 批量预测异常: {e}")
        return False

def test_debug_batch():
    """测试调试模式的批量预测"""
    print("\n🔍 测试调试模式批量预测（包含异常样本）...")
    
    # 故意创建一些有问题的样本
    samples = [
        [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0],  # 正常样本
        [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9],       # 9维，有问题
        [0.1, 0.2, 0.3, 0.4, 0.5, 0.6, 0.7, 0.8, 0.9, 1.0, 1.1]  # 11维，有问题
    ]
    
    payload = {
        "q_tag": "Q1",
        "samples": samples
    }
    
    print(f"发送样本数: {len(samples)}")
    for i, sample in enumerate(samples):
        print(f"  样本 {i}: 长度={len(sample)}")
    
    try:
        response = requests.post(
            f"{BASE_URL}/predict/batch",
            headers={'Content-Type': 'application/json'},
            data=json.dumps(payload)
        )
        
        print(f"状态码: {response.status_code}")
        print(f"响应: {response.text}")
        
    except Exception as e:
        print(f"❌ 调试批量预测异常: {e}")

if __name__ == "__main__":
    print("🚀 开始调试预测API...")
    
    # 测试单个预测
    single_ok = test_single_predict()
    
    # 测试正常批量预测
    batch_ok = test_batch_predict()
    
    # 测试有问题的批量预测
    test_debug_batch()
    
    print("\n📋 调试结果:")
    print(f"   单个预测: {'✅ 正常' if single_ok else '❌ 异常'}")
    print(f"   批量预测: {'✅ 正常' if batch_ok else '❌ 异常'}")
    
    if not batch_ok:
        print("\n💡 问题分析:")
        print("   批量预测返回None可能原因:")
        print("   1. 样本维度不是10")
        print("   2. ModelManager.predict()内部异常")
        print("   3. 特征值格式错误（NaN, 字符串等）")
        print("   4. 模型文件损坏或未正确加载")