"""
性能测试工具函数
提供通用的性能测试辅助功能
"""
import time
import statistics
from typing import List, Dict, Any, Callable
from functools import wraps
import json
from pathlib import Path


def measure_time(func: Callable) -> Callable:
    """
    装饰器：测量函数执行时间
    
    Args:
        func: 要测量的函数
        
    Returns:
        包装后的函数，返回 (结果, 耗时)
    """
    @wraps(func)
    def wrapper(*args, **kwargs):
        start_time = time.time()
        result = func(*args, **kwargs)
        elapsed_time = time.time() - start_time
        return result, elapsed_time
    return wrapper


def calculate_statistics(times: List[float]) -> Dict[str, float]:
    """
    计算响应时间统计信息
    
    Args:
        times: 响应时间列表（秒）
        
    Returns:
        包含平均值、中位数、P95、P99 的字典
    """
    if not times:
        return {
            "mean": 0.0,
            "median": 0.0,
            "p95": 0.0,
            "p99": 0.0,
            "min": 0.0,
            "max": 0.0
        }
    
    sorted_times = sorted(times)
    n = len(sorted_times)
    
    return {
        "mean": statistics.mean(times),
        "median": statistics.median(times),
        "p95": sorted_times[int(n * 0.95)] if n > 0 else 0.0,
        "p99": sorted_times[int(n * 0.99)] if n > 0 else 0.0,
        "min": min(times),
        "max": max(times),
        "count": n
    }


def format_time(seconds: float) -> str:
    """
    格式化时间为可读字符串
    
    Args:
        seconds: 秒数
        
    Returns:
        格式化后的时间字符串
    """
    if seconds < 0.001:
        return f"{seconds * 1000000:.2f}μs"
    elif seconds < 1:
        return f"{seconds * 1000:.2f}ms"
    else:
        return f"{seconds:.2f}s"


def print_statistics(stats: Dict[str, float], title: str = "统计信息"):
    """
    打印统计信息表格
    
    Args:
        stats: 统计信息字典
        title: 标题
    """
    print(f"\n{'='*60}")
    print(f"{title}")
    print(f"{'='*60}")
    print(f"  平均响应时间: {format_time(stats['mean'])}")
    print(f"  中位数 (P50): {format_time(stats['median'])}")
    print(f"  P95:          {format_time(stats['p95'])}")
    print(f"  P99:          {format_time(stats['p99'])}")
    print(f"  最小值:       {format_time(stats['min'])}")
    print(f"  最大值:       {format_time(stats['max'])}")
    print(f"  测试次数:     {stats['count']}")
    print(f"{'='*60}\n")


def save_results(results: Dict[str, Any], filepath: str):
    """
    保存测试结果到 JSON 文件
    
    Args:
        results: 测试结果字典
        filepath: 保存路径
    """
    output_path = Path(filepath)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    # 转换不可序列化的对象
    serializable_results = {}
    for key, value in results.items():
        if isinstance(value, (dict, list, str, int, float, bool, type(None))):
            serializable_results[key] = value
        else:
            serializable_results[key] = str(value)
    
    with open(output_path, 'w', encoding='utf-8') as f:
        json.dump(serializable_results, f, ensure_ascii=False, indent=2)
    
    print(f"✅ 测试结果已保存到: {output_path}")


def compare_results(results_list: List[Dict[str, Any]], labels: List[str]):
    """
    对比多个测试结果
    
    Args:
        results_list: 测试结果列表
        labels: 每个结果的标签
    """
    if len(results_list) != len(labels):
        raise ValueError("结果列表和标签列表长度必须一致")
    
    print(f"\n{'='*80}")
    print("性能对比")
    print(f"{'='*80}")
    print(f"{'指标':<20} " + "".join(f"{label:>15}" for label in labels))
    print(f"{'-'*80}")
    
    # 对比平均响应时间
    if all('mean_time' in r for r in results_list):
        print(f"{'平均响应时间':<20} " + 
              "".join(f"{format_time(r['mean_time']):>15}" for r in results_list))
    
    # 对比 P95
    if all('p95_time' in r for r in results_list):
        print(f"{'P95 响应时间':<20} " + 
              "".join(f"{format_time(r['p95_time']):>15}" for r in results_list))
    
    # 对比准确率
    if all('accuracy' in r for r in results_list):
        print(f"{'准确率':<20} " + 
              "".join(f"{r['accuracy']*100:>14.2f}%" for r in results_list))
    
    # 对比成功率
    if all('success_rate' in r for r in results_list):
        print(f"{'成功率':<20} " + 
              "".join(f"{r['success_rate']*100:>14.2f}%" for r in results_list))
    
    print(f"{'='*80}\n")


def load_test_questions(filepath: str) -> List[Dict[str, str]]:
    """
    从文件加载测试问题
    
    Args:
        filepath: 问题文件路径（JSON 或 JSONL 格式）
        
    Returns:
        问题列表，每个问题包含 'question' 和可选的 'category', 'expected_answer' 等字段
    """
    path = Path(filepath)
    if not path.exists():
        raise FileNotFoundError(f"测试问题文件不存在: {filepath}")
    
    questions = []
    
    if path.suffix == '.jsonl':
        with open(path, 'r', encoding='utf-8') as f:
            for line in f:
                line = line.strip()
                if line:
                    questions.append(json.loads(line))
    elif path.suffix == '.json':
        with open(path, 'r', encoding='utf-8') as f:
            data = json.load(f)
            if isinstance(data, list):
                questions = data
            else:
                questions = [data]
    else:
        raise ValueError(f"不支持的文件格式: {path.suffix}")
    
    return questions


def create_test_questions_file(filepath: str, questions: List[Dict[str, str]]):
    """
    创建测试问题文件
    
    Args:
        filepath: 输出文件路径
        questions: 问题列表
    """
    output_path = Path(filepath)
    output_path.parent.mkdir(parents=True, exist_ok=True)
    
    if output_path.suffix == '.jsonl':
        with open(output_path, 'w', encoding='utf-8') as f:
            for q in questions:
                f.write(json.dumps(q, ensure_ascii=False) + '\n')
    elif output_path.suffix == '.json':
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(questions, f, ensure_ascii=False, indent=2)
    else:
        raise ValueError(f"不支持的文件格式: {output_path.suffix}")
    
    print(f"✅ 测试问题已保存到: {output_path}")

