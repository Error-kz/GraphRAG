"""
测试图谱构建功能
将 JSON 文件的前三行数据写入知识图谱
"""
import sys
import json
import tempfile
import os
from pathlib import Path

# 将项目根目录添加到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

from core.framework import SchemaConfig, GraphBuilder, DataReader
from core.graph.neo4j_client import Neo4jClient
from core.graph.schemas import GraphSchema
from config.settings import settings


def create_test_data_file(num_lines: int = 3) -> str:
    """
    创建测试数据文件（包含前N行数据）
    
    Args:
        num_lines: 要包含的行数
        
    Returns:
        临时文件路径
    """
    # 从环境变量或配置中获取数据文件路径
    source_file_path = os.getenv("TEST_DATA_FILE") or settings.TEST_DATA_FILE
    source_file = Path(source_file_path)
    
    if not source_file.exists():
        raise FileNotFoundError(f"源数据文件不存在: {source_file}")
    
    # 创建临时文件
    temp_file = tempfile.NamedTemporaryFile(mode='w', suffix='.jsonl', delete=False, encoding='utf-8')
    temp_path = temp_file.name
    
    # 读取前N行并写入临时文件
    with open(source_file, 'r', encoding='utf-8') as f:
        for i, line in enumerate(f):
            if i >= num_lines:
                break
            if line.strip():
                temp_file.write(line)
    
    temp_file.close()
    return temp_path


def test_graph_builder_with_three_lines():
    """测试图谱构建：将前三行数据写入知识图谱"""
    print("=" * 80)
    print("测试图谱构建功能")
    print("=" * 80)
    
    try:
        # 步骤1: 创建测试数据文件（前三行）
        print("\n[步骤1] 创建测试数据文件（前三行）...")
        test_data_file = create_test_data_file(num_lines=3)
        print(f"✅ 测试数据文件已创建: {test_data_file}")
        
        # 验证测试数据
        reader = DataReader(test_data_file)
        sample_data = reader.read_sample_lines(n=3)
        print(f"✅ 测试数据包含 {len(sample_data)} 条记录")
        for i, data in enumerate(sample_data, 1):
            print(f"  记录 {i}: {data.get('name', 'Unknown')}")
        
        # 步骤2: 加载图模式
        print("\n[步骤2] 加载图模式...")
        config_manager = SchemaConfig()
        schema = config_manager.load_schema("medical", "1.0")
        
        if not schema:
            raise ValueError("无法加载 medical 模式，请先运行模式推断")
        
        print(f"✅ 模式加载成功")
        print(f"  节点类型: {[node.label for node in schema.nodes]}")
        print(f"  关系类型: {[rel.type for rel in schema.relationships]}")
        
        # 步骤3: 创建图谱构建器
        print("\n[步骤3] 创建图谱构建器...")
        builder = GraphBuilder(schema)
        print(f"✅ 构建器创建成功")
        print(f"  主实体: {builder.main_entity_label}")
        print(f"  字段映射数量: {len(builder.field_mapping)}")
        
        # 步骤4: 测试数据解析
        print("\n[步骤4] 测试数据解析...")
        first_data = sample_data[0]
        main_props, relationships = builder.parse_data(first_data)
        
        print(f"✅ 数据解析成功")
        print(f"  主实体属性 ({len(main_props)} 个):")
        for key, value in main_props.items():
            # 截断过长的值
            value_str = str(value)
            if len(value_str) > 100:
                value_str = value_str[:100] + "..."
            print(f"    - {key}: {value_str}")
        print(f"  识别到 {len(relationships)} 个关系:")
        for rel_type, target_label, target_name, _ in relationships:
            print(f"    - {rel_type}: {target_label} ({target_name})")
        
        # 步骤5: 构建图谱（可选，需要 Neo4j 连接）
        print("\n[步骤5] 构建知识图谱（可选）...")
        print("⚠️  注意: 此测试不会清空现有图谱，只会添加新数据")
        
        # 检查 Neo4j 连接
        try:
            client = Neo4jClient()
            if client.connect():
                client.close()
                
                # 实际构建（不清空现有数据）
                print("\n开始构建图谱...")
                builder.build_graph(
                    data_file=test_data_file,
                    batch_size=10,
                    clear_existing=False  # 不清空，避免影响现有数据
                )
                
                print("\n" + "=" * 80)
                print("✅ 图谱构建测试完成！")
                print("=" * 80)
            else:
                print("⚠️  警告: 无法连接到 Neo4j，跳过实际构建步骤")
                print("   请确保 Neo4j 已启动并配置正确")
                print("   数据解析测试已通过 ✓")
        except Exception as e:
            print(f"⚠️  警告: Neo4j 连接失败: {str(e)}")
            print("   跳过实际构建步骤，数据解析测试已通过 ✓")
        
        print(f"\n测试数据文件: {test_data_file}")
        print("（测试完成后可手动删除此文件）")
        
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    
    finally:
        # 清理临时文件（可选）
        # import os
        # if 'test_data_file' in locals() and os.path.exists(test_data_file):
        #     os.unlink(test_data_file)
        pass


def test_parse_data_only():
    """仅测试数据解析功能，不实际构建图谱"""
    print("=" * 80)
    print("测试数据解析功能（不构建图谱）")
    print("=" * 80)
    
    try:
        # 加载模式
        config_manager = SchemaConfig()
        schema = config_manager.load_schema("medical", "1.0")
        
        if not schema:
            raise ValueError("无法加载 medical 模式，请先运行模式推断")
        
        # 创建构建器
        builder = GraphBuilder(schema)
        
        # 读取前三行数据（从环境变量或配置中获取文件路径）
        source_file_path = os.getenv("TEST_DATA_FILE") or settings.TEST_DATA_FILE
        source_file = Path(source_file_path)
        
        if not source_file.exists():
            raise FileNotFoundError(f"测试数据文件不存在: {source_file}")
        
        reader = DataReader(str(source_file))
        sample_data = reader.read_sample_lines(n=3)
        
        print(f"\n解析 {len(sample_data)} 条数据记录...")
        
        all_main_entities = []
        all_relationships = []
        
        for i, data in enumerate(sample_data, 1):
            print(f"\n记录 {i}: {data.get('name', 'Unknown')}")
            main_props, relationships = builder.parse_data(data)
            
            all_main_entities.append(main_props)
            all_relationships.extend(relationships)
            
            print(f"  主实体属性 ({len(main_props)} 个):")
            for key, value in main_props.items():
                # 截断过长的值
                value_str = str(value)
                if len(value_str) > 100:
                    value_str = value_str[:100] + "..."
                print(f"    - {key}: {value_str}")
            print(f"  关系 ({len(relationships)} 个):")
            for rel_type, target_label, target_name, _ in relationships:
                print(f"    - {rel_type} -> {target_label}: {target_name}")
        
        print("\n" + "=" * 80)
        print("解析结果汇总:")
        print("=" * 80)
        print(f"主实体数量: {len(all_main_entities)}")
        print(f"关系总数: {len(all_relationships)}")
        
        # 统计关系类型
        rel_counts = {}
        for rel_type, _, _, _ in all_relationships:
            rel_counts[rel_type] = rel_counts.get(rel_type, 0) + 1
        
        print(f"\n关系类型统计:")
        for rel_type, count in sorted(rel_counts.items()):
            print(f"  {rel_type}: {count} 条")
        
        print("\n✅ 数据解析测试通过！")
        return True
        
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        return False


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="测试图谱构建功能")
    parser.add_argument(
        "--parse-only",
        action="store_true",
        help="仅测试数据解析，不实际构建图谱"
    )
    
    args = parser.parse_args()
    
    if args.parse_only:
        success = test_parse_data_only()
    else:
        success = test_graph_builder_with_three_lines()
    
    sys.exit(0 if success else 1)

