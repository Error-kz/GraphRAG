"""
通用图谱构建器
根据推断出的图模式动态构建知识图谱
"""
import json
import re
from typing import Dict, Any, List, Set, Optional, Tuple
from pathlib import Path
from core.graph.neo4j_client import Neo4jClient
from core.framework.data_reader import DataReader
from core.framework.schema_config import SchemaConfig
from core.graph.schemas import GraphSchema, NodeSchema, RelationshipSchema


class GraphBuilder:
    """通用图谱构建器类"""
    
    def __init__(self, schema: GraphSchema, neo4j_client: Optional[Neo4jClient] = None):
        """
        初始化图谱构建器
        
        Args:
            schema: GraphSchema对象，包含节点和关系定义
            neo4j_client: Neo4j客户端，如果为None则自动创建
        """
        self.schema = schema
        self.client = neo4j_client or Neo4jClient()
        
        # 构建节点标签映射（label -> NodeSchema）
        self.node_schemas = {node.label: node for node in schema.nodes}
        
        # 构建关系映射（from_node -> to_node -> [RelationshipSchema]）
        self.relationship_map: Dict[str, Dict[str, List[RelationshipSchema]]] = {}
        for rel in schema.relationships:
            if rel.from_node not in self.relationship_map:
                self.relationship_map[rel.from_node] = {}
            if rel.to_node not in self.relationship_map[rel.from_node]:
                self.relationship_map[rel.from_node][rel.to_node] = []
            self.relationship_map[rel.from_node][rel.to_node].append(rel)
        
        # 识别主实体（通常是第一个节点，或者包含最多属性的节点）
        self.main_entity_label = self._identify_main_entity()
        
        # 数据解析映射（字段名 -> 关系类型 -> 目标节点）
        self.field_mapping = self._build_field_mapping()
    
    def _identify_main_entity(self) -> str:
        """
        识别主实体标签
        
        Returns:
            主实体标签
        """
        if not self.schema.nodes:
            raise ValueError("图模式中没有定义节点")
        
        # 优先选择属性最多的节点作为主实体
        main_node = max(self.schema.nodes, key=lambda n: len(n.properties))
        return main_node.label
    
    def _build_field_mapping(self) -> Dict[str, Tuple[str, str]]:
        """
        构建字段到关系的映射
        
        Returns:
            字段名 -> (关系类型, 目标节点标签) 的映射
        """
        mapping = {}
        
        # 根据关系定义推断字段映射
        # 例如：has_symptom 关系可能对应 symptom 字段
        for rel in self.schema.relationships:
            # 尝试多种字段名推断方式
            possible_fields = self._relationship_to_fields(rel.type, rel.to_node)
            for field_name in possible_fields:
                mapping[field_name] = (rel.type, rel.to_node)
        
        return mapping
    
    def _relationship_to_fields(self, rel_type: str, target_label: str) -> List[str]:
        """
        将关系类型转换为可能的字段名列表（通用实现）
    
        使用多种启发式方法推断可能的字段名，不依赖特定领域
        
        Args:
            rel_type: 关系类型（如：has_symptom, belongs_to_category）
            target_label: 目标节点标签（如：Symptom, Category）
            
        Returns:
            可能的字段名列表（如：['symptom', 'symptoms']）
        """
        fields = []
        
        # 方式1: 从关系类型移除常见前缀和后缀
        # 常见的关系类型前缀
        prefixes = [
            'has_', 'have_', 'contains_', 'includes_',
            'belongs_to_', 'belong_to_',
            'needs_', 'need_', 'requires_', 'require_',
            'treated_in_', 'treated_by_', 'treated_with_',
            'cured_by_', 'cured_with_',
            'related_to_', 'relates_to_',
            'connected_to_', 'connects_to_',
            'linked_to_', 'links_to_',
            'associated_with_', 'associates_with_',
        ]
        
        field = rel_type
        for prefix in prefixes:
            if field.lower().startswith(prefix.lower()):
                field = field[len(prefix):]
                break
        
        # 移除常见后缀
        suffixes = ['_of', '_to', '_from', '_with', '_by', '_in']
        for suffix in suffixes:
            if field.lower().endswith(suffix.lower()):
                field = field[:-len(suffix)]
                break
        
        if field:
            fields.append(field)
            # 添加复数形式（简单规则）
            if not field.endswith('s'):
                fields.append(field + 's')
            elif field.endswith('s') and len(field) > 1:
                # 尝试单数形式（移除末尾的s）
                singular = field[:-1]
                if singular:
                    fields.append(singular)
        
        # 方式2: 从目标节点标签推断
        target_field = target_label.lower()
        fields.append(target_field)
        
        # 生成常见的字段名变体
        # 2.1: 复数形式
        if not target_field.endswith('s'):
            fields.append(target_field + 's')
        elif target_field.endswith('s') and len(target_field) > 1:
            fields.append(target_field[:-1])  # 单数形式
        
        # 2.2: 下划线变体（如果标签是驼峰命名）
        if not '_' in target_field and target_field:
            # 尝试在单词边界插入下划线（简单启发式）
            # 例如：CureWay -> cure_way
            camel_case_parts = []
            current_word = ''
            for char in target_field:
                if char.isupper() and current_word:
                    camel_case_parts.append(current_word.lower())
                    current_word = char.lower()
                else:
                    current_word += char.lower()
            if current_word:
                camel_case_parts.append(current_word)
            
            if len(camel_case_parts) > 1:
                snake_case = '_'.join(camel_case_parts)
                fields.append(snake_case)
                fields.append(snake_case + 's')
        
        # 2.3: 常见前缀变体
        # 如果目标标签可能是某种类型，尝试添加常见前缀
        common_prefixes = ['item_', 'list_', 'set_', 'collection_']
        for prefix in common_prefixes:
            fields.append(prefix + target_field)
        
        # 方式3: 从关系类型和目标标签的组合推断
        # 如果关系类型包含目标标签的信息，提取出来
        rel_lower = rel_type.lower()
        target_lower = target_label.lower()
        
        # 检查关系类型中是否包含目标标签的变体
        if target_lower in rel_lower:
            # 提取目标标签在关系类型中的位置
            idx = rel_lower.find(target_lower)
            if idx > 0:
                # 提取前面的部分作为可能的字段名
                before = rel_type[:idx].rstrip('_').lower()
                if before:
                    fields.append(before + '_' + target_lower)
        
        # 方式4: 基于常见命名模式的推断
        # 如果关系类型是 "X_to_Y" 或 "X_of_Y" 格式，X 可能是字段名
        pattern_match = re.match(r'^(.+?)_(?:to|of|from|with|by|in)_(.+)$', rel_type.lower())
        if pattern_match:
            prefix_part = pattern_match.group(1)
            suffix_part = pattern_match.group(2)
            # 如果后缀部分匹配目标标签，前缀部分可能是字段名
            if suffix_part in target_lower or target_lower in suffix_part:
                fields.append(prefix_part)
                if not prefix_part.endswith('s'):
                    fields.append(prefix_part + 's')
        
        # 去重并返回（保持顺序）
        seen = set()
        unique_fields = []
        for field in fields:
            if field and field not in seen:
                seen.add(field)
                unique_fields.append(field)
        
        return unique_fields
    
    def load_schema_from_file(self, schema_file: str) -> GraphSchema:
        """
        从文件加载图模式（已废弃，使用构造函数传入）
        
        Args:
            schema_file: 模式文件路径
            
        Returns:
            GraphSchema对象
        """
        config_manager = SchemaConfig()
        # 从文件路径提取领域和版本
        # 例如：config/schemas/medical_schema_v1.0.json
        path = Path(schema_file)
        name_parts = path.stem.split('_schema_v')
        if len(name_parts) == 2:
            domain = name_parts[0]
            version = name_parts[1]
            return config_manager.load_schema(domain, version)
        else:
            raise ValueError(f"无法从文件名解析领域和版本: {schema_file}")
    
    def parse_data(self, data: Dict[str, Any]) -> Tuple[Dict[str, Any], List[Tuple[str, str, str, Any]]]:
        """
        根据模式解析单条数据
        
        Args:
            data: 单条数据记录
            
        Returns:
            (主实体属性字典, 关系列表)
            关系列表格式: [(关系类型, 目标节点标签, 目标节点名称, 额外属性), ...]
        """
        # 提取主实体属性
        main_entity_props = {}
        main_node_schema = self.node_schemas.get(self.main_entity_label)
        
        if not main_node_schema:
            raise ValueError(f"主实体节点 '{self.main_entity_label}' 不存在于模式中")
        
        # 提取主实体的所有属性
        for prop_name in main_node_schema.properties.keys():
            if prop_name in data:
                value = data[prop_name]
                # 处理列表类型（转换为字符串）
                if isinstance(value, list):
                    value = str(value)
                main_entity_props[prop_name] = value
        
        # 提取关系
        relationships = []
        
        for field_name, (rel_type, target_label) in self.field_mapping.items():
            if field_name in data:
                field_value = data[field_name]
                
                # 处理列表类型的字段
                if isinstance(field_value, list):
                    for item in field_value:
                        if item:  # 跳过空值
                            relationships.append((rel_type, target_label, str(item), {}))
                elif field_value:  # 处理单个值
                    relationships.append((rel_type, target_label, str(field_value), {}))
        
        # 特殊处理：确保所有关系都被正确识别
        # 检查是否有遗漏的字段（通过目标节点标签反向查找）
        processed_fields = set(self.field_mapping.keys())
        for key, value in data.items():
            if key not in processed_fields and key not in main_entity_props:
                # 尝试通过值类型和内容推断
                if isinstance(value, list) and value:
                    # 可能是关联实体列表
                    for rel in self.schema.relationships:
                        # 检查目标节点标签是否与字段名相关
                        target_lower = rel.to_node.lower()
                        if target_lower in key.lower() or key.lower() in target_lower:
                            for item in value:
                                if item:
                                    relationships.append((rel.type, rel.to_node, str(item), {}))
                            break
        
        return main_entity_props, relationships
    
    def build_graph(self, data_file: str, batch_size: int = 100, clear_existing: bool = False):
        """
        构建知识图谱
        
        Args:
            data_file: 数据文件路径
            batch_size: 批量处理大小
            clear_existing: 是否清空现有图谱
        """
        print("=" * 80)
        print("开始构建知识图谱")
        print("=" * 80)
        
        # 连接 Neo4j
        if not self.client.connect():
            raise ConnectionError("无法连接到Neo4j数据库")
        
        try:
            # 清空现有图谱（如果需要）
            if clear_existing:
                print("\n[清理] 清空现有图谱...")
                self._clear_graph()
                print("✅ 图谱已清空")
            
            # 读取数据文件
            print(f"\n[步骤1] 加载图模式...")
            print(f"主实体: {self.main_entity_label}")
            print(f"节点类型: {[node.label for node in self.schema.nodes]}")
            print(f"关系类型: {[rel.type for rel in self.schema.relationships]}")
            
            print(f"\n[步骤2] 读取完整数据文件: {data_file}")
            reader = DataReader(data_file)
            
            # 批量处理数据
            main_entities = []
            all_relationships = []
            node_collections: Dict[str, Set[str]] = {node.label: set() for node in self.schema.nodes}
            
            count = 0
            with open(data_file, 'r', encoding='utf-8') as f:
                for line in f:
                    if not line.strip():
                        continue
                    
                    try:
                        data = json.loads(line.strip())
                        main_props, relationships = self.parse_data(data)
                        
                        # 收集主实体
                        if main_props.get('name'):
                            main_entities.append(main_props)
                            node_collections[self.main_entity_label].add(main_props['name'])
                        
                        # 收集关系和关联实体
                        for rel_type, target_label, target_name, extra_props in relationships:
                            all_relationships.append((main_props.get('name'), rel_type, target_label, target_name))
                            node_collections[target_label].add(target_name)
                        
                        count += 1
                        if count % 100 == 0:
                            print(f"  已解析 {count} 条数据...")
                    
                    except Exception as e:
                        print(f"  警告: 解析第 {count + 1} 行数据失败: {str(e)}")
                        continue
            
            print(f"✅ 数据读取完成，共 {count} 条记录")
            print(f"  主实体数量: {len(main_entities)}")
            print(f"  关系数量: {len(all_relationships)}")
            
            # 步骤3: 根据模式动态解析数据（已在上面完成）
            print(f"\n[步骤3] 数据解析完成")
            print(f"  识别到的主实体: {self.main_entity_label} ({len(main_entities)} 个)")
            for label, nodes in node_collections.items():
                if nodes:
                    print(f"  识别到的关联实体: {label} ({len(nodes)} 个)")
            
            # 步骤4: 批量创建节点和关系
            print(f"\n[步骤4] 批量创建节点和关系...")
            
            # 创建所有节点
            for label, nodes in node_collections.items():
                if nodes:
                    self._create_nodes_batch(label, list(nodes))
            
            # 创建主实体节点（带属性）
            if main_entities:
                self._create_main_entities_batch(main_entities)
            
            # 创建关系
            if all_relationships:
                self._create_relationships_batch(all_relationships)
            
            # 步骤5: 验证图谱完整性
            print(f"\n[步骤5] 验证图谱完整性...")
            stats = self._validate_graph()
            
            print("\n" + "=" * 80)
            print("图谱构建完成！")
            print("=" * 80)
            print(f"\n节点统计:")
            for label, count in stats['nodes'].items():
                print(f"  {label}: {count} 个")
            print(f"\n关系统计:")
            for rel_type, count in stats['relationships'].items():
                print(f"  {rel_type}: {count} 条")
            print("=" * 80)
        
        finally:
            self.client.close()
    
    def _clear_graph(self):
        """清空图谱"""
        with self.client.driver.session() as session:
            session.run("MATCH (n) DETACH DELETE n")
    
    def _create_nodes_batch(self, label: str, node_names: List[str]):
        """
        批量创建简单节点（只有name属性）
        
        Args:
            label: 节点标签
            node_names: 节点名称列表
        """
        if not node_names:
            return
        
        print(f"  创建 {label} 节点 ({len(node_names)} 个)...")
        
        with self.client.driver.session() as session:
            # 使用 UNWIND 批量创建
            query = f"""
            UNWIND $nodes AS node_name
            MERGE (n:{label} {{name: node_name}})
            """
            session.run(query, nodes=node_names)
        
        print(f"    ✅ {label} 节点创建完成")
    
    def _create_main_entities_batch(self, entities: List[Dict[str, Any]]):
        """
        批量创建主实体节点（带完整属性）
        
        Args:
            entities: 主实体属性列表
        """
        if not entities:
            return
        
        print(f"  创建 {self.main_entity_label} 节点 ({len(entities)} 个)...")
        
        with self.client.driver.session() as session:
            for entity in entities:
                try:
                    # 构建 SET 子句
                    set_clauses = []
                    params = {'name': entity.get('name', '')}
                    
                    for key, value in entity.items():
                        if key != 'name' and value:
                            set_clauses.append(f"n.{key} = ${key}")
                            params[key] = value
                    
                    if set_clauses:
                        query = f"""
                        MERGE (n:{self.main_entity_label} {{name: $name}})
                        SET {', '.join(set_clauses)}
                        """
                    else:
                        query = f"""
                        MERGE (n:{self.main_entity_label} {{name: $name}})
                        """
                    
                    session.run(query, **params)
                
                except Exception as e:
                    print(f"    警告: 创建节点失败 {entity.get('name', 'unknown')}: {str(e)}")
        
        print(f"    ✅ {self.main_entity_label} 节点创建完成")
    
    def _create_relationships_batch(self, relationships: List[Tuple[str, str, str, str]]):
        """
        批量创建关系
        
        Args:
            relationships: 关系列表，格式: (主实体名称, 关系类型, 目标节点标签, 目标节点名称)
        """
        if not relationships:
            return
        
        # 按关系类型分组
        rel_groups: Dict[str, List[Tuple[str, str, str]]] = {}
        for main_name, rel_type, target_label, target_name in relationships:
            key = f"{rel_type}:{target_label}"
            if key not in rel_groups:
                rel_groups[key] = []
            rel_groups[key].append((main_name, target_name))
        
        print(f"  创建关系 ({len(relationships)} 条)...")
        
        with self.client.driver.session() as session:
            for key, rels in rel_groups.items():
                rel_type, target_label = key.split(':')
                
                try:
                    query = f"""
                    UNWIND $rels AS rel
                    MATCH (a:{self.main_entity_label} {{name: rel.from}})
                    MATCH (b:{target_label} {{name: rel.to}})
                    MERGE (a)-[r:{rel_type}]->(b)
                    """
                    rel_data = [{"from": f, "to": t} for f, t in rels]
                    session.run(query, rels=rel_data)
                    print(f"    ✅ {rel_type} 关系创建完成 ({len(rels)} 条)")
                
                except Exception as e:
                    print(f"    警告: 创建关系失败 {rel_type}: {str(e)}")
    
    def _validate_graph(self) -> Dict[str, Any]:
        """
        验证图谱完整性
        
        Returns:
            统计信息字典
        """
        stats = {
            'nodes': {},
            'relationships': {}
        }
        
        with self.client.driver.session() as session:
            # 统计节点
            for label in self.node_schemas.keys():
                result = session.run(f"MATCH (n:{label}) RETURN count(n) AS count")
                count = result.single()['count']
                stats['nodes'][label] = count
            
            # 统计关系
            for rel in self.schema.relationships:
                result = session.run(
                    f"MATCH ()-[r:{rel.type}]->() RETURN count(r) AS count"
                )
                count = result.single()['count']
                stats['relationships'][rel.type] = count
        
        return stats

