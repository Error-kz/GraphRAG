"""
测试 NL2Cypher 功能
基于动态图模式生成 Cypher 查询
"""
import sys
import argparse
from pathlib import Path

# 将项目根目录添加到 Python 路径
project_root = Path(__file__).parent.parent
sys.path.insert(0, str(project_root))

from core.framework import SchemaConfig, NL2CypherService
from core.graph.neo4j_client import Neo4jClient


def test_nl2cypher(
    domain: str,
    version: str = None,
    query: str = None,
    execute: bool = False
):
    """
    测试 NL2Cypher 功能
    
    Args:
        domain: 领域名称
        version: 版本号
        query: 自然语言查询
        execute: 是否执行查询
    """
    print("=" * 80)
    print("测试 NL2Cypher 功能")
    print("=" * 80)
    
    try:
        # 步骤1: 加载图模式配置
        print("\n[步骤1] 加载图模式配置...")
        config_manager = SchemaConfig()
        schema = config_manager.load_schema(domain, version)
        
        if not schema:
            raise ValueError(f"无法加载模式: {domain} v{version or 'latest'}")
        
        print(f"✅ 模式加载成功")
        print(f"  领域: {domain}")
        print(f"  版本: {version or 'latest'}")
        print(f"  节点类型: {len(schema.nodes)} 个")
        print(f"  关系类型: {len(schema.relationships)} 个")
        
        # 创建 NL2Cypher 服务
        service = NL2CypherService(schema=schema)
        
        # 步骤2: 动态生成系统提示词
        print("\n[步骤2] 动态生成系统提示词...")
        prompt = service.prompt_generator.generate_system_prompt()
        print(f"✅ 提示词生成成功（长度: {len(prompt)} 字符）")
        print("\n提示词预览（前500字符）:")
        print(prompt[:500] + "...")
        
        # 步骤3: 用户输入自然语言查询
        if not query:
            query = input("\n请输入自然语言查询（或按回车使用默认查询）: ").strip()
            if not query:
                # 使用默认查询
                main_entity = max(schema.nodes, key=lambda n: len(n.properties))
                query = f"查找所有{main_entity.label.lower()}"
        
        print(f"\n[步骤3] 自然语言查询: {query}")
        
        # 步骤4: 使用动态提示词生成Cypher
        print("\n[步骤4] 生成 Cypher 查询...")
        result = service.generate_cypher(query)
        
        print(f"✅ Cypher 查询生成成功")
        print(f"\n生成的查询:")
        print(result['cypher_query'])
        print(f"\n查询解释:")
        print(result['explanation'])
        print(f"\n置信度: {result['confidence']:.2f}")
        print(f"验证状态: {'通过' if result['validated'] else '失败'}")
        if result['validation_errors']:
            print(f"验证错误:")
            for error in result['validation_errors']:
                print(f"  - {error}")
        
        # 步骤5: 验证和执行查询（可选）
        if execute:
            print("\n[步骤5] 执行查询...")
            try:
                query_result = service.execute_query(result['cypher_query'])
                print(f"✅ 查询执行成功")
                print(f"  返回记录数: {query_result.get('count', 0)}")
                print(f"  执行时间: {query_result.get('execution_time', 0):.3f} 秒")
                
                # 显示前几条结果
                records = query_result.get('records', [])
                if records:
                    print(f"\n查询结果（前5条）:")
                    for i, record in enumerate(records[:5], 1):
                        print(f"  {i}. {record}")
                    if len(records) > 5:
                        print(f"  ... 还有 {len(records) - 5} 条结果")
            except Exception as e:
                print(f"⚠️  查询执行失败: {str(e)}")
        else:
            print("\n[步骤5] 跳过查询执行（使用 --execute 参数可执行查询）")
        
        print("\n" + "=" * 80)
        print("✅ NL2Cypher 测试完成！")
        print("=" * 80)
        
        return True
        
    except Exception as e:
        print(f"\n❌ 错误: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """主函数"""
    parser = argparse.ArgumentParser(description="测试 NL2Cypher 功能")
    parser.add_argument(
        "--domain",
        type=str,
        required=True,
        help="领域名称（如：medical）"
    )
    parser.add_argument(
        "--version",
        type=str,
        default=None,
        help="版本号（默认：最新版本）"
    )
    parser.add_argument(
        "--query",
        type=str,
        default=None,
        help="自然语言查询（如果不提供则交互式输入）"
    )
    parser.add_argument(
        "--execute",
        action="store_true",
        help="执行生成的查询（需要 Neo4j 连接）"
    )
    
    args = parser.parse_args()
    
    success = test_nl2cypher(
        domain=args.domain,
        version=args.version,
        query=args.query,
        execute=args.execute
    )
    
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()

