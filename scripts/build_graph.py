"""
图谱构建主入口脚本
根据推断出的图模式构建知识图谱
"""
import sys
import argparse
from pathlib import Path
from typing import Optional

# 将项目根目录添加到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.framework import SchemaConfig, DataReader
from core.framework.graph_builder import GraphBuilder
from core.graph.neo4j_client import Neo4jClient


def build_graph_from_schema(
    schema_file: str,
    data_file: str,
    clear_existing: bool = False,
    batch_size: int = 100
):
    """
    根据模式文件构建知识图谱
    
    Args:
        schema_file: 模式配置文件路径（如：config/schemas/medical_schema_v1.0.json）
        data_file: 数据文件路径
        clear_existing: 是否清空现有图谱
        batch_size: 批量处理大小
    """
    print("=" * 80)
    print("开始图谱构建流程")
    print("=" * 80)
    
    # 步骤1: 加载推断出的图模式
    print("\n[步骤1] 加载推断出的图模式...")
    config_manager = SchemaConfig()
    
    # 从文件路径提取领域和版本
    schema_path = Path(schema_file)
    if not schema_path.exists():
        raise FileNotFoundError(f"模式文件不存在: {schema_file}")
    
    name_parts = schema_path.stem.split('_schema_v')
    if len(name_parts) != 2:
        raise ValueError(f"无法从文件名解析领域和版本: {schema_file}")
    
    domain = name_parts[0]
    version = name_parts[1]
    
    schema = config_manager.load_schema(domain, version)
    if not schema:
        raise ValueError(f"无法加载模式: {domain} v{version}")
    
    print(f"✅ 模式加载成功")
    print(f"  领域: {domain}")
    print(f"  版本: {version}")
    print(f"  节点类型: {len(schema.nodes)} 个")
    print(f"  关系类型: {len(schema.relationships)} 个")
    
    # 创建图谱构建器
    builder = GraphBuilder(schema)
    
    # 构建图谱（包含步骤2-5）
    builder.build_graph(
        data_file=data_file,
        batch_size=batch_size,
        clear_existing=clear_existing
    )


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="根据图模式构建知识图谱")
    parser.add_argument(
        "schema_file",
        type=str,
        help="模式配置文件路径（如：config/schemas/medical_schema_v1.0.json）"
    )
    parser.add_argument(
        "data_file",
        type=str,
        help="数据文件路径（支持JSONL/JSON/CSV格式）"
    )
    parser.add_argument(
        "--clear",
        action="store_true",
        help="清空现有图谱（谨慎使用）"
    )
    parser.add_argument(
        "--batch-size",
        type=int,
        default=100,
        help="批量处理大小（默认：100）"
    )
    
    args = parser.parse_args()
    
    try:
        build_graph_from_schema(
            schema_file=args.schema_file,
            data_file=args.data_file,
            clear_existing=args.clear,
            batch_size=args.batch_size
        )
        print("\n✅ 图谱构建流程执行成功！")
        return 0
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

