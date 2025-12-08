"""
知识图谱模式定义
定义Neo4j图数据库的节点和关系模式
"""
from pydantic import BaseModel
from typing import Dict, List


class NodeSchema(BaseModel):
    """节点模式定义"""
    label: str
    properties: Dict[str, str]


class RelationshipSchema(BaseModel):
    """关系模式定义"""
    from_node: str
    to_node: str
    type: str
    properties: Dict[str, str]


class GraphSchema(BaseModel):
    """图模式定义"""
    nodes: List[NodeSchema]
    relationships: List[RelationshipSchema]


# 通用示例图模型（仅用于演示，实际使用时应该从配置文件加载）
EXAMPLE_SCHEMA = GraphSchema(
    nodes=[
        NodeSchema(
            label="Entity",
            properties={
                "name": "string",
                "description": "string"
            }
        ),
        NodeSchema(
            label="Category",
            properties={"name": "string"}
        )
    ],
    relationships=[
        RelationshipSchema(
            type='belongs_to',
            from_node='Entity',
            to_node='Category',
            properties={}
        )
    ]
)

