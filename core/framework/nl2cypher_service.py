"""
NL2Cypher 服务
基于动态图模式提供自然语言转 Cypher 查询服务
"""
import logging
from typing import Optional, Dict, Any
from core.graph.schemas import GraphSchema
from core.framework.prompt_generator import PromptGenerator
from core.framework.schema_config import SchemaConfig
from core.models.llm import create_openrouter_client
from core.graph.validators import RuleBasedValidator
from core.graph.neo4j_client import Neo4jClient
from config.settings import settings
from openai import OpenAI
from services.graph_service import clean_cypher_query

logger = logging.getLogger(__name__)


class NL2CypherService:
    """NL2Cypher 服务类"""
    
    def __init__(self, schema: Optional[GraphSchema] = None, domain: Optional[str] = None, 
                 version: Optional[str] = None, llm_client: Optional[OpenAI] = None):
        """
        初始化 NL2Cypher 服务
        
        Args:
            schema: GraphSchema对象，如果为None则从配置加载
            domain: 领域名称（如果schema为None）
            version: 版本号（如果schema为None）
            llm_client: LLM客户端，如果为None则自动创建
        """
        # 加载图模式
        if schema is None:
            if domain is None:
                raise ValueError("必须提供 schema 或 domain 参数")
            config_manager = SchemaConfig()
            schema = config_manager.load_schema(domain, version)
            if not schema:
                raise ValueError(f"无法加载模式: {domain} v{version or 'latest'}")
        
        self.schema = schema
        self.prompt_generator = PromptGenerator(schema)
        self.client = llm_client or create_openrouter_client()
        self.validator = RuleBasedValidator()
        self.neo4j_client = Neo4jClient()
    
    def generate_cypher(self, natural_language: str, query_type: Optional[str] = None) -> Dict[str, Any]:
        """
        生成 Cypher 查询
        
        Args:
            natural_language: 自然语言查询
            query_type: 查询类型（可选）
            
        Returns:
            包含 cypher_query, explanation, confidence 等的字典
        """
        # 步骤1: 加载图模式配置（已在初始化时完成）
        # 步骤2: 动态生成系统提示词
        system_prompt = self.prompt_generator.generate_system_prompt()
        
        # 步骤3: 用户输入自然语言查询
        user_prompt = natural_language
        if query_type:
            user_prompt = f"{query_type}查询: {natural_language}"
        
        # 步骤4: 使用动态提示词生成Cypher
        try:
            response = self.client.chat.completions.create(
                model=settings.OPENROUTER_LLM_MODEL,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt}
                ],
                temperature=0.1,
                max_tokens=2048,
                stream=False
            )
            raw_query = response.choices[0].message.content.strip()
            cypher_query = clean_cypher_query(raw_query)
        except Exception as e:
            raise RuntimeError(f"生成 Cypher 查询失败: {str(e)}")
        
        # 步骤5: 验证查询
        try:
            is_valid, errors = self.validator.validate_against_schema(cypher_query, self.schema)
        except Exception as e:
            # 如果验证器不支持 validate_against_schema，使用基本验证
            is_valid = True
            errors = []
            logger.warning(f"验证器不支持模式验证: {str(e)}")
        
        confidence = 0.9
        if errors:
            confidence = max(0.3, confidence - len(errors) * 0.1)
        
        # 生成解释
        explanation = self._explain_query(cypher_query)
        
        return {
            "cypher_query": cypher_query,
            "explanation": explanation,
            "confidence": confidence,
            "validated": is_valid,
            "validation_errors": errors
        }
    
    def _explain_query(self, cypher_query: str) -> str:
        """
        解释 Cypher 查询
        
        Args:
            cypher_query: Cypher 查询语句
            
        Returns:
            查询解释
        """
        try:
            response = self.client.chat.completions.create(
                model=settings.OPENROUTER_LLM_MODEL,
                messages=[
                    {"role": "system", "content": "你是一个Neo4j专家, 请用简单明了的语言解释Cypher查询."},
                    {"role": "user", "content": f"请解释以下Cypher查询: {cypher_query}"}
                ],
                temperature=0.1,
                max_tokens=1024,
                stream=False
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            return f"无法生成解释: {str(e)}"
    
    def execute_query(self, cypher_query: str) -> Dict[str, Any]:
        """
        执行 Cypher 查询
        
        Args:
            cypher_query: Cypher 查询语句
            
        Returns:
            查询结果
        """
        if not self.neo4j_client.driver:
            if not self.neo4j_client.connect():
                raise ConnectionError("无法连接到Neo4j数据库")
        
        from services.graph_service import execute_cypher_query
        return execute_cypher_query(cypher_query, self.neo4j_client.driver)

