"""
统一的 Embedding 模型封装
使用智谱官方 OpenAI 兼容接口生成向量
"""
from langchain.embeddings.base import Embeddings
from openai import OpenAI
from config.settings import settings


class ZhipuAIEmbeddings(Embeddings):
    """
    Embedding模型封装（使用智谱官方 API）
    保持向后兼容的类名
    统一管理，避免在多个文件中重复定义
    """
    
    def __init__(self, client: OpenAI = None, model: str = None):
        """
        初始化Embedding模型
        
        Args:
            client: OpenAI 兼容客户端实例（智谱），如果为None则自动创建
            model: 模型名称，如果为None则使用配置中的默认模型
        """
        if client is None:
            api_key = settings.ZHIPU_API_KEY
            if not api_key:
                raise ValueError("ZHIPU_API_KEY 未配置，请设置环境变量或 .env 文件")
            
            self.client = OpenAI(
                api_key=api_key,
                # 智谱官方 OpenAI 兼容接口
                base_url='https://open.bigmodel.cn/api/paas/v4'
            )
        else:
            self.client = client
        
        self.model = model or settings.ZHIPU_EMBEDDING_MODEL
    
    def embed_documents(self, texts: list) -> list:
        """
        批量生成文档的嵌入向量
        
        Args:
            texts: 文本列表
            
        Returns:
            嵌入向量列表
        """
        embeddings = []
        for text in texts:
            try:
                # 使用智谱 OpenAI 兼容 embeddings API
                response = self.client.embeddings.create(
                    model=self.model,
                    input=text
                )
                embeddings.append(response.data[0].embedding)
            except Exception as e:
                raise ValueError(f"Embedding 生成失败: {str(e)}，请检查模型 {self.model} 是否支持 embedding")
        return embeddings
    
    def embed_query(self, text: str) -> list:
        """
        生成查询文本的嵌入向量
        
        Args:
            text: 查询文本
            
        Returns:
            嵌入向量
        """
        return self.embed_documents([text])[0]

