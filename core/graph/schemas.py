"""
知识图谱模式定义
定义Neo4j图数据库的节点和关系模式
"""
import os
import json
from pathlib import Path
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


def _load_schema_from_json(file_path: Path) -> GraphSchema:
    """
    从 JSON 文件加载图模式。
    该方法用于消除示例模式带来的模型幻觉，强制使用真实的模式配置。
    """
    if not file_path.exists():
        raise FileNotFoundError(f"模式文件不存在: {file_path}")
    with file_path.open("r", encoding="utf-8") as f:
        data = json.load(f)
    return GraphSchema(**data)


# 默认从环境变量读取模式文件路径，未配置时回落到 medical_schema_v1.0.json
SCHEMA_FILE_ENV = os.getenv("GRAPH_SCHEMA_FILE")
DEFAULT_SCHEMA_FILE = Path(__file__).parent.parent.parent / "config" / "schemas" / "medical_schema_v1.0.json"
SCHEMA_FILE = Path(SCHEMA_FILE_ENV).expanduser() if SCHEMA_FILE_ENV else DEFAULT_SCHEMA_FILE
EXAMPLE_SCHEMA = _load_schema_from_json(SCHEMA_FILE)

