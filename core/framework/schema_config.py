"""
模式配置管理
保存和加载图模式配置
"""
import json
from pathlib import Path
from typing import Optional, Dict, Any, List
from core.graph.schemas import GraphSchema, NodeSchema, RelationshipSchema
from config.settings import settings, PROJECT_ROOT


class SchemaConfig:
    """模式配置管理类"""
    
    def __init__(self, config_dir: Optional[str] = None):
        """
        初始化配置管理器
        
        Args:
            config_dir: 配置目录路径，如果为None则使用默认路径
        """
        if config_dir is None:
            # 使用项目根目录下的 config/schemas 目录
            self.config_dir = PROJECT_ROOT / "config" / "schemas"
        else:
            self.config_dir = Path(config_dir)
        
        self.config_dir.mkdir(parents=True, exist_ok=True)
    
    def save_schema(self, schema: GraphSchema, domain: str, version: str = "1.0") -> str:
        """
        保存图模式到配置文件
        
        Args:
            schema: GraphSchema对象
            domain: 领域名称（如：medical, finance等）
            version: 版本号
            
        Returns:
            保存的文件路径
        """
        config_data = {
            "version": version,
            "domain": domain,
            "nodes": [
                {
                    "label": node.label,
                    "properties": node.properties
                }
                for node in schema.nodes
            ],
            "relationships": [
                {
                    "type": rel.type,
                    "from_node": rel.from_node,
                    "to_node": rel.to_node,
                    "properties": rel.properties
                }
                for rel in schema.relationships
            ]
        }
        
        config_file = self.config_dir / f"{domain}_schema_v{version}.json"
        
        with open(config_file, 'w', encoding='utf-8') as f:
            json.dump(config_data, f, ensure_ascii=False, indent=2)
        
        return str(config_file)
    
    def load_schema(self, domain: str, version: Optional[str] = None) -> Optional[GraphSchema]:
        """
        从配置文件加载图模式
        
        Args:
            domain: 领域名称
            version: 版本号，如果为None则加载最新版本
            
        Returns:
            GraphSchema对象，如果文件不存在则返回None
        """
        if version:
            config_file = self.config_dir / f"{domain}_schema_v{version}.json"
        else:
            # 查找最新版本
            pattern = f"{domain}_schema_v*.json"
            files = list(self.config_dir.glob(pattern))
            if not files:
                return None
            # 按版本号排序，取最新的
            files.sort(key=lambda x: self._extract_version(x.stem), reverse=True)
            config_file = files[0]
        
        if not config_file.exists():
            return None
        
        with open(config_file, 'r', encoding='utf-8') as f:
            config_data = json.load(f)
        
        nodes = [
            NodeSchema(
                label=node_data['label'],
                properties=node_data.get('properties', {})
            )
            for node_data in config_data.get('nodes', [])
        ]
        
        relationships = [
            RelationshipSchema(
                type=rel_data['type'],
                from_node=rel_data['from_node'],
                to_node=rel_data['to_node'],
                properties=rel_data.get('properties', {})
            )
            for rel_data in config_data.get('relationships', [])
        ]
        
        return GraphSchema(nodes=nodes, relationships=relationships)
    
    def _extract_version(self, filename: str) -> float:
        """从文件名中提取版本号"""
        import re
        match = re.search(r'v(\d+\.?\d*)', filename)
        if match:
            return float(match.group(1))
        return 0.0
    
    def list_schemas(self) -> Dict[str, List[str]]:
        """
        列出所有可用的模式配置
        
        Returns:
            字典，key为领域名称，value为版本列表
        """
        schemas = {}
        pattern = "*_schema_v*.json"
        
        for config_file in self.config_dir.glob(pattern):
            # 解析文件名：domain_schema_v1.0.json
            parts = config_file.stem.split('_schema_v')
            if len(parts) == 2:
                domain = parts[0]
                version = parts[1]
                if domain not in schemas:
                    schemas[domain] = []
                schemas[domain].append(version)
        
        # 对每个领域的版本进行排序
        for domain in schemas:
            schemas[domain].sort(key=lambda x: float(x) if x.replace('.', '').isdigit() else 0.0, reverse=True)
        
        return schemas

