"""
知识图谱查询服务
提供NL2Cypher（自然语言转Cypher查询）服务
基于Agent/GraphDatabase/main.py重构，使用新的模块结构
"""
import os
import re
import logging
from datetime import datetime
from fastapi import FastAPI, HTTPException, Depends
from fastapi.middleware.cors import CORSMiddleware
import uvicorn
from contextlib import asynccontextmanager
from openai import OpenAI
from dotenv import load_dotenv
from neo4j import GraphDatabase
from typing import List, Dict, Any

from config.settings import settings
from config.neo4j_config import NEO4J_CONFIG
from core.graph.models import NL2CypherRequest, CypherResponse, ValidationRequest, ValidationResponse
from core.graph.schemas import EXAMPLE_SCHEMA, GraphSchema
from core.graph.prompts import create_system_prompt, create_validation_prompt
from core.graph.validators import CypherValidator, RuleBasedValidator
from core.framework import SchemaConfig, PromptGenerator
from pydantic import BaseModel
from typing import Optional

# 加载环境变量
load_dotenv()

# 配置日志
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(settings.GRAPH_QUERY_LOG, encoding='utf-8'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


def merge_multiple_queries(cypher_query: str) -> str:
    """检测并合并多个独立的 Cypher 查询（多个 MATCH-RETURN 语句）"""
    # 检测是否有多个 RETURN 语句（不在 UNION 中）
    return_count = len(re.findall(r'\bRETURN\b', cypher_query, re.IGNORECASE))
    
    # 如果只有一个 RETURN，不需要合并
    if return_count <= 1:
        return cypher_query
    
    # 检查是否有 UNION，如果有 UNION 则不需要合并
    if re.search(r'\bUNION\b', cypher_query, re.IGNORECASE):
        return cypher_query
    
    logger.warning(f"检测到 {return_count} 个 RETURN 语句，正在合并多个查询...")
    
    # 按 MATCH 分割查询块
    query_blocks = re.split(r'(?=\bMATCH\b)', cypher_query, flags=re.IGNORECASE)
    queries = [q.strip() for q in query_blocks if q.strip() and re.search(r'\bMATCH\b', q, re.IGNORECASE) and re.search(r'\bRETURN\b', q, re.IGNORECASE)]
    
    if len(queries) <= 1:
        return cypher_query
    
    # 解析每个查询
    main_node_var = None
    main_node_label = None
    common_where = None
    optional_matches = []
    return_fields = []
    
    for i, query in enumerate(queries):
        # 提取完整的 MATCH 子句（包括关系和目标节点）
        match_full = re.search(r'MATCH\s+(.+?)(?:\n|WHERE|RETURN|$)', query, re.IGNORECASE | re.DOTALL)
        where_clause = re.search(r'WHERE\s+(.+?)(?:\n|RETURN|$)', query, re.IGNORECASE | re.DOTALL)
        return_clause = re.search(r'RETURN\s+(.+?)$', query, re.IGNORECASE | re.DOTALL)
        
        if match_full:
            match_pattern = match_full.group(1).strip()
            
            # 提取第一个节点（主节点）
            first_node = re.search(r'\((\w+)(?::(\w+))?\)', match_pattern)
            if first_node:
                node_var = first_node.group(1)
                node_label = first_node.group(2)
                
                if i == 0:
                    # 第一个查询：确定主节点和 WHERE
                    main_node_var = node_var
                    main_node_label = node_label
                    if where_clause:
                        common_where = where_clause.group(1).strip()
                    
                    # 第一个查询的完整模式转为 OPTIONAL MATCH（如果包含关系）
                    if re.search(r'[-[]', match_pattern):
                        # 提取关系部分（从第一个节点之后开始）
                        # 查找第一个节点后的内容
                        node_pattern = f"({node_var}{':' + node_label if node_label else ''})"
                        if match_pattern.startswith(node_pattern):
                            rel_part = match_pattern[len(node_pattern):].strip()
                            if rel_part:
                                optional_matches.append(f"OPTIONAL MATCH ({main_node_var}{':' + main_node_label if main_node_label else ''}){rel_part}")
                        else:
                            optional_matches.append(f"OPTIONAL MATCH {match_pattern}")
                else:
                    # 后续查询：转换为 OPTIONAL MATCH
                    if node_var == main_node_var:
                        # 使用相同的主节点，提取关系部分
                        node_pattern = f"({node_var}{':' + node_label if node_label else ''})"
                        if match_pattern.startswith(node_pattern):
                            rel_part = match_pattern[len(node_pattern):].strip()
                            if rel_part:
                                optional_matches.append(f"OPTIONAL MATCH ({main_node_var}{':' + main_node_label if main_node_label else ''}){rel_part}")
                        else:
                            optional_matches.append(f"OPTIONAL MATCH {match_pattern}")
                    else:
                        # 替换节点变量
                        new_pattern = re.sub(
                            rf'\(\s*{node_var}(?::\w+)?\s*\)',
                            f'({main_node_var}{":" + main_node_label if main_node_label else ""})',
                            match_pattern,
                            count=1
                        )
                        optional_matches.append(f"OPTIONAL MATCH {new_pattern}")
        
        # 收集 RETURN 字段
        if return_clause:
            fields = return_clause.group(1).strip()
            field_list = [f.strip() for f in re.split(r',(?![^()]*\))', fields) if f.strip()]
            return_fields.extend(field_list)
    
    # 构建合并后的查询
    if main_node_var:
        parts = []
        
        # 主 MATCH（只匹配主节点）
        if main_node_label:
            parts.append(f"MATCH ({main_node_var}:{main_node_label})")
        else:
            parts.append(f"MATCH ({main_node_var})")
        
        # WHERE
        if common_where:
            parts.append(f"WHERE {common_where}")
        
        # OPTIONAL MATCH
        parts.extend(optional_matches)
        
        # RETURN（去重）
        seen = set()
        unique = []
        for field in return_fields:
            alias_match = re.search(r'AS\s+(\w+)', field, re.IGNORECASE)
            if alias_match:
                alias = alias_match.group(1)
                if alias not in seen:
                    unique.append(field)
                    seen.add(alias)
            elif field not in unique:
                unique.append(field)
        
        if unique:
            parts.append('RETURN ' + ', '.join(unique))
        
        merged = '\n'.join(parts)
        logger.info(f"合并后的查询:\n{merged}")
        return merged
    
    return cypher_query


def clean_cypher_query(cypher_query: str) -> str:
    """清理 Cypher 查询字符串，移除 markdown 代码块标记和注释，修复关系类型语法"""
    if not cypher_query:
        return cypher_query
    
    # 移除 markdown 代码块标记
    pattern = r'```(?:cypher)?\s*\n?(.*?)\n?```'
    match = re.search(pattern, cypher_query, re.DOTALL | re.IGNORECASE)
    if match:
        cypher_query = match.group(1).strip()
    else:
        cypher_query = cypher_query.strip()
    
    # 移除可能残留的前导/尾随标记
    cypher_query = re.sub(r'^```(?:cypher)?\s*', '', cypher_query, flags=re.IGNORECASE)
    cypher_query = re.sub(r'```\s*$', '', cypher_query)
    
    # 提取实际的 Cypher 查询部分（移除说明文字）
    # 查找第一个 MATCH、CREATE、MERGE 等关键字，之前的内容可能是说明
    cypher_keywords = r'\b(MATCH|CREATE|MERGE|DELETE|SET|REMOVE|WITH|UNWIND|CALL|RETURN|START)\b'
    match = re.search(cypher_keywords, cypher_query, re.IGNORECASE)
    if match:
        # 从第一个关键字开始提取
        cypher_query = cypher_query[match.start():]
    
    # 如果包含说明文字（如 "# 说明"、"# Cypher查询" 等），移除说明部分
    # 查找最后一个 RETURN 语句，之后可能是说明
    return_matches = list(re.finditer(r'\bRETURN\b', cypher_query, re.IGNORECASE))
    if return_matches:
        last_return = return_matches[-1]
        # 查找 RETURN 之后的内容
        after_return = cypher_query[last_return.end():]
        # 提取 RETURN 子句（到行尾或分号）
        return_clause_match = re.search(r'^[^\n#]*', after_return, re.MULTILINE)
        if return_clause_match:
            # 找到 RETURN 子句的结束位置
            return_end = last_return.end() + return_clause_match.end()
            # 检查后面是否有说明文字（以 # 开头的行）
            remaining = cypher_query[return_end:]
            if remaining.strip():
                # 查找第一个以 # 开头的行
                comment_match = re.search(r'\n\s*#', remaining)
                if comment_match:
                    # 截取到说明文字之前
                    cypher_query = cypher_query[:return_end].strip()
                else:
                    # 如果没有 # 注释，保留到 RETURN 子句结束
                    cypher_query = cypher_query[:return_end].strip()
            else:
                cypher_query = cypher_query[:return_end].strip()
    
    # 移除 Cypher 多行注释 /* ... */
    cypher_query = re.sub(r'/\*.*?\*/', '', cypher_query, flags=re.DOTALL)
    
    # 移除 Cypher 单行注释 // ... 和 # ...
    lines = []
    found_return = False  # 标记是否已经找到 RETURN 语句
    
    for line in cypher_query.split('\n'):
        # 检查是否包含 RETURN 语句
        if re.search(r'\bRETURN\b', line, re.IGNORECASE):
            found_return = True
        
        # 如果已经找到 RETURN，且当前行以 # 开头，说明是说明文字，跳过
        if found_return and line.strip().startswith('#'):
            continue
        
        # 处理 // 注释
        if '//' in line:
            comment_pos = line.find('//')
            if comment_pos >= 0:
                line = line[:comment_pos].rstrip()
        
        # 处理 # 注释（整行注释或行尾注释）
        if '#' in line:
            # 检查是否是字符串中的 #（在引号内）
            in_string = False
            quote_char = None
            comment_pos = -1
            
            for i, char in enumerate(line):
                if char in ['"', "'"] and (i == 0 or line[i-1] != '\\'):
                    if not in_string:
                        in_string = True
                        quote_char = char
                    elif char == quote_char:
                        in_string = False
                        quote_char = None
                elif char == '#' and not in_string:
                    comment_pos = i
                    break
            
            if comment_pos >= 0:
                line = line[:comment_pos].rstrip()
        
        # 只保留非空行
        if line.strip():
            lines.append(line)
    
    cypher_query = '\n'.join(lines)
    
    # 最后清理：移除所有以 # 开头的行（说明文字）
    final_lines = []
    for line in cypher_query.split('\n'):
        if not line.strip().startswith('#'):
            final_lines.append(line)
        elif line.strip() and not re.search(r'\b(MATCH|CREATE|MERGE|RETURN|WHERE|WITH)\b', line, re.IGNORECASE):
            # 如果是以 # 开头的行，且不包含 Cypher 关键字，则跳过
            continue
        else:
            final_lines.append(line)
    
    cypher_query = '\n'.join(final_lines).strip()
    
    # 检测并合并多个独立查询（必须在其他修复之前进行）
    cypher_query = merge_multiple_queries(cypher_query)
    
    # 修复关系类型语法错误：将 :type1|:type2 修复为 :type1|type2
    # Neo4j 新版本不支持在关系类型列表中使用多个冒号
    # 匹配模式：-[r:type1|:type2]- 或 -[:type1|:type2]- 或 [r:type1|:type2|:type3]
    cypher_query = re.sub(r':(\w+)\|:(\w+)', r':\1|\2', cypher_query)
    # 处理多个关系类型的情况，如 :type1|:type2|:type3
    while re.search(r':(\w+)\|:(\w+)', cypher_query):
        cypher_query = re.sub(r':(\w+)\|:(\w+)', r':\1|\2', cypher_query)
    
    # 修复 COLLECT 函数中的 AS 语法错误
    # 错误: COLLECT(DISTINCT field.name AS alias)
    # 正确: COLLECT(DISTINCT field.name) AS alias
    # 匹配 COLLECT(... AS alias) 的模式，将 AS 移到函数外面
    def fix_collect_as(match):
        collect_content = match.group(1)  # COLLECT 函数内的内容（包含 AS alias）
        # 移除内部的 AS 和别名，保留表达式
        # 例如: "DISTINCT bad_food.name AS foods_to_avoid" -> "DISTINCT bad_food.name"
        # 提取别名
        alias_match = re.search(r'\s+AS\s+(\w+)\s*$', collect_content, re.IGNORECASE)
        if alias_match:
            alias = alias_match.group(1)
            # 移除 AS alias 部分
            collect_content = re.sub(r'\s+AS\s+\w+\s*$', '', collect_content, flags=re.IGNORECASE).strip()
            return f'COLLECT({collect_content}) AS {alias}'
        return match.group(0)
    
    # 匹配 COLLECT(... AS alias) 的模式（AS 在函数内部）
    cypher_query = re.sub(
        r'COLLECT\s*\(([^)]+\s+AS\s+\w+)\)',
        fix_collect_as,
        cypher_query,
        flags=re.IGNORECASE
    )
    
    
    # 清理多余的空行
    cypher_query = re.sub(r'\n\s*\n+', '\n', cypher_query)
    
    return cypher_query.strip()


# 生命周期管理
@asynccontextmanager
async def lifespan(app: FastAPI):
    # 启动初始化
    neo4j_uri = NEO4J_CONFIG['uri']
    neo4j_user = NEO4J_CONFIG['auth'][0]
    neo4j_password = NEO4J_CONFIG['auth'][1]

    if all([neo4j_uri, neo4j_user, neo4j_password]):
        app.state.validator = CypherValidator(neo4j_uri, neo4j_user, neo4j_password)
        try:
            app.state.neo4j_driver = GraphDatabase.driver(neo4j_uri, auth=(neo4j_user, neo4j_password))
            logger.info(f"成功连接到 Neo4j: {neo4j_uri}")
        except Exception as e:
            logger.error(f"连接 Neo4j 失败: {str(e)}")
            app.state.neo4j_driver = None
    else:
        app.state.validator = RuleBasedValidator()
        app.state.neo4j_driver = None
        logger.warning("Neo4j 配置不完整，将使用基于规则的验证器")
    yield

    # 关闭时清理
    if hasattr(app.state, "neo4j_driver") and app.state.neo4j_driver:
        app.state.neo4j_driver.close()
        logger.info("Neo4j 连接已关闭")
    if hasattr(app.state.validator, "close"):
        app.state.validator.close()


# 创建 FastAPI 应用
app = FastAPI(title='NL2Cypher API', lifespan=lifespan)

# 初始化 OpenRouter 客户端
from core.models.llm import create_openrouter_client
client = create_openrouter_client()

# 添加CORS中间件
app.add_middleware(
    CORSMiddleware,
    allow_origins=['*'],
    allow_credentials=True,
    allow_methods=['*'],
    allow_headers=['*'],
)


def generate_cypher_query(natural_language: str, query_type: str = None, 
                          schema: GraphSchema = None, domain: str = None, version: str = None) -> str:
    """
    使用 OpenRouter LLM 生成 Cypher 查询
    
    Args:
        natural_language: 自然语言查询
        query_type: 查询类型
        schema: GraphSchema对象（可选，如果提供则使用动态模式）
        domain: 领域名称（可选，如果提供则从配置加载模式）
        version: 版本号（可选，配合domain使用）
    """
    # 确定使用的模式
    if schema:
        # 使用提供的模式
        prompt_generator = PromptGenerator(schema)
        system_prompt = prompt_generator.generate_system_prompt()
    elif domain:
        # 从配置加载模式
        config_manager = SchemaConfig()
        loaded_schema = config_manager.load_schema(domain, version)
        if not loaded_schema:
            raise HTTPException(status_code=404, detail=f"无法加载模式: {domain} v{version or 'latest'}")
        prompt_generator = PromptGenerator(loaded_schema)
        system_prompt = prompt_generator.generate_system_prompt()
    else:
        # 使用默认模式
        system_prompt = create_system_prompt(str(EXAMPLE_SCHEMA.model_dump()))
    
    user_prompt = natural_language
    if query_type:
        user_prompt = f"{query_type}查询: {natural_language}"
    
    try:
        response = client.chat.completions.create(
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
        return clean_cypher_query(raw_query)
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"OpenRouter API错误: {str(e)}")


def explain_cypher_query(cypher_query: str) -> str:
    """解释Cypher查询"""
    try:
        response = client.chat.completions.create(
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


def execute_cypher_query(cypher_query: str, driver) -> Dict[str, Any]:
    """执行Cypher查询并返回结果"""
    if not driver:
        raise HTTPException(status_code=503, detail="Neo4j 连接不可用")
    
    cypher_query = clean_cypher_query(cypher_query)
    
    logger.info(f"执行 Cypher 查询: {cypher_query}")
    start_time = datetime.now()
    
    try:
        with driver.session() as session:
            result = session.run(cypher_query)
            
            records = []
            for record in result:
                record_dict = {}
                for key in record.keys():
                    value = record[key]
                    if hasattr(value, 'id'):
                        if hasattr(value, 'labels'):
                            record_dict[key] = {
                                'type': 'Node',
                                'labels': list(value.labels),
                                'properties': dict(value)
                            }
                        elif hasattr(value, 'type'):
                            record_dict[key] = {
                                'type': 'Relationship',
                                'relationship_type': value.type,
                                'properties': dict(value)
                            }
                        else:
                            record_dict[key] = str(value)
                    else:
                        record_dict[key] = value
                records.append(record_dict)
            
            execution_time = (datetime.now() - start_time).total_seconds()
            result_count = len(records)
            
            logger.info(f"查询执行成功，耗时: {execution_time:.3f}秒，返回 {result_count} 条记录")
            
            return {
                "success": True,
                "records": records,
                "count": result_count,
                "execution_time": execution_time
            }
    except Exception as e:
        execution_time = (datetime.now() - start_time).total_seconds()
        error_msg = str(e)
        logger.error(f"查询执行失败，耗时: {execution_time:.3f}秒，错误: {error_msg}")
        raise HTTPException(status_code=500, detail=f"查询执行失败: {error_msg}")


@app.post("/generate", response_model=CypherResponse)
async def generate_cypher(request: NL2CypherRequest):
    """生成Cypher查询端点"""
    logger.info(f"收到生成查询请求: {request.natural_language_query}")
    
    cypher_query = generate_cypher_query(
        request.natural_language_query,
        request.query_type.value if request.query_type else None
    )
    logger.info(f"生成的 Cypher 查询: {cypher_query}")
    
    explanation = explain_cypher_query(cypher_query)
    logger.info(f"查询解释: {explanation}")
    
    is_valid, errors = app.state.validator.validate_against_schema(cypher_query, EXAMPLE_SCHEMA)
    if errors:
        logger.warning(f"查询验证发现错误: {errors}")
    else:
        logger.info("查询验证通过")
    
    confidence = 0.9
    if errors:
        confidence = max(0.3, confidence - len(errors) * 0.1)
    
    return CypherResponse(
        cypher_query=cypher_query,
        explanation=explanation,
        confidence=confidence,
        validated=is_valid,
        validation_errors=errors
    )


@app.post("/validate", response_model=ValidationResponse)
async def validate_cypher(request: ValidationRequest):
    """验证Cypher查询端点"""
    logger.info(f"收到验证查询请求: {request.cypher_query}")
    
    is_valid, errors = app.state.validator.validate_against_schema(request.cypher_query, EXAMPLE_SCHEMA)
    
    if is_valid:
        logger.info("查询验证通过")
    else:
        logger.warning(f"查询验证失败，发现 {len(errors)} 个错误: {errors}")
    
    suggestions = []
    if errors:
        try:
            response = client.chat.completions.create(
                model=settings.OPENROUTER_LLM_MODEL,
                messages=[
                    {"role": "system", "content": "你是一个Neo4j专家, 请提供Cypher查询的改进建议."},
                    {"role": "user", "content": create_validation_prompt(request.cypher_query)}
                ],
                temperature=0.1,
                max_tokens=1024,
                stream=False
            )
            suggestions = [response.choices[0].message.content.strip()]
            logger.info(f"生成改进建议: {suggestions}")
        except Exception as e:
            suggestions = ["无法生成建议"]
            logger.error(f"生成改进建议失败: {str(e)}")
    
    return ValidationResponse(
        is_valid=is_valid,
        errors=errors,
        suggestions=suggestions
    )


@app.post("/execute")
async def execute_query(request: ValidationRequest):
    """执行Cypher查询端点"""
    logger.info(f"收到执行查询请求: {request.cypher_query}")
    
    if not hasattr(app.state, "neo4j_driver") or not app.state.neo4j_driver:
        raise HTTPException(status_code=503, detail="Neo4j 连接不可用，无法执行查询")
    
    try:
        result = execute_cypher_query(request.cypher_query, app.state.neo4j_driver)
        logger.info(f"查询执行完成，返回 {result['count']} 条记录")
        return result
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"执行查询时发生异常: {str(e)}")
        raise HTTPException(status_code=500, detail=f"执行查询失败: {str(e)}")


@app.get("/")
async def root():
    """根路径，返回服务信息"""
    logger.info("收到根路径访问请求")
    return {
        "service": "NL2Cypher API - 知识图谱查询服务",
        "status": "运行中",
        "version": "1.0",
        "endpoints": {
            "POST /generate": "生成 Cypher 查询",
            "POST /validate": "验证 Cypher 查询",
            "POST /execute": "执行 Cypher 查询",
            "GET /schema": "获取图数据库模式"
        },
        "port": settings.GRAPH_SERVICE_PORT,
        "neo4j_connected": hasattr(app.state, "neo4j_driver") and app.state.neo4j_driver is not None
    }


@app.get("/schema")
async def get_schema(domain: Optional[str] = None, version: Optional[str] = None):
    """
    获取图模式端点
    
    Args:
        domain: 领域名称（可选，如果不提供则返回默认模式）
        version: 版本号（可选，配合domain使用）
    """
    logger.info(f"获取图模式请求 - domain: {domain}, version: {version}")
    
    if domain:
        # 从配置加载模式
        config_manager = SchemaConfig()
        schema = config_manager.load_schema(domain, version)
        if not schema:
            raise HTTPException(status_code=404, detail=f"无法加载模式: {domain} v{version or 'latest'}")
        return schema.model_dump()
    else:
        # 返回默认模式
        return EXAMPLE_SCHEMA.model_dump()


class DynamicNL2CypherRequest(BaseModel):
    """动态 NL2Cypher 请求模型"""
    natural_language_query: str
    query_type: Optional[str] = None
    domain: Optional[str] = None
    version: Optional[str] = None


@app.post("/generate-dynamic", response_model=CypherResponse)
async def generate_cypher_dynamic(request: DynamicNL2CypherRequest):
    """
    生成Cypher查询端点（支持动态模式）
    
    支持通过 domain 和 version 参数动态加载图模式
    """
    logger.info(f"收到动态生成查询请求: {request.natural_language_query}, domain: {request.domain}")
    
    try:
        cypher_query = generate_cypher_query(
            request.natural_language_query,
            request.query_type,
            domain=request.domain,
            version=request.version
        )
        logger.info(f"生成的 Cypher 查询: {cypher_query}")
        
        explanation = explain_cypher_query(cypher_query)
        logger.info(f"查询解释: {explanation}")
        
        # 加载用于验证的模式
        if request.domain:
            config_manager = SchemaConfig()
            validation_schema = config_manager.load_schema(request.domain, request.version)
            if not validation_schema:
                logger.warning(f"无法加载验证模式: {request.domain} v{request.version or 'latest'}")
                validation_schema = EXAMPLE_SCHEMA
        else:
            validation_schema = EXAMPLE_SCHEMA
        
        is_valid, errors = app.state.validator.validate_against_schema(cypher_query, validation_schema)
        if errors:
            logger.warning(f"查询验证发现错误: {errors}")
        else:
            logger.info("查询验证通过")
        
        confidence = 0.9
        if errors:
            confidence = max(0.3, confidence - len(errors) * 0.1)
        
        return CypherResponse(
            cypher_query=cypher_query,
            explanation=explanation,
            confidence=confidence,
            validated=is_valid,
            validation_errors=errors
        )
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"生成查询时发生异常: {str(e)}")
        raise HTTPException(status_code=500, detail=f"生成查询失败: {str(e)}")


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=settings.GRAPH_SERVICE_PORT)

