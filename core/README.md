# Core 模块说明

`core` 模块封装了项目的**底层通用能力**，包括 Embedding、LLM、向量库、缓存、知识图谱构建框架、上下文增强等，是上层业务服务的基础。

## 📁 目录结构

```
core/
├── __init__.py
├── models/              # 模型相关封装（Embedding / LLM）
├── vector_store/        # 向量数据库（Milvus）封装
├── cache/               # 缓存（Redis）封装
├── graph/               # 知识图谱（Neo4j）相关封装
├── framework/           # 通用图谱构建框架（核心创新）
└── context/             # 上下文增强模块
```

---

## 🤖 models 子模块

- **路径**：`core/models/`
- **职责**：统一管理和封装模型，避免在业务代码中直接操作底层模型类。

### 主要文件

- **`embeddings.py`**
  - 封装 Embedding 模型为统一接口
  - 支持 OpenRouter API 提供的各种 Embedding 模型
  - 负责把文本转换成稠密向量，并可用于 Milvus 等向量库
  - 默认使用 `zhipuai/glm-4-embedding`，可通过配置切换

- **`llm.py`**
  - 封装大语言模型客户端，通过 OpenRouter API 统一管理
  - 支持多种 LLM 模型（DeepSeek、GPT-4、Claude 等）
  - 提供创建客户端的工厂方法 `create_openrouter_client()`
  - 统一的模型接口，易于切换和扩展

### 典型用法

```python
from core.models.llm import create_openrouter_client
from core.models.embeddings import create_embedding_client

# 创建 LLM 客户端
llm_client = create_openrouter_client()

# 创建 Embedding 客户端
embedding_client = create_embedding_client()
```

---

## 🔍 vector_store 子模块

- **路径**：`core/vector_store/`
- **职责**：封装与 Milvus 的交互逻辑，提供更高层的"向量检索"接口。

### 主要文件

- **`milvus_client.py`**
  - 负责连接 Milvus、本地向量数据库文件、索引参数配置等
    - 给上层提供：
      - 写入文档（向量化 + 建索引）
      - 相似度检索（`similarity_search` 等）
    - 混合检索：稠密向量 + BM25 稀疏检索
    - RRF 重排序：融合多路检索结果

在 `services/agent_service.py` 中，已经直接通过 `langchain_milvus.Milvus` + Embedding 构建了向量存储和检索器；如需扩展统一封装，可以在 `milvus_client.py` 中抽象常用操作。

---

## 💾 cache 子模块

- **路径**：`core/cache/`
- **职责**：统一管理 Redis 连接与常用缓存操作，避免在业务层到处维护 Redis 客户端。

### 主要文件

- **`redis_client.py`**
  - 基于 `config.settings` 中的 Redis 配置，创建 Redis 连接池 / 客户端
  - 可根据需要封装：简单 KV 缓存、TTL 设置、业务级缓存封装等
  - 对话历史管理：保存、查询、更新
  - 会话列表管理：Sorted Set 实现时间排序

当前项目中 Redis 为可选依赖，主要用于缓存加速和对话历史存储，实际使用场景可以按需要扩展。

---

## 🗺️ graph 子模块

- **路径**：`core/graph/`
- **职责**：封装与 Neo4j 知识图谱和 NL2Cypher 相关的所有逻辑。

### 主要文件

- **`schemas.py`**
  - 定义图模式的数据结构（`GraphSchema`、`NodeSchema`、`RelationshipSchema`）
  - 提供通用的示例模式（`EXAMPLE_SCHEMA`）
  - 支持 Pydantic 模型验证

- **`neo4j_client.py`**
  - 基于 `config.neo4j_config` 或 `config.settings` 中的配置，创建 Neo4j 驱动
  - 封装图谱查询、Cypher 执行、结果解析等
  - 提供连接管理和会话管理

- **`prompts.py`**
  - 存放与 NL2Cypher 或图谱问答相关的 Prompt 模板（通用版本）
  - 提供 `create_system_prompt()` 和 `create_validation_prompt()` 函数
  - 支持动态模式适配

- **`models.py`**
  - 定义请求 / 响应的数据结构（如 Pydantic 模型），用于 FastAPI 等
  - `NL2CypherRequest`、`CypherResponse`、`ValidationRequest` 等

- **`validators.py`**
  - 提供对 Cypher、查询参数等的校验逻辑，提升安全性和稳定性
  - `CypherValidator`：基于 Neo4j 的验证器
  - `RuleBasedValidator`：基于规则的验证器

### 典型流程（结合 `services/graph_service.py`）

1. 接收自然语言问题
2. 使用 `prompts.py` 中模板 + LLM 生成 Cypher
3. 使用 `validators.py` 验证查询安全性
4. 使用 `neo4j_client.py` 执行查询
5. 使用 `models.py` / `schemas.py` 解析结果
6. 将结构化结果返回给 Agent 服务或前端

---

## 🎯 framework 子模块（核心创新）

- **路径**：`core/framework/`
- **职责**：提供通用知识图谱构建框架，支持自动模式推断和动态图谱构建。

### 主要文件

- **`data_reader.py`**
  - 读取数据文件的第一行或前N行
  - 支持 JSONL、JSON、CSV 格式
  - 提供统一的数据读取接口

- **`schema_inferrer.py`**
  - 调用大模型分析数据结构
  - 自动识别节点类型、属性和关系
  - 生成标准化的图模式配置

- **`schema_generator.py`**
  - 将推断结果转换为 `GraphSchema` 对象
  - 验证模式的有效性
  - 处理模式生成过程中的异常

- **`schema_config.py`**
  - 保存和加载图模式配置
  - 支持领域和版本管理
  - 配置文件格式：JSON Schema 标准
  - 提供 `load_schema()` 和 `save_schema()` 方法

- **`graph_builder.py`**
  - 根据模式动态解析数据
  - 智能字段映射：自动识别数据字段到图关系的映射
  - 批量创建节点和关系
  - 验证图谱完整性

- **`prompt_generator.py`**
  - 根据图模式动态生成 NL2Cypher 提示词
  - 支持多领域适配
  - 生成包含节点、关系、示例的系统提示词

- **`nl2cypher_service.py`**
  - 基于动态图模式提供 NL2Cypher 服务
  - 支持通过 domain 和 version 参数加载图模式
  - 提供 `generate_cypher()` 和 `execute_query()` 方法

### 典型用法

```python
from core.framework import SchemaConfig, GraphBuilder, NL2CypherService

# 1. 加载模式
config_manager = SchemaConfig()
schema = config_manager.load_schema("your_domain", "1.0")

# 2. 创建构建器并构建图谱
builder = GraphBuilder(schema)
builder.build_graph(
    data_file="data/raw/your_data.jsonl",
    batch_size=100,
    clear_existing=False
)

# 3. 使用 NL2Cypher 服务
nl2cypher = NL2CypherService(domain="your_domain", version="1.0")
result = nl2cypher.generate_cypher("你的自然语言问题")
```

> 📖 详细文档：[通用知识图谱构建框架](../../docs/framework/README.md)

---

## 🧠 context 子模块

- **路径**：`core/context/`
- **职责**：提供智能上下文增强功能，自动识别指代性问题并补充上下文。

### 主要文件

- **`enhancer.py`**
  - `enhance_query_with_context()`：根据对话历史增强用户问题
  - `extract_entities_from_history()`：从对话历史中提取主题实体
  - `has_reference_pronouns()`：检测问题是否包含指代性词语
  - 基于大模型的智能理解，而非简单规则匹配

### 功能特性

- **指代检测**：识别"有什么"、"怎么"、"如何"等指代性词语
- **主题提取**：从对话历史中提取核心实体和主题
- **问题增强**：将提取的主题补充到问题中，生成完整清晰的问题
- **智能判断**：使用大模型进行语义理解

### 典型用法

```python
from core.context import enhance_query_with_context, extract_entities_from_history

# 增强问题
enhanced_query, was_enhanced = enhance_query_with_context(
    query="有什么特效药？",
    history=[
        {"question": "感冒了有什么症状？", "answer": "..."}
    ]
)

# 提取实体
entities = extract_entities_from_history(history)
```

> 📖 详细文档：[上下文增强系统](../docs/architecture/context_enhancement.md)

---

## 🔗 模块间关系

```
┌─────────────────────────────────────────┐
│         services/ (业务服务层)          │
└──────────────┬──────────────────────────┘
               │
    ┌──────────┼──────────┐
    │          │          │
    ▼          ▼          ▼
┌────────┐ ┌────────┐ ┌────────┐
│ models │ │ graph  │ │context │
└────────┘ └────────┘ └────────┘
    │          │
    ▼          ▼
┌────────┐ ┌────────┐
│vector_ │ │framework│
│store   │ │        │
└────────┘ └────────┘
    │          │
    ▼          ▼
┌────────┐ ┌────────┐
│ Milvus │ │ Neo4j  │
└────────┘ └────────┘
```

---

## 📚 相关文档

- [通用知识图谱构建框架](../../docs/framework/README.md)
- [上下文增强系统](../docs/architecture/context_enhancement.md)
- [知识图谱服务](./graph/README.md)
- [模型封装](./models/README.md)
- [向量存储](./vector_store/README.md)
- [缓存系统](./cache/README.md)
