"""
MMSE数据API扩展模块
提供MMSE分数数据的API接口，支持第八模块的眼动系数与MMSE对比分析
"""

import pandas as pd
import json
import os
from flask import jsonify, request

def generate_sub_questions(task_id, row):
    """生成子问题详细信息"""
    if task_id == 'Q1':
        return [
            {'sub_question_id': 'Q1_1', 'sub_question_name': '年份', 'sub_question_score': row.get('年份', 0), 'sub_question_max_score': 1, 'sub_question_performance_ratio': row.get('年份', 0) / 1},
            {'sub_question_id': 'Q1_2', 'sub_question_name': '季节', 'sub_question_score': row.get('季节', 0), 'sub_question_max_score': 1, 'sub_question_performance_ratio': row.get('季节', 0) / 1},
            {'sub_question_id': 'Q1_3', 'sub_question_name': '月份', 'sub_question_score': row.get('月份', 0), 'sub_question_max_score': 1, 'sub_question_performance_ratio': row.get('月份', 0) / 1},
            {'sub_question_id': 'Q1_4', 'sub_question_name': '星期', 'sub_question_score': row.get('星期', 0), 'sub_question_max_score': 2, 'sub_question_performance_ratio': row.get('星期', 0) / 2}
        ]
    elif task_id == 'Q2':
        return [
            {'sub_question_id': 'Q2_1', 'sub_question_name': '省市区', 'sub_question_score': row.get('省市区', 0), 'sub_question_max_score': 2, 'sub_question_performance_ratio': row.get('省市区', 0) / 2},
            {'sub_question_id': 'Q2_2', 'sub_question_name': '街道', 'sub_question_score': row.get('街道', 0), 'sub_question_max_score': 1, 'sub_question_performance_ratio': row.get('街道', 0) / 1},
            {'sub_question_id': 'Q2_3', 'sub_question_name': '建筑', 'sub_question_score': row.get('建筑', 0), 'sub_question_max_score': 1, 'sub_question_performance_ratio': row.get('建筑', 0) / 1},
            {'sub_question_id': 'Q2_4', 'sub_question_name': '楼层', 'sub_question_score': row.get('楼层', 0), 'sub_question_max_score': 1, 'sub_question_performance_ratio': row.get('楼层', 0) / 1}
        ]
    elif task_id == 'Q3':
        return [
            {'sub_question_id': 'Q3_1', 'sub_question_name': '即刻记忆', 'sub_question_score': row.get('即刻记忆', 0), 'sub_question_max_score': 3, 'sub_question_performance_ratio': row.get('即刻记忆', 0) / 3}
        ]
    elif task_id == 'Q4':
        return [
            {'sub_question_id': 'Q4_1', 'sub_question_name': '100-7', 'sub_question_score': row.get('100-7', 0), 'sub_question_max_score': 1, 'sub_question_performance_ratio': row.get('100-7', 0) / 1},
            {'sub_question_id': 'Q4_2', 'sub_question_name': '93-7', 'sub_question_score': row.get('93-7', 0), 'sub_question_max_score': 1, 'sub_question_performance_ratio': row.get('93-7', 0) / 1},
            {'sub_question_id': 'Q4_3', 'sub_question_name': '86-7', 'sub_question_score': row.get('86-7', 0), 'sub_question_max_score': 1, 'sub_question_performance_ratio': row.get('86-7', 0) / 1},
            {'sub_question_id': 'Q4_4', 'sub_question_name': '79-7', 'sub_question_score': row.get('79-7', 0), 'sub_question_max_score': 1, 'sub_question_performance_ratio': row.get('79-7', 0) / 1},
            {'sub_question_id': 'Q4_5', 'sub_question_name': '72-7', 'sub_question_score': row.get('72-7', 0), 'sub_question_max_score': 1, 'sub_question_performance_ratio': row.get('72-7', 0) / 1}
        ]
    elif task_id == 'Q5':
        return [
            {'sub_question_id': 'Q5_1', 'sub_question_name': '词1', 'sub_question_score': row.get('词1', 0), 'sub_question_max_score': 1, 'sub_question_performance_ratio': row.get('词1', 0) / 1},
            {'sub_question_id': 'Q5_2', 'sub_question_name': '词2', 'sub_question_score': row.get('词2', 0), 'sub_question_max_score': 1, 'sub_question_performance_ratio': row.get('词2', 0) / 1},
            {'sub_question_id': 'Q5_3', 'sub_question_name': '词3', 'sub_question_score': row.get('词3', 0), 'sub_question_max_score': 1, 'sub_question_performance_ratio': row.get('词3', 0) / 1}
        ]
    else:
        return []

def register_mmse_routes(app):
    """注册MMSE相关的API路由"""
    
    @app.route('/api/mmse-scores/control', methods=['GET'])
    def get_control_mmse_scores():
        """获取控制组MMSE分数"""
        try:
            # 读取控制组MMSE数据
            file_path = os.path.join('data', 'MMSE_Score', '控制组.csv')
            if os.path.exists(file_path):
                df = pd.read_csv(file_path)
                
                # 转换数据格式
                result = []
                for _, row in df.iterrows():
                    if row['受试者'] != '平均' and pd.notna(row['受试者']):
                        # 计算各题目分数
                        q1_score = sum([row.get('年份', 0), row.get('季节', 0), row.get('月份', 0), row.get('星期', 0)])
                        q2_score = sum([row.get('省市区', 0), row.get('街道', 0), row.get('建筑', 0), row.get('楼层', 0)])
                        q3_score = row.get('即刻记忆', 0)
                        q4_score = sum([row.get('100-7', 0), row.get('93-7', 0), row.get('86-7', 0), row.get('79-7', 0), row.get('72-7', 0)])
                        q5_score = sum([row.get('词1', 0), row.get('词2', 0), row.get('词3', 0)])
                        
                        subject_id = row['受试者']
                        
                        # 为每个任务创建记录
                        tasks_scores = [
                            {'task_id': 'Q1', 'mmse_score': q1_score, 'mmse_max_score': 5},
                            {'task_id': 'Q2', 'mmse_score': q2_score, 'mmse_max_score': 5},
                            {'task_id': 'Q3', 'mmse_score': q3_score, 'mmse_max_score': 3},
                            {'task_id': 'Q4', 'mmse_score': q4_score, 'mmse_max_score': 5},
                            {'task_id': 'Q5', 'mmse_score': q5_score, 'mmse_max_score': 3}
                        ]
                        
                        for task in tasks_scores:
                            result.append({
                                'subject_id': subject_id,
                                'task_id': task['task_id'],
                                'mmse_score': task['mmse_score'],
                                'mmse_max_score': task['mmse_max_score'],
                                'performance_ratio': task['mmse_score'] / task['mmse_max_score'],
                                'subQuestions': generate_sub_questions(task['task_id'], row)
                            })

                return jsonify({'success': True, 'data': result})
            else:
                return jsonify({'success': False, 'error': '控制组MMSE数据文件不存在'}), 404
                
        except Exception as e:
            return jsonify({'success': False, 'error': f'读取控制组MMSE数据失败: {str(e)}'}), 500

    @app.route('/api/mmse-scores/mci', methods=['GET'])
    def get_mci_mmse_scores():
        """获取MCI组MMSE分数"""
        try:
            # 读取MCI组MMSE数据
            file_path = os.path.join('data', 'MMSE_Score', '轻度认知障碍组.csv')
            if os.path.exists(file_path):
                df = pd.read_csv(file_path)

                # 转换数据格式（与控制组相同的逻辑）
                result = []
                for _, row in df.iterrows():
                    if row['受试者'] != '平均' and pd.notna(row['受试者']):
                        # 计算各题目分数
                        q1_score = sum([row.get('年份', 0), row.get('季节', 0), row.get('月份', 0), row.get('星期', 0)])
                        q2_score = sum([row.get('省市区', 0), row.get('街道', 0), row.get('建筑', 0), row.get('楼层', 0)])
                        q3_score = row.get('即刻记忆', 0)
                        q4_score = sum([row.get('100-7', 0), row.get('93-7', 0), row.get('86-7', 0), row.get('79-7', 0), row.get('72-7', 0)])
                        q5_score = sum([row.get('词1', 0), row.get('词2', 0), row.get('词3', 0)])

                        subject_id = row['受试者']

                        # 为每个任务创建记录
                        tasks_scores = [
                            {'task_id': 'Q1', 'mmse_score': q1_score, 'mmse_max_score': 5},
                            {'task_id': 'Q2', 'mmse_score': q2_score, 'mmse_max_score': 5},
                            {'task_id': 'Q3', 'mmse_score': q3_score, 'mmse_max_score': 3},
                            {'task_id': 'Q4', 'mmse_score': q4_score, 'mmse_max_score': 5},
                            {'task_id': 'Q5', 'mmse_score': q5_score, 'mmse_max_score': 3}
                        ]

                        for task in tasks_scores:
                            result.append({
                                'subject_id': subject_id,
                                'task_id': task['task_id'],
                                'mmse_score': task['mmse_score'],
                                'mmse_max_score': task['mmse_max_score'],
                                'performance_ratio': task['mmse_score'] / task['mmse_max_score'],
                                'subQuestions': generate_sub_questions(task['task_id'], row)
                            })

                return jsonify({'success': True, 'data': result})
            else:
                return jsonify({'success': False, 'error': 'MCI组MMSE数据文件不存在'}), 404
                
        except Exception as e:
            return jsonify({'success': False, 'error': f'读取MCI组MMSE数据失败: {str(e)}'}), 500

    @app.route('/api/mmse-scores/ad', methods=['GET'])
    def get_ad_mmse_scores():
        """获取AD组MMSE分数"""
        try:
            # 读取AD组MMSE数据
            file_path = os.path.join('data', 'MMSE_Score', '阿尔兹海默症组.csv')
            if os.path.exists(file_path):
                df = pd.read_csv(file_path)

                # 转换数据格式（与控制组相同的逻辑）
                result = []
                for _, row in df.iterrows():
                    # 处理AD组CSV文件第一列名不一致的问题
                    subject_col = '试者' if '试者' in df.columns else '受试者'
                    if row[subject_col] != '平均' and pd.notna(row[subject_col]):
                        # 计算各题目分数
                        q1_score = sum([row.get('年份', 0), row.get('季节', 0), row.get('月份', 0), row.get('星期', 0)])
                        q2_score = sum([row.get('省市区', 0), row.get('街道', 0), row.get('建筑', 0), row.get('楼层', 0)])
                        q3_score = row.get('即刻记忆', 0)
                        q4_score = sum([row.get('100-7', 0), row.get('93-7', 0), row.get('86-7', 0), row.get('79-7', 0), row.get('72-7', 0)])
                        q5_score = sum([row.get('词1', 0), row.get('词2', 0), row.get('词3', 0)])

                        subject_id = row[subject_col]

                        # 为每个任务创建记录
                        tasks_scores = [
                            {'task_id': 'Q1', 'mmse_score': q1_score, 'mmse_max_score': 5},
                            {'task_id': 'Q2', 'mmse_score': q2_score, 'mmse_max_score': 5},
                            {'task_id': 'Q3', 'mmse_score': q3_score, 'mmse_max_score': 3},
                            {'task_id': 'Q4', 'mmse_score': q4_score, 'mmse_max_score': 5},
                            {'task_id': 'Q5', 'mmse_score': q5_score, 'mmse_max_score': 3}
                        ]

                        for task in tasks_scores:
                            result.append({
                                'subject_id': subject_id,
                                'task_id': task['task_id'],
                                'mmse_score': task['mmse_score'],
                                'mmse_max_score': task['mmse_max_score'],
                                'performance_ratio': task['mmse_score'] / task['mmse_max_score'],
                                'subQuestions': generate_sub_questions(task['task_id'], row)
                            })

                return jsonify({'success': True, 'data': result})
            else:
                return jsonify({'success': False, 'error': 'AD组MMSE数据文件不存在'}), 404
                
        except Exception as e:
            return jsonify({'success': False, 'error': f'读取AD组MMSE数据失败: {str(e)}'}), 500

    @app.route('/api/normalized-features', methods=['GET'])
    def get_normalized_features():
        """获取归一化特征数据"""
        try:
            # 读取归一化特征数据
            file_path = os.path.join('data', 'normalized_features', 'normalized_features_summary.csv')
            if os.path.exists(file_path):
                df = pd.read_csv(file_path)
                
                # 转换为JSON格式
                result = df.to_dict('records')
                return jsonify(result)
            else:
                return jsonify({'error': '归一化特征数据文件不存在'}), 404
                
        except Exception as e:
            return jsonify({'error': f'读取归一化特征数据失败: {str(e)}'}), 500

    print("✅ MMSE API路由注册完成")