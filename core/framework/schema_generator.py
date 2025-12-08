"""
模式生成器
将推断出的模式转换为GraphSchema对象
"""
from typing import Dict, Any, List
from core.graph.schemas import GraphSchema, NodeSchema, RelationshipSchema


class SchemaGenerator:
    """模式生成器类"""
    
    def generate_schema(self, inferred_schema: Dict[str, Any]) -> GraphSchema:
        """
        生成GraphSchema对象
        
        Args:
            inferred_schema: 推断出的模式字典
            
        Returns:
            GraphSchema对象
        """
        nodes = self._generate_nodes(inferred_schema.get('nodes', []))
        relationships = self._generate_relationships(inferred_schema.get('relationships', []))
        
        return GraphSchema(
            nodes=nodes,
            relationships=relationships
        )
    
    def _generate_nodes(self, nodes_data: List[Dict[str, Any]]) -> List[NodeSchema]:
        """
        生成节点模式列表
        
        Args:
            nodes_data: 节点数据列表
            
        Returns:
            NodeSchema列表
        """
        nodes = []
        
        for node_data in nodes_data:
            label = node_data.get('label', '').strip()
            if not label:
                continue
            
            # 获取属性定义
            properties = node_data.get('properties', {})
            if not properties:
                # 如果没有指定属性，至少添加name属性
                properties = {'name': 'string'}
            
            node = NodeSchema(
                label=label,
                properties=properties
            )
            nodes.append(node)
        
        return nodes
    
    def _generate_relationships(self, relationships_data: List[Dict[str, Any]]) -> List[RelationshipSchema]:
        """
        生成关系模式列表
        
        Args:
            relationships_data: 关系数据列表
            
        Returns:
            RelationshipSchema列表
        """
        relationships = []
        
        for rel_data in relationships_data:
            rel_type = rel_data.get('type', '').strip()
            from_node = rel_data.get('from_node', '').strip()
            to_node = rel_data.get('to_node', '').strip()
            
            if not all([rel_type, from_node, to_node]):
                continue
            
            properties = rel_data.get('properties', {})
            
            relationship = RelationshipSchema(
                type=rel_type,
                from_node=from_node,
                to_node=to_node,
                properties=properties
            )
            relationships.append(relationship)
        
        return relationships
    
    def validate_schema(self, schema: GraphSchema) -> tuple[bool, List[str]]:
        """
        验证模式的有效性
        
        Args:
            schema: GraphSchema对象
            
        Returns:
            (是否有效, 错误列表)
        """
        errors = []
        
        # 验证节点
        if not schema.nodes:
            errors.append("至少需要一个节点类型")
        
        node_labels = set()
        for node in schema.nodes:
            if not node.label:
                errors.append("节点标签不能为空")
            elif node.label in node_labels:
                errors.append(f"重复的节点标签: {node.label}")
            else:
                node_labels.add(node.label)
        
        # 验证关系
        for rel in schema.relationships:
            if not rel.type:
                errors.append("关系类型不能为空")
            if rel.from_node not in node_labels:
                errors.append(f"关系中的起始节点 '{rel.from_node}' 不存在")
            if rel.to_node not in node_labels:
                errors.append(f"关系中的目标节点 '{rel.to_node}' 不存在")
        
        return len(errors) == 0, errors

