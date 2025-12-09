"""
检索策略性能对比测试
对比纯向量检索、纯知识图谱检索和混合检索的性能
"""
import sys
from pathlib import Path

# 将项目根目录添加到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from tests.performance.utils import (
    measure_time,
    calculate_statistics,
    print_statistics,
    save_results,
    compare_results,
    load_test_questions
)


def benchmark_vector_retrieval(questions: list, retriever):
    """
    测试纯向量检索性能
    
    Args:
        questions: 测试问题列表
        retriever: 向量检索器
        
    Returns:
        测试结果字典
    """
    print("\n开始测试：纯向量检索")
    times = []
    success_count = 0
    
    for i, q in enumerate(questions, 1):
        question = q.get('question', q) if isinstance(q, dict) else q
        print(f"  测试 {i}/{len(questions)}: {question[:50]}...", end=" ")
        
        try:
            result, elapsed = measure_time(retriever.get_relevant_documents)(question)
            times.append(elapsed)
            success_count += 1
            print(f"✓ ({elapsed:.2f}s)")
        except Exception as e:
            print(f"✗ 错误: {str(e)}")
    
    stats = calculate_statistics(times)
    return {
        "strategy": "纯向量检索",
        "mean_time": stats["mean"],
        "p95_time": stats["p95"],
        "p99_time": stats["p99"],
        "success_rate": success_count / len(questions) if questions else 0,
        "total_tests": len(questions),
        "success_count": success_count,
        "statistics": stats
    }


def benchmark_graph_retrieval(questions: list, graph_service):
    """
    测试纯知识图谱检索性能
    
    Args:
        questions: 测试问题列表
        graph_service: 图服务
        
    Returns:
        测试结果字典
    """
    print("\n开始测试：纯知识图谱检索")
    times = []
    success_count = 0
    
    for i, q in enumerate(questions, 1):
        question = q.get('question', q) if isinstance(q, dict) else q
        print(f"  测试 {i}/{len(questions)}: {question[:50]}...", end=" ")
        
        try:
            # 这里需要根据实际的图服务接口调整
            result, elapsed = measure_time(graph_service.query)(question)
            times.append(elapsed)
            success_count += 1
            print(f"✓ ({elapsed:.2f}s)")
        except Exception as e:
            print(f"✗ 错误: {str(e)}")
    
    stats = calculate_statistics(times)
    return {
        "strategy": "纯知识图谱检索",
        "mean_time": stats["mean"],
        "p95_time": stats["p95"],
        "p99_time": stats["p99"],
        "success_rate": success_count / len(questions) if questions else 0,
        "total_tests": len(questions),
        "success_count": success_count,
        "statistics": stats
    }


def benchmark_hybrid_retrieval(questions: list, agent_service):
    """
    测试混合检索性能
    
    Args:
        questions: 测试问题列表
        agent_service: Agent 服务（包含混合检索）
        
    Returns:
        测试结果字典
    """
    print("\n开始测试：混合检索（向量 + 图谱）")
    times = []
    success_count = 0
    
    for i, q in enumerate(questions, 1):
        question = q.get('question', q) if isinstance(q, dict) else q
        print(f"  测试 {i}/{len(questions)}: {question[:50]}...", end=" ")
        
        try:
            # 这里需要根据实际的 Agent 服务接口调整
            result, elapsed = measure_time(agent_service.query)(question)
            times.append(elapsed)
            success_count += 1
            print(f"✓ ({elapsed:.2f}s)")
        except Exception as e:
            print(f"✗ 错误: {str(e)}")
    
    stats = calculate_statistics(times)
    return {
        "strategy": "混合检索",
        "mean_time": stats["mean"],
        "p95_time": stats["p95"],
        "p99_time": stats["p99"],
        "success_rate": success_count / len(questions) if questions else 0,
        "total_tests": len(questions),
        "success_count": success_count,
        "statistics": stats
    }


def main():
    """主测试函数"""
    print("=" * 80)
    print("检索策略性能对比测试")
    print("=" * 80)
    
    # 加载测试问题
    # TODO: 替换为实际的测试问题文件路径
    questions_file = "tests/performance/data/test_questions.jsonl"
    
    try:
        questions = load_test_questions(questions_file)
        print(f"\n✅ 加载了 {len(questions)} 个测试问题")
    except FileNotFoundError:
        print(f"\n⚠️  测试问题文件不存在: {questions_file}")
        print("请先创建测试问题文件，或使用示例问题")
        # 使用示例问题
        questions = [
            {"question": "感冒有什么症状？", "category": "简单查询"},
            {"question": "哪些疾病会导致高血压？", "category": "复杂查询"},
        ]
        print(f"使用 {len(questions)} 个示例问题")
    
    # TODO: 初始化检索器和服务
    # retriever = ...
    # graph_service = ...
    # agent_service = ...
    
    # 运行测试
    results = []
    
    # 测试纯向量检索
    # vector_result = benchmark_vector_retrieval(questions, retriever)
    # results.append(vector_result)
    # print_statistics(vector_result["statistics"], "纯向量检索统计")
    
    # 测试纯知识图谱检索
    # graph_result = benchmark_graph_retrieval(questions, graph_service)
    # results.append(graph_result)
    # print_statistics(graph_result["statistics"], "纯知识图谱检索统计")
    
    # 测试混合检索
    # hybrid_result = benchmark_hybrid_retrieval(questions, agent_service)
    # results.append(hybrid_result)
    # print_statistics(hybrid_result["statistics"], "混合检索统计")
    
    # 对比结果
    if len(results) > 1:
        labels = [r["strategy"] for r in results]
        compare_results(results, labels)
    
    # 保存结果
    output_file = "tests/performance/results/retrieval_benchmark.json"
    save_results({
        "test_name": "检索策略性能对比",
        "questions_count": len(questions),
        "results": results
    }, output_file)
    
    print("\n✅ 测试完成！")


if __name__ == "__main__":
    main()

