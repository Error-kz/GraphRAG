"""
动态提示词生成器
根据图模式动态生成 NL2Cypher 系统提示词
"""
from typing import List, Dict, Any
from core.graph.schemas import GraphSchema, NodeSchema, RelationshipSchema


class PromptGenerator:
    """动态提示词生成器类"""
    
    def __init__(self, schema: GraphSchema):
        """
        初始化提示词生成器
        
        Args:
            schema: GraphSchema对象
        """
        self.schema = schema
    
    def generate_system_prompt(self) -> str:
        """
        生成系统提示词
        
        Returns:
            完整的系统提示词字符串
        """
        # 1. 构建图模式描述
        schema_description = self._build_schema_description()
        
        # 2. 生成示例查询
        examples = self._generate_examples()
        
        # 3. 组合完整提示词
        prompt = f"""
你是一个专业的Neo4j Cypher查询生成器, 你的任务是将自然语言描述转换为准确, 高效的Cypher查询.

# 图数据库模式
{schema_description}

# 重要规则
1. 始终使用参数化查询风格, 对字符串值使用单引号
2. 确保节点标签和关系类型使用正确的大小写
3. 对于模糊查询, 使用 CONTAINS 或 STARTS WITH 而不是 "="
4. 对于可选模式, 使用 OPTIONAL MATCH
5. 始终考虑查询性能, 使用适当的索引和约束
6. 对于需要返回多个实体的查询, 使用 RETURN 子句明确指定要返回的内容
7. 避免使用可能导致性能问题的查询模式
8. **关系类型语法规则（重要）**：当需要匹配多个关系类型时，只能第一个关系类型前使用冒号，后续关系类型不需要冒号
   - 正确: [r:type1|type2|type3] 或 -[:type1|type2]-
   - 错误: [r:type1|:type2|:type3] 或 -[:type1|:type2]-
9. **COLLECT 函数语法规则（重要）**：COLLECT 函数内部不能使用 AS 别名，AS 必须在函数外面
   - 正确: COLLECT(DISTINCT field.name) AS alias
   - 错误: COLLECT(DISTINCT field.name AS alias)
10. **空值处理**：当查询可能返回空结果时，可以使用 IS NOT NULL 和 <> '' 来过滤空值

# 查询示例
{examples}

注意：在多个关系类型中，只有第一个关系类型前使用冒号，后续关系类型不需要冒号。

现在请根据以下自然语言描述生成Cypher查询:
"""
        return prompt.strip()
    
    def _build_schema_description(self) -> str:
        """
        构建图模式描述
        
        Returns:
            图模式描述字符串
        """
        lines = []
        
        # 节点类型描述
        lines.append("## 节点类型")
        for node in self.schema.nodes:
            prop_list = ", ".join([f"{k} ({v})" for k, v in node.properties.items()])
            lines.append(f"- {node.label}: {prop_list}")
        
        # 关系类型描述
        lines.append("\n## 关系类型")
        for rel in self.schema.relationships:
            lines.append(f"- {rel.from_node} --[{rel.type}]--> {rel.to_node}")
        
        return "\n".join(lines)
    
    def _generate_examples(self) -> str:
        """
        自动生成示例查询
        
        Returns:
            示例查询字符串
        """
        examples = []
        
        # 识别主实体（属性最多的节点）
        main_entity = max(self.schema.nodes, key=lambda n: len(n.properties))
        main_label = main_entity.label
        
        # 为主实体生成基本查询示例
        if main_entity.properties:
            main_name_prop = 'name' if 'name' in main_entity.properties else list(main_entity.properties.keys())[0]
            examples.append(self._generate_basic_query_example(main_label, main_name_prop))
        
        # 为每个关系生成示例
        for rel in self.schema.relationships:
            if rel.from_node == main_label:
                example = self._generate_relationship_example(rel, main_label)
                if example:
                    examples.append(example)
        
        # 生成属性查询示例
        if main_entity.properties and len(main_entity.properties) > 1:
            examples.append(self._generate_property_query_example(main_label, main_entity.properties))
        
        # 生成聚合查询示例
        if len(self.schema.relationships) > 0:
            examples.append(self._generate_collect_example(main_label, self.schema.relationships[0]))
        
        return "\n\n".join(examples)
    
    def _generate_basic_query_example(self, label: str, name_prop: str) -> str:
        """
        生成基本查询示例
        
        Args:
            label: 节点标签
            name_prop: 名称属性
            
        Returns:
            示例字符串
        """
        # 使用通用占位符
        entity_name = "示例实体"
        
        return f"""自然语言: "查找{entity_name}的详细信息"
Cypher: "MATCH (n:{label}) WHERE n.{name_prop}='{entity_name}' RETURN n.{name_prop}, n.*"
"""
    
    def _generate_relationship_example(self, rel: RelationshipSchema, main_label: str) -> str:
        """
        生成关系查询示例
        
        Args:
            rel: 关系模式
            main_label: 主实体标签
            
        Returns:
            示例字符串
        """
        if rel.from_node != main_label:
            return None
        
        # 推断关系语义
        rel_semantic = self._infer_relationship_semantic(rel.type, rel.to_node)
        
        # 获取主实体和目标实体的名称属性
        main_name_prop = 'name'
        target_name_prop = 'name'
        
        main_node = next((n for n in self.schema.nodes if n.label == main_label), None)
        target_node = next((n for n in self.schema.nodes if n.label == rel.to_node), None)
        
        if main_node and 'name' not in main_node.properties:
            main_name_prop = list(main_node.properties.keys())[0] if main_node.properties else 'name'
        
        if target_node and 'name' not in target_node.properties:
            target_name_prop = list(target_node.properties.keys())[0] if target_node.properties else 'name'
        
        main_var = main_label[0].lower()  # 使用标签首字母作为变量名
        target_var = rel.to_node[0].lower()
        
        return f"""自然语言: "查找{rel_semantic['main_entity']}的{rel_semantic['description']}"
Cypher: "MATCH ({main_var}:{main_label})-[r:{rel.type}]->({target_var}:{rel.to_node}) WHERE {main_var}.{main_name_prop}='示例' RETURN {target_var}.{target_name_prop}"
"""
    
    def _infer_relationship_semantic(self, rel_type: str, target_label: str) -> Dict[str, str]:
        """
        推断关系的语义描述
        
        Args:
            rel_type: 关系类型
            target_label: 目标节点标签
            
        Returns:
            语义描述字典
        """
        # 识别主实体（属性最多的节点）
        main_entity = max(self.schema.nodes, key=lambda n: len(n.properties))
        main_label = main_entity.label
        
        # 通用语义映射
        semantic_map = {
            'has_': '拥有',
            'belongs_to_': '属于',
            'needs_': '需要',
            'treated_in': '在...治疗',
            'treated_by': '通过...治疗',
            'cured_by': '通过...治愈',
            'related_to': '与...相关',
            'connected_to': '连接到',
        }
        
        description = target_label.lower()
        for prefix, semantic in semantic_map.items():
            if rel_type.startswith(prefix):
                description = f"{semantic}{target_label.lower()}"
                break
        
        return {
            'main_entity': main_label,
            'description': description
        }
    
    def _generate_property_query_example(self, label: str, properties: Dict[str, str]) -> str:
        """
        生成属性查询示例
        
        Args:
            label: 节点标签
            properties: 属性字典
            
        Returns:
            示例字符串
        """
        # 选择几个主要属性
        main_props = list(properties.keys())[:5]
        prop_list = ", ".join([f"n.{prop}" for prop in main_props])
        
        name_prop = 'name' if 'name' in properties else main_props[0]
        
        return f"""自然语言: "查找某个{label.lower()}的所有信息"
Cypher: "MATCH (n:{label}) WHERE n.{name_prop}='示例' RETURN {prop_list}"
"""
    
    def _generate_collect_example(self, main_label: str, rel: RelationshipSchema) -> str:
        """
        生成聚合查询示例（使用 COLLECT）
        
        Args:
            main_label: 主实体标签
            rel: 关系模式
            
        Returns:
            示例字符串
        """
        main_var = main_label[0].lower()
        target_var = rel.to_node[0].lower()
        
        target_name_prop = 'name'
        target_node = next((n for n in self.schema.nodes if n.label == rel.to_node), None)
        if target_node and 'name' not in target_node.properties:
            target_name_prop = list(target_node.properties.keys())[0] if target_node.properties else 'name'
        
        main_name_prop = 'name'
        main_node = next((n for n in self.schema.nodes if n.label == main_label), None)
        if main_node and 'name' not in main_node.properties:
            main_name_prop = list(main_node.properties.keys())[0] if main_node.properties else 'name'
        
        return f"""自然语言: "查找某个{main_label.lower()}的所有{rel.to_node.lower()}列表"
Cypher: "MATCH ({main_var}:{main_label})-[r:{rel.type}]->({target_var}:{rel.to_node}) WHERE {main_var}.{main_name_prop}='示例' RETURN {main_var}.{main_name_prop}, COLLECT({target_var}.{target_name_prop}) AS {rel.to_node.lower()}_list"
"""
    
    def generate_validation_prompt(self, cypher_query: str) -> str:
        """
        生成验证提示词
        
        Args:
            cypher_query: Cypher查询语句
            
        Returns:
            验证提示词
        """
        schema_desc = self._build_schema_description()
        
        return f"""
请分析以下Cypher查询, 指出其中的任何错误或潜在问题, 并提供改进建议.

# 图数据库模式
{schema_desc}

# 需要验证的查询
{cypher_query}

请按以下格式回答:
错误: [列出所有错误]
建议: [提供改进建议]
"""

