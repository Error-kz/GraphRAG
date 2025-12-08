"""
通用知识图谱构建框架
支持自动推断图模式并构建知识图谱
"""
from .data_reader import DataReader
from .schema_generator import SchemaGenerator
from .schema_config import SchemaConfig
from .graph_builder import GraphBuilder
from .prompt_generator import PromptGenerator

# 延迟导入SchemaInferrer和NL2CypherService，因为它们依赖openai
try:
    from .schema_inferrer import SchemaInferrer
    from .nl2cypher_service import NL2CypherService
    __all__ = [
        'DataReader',
        'SchemaInferrer',
        'SchemaGenerator',
        'SchemaConfig',
        'GraphBuilder',
        'PromptGenerator',
        'NL2CypherService',
    ]
except ImportError:
    __all__ = [
        'DataReader',
        'SchemaGenerator',
        'SchemaConfig',
        'GraphBuilder',
        'PromptGenerator',
    ]

