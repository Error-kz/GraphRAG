"""
模式推断主入口脚本
自动推断数据文件的图模式并保存配置
"""
import sys
import argparse
from pathlib import Path
from typing import Optional

# 将项目根目录添加到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.framework import DataReader, SchemaInferrer, SchemaGenerator, SchemaConfig
from core.graph.schemas import GraphSchema


def infer_and_save_schema(
    data_file: str,
    domain: str,
    version: str = "1.0",
    output_dir: Optional[str] = None
) -> GraphSchema:
    """
    推断图模式并保存
    
    Args:
        data_file: 数据文件路径
        domain: 领域名称
        version: 版本号
        output_dir: 输出目录，如果为None则使用默认目录
        
    Returns:
        GraphSchema对象
    """
    print("=" * 80)
    print("开始模式推断流程")
    print("=" * 80)
    
    # 步骤1: 读取数据文件第一行
    print("\n[步骤1] 读取数据文件第一行...")
    reader = DataReader(data_file)
    first_line = reader.read_first_line()
    
    if not first_line:
        raise ValueError("数据文件为空或无法读取第一行数据")
    
    print(f"✅ 成功读取第一行数据，包含 {len(first_line)} 个字段")
    print(f"字段列表: {', '.join(list(first_line.keys())[:10])}...")
    
    # 步骤2: 调用大模型分析数据结构
    print("\n[步骤2] 调用大模型分析数据结构...")
    inferrer = SchemaInferrer()
    inferred_schema = inferrer.infer_schema(first_line)
    
    print("✅ LLM分析完成")
    print(f"推断出 {len(inferred_schema.get('nodes', []))} 个节点类型")
    print(f"推断出 {len(inferred_schema.get('relationships', []))} 种关系类型")
    
    # 步骤3: 解析LLM返回的图模式
    print("\n[步骤3] 解析LLM返回的图模式...")
    generator = SchemaGenerator()
    schema = generator.generate_schema(inferred_schema)
    
    # 验证模式
    is_valid, errors = generator.validate_schema(schema)
    if not is_valid:
        print("⚠️  模式验证发现以下问题:")
        for error in errors:
            print(f"  - {error}")
        raise ValueError("生成的图模式无效，请检查LLM返回结果")
    
    print("✅ 模式解析完成")
    print(f"节点类型: {[node.label for node in schema.nodes]}")
    print(f"关系类型: {[rel.type for rel in schema.relationships]}")
    
    # 步骤4: 生成 GraphSchema 对象（已在步骤3完成）
    print("\n[步骤4] GraphSchema对象已生成")
    
    # 步骤5: 保存模式到配置文件
    print("\n[步骤5] 保存模式到配置文件...")
    config_manager = SchemaConfig(output_dir)
    config_file = config_manager.save_schema(schema, domain, version)
    
    print(f"✅ 模式已保存到: {config_file}")
    
    # 打印模式摘要
    print("\n" + "=" * 80)
    print("模式推断完成！")
    print("=" * 80)
    print(f"\n领域: {domain}")
    print(f"版本: {version}")
    print(f"\n节点类型 ({len(schema.nodes)} 个):")
    for node in schema.nodes:
        prop_count = len(node.properties)
        print(f"  - {node.label} ({prop_count} 个属性)")
    
    print(f"\n关系类型 ({len(schema.relationships)} 个):")
    for rel in schema.relationships:
        print(f"  - {rel.from_node} --[{rel.type}]--> {rel.to_node}")
    
    print(f"\n配置文件: {config_file}")
    print("=" * 80)
    
    return schema


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="自动推断数据文件的图模式")
    parser.add_argument(
        "data_file",
        type=str,
        help="数据文件路径（支持JSONL/JSON/CSV格式）"
    )
    parser.add_argument(
        "--domain",
        type=str,
        required=True,
        help="领域名称（如：medical, finance等）"
    )
    parser.add_argument(
        "--version",
        type=str,
        default="1.0",
        help="版本号（默认：1.0）"
    )
    parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="输出目录（默认：config/schemas）"
    )
    
    args = parser.parse_args()
    
    try:
        schema = infer_and_save_schema(
            data_file=args.data_file,
            domain=args.domain,
            version=args.version,
            output_dir=args.output_dir
        )
        print("\n✅ 模式推断流程执行成功！")
        return 0
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc()
        return 1


if __name__ == "__main__":
    sys.exit(main())

