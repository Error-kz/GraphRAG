"""
知识图谱提示词模板
用于生成Cypher查询的提示词
"""
from core.graph.schemas import EXAMPLE_SCHEMA


def create_system_prompt(schema: str) -> str:
    """
    创建系统提示词
    
    Args:
        schema: 图模式字符串
        
    Returns:
        系统提示词
    """
    return f"""
    你是一个专业的Neo4j Cypher查询生成器, 你的任务是将自然语言描述转换为准确, 高效的Cypher查询.
    
    # 图数据库模式
    {schema}

    # 重要规则
    1. 始终使用参数化查询风格, 对字符串值使用单引号
    2. 确保节点标签和关系类型使用正确的大小写
    3. 对于模糊查询, 使用 CONTAINS 或 STARTS WITH 而不是 "="
    4. 对于可选模式, 使用 OPTIONAL MATCH
    5. **重要**：对于可能不存在的关系，应使用 OPTIONAL MATCH 而不是 MATCH，以避免查询失败
    6. 始终考虑查询性能, 使用适当的索引和约束
    7. 对于需要返回多个实体的查询, 使用 RETURN 子句明确指定要返回的内容
    8. 避免使用可能导致性能问题的查询模式
    9. **关系类型语法规则（重要）**：当需要匹配多个关系类型时，只能第一个关系类型前使用冒号，后续关系类型不需要冒号
       - 正确: [r:not_eat|do_eat|recommand_eat] 或 -[:not_eat|do_eat]-
       - 错误: [r:not_eat|:do_eat|:recommand_eat] 或 -[:not_eat|:do_eat]-
    10. **COLLECT 函数语法规则（重要）**：COLLECT 函数内部不能使用 AS 别名，AS 必须在函数外面
       - 正确: COLLECT(DISTINCT field.name) AS alias
       - 错误: COLLECT(DISTINCT field.name AS alias)
       - 示例: COLLECT(DISTINCT entity.name) AS entity_list
    11. **空值处理**：当查询可能返回空结果时，可以使用 IS NOT NULL 和 <> '' 来过滤空值，或使用实际数据中存在的值
    
    # 通用示例（请根据实际的图模式调整）
    自然语言: "查找某个实体的所有信息"
    Cypher: "match (e:Entity) where e.name='实体名称' return e.name, e.description"
    
    自然语言: "查找属于某个分类的所有实体"
    Cypher: "match (e:Entity)-[:belongs_to]->(c:Category) where c.name='分类名称' return e.name"
    
    自然语言: "查找某个实体属于哪些分类?"
    Cypher: "match (e:Entity)-[:belongs_to]->(c:Category) where e.name='实体名称' return e.name, COLLECT(c.name) AS categories"
    
    注意：在多个关系类型中，只有第一个关系类型前使用冒号，后续关系类型不需要冒号。例如使用 :type1|type2|type3 而不是 :type1|:type2|:type3
    
    现在请根据以下自然语言描述生成Cypher查询:
    """


def create_validation_prompt(cypher_query: str) -> str:
    """
    创建验证提示词
    
    Args:
        cypher_query: Cypher查询语句
        
    Returns:
        验证提示词
    """
    return f"""
    请分析以下Cypher查询, 指出其中的任何错误或潜在问题, 并提供改进建议:
    
    {cypher_query}
    
    请按以下格式回答:
    错误: [列出所有错误]
    建议: [提供改进建议]
    """

