"""
通用知识图谱构建框架
支持自动推断图模式并构建知识图谱
"""
from .data_reader import DataReader
from .schema_generator import SchemaGenerator
from .schema_config import SchemaConfig

# 延迟导入SchemaInferrer，因为它依赖openai
try:
    from .schema_inferrer import SchemaInferrer
    __all__ = [
        'DataReader',
        'SchemaInferrer',
        'SchemaGenerator',
        'SchemaConfig',
    ]
except ImportError:
    __all__ = [
        'DataReader',
        'SchemaGenerator',
        'SchemaConfig',
    ]

