"""
模型模块
包含Embedding模型和LLM模型
"""
from core.models.embeddings import ZhipuAIEmbeddings
from core.models.llm import create_openrouter_client, create_deepseek_client, generate_answer, generate_deepseek_answer

__all__ = [
    'ZhipuAIEmbeddings',
    'create_openrouter_client',
    'create_deepseek_client',  # 向后兼容
    'generate_answer',
    'generate_deepseek_answer',  # 向后兼容
]

