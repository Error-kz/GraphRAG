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
        
        # 3. 生成中文语义映射说明
        semantic_mapping = self._generate_semantic_mapping()
        
        # 4. 组合完整提示词
        prompt = f"""
你是一个专业的Neo4j Cypher查询生成器, 你的任务是将自然语言描述转换为准确, 高效的Cypher查询.

# 图数据库模式
{schema_description}

# 重要规则
0. **严格使用提供的图模式**：只能使用上述模式中的节点标签、关系类型和属性，禁止编造或使用模式未列出的标签/关系/属性。
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

# 中文语义映射（重要）
{semantic_mapping}

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
    
    def _generate_semantic_mapping(self) -> str:
        """
        生成中文语义映射说明
        
        Returns:
            语义映射说明字符串
        """
        lines = []
        lines.append("以下是对关系类型与中文表达的映射规则，请根据用户查询中的关键词和意图正确选择关系类型：")
        lines.append("")
        
        # 按目标节点类型分组关系
        rels_by_target = {}
        for rel in self.schema.relationships:
            if rel.to_node not in rels_by_target:
                rels_by_target[rel.to_node] = []
            rels_by_target[rel.to_node].append(rel)
        
        # 为每个目标节点类型生成映射说明
        for target_label, rels in rels_by_target.items():
            if len(rels) == 0:
                continue
                
            # 获取目标节点的中文描述
            target_node = next((n for n in self.schema.nodes if n.label == target_label), None)
            target_desc = self._get_node_description(target_label)
            
            lines.append(f"## {target_desc}相关关系")
            
            for rel in rels:
                # 自动推断关系的中文语义和关键词
                semantic_info = self._infer_relationship_keywords(rel)
                lines.append(f"- **{rel.type}关系**：{semantic_info['description']}")
                if semantic_info['keywords']:
                    lines.append(f"  - 中文表达：{semantic_info['keywords']}")
                if semantic_info['example']:
                    lines.append(f"  - 查询示例：{semantic_info['example']}")
            
            lines.append("")
        
        # 添加通用映射规则
        lines.append("## 通用映射规则")
        lines.append("1. **否定关系识别**：当关系名称包含 'not'、'no'、'avoid'、'禁止'、'忌' 等否定词时，对应中文表达为'不能'、'忌'、'禁止'、'避免'等")
        lines.append("2. **推荐关系识别**：当关系名称包含 'recommend'、'suggest'、'recommand'、'推荐'、'建议' 等词时，对应中文表达为'推荐'、'建议'、'宜'等")
        lines.append("3. **拥有关系识别**：当关系名称以 'has'、'have'、'拥有' 开头时，对应中文表达为'有'、'包含'、'具备'等")
        lines.append("4. **动作关系识别**：根据关系名称中的动词（如 eat、take、use、do等）推断对应的中文动作表达")
        lines.append("5. **目标节点识别**：根据目标节点类型（如 Food、Drug、Symptom等）推断查询意图")
        lines.append("")
        lines.append("**关键提示**：请仔细分析用户查询中的关键词，根据上述映射规则选择最匹配的关系类型。")
        
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
        
        # 使用通用语义推断生成自然语言示例
        rel_keywords = self._infer_relationship_keywords(rel)
        main_entity_name = rel_semantic["main_entity"]
        target_desc = self._get_node_description(rel.to_node)
        rel_lower = rel.type.lower()
        
        # 生成自然语言示例（基于关系类型模式）
        # 否定关系（not_eat, not_use等）
        if any(neg in rel_lower for neg in ['not', 'no', 'avoid', '禁止', '忌']):
            if 'eat' in rel_lower or 'food' in rel_lower or target_desc == '食物':
                nl_example = f'"{main_entity_name}有什么忌口的吗" 或 "{main_entity_name}不能吃什么"'
            else:
                nl_example = f'"{main_entity_name}不能{target_desc}"'
        # 推荐关系
        elif any(rec in rel_lower for rec in ['recommend', 'suggest', 'recommand', '推荐', '建议']):
            action = self._extract_action_from_rel(rel.type)
            if action:
                nl_example = f'"{main_entity_name}推荐{action}什么{target_desc}"'
            else:
                nl_example = f'"{main_entity_name}推荐什么{target_desc}"'
        # 拥有关系
        elif rel_lower.startswith('has_') or rel_lower.startswith('have_'):
            nl_example = f'"{main_entity_name}有什么{target_desc}"'
        # 其他关系
        else:
            action = self._extract_action_from_rel(rel.type)
            if action:
                nl_example = f'"{main_entity_name}{action}什么{target_desc}"'
            else:
                nl_example = f'"查找{main_entity_name}的{rel_semantic["description"]}"'
        
        return f"""自然语言: {nl_example}
Cypher: "MATCH ({main_var}:{main_label})-[r:{rel.type}]->({target_var}:{rel.to_node}) WHERE {main_var}.{main_name_prop} CONTAINS '示例' RETURN {target_var}.{target_name_prop}"
"""
    
    def _infer_relationship_semantic(self, rel_type: str, target_label: str) -> Dict[str, str]:
        """
        推断关系的语义描述（通用版本）
        
        Args:
            rel_type: 关系类型
            target_label: 目标节点标签
            
        Returns:
            语义描述字典
        """
        # 识别主实体（属性最多的节点）
        main_entity = max(self.schema.nodes, key=lambda n: len(n.properties))
        main_label = main_entity.label
        
        # 获取目标节点的描述
        target_desc = self._get_node_description(target_label)
        
        # 基于关系名称模式推断语义
        rel_lower = rel_type.lower()
        
        # 否定关系
        if any(neg in rel_lower for neg in ['not', 'no', 'avoid', '禁止', '忌']):
            action = self._extract_action_from_rel(rel_type)
            description = f"不能{action}{target_desc}" if action else f"不能{target_desc}（禁止/忌）"
        # 推荐关系
        elif any(rec in rel_lower for rec in ['recommend', 'suggest', 'recommand', '推荐', '建议']):
            action = self._extract_action_from_rel(rel_type)
            description = f"推荐{action}{target_desc}" if action else f"推荐{target_desc}"
        # 拥有关系
        elif rel_lower.startswith('has_') or rel_lower.startswith('have_'):
            description = f"拥有{target_desc}"
        # 需要关系
        elif rel_lower.startswith('needs_') or rel_lower.startswith('need_'):
            description = f"需要{target_desc}"
        # 属于关系
        elif rel_lower.startswith('belongs_to_') or rel_lower.startswith('belong_to_'):
            description = f"属于{target_desc}"
        # 治疗相关
        elif 'cure' in rel_lower or 'treat' in rel_lower:
            if 'department' in rel_lower:
                description = f"就诊科室"
            else:
                description = f"治疗相关的{target_desc}"
        # 动作关系（提取动作词）
        else:
            action = self._extract_action_from_rel(rel_type)
            if action:
                description = f"{action}{target_desc}"
            else:
                description = target_desc
        
        return {
            'main_entity': main_label,
            'description': description
        }
    
    def _infer_relationship_keywords(self, rel: RelationshipSchema) -> Dict[str, str]:
        """
        推断关系的中文关键词和示例
        
        Args:
            rel: 关系模式
            
        Returns:
            包含description、keywords、example的字典
        """
        rel_type = rel.type
        target_label = rel.to_node
        rel_lower = rel_type.lower()
        
        # 获取目标节点描述
        target_desc = self._get_node_description(target_label)
        
        # 推断描述
        semantic = self._infer_relationship_semantic(rel_type, target_label)
        description = semantic['description']
        
        # 推断关键词
        keywords = []
        
        # 否定关系关键词
        if any(neg in rel_lower for neg in ['not', 'no', 'avoid', '禁止', '忌']):
            keywords.extend(['忌', '不能', '禁止', '避免', '忌口', '忌吃', '不能吃', '禁止吃'])
        # 推荐关系关键词
        elif any(rec in rel_lower for rec in ['recommend', 'suggest', 'recommand', '推荐', '建议']):
            keywords.extend(['推荐', '建议', '宜', '推荐吃', '建议吃', '推荐用'])
        # 拥有关系关键词
        elif rel_lower.startswith('has_') or rel_lower.startswith('have_'):
            keywords.extend(['有', '包含', '具备', '有什么'])
        # 动作关系关键词
        else:
            action = self._extract_action_from_rel(rel_type)
            if action:
                keywords.append(action)
        
        # 生成示例
        main_label = semantic['main_entity']
        example = None
        
        if keywords:
            # 使用第一个关键词生成示例
            keyword = keywords[0]
            if '忌' in keyword or '不能' in keyword:
                example = f"'{main_label}有什么忌口的吗' 或 '{main_label}不能吃什么' → 使用 {rel_type} 关系"
            elif '推荐' in keyword or '建议' in keyword:
                example = f"'{main_label}推荐什么' → 使用 {rel_type} 关系"
            elif '有' in keyword:
                example = f"'{main_label}有什么{target_desc}' → 使用 {rel_type} 关系"
            else:
                example = f"'{main_label}的{description}' → 使用 {rel_type} 关系"
        
        return {
            'description': description,
            'keywords': '、'.join([f"'{k}'" for k in keywords[:5]]) if keywords else None,
            'example': example
        }
    
    def _get_node_description(self, label: str) -> str:
        """
        获取节点的中文描述（基于命名模式自动推断）
        
        Args:
            label: 节点标签
            
        Returns:
            中文描述
        """
        # 首先尝试从schema中获取节点信息
        node = next((n for n in self.schema.nodes if n.label == label), None)
        
        # 如果有description或desc属性，优先使用（虽然当前schema没有，但为未来扩展预留）
        if node:
            # 可以检查是否有description相关的属性
            pass
        
        # 基于命名模式自动推断
        return self._infer_node_description_from_label(label)
    
    def _infer_node_description_from_label(self, label: str) -> str:
        """
        基于节点标签的命名模式推断中文描述
        
        Args:
            label: 节点标签
            
        Returns:
            中文描述
        """
        label_lower = label.lower()
        
        # 常见英文词根到中文的映射（基于模式匹配）
        word_mappings = {
            # 实体类型
            'food': '食物',
            'drug': '药物',
            'medicine': '药物',
            'symptom': '症状',
            'disease': '疾病',
            'illness': '疾病',
            'department': '科室',
            'check': '检查',
            'examination': '检查',
            'person': '人员',
            'people': '人员',
            'user': '用户',
            'organization': '组织',
            'org': '组织',
            'company': '公司',
            'location': '地点',
            'place': '地点',
            'address': '地址',
            'category': '分类',
            'type': '类型',
            'tag': '标签',
            'product': '产品',
            'item': '物品',
            'order': '订单',
            'transaction': '交易',
            'event': '事件',
            'article': '文章',
            'post': '帖子',
            'comment': '评论',
        }
        
        # 直接匹配
        if label_lower in word_mappings:
            return word_mappings[label_lower]
        
        # 部分匹配（检查是否包含已知词根）
        for word, desc in word_mappings.items():
            if word in label_lower:
                return desc
        
        # 处理复合词（如AcompanyDisease -> 并发症）
        # 分割PascalCase或camelCase
        import re
        words = re.findall(r'[A-Z]?[a-z]+|[A-Z]+(?=[A-Z]|$)', label)
        
        if words:
            # 检查第一个词
            first_word = words[0].lower()
            if first_word in word_mappings:
                return word_mappings[first_word]
            
            # 检查所有词
            for word in words:
                word_lower = word.lower()
                if word_lower in word_mappings:
                    return word_mappings[word_lower]
        
        # 如果无法推断，返回标签的小写形式（作为通用描述）
        # 对于中文标签，直接返回
        if any('\u4e00' <= char <= '\u9fff' for char in label):
            return label
        
        # 对于英文标签，转换为更友好的形式
        # 将PascalCase转换为空格分隔的小写形式
        if re.match(r'^[A-Z][a-z]+', label):
            # PascalCase: 在每个大写字母前插入空格（除了第一个）
            spaced = re.sub(r'(?<!^)(?=[A-Z])', ' ', label)
            return spaced.lower()
        
        return label.lower()
    
    def _extract_action_from_rel(self, rel_type: str) -> str:
        """
        从关系名称中提取动作词
        
        Args:
            rel_type: 关系类型
            
        Returns:
            动作词（中文）
        """
        rel_lower = rel_type.lower()
        
        # 动作词映射
        action_map = {
            'eat': '吃',
            'take': '服用',
            'use': '使用',
            'do': '做',
            'have': '有',
            'get': '获取',
            'visit': '访问',
            'see': '看',
            'check': '检查',
        }
        
        # 查找匹配的动作词
        for eng_action, cn_action in action_map.items():
            if eng_action in rel_lower:
                return cn_action
        
        # 如果没有匹配，尝试从下划线分割的关系名中提取
        parts = rel_type.split('_')
        if len(parts) > 1:
            # 跳过常见前缀
            skip_prefixes = ['not', 'no', 'do', 'recommand', 'recommend', 'has', 'have']
            for part in parts:
                if part.lower() not in skip_prefixes and part.lower() in action_map:
                    return action_map[part.lower()]
        
        return ""
    
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

