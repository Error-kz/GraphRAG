"""
数据读取器
支持读取JSONL/JSON/CSV等格式的数据文件
"""
import json
import csv
from pathlib import Path
from typing import Dict, Any, Optional, List


class DataReader:
    """数据读取器类"""
    
    def __init__(self, file_path: str):
        """
        初始化数据读取器
        
        Args:
            file_path: 数据文件路径
        """
        self.file_path = Path(file_path)
        if not self.file_path.exists():
            raise FileNotFoundError(f"数据文件不存在: {file_path}")
        
        self.file_extension = self.file_path.suffix.lower()
    
    def read_first_line(self) -> Optional[Dict[str, Any]]:
        """
        读取数据文件的第一行
        
        Returns:
            第一行数据的字典表示，如果文件为空则返回None
        """
        if self.file_extension == '.jsonl':
            return self._read_jsonl_first_line()
        elif self.file_extension == '.json':
            return self._read_json_first_line()
        elif self.file_extension == '.csv':
            return self._read_csv_first_line()
        else:
            raise ValueError(f"不支持的文件格式: {self.file_extension}")
    
    def _read_jsonl_first_line(self) -> Optional[Dict[str, Any]]:
        """读取JSONL文件的第一行"""
        with open(self.file_path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    return json.loads(line)
                except json.JSONDecodeError as e:
                    raise ValueError(f"JSONL文件第一行解析失败: {str(e)}")
        return None
    
    def _read_json_first_line(self) -> Optional[Dict[str, Any]]:
        """读取JSON文件的第一条记录"""
        with open(self.file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list) and len(data) > 0:
                return data[0]
            elif isinstance(data, dict):
                return data
        return None
    
    def _read_csv_first_line(self) -> Optional[Dict[str, Any]]:
        """读取CSV文件的第一行"""
        with open(self.file_path, 'r', encoding='utf-8') as f:
            reader = csv.DictReader(f)
            for row in reader:
                return dict(row)
        return None
    
    def read_sample_lines(self, n: int = 3) -> List[Dict[str, Any]]:
        """
        读取前N行数据作为样本
        
        Args:
            n: 要读取的行数
            
        Returns:
            前N行数据的列表
        """
        samples = []
        
        if self.file_extension == '.jsonl':
            with open(self.file_path, 'r', encoding='utf-8') as f:
                for i, line in enumerate(f):
                    if i >= n:
                        break
                    line = line.strip()
                    if not line:
                        continue
                    try:
                        samples.append(json.loads(line))
                    except json.JSONDecodeError:
                        continue
        elif self.file_extension == '.json':
            with open(self.file_path, 'r', encoding='utf-8') as f:
                data = json.load(f)
                if isinstance(data, list):
                    samples = data[:n]
                elif isinstance(data, dict):
                    samples = [data]
        elif self.file_extension == '.csv':
            with open(self.file_path, 'r', encoding='utf-8') as f:
                reader = csv.DictReader(f)
                for i, row in enumerate(reader):
                    if i >= n:
                        break
                    samples.append(dict(row))
        
        return samples

