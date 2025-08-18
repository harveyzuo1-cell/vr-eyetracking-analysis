# -*- coding: utf-8 -*-
"""
自定义VR眼动数据格式解析器
处理项目特定的VR眼动数据格式
"""
import re
import math
import pandas as pd
from datetime import datetime
from typing import List, Dict

def parse_custom_vr_format(content: str) -> List[Dict]:
    """
    解析自定义格式的VR眼动数据
    
    格式: x:0.116499y:0.490174z:0.000000/2025-7-5-16-18-4-487----
    
    Args:
        content: 原始文件内容
        
    Returns:
        解析后的数据记录列表，包含完整的时间信息
    """
    # 匹配模式：x:数字y:数字z:数字/年-月-日-时-分-秒-毫秒----
    pattern = r'x:([\d.]+)y:([\d.]+)z:([\d.]+)/(\d{4})-(\d{1,2})-(\d{1,2})-(\d{1,2})-(\d{1,2})-(\d{1,2})-(\d{1,3})----'
    
    matches = re.findall(pattern, content)
    print(f"🔍 找到 {len(matches)} 个数据点")
    
    if not matches:
        print("❌ 未找到匹配的数据格式")
        return []
    
    records = []
    base_time = None
    
    for i, (x_str, y_str, z_str, year_str, month_str, day_str, hour_str, minute_str, second_str, ms_str) in enumerate(matches):
        try:
            x = float(x_str)
            y = float(y_str)
            z = float(z_str)
            
            # 解析时间戳
            year = int(year_str)
            month = int(month_str)
            day = int(day_str)
            hour = int(hour_str)
            minute = int(minute_str)
            second = int(second_str)
            millisecond = int(ms_str)
            
            # 创建绝对时间
            abs_datetime = datetime(year, month, day, hour, minute, second, millisecond * 1000)
            
            # 计算相对时间戳
            if i == 0:
                base_time = abs_datetime
                relative_timestamp = 0.0
                relative_milliseconds = 0.0
            else:
                time_diff = abs_datetime - base_time
                relative_timestamp = time_diff.total_seconds()
                relative_milliseconds = time_diff.total_seconds() * 1000
            
            # 验证坐标范围（应该在0-1之间）
            if 0.0 <= x <= 1.0 and 0.0 <= y <= 1.0:
                records.append({
                    'timestamp': relative_timestamp,
                    'x': x,
                    'y': y,
                    'z': z,
                    'abs_datetime': abs_datetime.strftime('%Y-%m-%d %H:%M:%S.%f')[:-3],  # 格式化为毫秒精度
                    'milliseconds': relative_milliseconds
                })
                
        except (ValueError, IndexError) as e:
            print(f"⚠️  解析第{i+1}个数据点时出错: {e}")
            continue
    
    print(f"✅ 成功解析 {len(records)} 条有效记录")
    return records

def process_custom_vr_file(input_file: str, output_file: str) -> bool:
    """
    处理自定义格式的VR眼动数据文件，生成完整的数据结构
    
    Args:
        input_file: 输入文件路径
        output_file: 输出CSV文件路径
        
    Returns:
        处理是否成功
    """
    try:
        print(f"🔄 开始处理自定义格式文件: {input_file}")
        
        # 读取文件
        with open(input_file, 'r', encoding='utf-8') as f:
            content = f.read()
        
        print(f"📁 文件大小: {len(content)} 字符")
        print(f"📄 文件前100字符: {content[:100]}...")
        
        # 解析数据
        records = parse_custom_vr_format(content)
        
        if not records:
            print("❌ 未找到有效数据")
            return False
        
        # 转换为DataFrame
        df = pd.DataFrame(records)
        
        # 计算时间差
        df['time_diff'] = df['timestamp'].diff().fillna(0) * 1000  # 转换为毫秒
        
        print(f"🕐 时间转换:")
        print(f"   原始timestamp范围: {df['timestamp'].min():.3f}s ~ {df['timestamp'].max():.3f}s")
        print(f"   相对milliseconds范围: {df['milliseconds'].min():.1f} ~ {df['milliseconds'].max():.1f}")
        
        # 坐标转换为度数（假设视场角为110度）
        fov_deg = 110.0
        df['x_deg'] = (df['x'] - 0.5) * fov_deg  # -55 to +55 度
        df['y_deg'] = (df['y'] - 0.5) * fov_deg  # -55 to +55 度
        
        print(f"📐 坐标转换为度数:")
        print(f"   x_deg: {df['x_deg'].min():.1f}° ~ {df['x_deg'].max():.1f}°")
        print(f"   y_deg: {df['y_deg'].min():.1f}° ~ {df['y_deg'].max():.1f}°")
        
        # 计算角度差值
        df['x_deg_diff'] = df['x_deg'].diff().fillna(0)
        df['y_deg_diff'] = df['y_deg'].diff().fillna(0)
        
        # 计算角度距离（欧几里得距离）
        df['dist_deg'] = 0.0
        
        # 计算角速度
        df['velocity_deg_s'] = 0.0
        
        for i in range(1, len(df)):
            # 角度距离
            dx_deg = df.iloc[i]['x_deg_diff']
            dy_deg = df.iloc[i]['y_deg_diff']
            dist_deg = math.sqrt(dx_deg**2 + dy_deg**2)
            df.iloc[i, df.columns.get_loc('dist_deg')] = dist_deg
            
            # 角速度
            dt = df.iloc[i]['time_diff'] / 1000.0  # 转换为秒
            if dt > 0:
                velocity_deg_s = dist_deg / dt
                df.iloc[i, df.columns.get_loc('velocity_deg_s')] = velocity_deg_s
        
        # 计算平均角速度
        avg_velocity = df['velocity_deg_s'].mean()
        df['avg_velocity_deg_s'] = avg_velocity
        
        print(f"📊 数据统计:")
        print(f"   记录数: {len(df)}")
        print(f"   时间跨度: {df['timestamp'].max():.2f} 秒")
        print(f"   X范围: {df['x'].min():.3f} ~ {df['x'].max():.3f}")
        print(f"   Y范围: {df['y'].min():.3f} ~ {df['y'].max():.3f}")
        print(f"   平均角速度: {avg_velocity:.3f} deg/s")
        print(f"   最大角距离: {df['dist_deg'].max():.3f} deg")
        
        # 重新排列列顺序以匹配期望格式
        # 期望格式：x,y,z,abs_datetime,milliseconds,time_diff,x_deg,y_deg,x_deg_diff,y_deg_diff,dist_deg,velocity_deg_s,avg_velocity_deg_s
        columns_order = [
            'x', 'y', 'z', 'abs_datetime', 'milliseconds', 'time_diff',
            'x_deg', 'y_deg', 'x_deg_diff', 'y_deg_diff', 'dist_deg',
            'velocity_deg_s', 'avg_velocity_deg_s'
        ]
        
        # 确保所有列都存在，重新排序
        existing_columns = [col for col in columns_order if col in df.columns]
        df = df[existing_columns]
        
        print(f"📋 最终列结构: {list(df.columns)}")
        
        # 保存结果
        df.to_csv(output_file, index=False, encoding='utf-8')
        print(f"✅ 处理完成，结果保存到: {output_file}")
        
        return True
        
    except Exception as e:
        print(f"❌ 处理文件时出错: {e}")
        import traceback
        print(f"📋 详细错误信息:\n{traceback.format_exc()}")
        return False

# 主函数（用于独立测试）
if __name__ == "__main__":
    import sys
    if len(sys.argv) != 3:
        print("用法: python custom_vr_parser.py <输入文件> <输出文件>")
        sys.exit(1)
    
    input_file = sys.argv[1]
    output_file = sys.argv[2]
    
    success = process_custom_vr_file(input_file, output_file)
    if success:
        print("✅ 处理成功!")
    else:
        print("❌ 处理失败!")
        sys.exit(1) 