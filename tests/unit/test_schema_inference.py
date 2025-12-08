"""
测试模式推断功能
"""
import sys
from pathlib import Path

# 将项目根目录添加到 Python 路径
project_root = Path(__file__).parent.parent.parent
sys.path.insert(0, str(project_root))

import json
from core.framework import DataReader, SchemaGenerator, SchemaConfig
from core.graph.schemas import GraphSchema


def test_data_reader():
    """测试数据读取器"""
    print("测试数据读取器...")
    reader = DataReader("data/raw/medical.jsonl")
    first_line = reader.read_first_line()
    
    assert first_line is not None
    assert "name" in first_line
    print(f"✅ 数据读取器测试通过，读取到 {len(first_line)} 个字段")


def test_schema_generator():
    """测试模式生成器"""
    print("\n测试模式生成器...")
    
    # 模拟推断出的模式
    inferred_schema = {
        "nodes": [
            {
                "label": "Disease",
                "properties": {
                    "name": "string",
                    "desc": "string"
                }
            },
            {
                "label": "Symptom",
                "properties": {
                    "name": "string"
                }
            }
        ],
        "relationships": [
            {
                "type": "has_symptom",
                "from_node": "Disease",
                "to_node": "Symptom",
                "properties": {}
            }
        ]
    }
    
    generator = SchemaGenerator()
    schema = generator.generate_schema(inferred_schema)
    
    assert isinstance(schema, GraphSchema)
    assert len(schema.nodes) == 2
    assert len(schema.relationships) == 1
    
    # 验证模式
    is_valid, errors = generator.validate_schema(schema)
    assert is_valid, f"模式验证失败: {errors}"
    
    print("✅ 模式生成器测试通过")


def test_schema_config():
    """测试模式配置管理"""
    print("\n测试模式配置管理...")
    
    # 创建测试模式
    from core.graph.schemas import NodeSchema, RelationshipSchema
    
    test_schema = GraphSchema(
        nodes=[
            NodeSchema(label="TestNode", properties={"name": "string"})
        ],
        relationships=[
            RelationshipSchema(
                type="test_rel",
                from_node="TestNode",
                to_node="TestNode",
                properties={}
            )
        ]
    )
    
    config_manager = SchemaConfig()
    config_file = config_manager.save_schema(test_schema, "test", "1.0")
    
    assert Path(config_file).exists()
    
    # 加载模式
    loaded_schema = config_manager.load_schema("test", "1.0")
    assert loaded_schema is not None
    assert len(loaded_schema.nodes) == 1
    assert len(loaded_schema.relationships) == 1
    
    print("✅ 模式配置管理测试通过")


if __name__ == "__main__":
    try:
        test_data_reader()
        test_schema_generator()
        test_schema_config()
        print("\n" + "=" * 80)
        print("所有测试通过！")
        print("=" * 80)
    except Exception as e:
        print(f"\n❌ 测试失败: {str(e)}")
        import traceback
        traceback.print_exc()
        sys.exit(1)

