"""
数据格式转换器
将原始TXT格式转换为标准CSV格式
"""
import re
import csv
from pathlib import Path
from typing import Dict, List, Optional
from datetime import datetime


class EyeTrackingDataConverter:
    """眼动数据格式转换器"""

    @staticmethod
    def parse_line(line: str) -> Optional[Dict]:
        """
        解析单行眼动数据

        Args:
            line: 原始数据行
                  例如: x:0.296941y:0.769334z:0.000000/2025-3-27-11-37-31-522

        Returns:
            解析后的字典:
            {
                'x': 0.296941,
                'y': 0.769334,
                'timestamp': '2025-03-27 11:37:31.522'
            }
            如果解析失败返回None
        """
        # 正则匹配: x:(float) y:(float) z:(float) / (timestamp)
        pattern = r'x:([\d.]+)y:([\d.]+)z:([\d.]+)/([\d-]+)'
        match = re.match(pattern, line.strip())

        if not match:
            return None

        x, y, z, timestamp_str = match.groups()

        try:
            # 解析时间戳: 2025-3-27-11-37-31-522 → 2025-03-27 11:37:31.522
            parts = timestamp_str.split('-')

            if len(parts) < 7:
                return None

            year, month, day, hour, minute, second, ms = parts[:7]

            # 格式化时间戳
            timestamp_formatted = (
                f"{year}-{month.zfill(2)}-{day.zfill(2)} "
                f"{hour.zfill(2)}:{minute.zfill(2)}:{second.zfill(2)}.{ms.zfill(3)}"
            )

            return {
                'x': float(x),
                'y': float(y),
                'timestamp': timestamp_formatted
            }
        except (ValueError, IndexError) as e:
            # 解析失败，返回None
            return None

    def convert_txt_to_csv(self, txt_path: Path, csv_path: Path) -> Dict:
        """
        转换单个TXT文件到CSV格式

        Args:
            txt_path: 输入TXT文件路径
            csv_path: 输出CSV文件路径

        Returns:
            转换统计信息:
            {
                'success': True,
                'total_lines': 1000,
                'parsed_lines': 995,
                'failed_lines': 5,
                'output_path': 'path/to/output.csv'
            }
        """
        if not txt_path.exists():
            raise FileNotFoundError(f"Input file not found: {txt_path}")

        # 读取TXT文件
        with open(txt_path, 'r', encoding='utf-8') as f:
            content = f.read()

        # 按 ---- 分割数据点
        data_points = [point.strip() for point in content.split('----') if point.strip()]

        # 解析每个数据点
        parsed_data = []
        failed_count = 0

        for point in data_points:
            parsed = self.parse_line(point)
            if parsed:
                parsed_data.append(parsed)
            else:
                failed_count += 1

        # 确保输出目录存在
        csv_path.parent.mkdir(parents=True, exist_ok=True)

        # 写入CSV
        with open(csv_path, 'w', newline='', encoding='utf-8') as f:
            if parsed_data:
                writer = csv.DictWriter(f, fieldnames=['timestamp', 'x', 'y'])
                writer.writeheader()
                writer.writerows(parsed_data)

        return {
            'success': True,
            'total_lines': len(data_points),
            'parsed_lines': len(parsed_data),
            'failed_lines': failed_count,
            'output_path': str(csv_path)
        }

    def convert_subject_all_tasks(self,
                                   source_dir: Path,
                                   output_dir: Path,
                                   subject_id: str,
                                   task_count: int = 5) -> Dict:
        """
        转换受试者的所有任务数据

        Args:
            source_dir: 源数据目录
            output_dir: 输出目录
            subject_id: 受试者ID
            task_count: 任务数量(默认5)

        Returns:
            转换结果:
            {
                'success': True,
                'subject_id': 'control_000000',
                'converted_tasks': ['q1', 'q2', 'q3', 'q4', 'q5'],
                'failed_tasks': [],
                'statistics': {...}
            }
        """
        converted_tasks = []
        failed_tasks = []
        statistics = {}

        # 确保输出目录存在
        output_dir.mkdir(parents=True, exist_ok=True)

        for i in range(1, task_count + 1):
            task_id = f"q{i}"

            # 尝试多种文件名格式
            possible_names = [f"level_{i}.txt", f"{i}.txt"]
            txt_path = None

            for name in possible_names:
                candidate = source_dir / name
                if candidate.exists():
                    txt_path = candidate
                    break

            if not txt_path:
                failed_tasks.append(task_id)
                continue

            # 输出CSV路径
            csv_path = output_dir / f"{subject_id}_{task_id}.csv"

            try:
                # 转换
                result = self.convert_txt_to_csv(txt_path, csv_path)
                converted_tasks.append(task_id)
                statistics[task_id] = result
            except Exception as e:
                failed_tasks.append(task_id)
                statistics[task_id] = {
                    'success': False,
                    'error': str(e)
                }

        return {
            'success': len(failed_tasks) == 0,
            'subject_id': subject_id,
            'converted_tasks': converted_tasks,
            'failed_tasks': failed_tasks,
            'statistics': statistics
        }

    def batch_convert(self,
                     source_dirs: List[Path],
                     output_base_dir: Path,
                     subject_mapping: Dict) -> Dict:
        """
        批量转换多个受试者数据

        Args:
            source_dirs: 源数据目录列表
            output_base_dir: 输出基础目录
            subject_mapping: 受试者映射 {source_dir: subject_id}

        Returns:
            批量转换结果
        """
        results = []

        for source_dir in source_dirs:
            if source_dir not in subject_mapping:
                continue

            subject_id = subject_mapping[source_dir]

            # 根据subject_id确定组别
            group = subject_id.split('_')[0]
            output_dir = output_base_dir / group

            try:
                result = self.convert_subject_all_tasks(
                    source_dir, output_dir, subject_id
                )
                results.append(result)
            except Exception as e:
                results.append({
                    'success': False,
                    'subject_id': subject_id,
                    'error': str(e)
                })

        success_count = sum(1 for r in results if r['success'])

        return {
            'success': True,
            'total': len(results),
            'success_count': success_count,
            'failed_count': len(results) - success_count,
            'results': results
        }


if __name__ == '__main__':
    # 测试代码
    converter = EyeTrackingDataConverter()

    # 测试解析单行
    test_line = "x:0.296941y:0.769334z:0.000000/2025-3-27-11-37-31-522"
    parsed = converter.parse_line(test_line)
    print("Parsed line:", parsed)

    # 测试转换
    # txt_path = Path("data/control_raw/control_group_1/1.txt")
    # csv_path = Path("test_output/control_legacy_1_q1.csv")
    # result = converter.convert_txt_to_csv(txt_path, csv_path)
    # print("Conversion result:", result)
