# graph 模块说明

`graph` 模块封装了与 Neo4j 知识图谱相关的所有功能，包括图数据库连接、NL2Cypher（自然语言转 Cypher 查询）、查询验证等。

## 目录结构

```
graph/
├── __init__.py
├── models.py        # 图数据模型定义
├── neo4j_client.py  # Neo4j 客户端封装
├── prompts.py       # NL2Cypher 提示词模板
├── schemas.py       # 图模式定义和数据模型
└── validators.py    # Cypher 查询验证器
```

## 主要功能

### 图数据库连接

- **统一连接管理**：封装 Neo4j 驱动，提供连接、查询、关闭等基本操作
- **连接测试**：自动测试连接可用性
- **错误处理**：完善的错误处理机制

### NL2Cypher 转换

- **自然语言理解**：将用户的自然语言问题转换为 Cypher 查询语句
- **提示词模板**：提供结构化的提示词模板，包含图模式、示例和规则
- **模式验证**：根据图模式验证生成的查询

### 查询验证

- **语法验证**：验证 Cypher 查询的语法正确性
- **模式验证**：验证查询是否符合图数据库模式
- **安全检查**：检测潜在的危险操作

### 数据模型

- **图模式定义**：定义节点、关系和属性
- **API 模型**：定义请求和响应的数据结构

## 主要文件

### neo4j_client.py

#### `Neo4jClient` 类

Neo4j 客户端封装类，提供图数据库的基本操作。

**初始化**：
```python
client = Neo4jClient(uri=None, auth=None)
```

**参数**：
- `uri`：Neo4j URI，如果为 `None` 则使用 `config.neo4j_config.NEO4J_CONFIG['uri']`
- `auth`：`(用户名, 密码)` 元组，如果为 `None` 则使用配置中的值

**主要方法**：

##### `connect() -> bool`

建立 Neo4j 连接并测试。

**返回**：连接成功返回 `True`，失败返回 `False`

##### `execute_query(query: str)`

执行 Cypher 查询。

**参数**：
- `query`：Cypher 查询语句

**返回**：查询结果列表

**异常**：如果连接未建立，抛出 `ConnectionError`

##### `close()`

关闭 Neo4j 连接。

### models.py

定义图数据库的模式结构，包括节点和关系的定义。

**主要类**：

- `NodeSchema`：节点模式定义
- `RelationshipSchema`：关系模式定义
- `GraphSchema`：完整的图模式定义

**预定义节点类型**：
- `Disease`（疾病）：包含名称、描述、预防、病因、治疗方式等属性
- `Drug`（药物）
- `Food`（食物）
- `Symptom`（症状）
- `Check`（检查项）
- `Department`（科室）
- `Producer`（生产商）
- `Category`（分类）
- `Treatment`（治疗方式）

**预定义关系类型**：
- `has_symptom`：疾病-症状
- `recommand_drug`：疾病-推荐药物
- `recommand_eat`：疾病-推荐食物
- `not_eat`：疾病-禁忌食物
- `do_eat`：疾病-可食用食物
- `command_drug`：疾病-常用药物
- `drugs_of`：药物-生产商
- `need_check`：疾病-检查项
- `acompany_with`：疾病-并发症
- `belongs_to`：疾病-科室
- `sub_department`：科室-子科室
- `has_category`：疾病-分类
- `treated_by`：疾病-治疗方式

### schemas.py

定义 API 请求和响应的数据模型（使用 Pydantic）。

**主要模型**：

#### `NL2CypherRequest`

自然语言转 Cypher 请求模型。

**字段**：
- `natural_language_query`：自然语言描述
- `query_type`：查询类型（可选，MATCH/CREATE/MERGE/DELETE/SET/REMOVE）
- `limit`：结果限制数量（默认 10，范围 1-1000）

#### `CypherResponse`

Cypher 查询响应模型。

**字段**：
- `cypher_query`：生成的 Cypher 查询语句
- `explanation`：查询解释
- `confidence`：模型信心度（0-1）
- `validated`：是否通过验证
- `validation_errors`：验证错误列表

#### `ValidationRequest` / `ValidationResponse`

Cypher 查询验证的请求和响应模型。

### prompts.py

提供 NL2Cypher 转换的提示词模板。

#### `create_system_prompt(schema: str) -> str`

创建系统提示词，用于指导 LLM 生成 Cypher 查询。

**功能**：
- 包含图数据库模式信息
- 提供查询规则和最佳实践
- 包含丰富的示例
- 强调语法规则（如关系类型、COLLECT 函数等）

**重要规则**：
1. 使用参数化查询风格
2. 对于可能不存在的关系使用 `OPTIONAL MATCH`
3. 关系类型语法：多个关系类型时，只有第一个需要冒号
4. COLLECT 函数语法：AS 别名必须在函数外面
5. 空值处理：使用 `IS NOT NULL` 和 `<> ''` 过滤空值

#### `create_validation_prompt(cypher_query: str) -> str`

创建验证提示词，用于验证 Cypher 查询。

### validators.py

提供 Cypher 查询验证功能。

#### `CypherValidator` 类

使用 Neo4j 连接进行验证的验证器。

**方法**：

##### `validate_syntax(cypher_query: str) -> Tuple[bool, List[str]]`

验证 Cypher 查询的语法。

**检查项**：
- 查询必须以 MATCH/CREATE/MERGE/CALL 开头
- MATCH 查询必须包含 RETURN 语句
- 检测潜在的危险操作
- 使用 Neo4j 的 EXPLAIN 功能验证语法

##### `validate_against_schema(cypher_query: str, schema: GraphSchema) -> Tuple[bool, List[str]]`

根据图模式验证查询。

**检查项**：
- 验证节点标签是否存在
- 验证关系类型是否存在

#### `RuleBasedValidator` 类

基于规则的验证器（当无法连接 Neo4j 时使用）。

**功能**：
- 基本结构检查
- 危险操作检测
- 模式验证（基于正则表达式）

## 使用示例

### 连接 Neo4j

```python
from core.graph.neo4j_client import Neo4jClient

# 创建客户端
client = Neo4jClient()

# 建立连接
if client.connect():
    # 执行查询
    result = client.execute_query("MATCH (d:Disease) RETURN d.name LIMIT 10")
    print(result)
    
    # 关闭连接
    client.close()
```

### NL2Cypher 转换

```python
from core.graph.prompts import create_system_prompt
from core.graph.schemas import EXAMPLE_SCHEMA
from core.models.llm import create_deepseek_client

# 创建系统提示词
schema_str = str(EXAMPLE_SCHEMA)
system_prompt = create_system_prompt(schema_str)

# 使用 LLM 生成 Cypher
client = create_deepseek_client()
user_query = "查找高血压建议服用什么药物？"
full_prompt = system_prompt + f"\n自然语言: {user_query}\nCypher:"

# 调用 LLM 生成查询...
```

### 查询验证

```python
from core.graph.validators import CypherValidator
from core.graph.schemas import EXAMPLE_SCHEMA
from config.neo4j_config import NEO4J_CONFIG

# 创建验证器
validator = CypherValidator(
    neo4j_uri=NEO4J_CONFIG['uri'],
    neo4j_user=NEO4J_CONFIG['auth'][0],
    neo4j_password=NEO4J_CONFIG['auth'][1]
)

# 验证查询
cypher_query = "MATCH (d:Disease)-[:recommand_drug]->(dr:Drug) WHERE d.name='高血压' RETURN dr.name"
is_valid, errors = validator.validate_syntax(cypher_query)
if is_valid:
    is_valid_schema, schema_errors = validator.validate_against_schema(cypher_query, EXAMPLE_SCHEMA)
    if is_valid_schema:
        print("查询有效")
    else:
        print(f"模式错误: {schema_errors}")
else:
    print(f"语法错误: {errors}")

validator.close()
```

## 配置要求

### Neo4j 配置

需要在 `config/neo4j_config.py` 中配置：
```python
NEO4J_CONFIG = {
    'uri': 'bolt://localhost:7687',
    'auth': ('username', 'password')
}
```

## 典型工作流程

1. **接收自然语言问题**：从用户或 API 接收自然语言查询
2. **生成 Cypher 查询**：使用 `prompts.py` 中的模板和 LLM 生成 Cypher
3. **验证查询**：使用 `validators.py` 验证查询的语法和模式
4. **执行查询**：使用 `neo4j_client.py` 执行查询
5. **解析结果**：使用 `schemas.py` 中的模型解析结果
6. **返回响应**：将结构化结果返回给调用方

## 注意事项

1. **连接管理**：确保在使用后关闭连接，避免资源泄漏
2. **查询安全**：验证器会检测危险操作，但建议在生产环境中添加更严格的权限控制
3. **模式一致性**：确保 `models.py` 中定义的节点和关系与 Neo4j 数据库中的实际结构一致
4. **性能优化**：对于复杂查询，考虑添加索引和优化查询语句
5. **错误处理**：在实际使用中应添加完善的错误处理和重试机制

## 扩展建议

1. **查询优化**：添加查询性能分析和优化建议
2. **缓存机制**：对常见查询结果进行缓存
3. **批量操作**：支持批量查询和更新操作
4. **监控告警**：添加图数据库的监控和告警机制
5. **查询日志**：记录查询历史，用于分析和优化

