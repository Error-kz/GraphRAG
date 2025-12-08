"""
模式推断器
使用大模型分析数据结构并推断图模式
"""
import json
import re
from typing import Dict, Any, Optional
from openai import OpenAI
from config.settings import settings
from core.models.llm import create_openrouter_client


class SchemaInferrer:
    """模式推断器类"""
    
    def __init__(self, llm_client: Optional[OpenAI] = None):
        """
        初始化模式推断器
        
        Args:
            llm_client: LLM客户端，如果为None则自动创建
        """
        self.client = llm_client or create_openrouter_client()
        if not self.client:
            raise ValueError("无法创建LLM客户端，请检查OPENROUTER_API_KEY配置")
    
    def infer_schema(self, sample_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        推断图模式
        
        Args:
            sample_data: 样本数据（通常是第一行数据）
            
        Returns:
            推断出的图模式字典
        """
        prompt = self._create_inference_prompt(sample_data)
        
        try:
            response = self.client.chat.completions.create(
                model=settings.OPENROUTER_LLM_MODEL,
                messages=[
                    {
                        "role": "system",
                        "content": "你是一个知识图谱模式分析专家。请仔细分析JSON数据，识别节点类型、属性和关系。"
                    },
                    {"role": "user", "content": prompt}
                ],
                temperature=0.1,
                max_tokens=4096,
                stream=False
            )
            
            raw_response = response.choices[0].message.content.strip()
            return self._parse_llm_response(raw_response)
            
        except Exception as e:
            raise RuntimeError(f"LLM推断失败: {str(e)}")
    
    def _create_inference_prompt(self, sample_data: Dict[str, Any]) -> str:
        """
        创建推断提示词
        
        Args:
            sample_data: 样本数据
            
        Returns:
            提示词字符串
        """
        data_str = json.dumps(sample_data, ensure_ascii=False, indent=2)
        
        prompt = f"""
请分析以下JSON数据，识别知识图谱的结构：

{data_str}

请识别以下内容：

1. **节点类型识别**：
   - 哪些字段代表实体（如：疾病、药品、食物、症状等）
   - 为每个实体类型指定一个合适的标签名称（使用英文，首字母大写，如：Disease, Drug, Food）
   - 识别主实体（通常是数据记录的核心实体，如疾病名称）

2. **节点属性识别**：
   - 主实体的属性有哪些（如：desc, prevent, cause等）
   - 每个属性的数据类型（string, number, list等）

3. **关系识别**：
   - 哪些字段表示实体间的关系（如：symptom表示疾病-症状关系）
   - 关系的方向（从哪个节点到哪个节点）
   - 关系的语义名称（使用英文，小写下划线，如：has_symptom, recommand_drug）
   - 列表字段通常表示一对多关系

4. **关联实体识别**：
   - 哪些字段的值应该作为独立的节点（如：symptom列表中的每个症状应该是一个Symptom节点）

请以JSON格式返回结果，格式如下：

{{
  "nodes": [
    {{
      "label": "Disease",
      "primary_key": "name",
      "properties": {{
        "name": "string",
        "desc": "string",
        "prevent": "string"
      }},
      "is_main_entity": true
    }},
    {{
      "label": "Symptom",
      "primary_key": "name",
      "properties": {{
        "name": "string"
      }},
      "is_main_entity": false
    }}
  ],
  "relationships": [
    {{
      "type": "has_symptom",
      "from_node": "Disease",
      "to_node": "Symptom",
      "source_field": "symptom",
      "properties": {{}}
    }}
  ],
  "field_mappings": {{
    "symptom": {{
      "relationship_type": "has_symptom",
      "target_node": "Symptom"
    }}
  }}
}}

注意：
- 节点标签使用英文，首字母大写（如：Disease, Drug, Food）
- 关系类型使用英文，小写下划线（如：has_symptom, recommand_drug）
- 主实体通常是数据记录的核心（如疾病名称）
- 列表字段通常表示一对多关系
- 确保返回有效的JSON格式
"""
        return prompt
    
    def _parse_llm_response(self, raw_response: str) -> Dict[str, Any]:
        """
        解析LLM返回的响应
        
        Args:
            raw_response: LLM原始响应
            
        Returns:
            解析后的图模式字典
        """
        # 尝试提取JSON代码块
        json_match = re.search(r'```json\s*(\{.*?\})\s*```', raw_response, re.DOTALL)
        if json_match:
            json_str = json_match.group(1)
        else:
            # 尝试提取普通代码块
            json_match = re.search(r'```\s*(\{.*?\})\s*```', raw_response, re.DOTALL)
            if json_match:
                json_str = json_match.group(1)
            else:
                # 尝试直接查找JSON对象
                json_match = re.search(r'\{.*\}', raw_response, re.DOTALL)
                if json_match:
                    json_str = json_match.group(0)
                else:
                    raise ValueError("无法从LLM响应中提取JSON数据")
        
        try:
            # 清理JSON字符串
            json_str = json_str.strip()
            # 移除可能的注释
            json_str = re.sub(r'//.*?$', '', json_str, flags=re.MULTILINE)
            
            schema = json.loads(json_str)
            
            # 验证必需字段
            if 'nodes' not in schema:
                raise ValueError("缺少 'nodes' 字段")
            if 'relationships' not in schema:
                schema['relationships'] = []
            
            return schema
            
        except json.JSONDecodeError as e:
            raise ValueError(f"JSON解析失败: {str(e)}\n原始响应: {raw_response[:500]}")

