# GraphRAG：通用知识图谱 + RAG 问答系统

GraphRAG 是一个**领域无关**的通用知识图谱问答系统，结合 **知识图谱 (Neo4j)**、**向量检索 (Milvus)** 和 **大语言模型 (LLM)**，支持自动模式推断、动态图谱构建和智能问答。  
后端基于 FastAPI，前端为纯 HTML/JavaScript 聊天页面，支持可视化展示多源检索路径，适合作为 **教学 Demo** 或 **二次开发起点**。

---

## 🌟 核心特性与技术亮点

### 🚀 自动化知识图谱构建

**零配置模式推断**：无需手动定义图模式，系统自动分析数据结构并生成图谱配置

- **智能模式推断**（[`core/framework/schema_inferrer.py`](../core/framework/schema_inferrer.py)）
  - 使用大模型自动分析数据结构
  - 识别节点类型、属性和关系
  - 生成标准化的图模式配置
  - 支持多领域数据（医疗、金融、电商等）

- **动态图谱构建**（[`core/framework/graph_builder.py`](../core/framework/graph_builder.py)）
  - 根据推断的模式自动构建知识图谱
  - 智能字段映射：自动识别数据字段到图关系的映射
  - 批量处理：支持大规模数据的高效导入
  - 模式版本管理：支持多版本模式配置

- **模式配置管理**（[`core/framework/schema_config.py`](../core/framework/schema_config.py)）
  - 自动保存和加载图模式配置
  - 支持领域和版本管理
  - 配置文件格式：JSON Schema 标准

> 📖 详细文档：[通用知识图谱构建框架](../core/framework/README.md)

### 🧠 多源知识融合架构

**混合检索策略**：结合结构化知识图谱与向量检索，实现精准问答

- **知识图谱检索**（[Neo4j](https://neo4j.com/)）
  - 动态模式支持：根据领域自动加载图模式
  - NL2Cypher 自动转换：自然语言 → Cypher 查询
  - 查询验证机制：语法检查 + 语义验证
  - 置信度评估：返回查询结果的可信度分数

- **向量检索**（[Milvus](https://milvus.io/)）
  - 混合检索：稠密向量（Embedding）+ 稀疏检索（BM25）
  - RRF 重排序：Reciprocal Rank Fusion 融合多路结果
  - 大规模语料支持：文档、知识库等非结构化数据

- **大模型生成**（[OpenRouter](https://openrouter.ai/)）
  - 流式输出：实时展示生成过程，提升用户体验
  - 上下文融合：优先使用知识图谱结果，向量检索作为补充
  - 纯文本输出：自动清理 Markdown 格式，保证回答简洁

### 💡 智能上下文增强系统

**基于大模型的对话理解**：自动识别指代性问题，智能补充上下文

- **指代检测**：识别"有什么"、"怎么"、"如何"等指代性词语
- **主题提取**：从对话历史中提取核心实体和主题
- **问题增强**：将提取的主题补充到问题中，生成完整清晰的问题
- **智能判断**：使用大模型进行语义理解，而非简单规则匹配

**示例**：
```
用户：感冒了有什么症状？
助手：感冒的常见症状包括发热、咳嗽、流鼻涕等。

用户：有什么特效药？  ← 包含指代
系统增强：感冒有什么特效药？  ← 自动补充主题
```

> 📖 详细文档：[上下文增强系统](./architecture/context_enhancement.md)

### 💬 对话历史管理系统

**Redis 驱动的会话管理**：支持多轮对话、历史记录、会话切换

- **会话管理**：
  - 自动生成唯一会话ID（UUID）
  - 每个会话最多保存10条对话记录
  - 达到上限自动创建新会话
  - 支持手动创建新会话

- **历史记录**：
  - 实时保存对话到 Redis
  - 历史会话列表展示（最多50个）
  - 点击历史记录可查看完整对话
  - 支持搜索和导出功能

> 📖 详细文档：[对话记录系统](./architecture/conversation_history_system.md)

### 🏗️ 模块化开放架构设计

**清晰的职责划分**：每个模块独立封装，易于维护和扩展

- **配置层**（[`config/`](../config/)）
  - 集中配置管理：环境变量 + 默认值
  - 类型安全：使用 Pydantic Settings
  - 敏感信息隔离：API Key、密码等通过环境变量配置

- **核心层**（[`core/`](../core/)）
  - **模型封装**：Embedding、LLM 统一接口
  - **向量存储**：Milvus 客户端封装，支持混合检索
  - **知识图谱框架**（[`core/framework/`](../core/framework/)）：
    - 自动模式推断（`schema_inferrer.py`）
    - 动态图谱构建（`graph_builder.py`）
    - 模式配置管理（`schema_config.py`）
    - 提示词生成（`prompt_generator.py`）
  - **知识图谱服务**（[`core/graph/`](../core/graph/)）：
    - Neo4j 客户端、图模式定义
    - NL2Cypher 服务（`nl2cypher_service.py`）
    - 查询验证器
  - **缓存系统**：Redis 客户端、对话历史管理
  - **上下文增强**：智能问题增强模块

- **服务层**（[`services/`](../services/)）
  - **Agent 服务**：整合多源检索 + LLM 生成，提供统一问答接口
  - **图服务**：NL2Cypher 生成、验证、执行，独立图服务 API
  - **流式处理**：SSE 流式输出，实时展示检索和生成过程

- **接口层**（[`api/`](../api/)）
  - FastAPI 路由与中间件
  - RESTful API 设计
  - 跨域支持（CORS）

- **展示层**（[`web/`](../web/)）
  - 纯 HTML/JavaScript，无需构建工具
  - 实时流式展示：检索路径、生成过程
  - 对话历史管理：创建、查看、搜索、导出
  - 响应式设计：支持移动端和桌面端

### ⚡ 性能优化与工程实践

**生产级工程化**：注重性能、可维护性和可扩展性

- **检索优化**：
  - 并行检索：向量检索与知识图谱查询同时进行
  - 结果融合：优先使用知识图谱的结构化结果
  - 缓存机制：Redis 缓存常用问答对

- **流式处理**：
  - Server-Sent Events (SSE) 实时推送
  - 分阶段展示：检索进度、生成过程、最终结果
  - 用户体验优化：实时反馈，减少等待焦虑

- **错误处理**：
  - 多层错误处理：API 调用失败自动回退
  - 服务降级：大模型失败时使用规则判断
  - 详细日志：记录每个环节的执行情况

- **开发体验**：
  - 一键启动：`start.sh` 脚本自动启动所有服务
  - 模块化文档：每个模块独立的 README
  - 测试支持：单元测试和集成测试框架

更细粒度的模块说明见各模块目录下的 `README.md`，以及：
- `docs/architecture/technical_workflow.md` - 技术流程说明
- `docs/architecture/conversation_history_system.md` - 对话记录系统
- `docs/architecture/context_enhancement.md` - 上下文增强系统
- `core/framework/README.md` - 通用图谱构建框架

---

## 📍 快速导航

- 🔧 [环境准备](#环境准备) | 🚀 [启动与运行](#启动与运行) | 💻 [使用方式](#使用方式) | 🏗️ [架构概览](#架构概览)
- 📚 [配置模块文档](../config/README.md) | 🧩 [核心模块文档](../core/README.md) | 🔌 [服务层文档](../services/README.md)
- 📖 [技术流程文档](./architecture/technical_workflow.md) | 💬 [对话记录系统](./architecture/conversation_history_system.md) | 🧠 [上下文增强系统](./architecture/context_enhancement.md) | 🎯 [通用图谱构建框架](../core/framework/README.md) | 📦 [项目根目录](../)

---

## 🔄 系统核心流程与技术架构

### 📊 完整工作流程

```
┌─────────────────────────────────────────────────────────────┐
│                    用户查询入口                              │
│              (前端界面 / API 请求)                          │
└────────────────────┬──────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              上下文增强模块                                  │
│  • 获取对话历史 (Redis)                                     │
│  • 大模型分析：判断是否需要增强                             │
│  • 提取主题实体                                             │
│  • 生成增强后的问题                                         │
└────────────────────┬──────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              并行检索阶段                                    │
│  ┌────────────────────┐    ┌────────────────────┐         │
│  │  向量检索 (Milvus) │    │ 知识图谱 (Neo4j)   │         │
│  │  • 稠密向量检索    │    │  • NL2Cypher 生成  │         │
│  │  • BM25 稀疏检索   │    │  • 动态模式加载    │         │
│  │  • RRF 重排序      │    │  • 查询验证        │         │
│  └────────────────────┘    └────────────────────┘         │
└────────────────────┬──────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              结果融合策略                                    │
│  • 优先使用知识图谱的结构化结果（高置信度）                  │
│  • 向量检索结果作为补充（丰富细节）                          │
│  • 构建统一上下文传递给 LLM                                  │
└────────────────────┬──────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              LLM 生成答案 (流式)                            │
│  • OpenRouter 模型生成                                      │
│  • Server-Sent Events 实时推送                             │
│  • 分阶段展示：检索进度 → 生成过程 → 最终结果              │
└────────────────────┬──────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              对话历史保存                                    │
│  • 保存到 Redis (原始问题 + 回答)                           │
│  • 更新会话标题（首次对话后）                                │
│  • 检查会话限制（最多10条）                                  │
└─────────────────────────────────────────────────────────────┘
```

### 🗺️ 知识图谱构建流程

```
┌─────────────────────────────────────────────────────────────┐
│              步骤1：模式推断                                 │
│  • 读取数据文件第一行                                        │
│  • 调用大模型分析数据结构                                    │
│  • 识别节点类型、属性和关系                                  │
│  • 生成 GraphSchema 对象                                    │
│  • 保存模式到配置文件                                        │
└────────────────────┬──────────────────────────────────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│              步骤2：图谱构建                                 │
│  • 加载推断出的图模式                                        │
│  • 读取完整数据文件                                          │
│  • 根据模式动态解析数据                                      │
│  • 批量创建节点和关系                                        │
│  • 验证图谱完整性                                            │
└─────────────────────────────────────────────────────────────┘
```

> 📖 详细文档：[通用知识图谱构建框架](../core/framework/README.md)

### 🔑 核心技术点

1. **🤖 自动化模式推断**（核心创新）
   - ✨ 使用大模型自动分析数据结构
   - 🎯 无需手动定义图模式
   - 🌍 支持多领域数据适配

2. **🏗️ 动态图谱构建**
   - 📊 根据推断的模式自动构建知识图谱
   - 🔗 智能字段映射
   - 📦 支持大规模数据批量处理

3. **🧠 智能上下文增强**
   - 🔍 基于大模型的指代检测和主题提取
   - 💡 自动补充对话历史中的主题实体
   - 📈 提升指代性问题的理解准确性

4. **⚡ 并行检索优化**
   - 🔄 向量检索与知识图谱查询并行执行
   - 🎯 RRF 重排序融合多路检索结果
   - ✅ 查询验证确保知识图谱查询的准确性

5. **🔀 结果融合策略**
   - 🎯 知识图谱结果优先（结构化、高置信度）
   - 📚 向量检索结果补充（非结构化、细节丰富）
   - ⚖️ 智能权重分配，确保答案准确性

6. **🌊 流式生成与展示**
   - 📡 SSE 实时推送检索和生成进度
   - 👁️ 分阶段可视化展示，提升用户体验
   - 🔄 支持中断和错误恢复

7. **💾 对话历史管理**
   - 💿 Redis 持久化存储对话记录
   - 🔄 自动会话管理和标题更新
   - 🔍 支持历史查看、搜索、导出

---

## 📁 目录结构概览

```bash
GraphRAG/
├── requirements.txt            # 项目依赖
├── start.sh                    # 一键启动脚本（启动两大服务并自动打开浏览器）
├── api/                        # API 层（FastAPI 路由与中间件，可选入口）
├── config/                     # 配置管理（环境变量 + 默认值）
├── core/                       # 核心能力
│   ├── framework/              # 通用图谱构建框架（核心）
│   │   ├── schema_inferrer.py  # 自动模式推断
│   │   ├── graph_builder.py    # 动态图谱构建
│   │   ├── schema_config.py    # 模式配置管理
│   │   └── prompt_generator.py  # 提示词生成
│   ├── graph/                  # 知识图谱服务
│   ├── models/                 # 模型封装
│   ├── vector_store/           # 向量存储
│   ├── cache/                  # 缓存系统
│   └── context/                # 上下文增强
├── services/                   # 服务层（Agent 服务、图服务）
├── data/                       # 数据文件（原始 / 处理后 / 词典）
├── storage/                    # 本地数据库 / 模型 / 日志 / PID 等
├── utils/                      # 工具脚本（文档加载、文本切分等）
├── web/                        # 前端静态页面（问答界面）
├── scripts/                    # Python 启动脚本（被 `start.sh` 调用）
│   ├── infer_schema.py         # 模式推断脚本
│   └── build_graph.py          # 图谱构建脚本
├── tests/                      # 测试用例
└── docs/                       # 文档（本文件 + 技术流程）
```

---

## 🔧 环境准备

### 📋 基础依赖

- 🐍 Python 3.8+
- 🗺️ Neo4j 数据库（知识图谱）
- 🔍 Milvus（向量数据库，当前使用本地文件存储）
- 💾 Redis（可选，用于缓存问答）
- 💿 足够磁盘空间（本地模型权重 + 向量库 + 日志）

### 📦 安装 Python 依赖

在项目根目录执行：

```bash
pip install -r requirements.txt
```

推荐使用虚拟环境（`venv` 或 `conda`）：

```bash
python -m venv .venv
source .venv/bin/activate        # Windows 使用 .venv\Scripts\activate
pip install -r requirements.txt
```

### ⚙️ 配置环境变量 / API Key

主要配置集中在 [`config/settings.py`](../config/settings.py)，支持从 `.env` 文件或环境变量中读取。

#### 🚀 快速开始

1. **📋 复制环境变量模板**：
   ```bash
   cp .env.example .env
   ```

2. **✏️ 编辑 `.env` 文件**，填写您的配置：
   ```bash
   # 必需：OpenRouter API Key
   OPENROUTER_API_KEY=your_openrouter_api_key_here
   
   # Neo4j 配置
   NEO4J_URI=bolt://localhost:7687
   NEO4J_USER=neo4j
   NEO4J_PASSWORD=your_password
   ```

#### 📝 主要配置项

- **🤖 OpenRouter API**（统一管理所有大模型调用）：
  - `OPENROUTER_API_KEY`：OpenRouter API Key（**必需**）
    - 🔗 获取方式：访问 https://openrouter.ai/keys 注册并获取
  - `OPENROUTER_LLM_MODEL`：LLM 模型（默认：`deepseek/deepseek-chat`）
    - 📋 可选：`openai/gpt-4`、`openai/gpt-3.5-turbo`、`anthropic/claude-3-opus` 等
  - `OPENROUTER_EMBEDDING_MODEL`：Embedding 模型（默认：`zhipuai/glm-4-embedding`）
    - 📋 可选：`openai/text-embedding-ada-002`、`cohere/embed-english-v3.0` 等

- **🗺️ Neo4j 图数据库**：
  - `NEO4J_URI`：数据库地址（默认：`bolt://localhost:7687`）
  - `NEO4J_USER`：用户名（默认：`neo4j`）
  - `NEO4J_PASSWORD`：密码

- **💾 Redis 缓存**（可选）：
  - `REDIS_HOST`（默认：`0.0.0.0`）
  - `REDIS_PORT`（默认：`6379`）
  - `REDIS_PASSWORD`（可选）

- **🔌 服务端口**：
  - `AGENT_SERVICE_PORT`（默认：`8103`）
  - `GRAPH_SERVICE_PORT`（默认：`8101`）

> ⚠️ **重要提示**：
> - `.env` 文件包含敏感信息，已被 `.gitignore` 忽略，不会提交到代码仓库
> - 建议通过 `.env` 文件配置，而不是系统环境变量
> - 详细配置说明请查看：`config/README.md`
> - 迁移指南：`docs/migration_to_openrouter.md`

---

## 🚀 快速开始

### 第一步：🔍 模式推断

使用 `infer_schema.py` 脚本自动推断数据文件的图模式：

```bash
python scripts/infer_schema.py data/raw/your_data.jsonl --domain your_domain --version 1.0
```

这将自动分析数据结构，识别节点、属性和关系，并生成图模式配置文件（保存在 `config/schemas/your_domain_schema_v1.0.json`）。

### 第二步：🏗️ 构建图谱

使用 `build_graph.py` 脚本根据模式构建知识图谱：

```bash
python scripts/build_graph.py config/schemas/your_domain_schema_v1.0.json data/raw/your_data.jsonl
```

### 第三步：▶️ 启动服务

在项目根目录执行：

```bash
chmod +x start.sh        # 第一次使用需要赋予执行权限
./start.sh
```

该脚本会：
1. 🔍 自动选择 Python 解释器（默认 `python3.11`，可通过环境变量 `PYTHON_CMD` 覆盖）  
2. 🚀 后台启动两个服务：
   - 🤖 Agent 服务：[`scripts/start_agent.py`](../scripts/start_agent.py)（默认端口 `8103`）
   - 🗺️ 图服务：[`scripts/start_graph_service.py`](../scripts/start_graph_service.py)（默认端口 `8101`）
3. ⏳ 等待端口就绪
4. 🌐 在 macOS 上自动打开浏览器访问 `http://localhost:8103/`
5. 👀 监控服务进程，脚本退出时尝试清理子进程

日志输出默认位于：
- [`storage/logs/agent_service_simple.log`](../storage/logs/agent_service_simple.log)
- [`storage/logs/graph_service_simple.log`](../storage/logs/graph_service_simple.log)

> 启动脚本说明：`scripts/README.md` | 启动脚本源码 `start.sh`

---

## 💻 使用方式

### 🖥️ 前端聊天页面

启动 Agent 服务后，在浏览器访问：

```text
http://localhost:8103/
```

#### ✨ 功能特性

页面提供：
- 💬 问答聊天窗口
- 🔘 示例问题按钮
- 📊 多源检索路径可视化：
  - 🔍 向量检索（Milvus）
  - 🗺️ 知识图谱查询（Neo4j）
- 📝 知识图谱生成的 Cypher 语句与置信度展示

### 🔌 直接调用 API

问答接口示例：

```bash
curl -X POST "http://localhost:8103/" \
  -H "Content-Type: application/json" \
  -d '{"question": "你的问题"}'
```

服务信息接口示例：

```bash
curl "http://localhost:8103/api/info"
```

图服务还提供 `/generate`、`/validate`、`/execute` 等接口，详见 `services/README.md` 与 `services/graph_service.py`。

---

## 🏗️ 技术架构详解

### 📐 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                        前端层                                │
│  • HTML/JavaScript 单页应用                                 │
│  • SSE 流式展示                                              │
│  • 对话历史管理                                              │
└────────────────────┬────────────────────────────────────────┘
                     │ HTTP/SSE
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                      API 服务层                               │
│  ┌────────────────────┐    ┌────────────────────┐         │
│  │  Agent Service     │    │  Graph Service     │         │
│  │  (端口: 8103)      │    │  (端口: 8101)       │         │
│  │  • 问答接口        │    │  • NL2Cypher        │         │
│  │  • 流式处理        │    │  • 动态模式加载     │         │
│  │  • 会话管理        │    │  • 查询验证         │         │
│  └────────────────────┘    └────────────────────┘         │
└────────────────────┬────────────────────────────────────────┘
                     │
         ┌───────────┼───────────┐
         │           │           │
         ▼           ▼           ▼
┌─────────────┐ ┌─────────────┐ ┌─────────────┐
│   Milvus    │ │    Neo4j    │ │   Redis     │
│  向量数据库  │ │  知识图谱   │ │  缓存/历史  │
└─────────────┘ └─────────────┘ └─────────────┘
         │           │           │
         └───────────┼───────────┘
                     │
                     ▼
┌─────────────────────────────────────────────────────────────┐
│                      大模型服务                              │
│  • OpenRouter API (LLM 生成)                                  │
│  • OpenRouter API (Embedding)                               │
└─────────────────────────────────────────────────────────────┘
```

### 🔍 核心模块详解

#### ⚙️ `config/` – 配置管理
- 📋 **统一配置中心**：`settings.py` 使用 Pydantic Settings
- 🔐 **环境变量支持**：敏感信息通过环境变量配置
- ✅ **类型安全**：配置项类型检查和验证
- 🎯 **默认值管理**：提供合理的默认配置

#### 🎯 `core/framework/` – 通用图谱构建框架（核心创新）

**`schema_inferrer.py`** - 🤖 自动模式推断
- ✨ 使用大模型分析数据结构
- 🔍 自动识别节点类型、属性和关系
- 📊 生成标准化的 GraphSchema 对象

**`graph_builder.py`** - 🏗️ 动态图谱构建
- 📝 根据模式动态解析数据
- 🔗 智能字段映射：自动识别数据字段到图关系的映射
- 📦 批量创建节点和关系
- ✅ 验证图谱完整性

**`schema_config.py`** - 💾 模式配置管理
- 💿 保存和加载图模式配置
- 🔄 支持领域和版本管理
- 📋 配置文件格式：JSON Schema 标准

**`prompt_generator.py`** - 📝 提示词生成
- 🎯 根据图模式动态生成 NL2Cypher 提示词
- 🌍 支持多领域适配

#### 🗺️ `core/graph/` – 知识图谱服务

**`nl2cypher_service.py`** - 🔄 NL2Cypher 服务
- 🎯 基于动态图模式生成 Cypher 查询
- 🌍 支持领域和版本参数
- ✅ 查询验证和执行

**`neo4j_client.py`** - 🔌 Neo4j 数据库连接
**`schemas.py`** - 📊 图模式定义（节点、关系类型）
**`prompts.py`** - 📝 NL2Cypher 提示词模板（通用版本）
**`validators.py`** - ✅ 查询验证器（语法 + 语义）

#### 🧩 `core/` – 其他核心能力

**`models/`** - 🤖 模型封装
- `embeddings.py`：🔢 Embedding 封装
- `llm.py`：💬 LLM 客户端封装
- 🔌 统一的模型接口，易于切换和扩展

**`vector_store/`** - 🔍 向量存储
- `milvus_client.py`：💾 Milvus 客户端封装
- 🔀 混合检索：稠密向量 + BM25 稀疏检索
- 🎯 RRF 重排序：融合多路检索结果

**`cache/`** - 💾 缓存系统
- `redis_client.py`：🔌 Redis 客户端封装
- 💬 对话历史管理：保存、查询、更新
- 📋 会话列表管理：Sorted Set 实现时间排序

**`context/`** - 🧠 上下文增强
- `enhancer.py`：✨ 智能问题增强模块
- 🔍 大模型驱动的指代检测和主题提取
- 💡 自动问题补全，提升问答准确性

#### 🔌 `services/` – 业务服务层

**`agent_service.py`** - 🤖 Agent 服务
- 🔀 整合多源检索：向量检索 + 知识图谱查询
- 🌊 流式处理：SSE 实时推送检索和生成过程
- 🧠 上下文增强：在检索前增强用户问题
- 💬 会话管理：创建、查询、更新会话
- 🔌 统一问答接口：`POST /` 和 `GET /`

**`graph_service.py`** - 🗺️ 图服务
- 🔄 NL2Cypher 生成：自然语言转 Cypher 查询
- 🎯 动态模式支持：根据领域和版本加载图模式
- ✅ 查询验证：语法检查 + 语义验证
- ⚡ 查询执行：执行 Cypher 并格式化结果
- 🚀 独立服务：可单独部署和扩展

**`streaming_handler.py`** - 🌊 流式处理
- 📡 SSE 事件流：分阶段推送检索和生成进度
- 📋 事件类型：`search_stage`、`answer_chunk`、`query_enhanced` 等
- 🛡️ 错误处理：优雅降级和错误恢复

#### 🖥️ `web/` – 前端展示层
- ✨ **纯前端实现**：无需构建工具，直接运行
- 📊 **实时流式展示**：检索路径、生成过程可视化
- 💬 **对话历史管理**：创建、查看、搜索、导出
- 📱 **响应式设计**：适配移动端和桌面端
- 🎨 **用户体验优化**：加载状态、错误提示、空状态处理

#### 🛠️ `scripts/` – 启动脚本
- `start_agent.py`：🚀 启动 Agent 服务
- `start_graph_service.py`：🗺️ 启动图服务
- `infer_schema.py`：🔍 模式推断脚本
- `build_graph.py`：🏗️ 图谱构建脚本
- `start.sh`：⚡ 一键启动脚本，自动管理进程

### 📊 技术栈总结

| 层级 | 技术选型 | 用途 |
|------|---------|------|
| **🖥️ 前端** | HTML5 + JavaScript (原生) | 单页应用，无需构建 |
| **⚡ 后端框架** | FastAPI | 高性能异步 Web 框架 |
| **🗺️ 知识图谱** | Neo4j | 结构化知识存储 |
| **🔍 向量数据库** | Milvus | 大规模向量检索 |
| **💾 缓存/存储** | Redis | 对话历史、会话管理 |
| **🤖 大模型** | OpenRouter API | LLM 生成和上下文增强 |
| **🔢 Embedding** | OpenRouter API | 文本向量化 |
| **🎯 检索算法** | RRF (Reciprocal Rank Fusion) | 多路检索结果融合 |

### ✨ 核心技术亮点

1. **🤖 自动化模式推断**：无需手动定义图模式，系统自动分析数据结构
2. **🏗️ 动态图谱构建**：根据推断的模式自动构建知识图谱
3. **🔀 混合检索架构**：结合结构化（知识图谱）和非结构化（向量检索）数据
4. **🧠 智能上下文增强**：基于大模型的指代消解和主题提取
5. **🌊 流式处理**：SSE 实时推送，提升用户体验
6. **✅ 查询验证机制**：确保知识图谱查询的准确性和安全性
7. **🧩 模块化设计**：清晰的职责划分，易于维护和扩展
8. **🛠️ 工程化实践**：配置管理、错误处理、日志记录、测试支持

> 📖 更详细的架构与调用链说明，见 [`docs/architecture/technical_workflow.md`](./architecture/technical_workflow.md)

---

## 技术优势与创新点

### 🎯 核心技术优势

1. **自动化知识图谱构建**
   - 零配置模式推断，无需手动定义图模式
   - 智能字段映射，自动识别数据字段到图关系的映射
   - 支持多领域数据适配（医疗、金融、电商等）

2. **混合检索架构**
   - 知识图谱提供结构化、高置信度的答案
   - 向量检索补充非结构化、细节丰富的信息
   - RRF 融合算法优化检索结果排序

3. **智能上下文理解**
   - 基于大模型的指代消解，无需规则维护
   - 自动提取对话主题，智能补充问题上下文
   - 提升多轮对话的理解准确性

4. **流式处理体验**
   - SSE 实时推送，用户可看到检索和生成过程
   - 分阶段可视化展示，减少等待焦虑
   - 支持中断和错误恢复

5. **查询安全保障**
   - NL2Cypher 查询验证：语法检查 + 语义验证
   - 防止恶意查询和注入攻击
   - 置信度评估，确保结果可靠性

6. **工程化实践**
   - 模块化设计，职责清晰
   - 配置集中管理，环境变量支持
   - 完善的错误处理和日志记录
   - 一键启动，开箱即用

### ⚡ 性能指标

- ⚡ **检索速度**：并行检索，总耗时约 2-5 秒
- 🌊 **生成速度**：流式输出，首字延迟 < 1 秒
- 🔄 **并发支持**：FastAPI 异步框架，支持高并发
- 💾 **存储效率**：Redis 压缩存储，支持大规模历史记录

### 🎯 适用场景

- 🌍 **通用知识问答系统**：快速构建领域无关的问答应用
- 🗺️ **知识图谱应用**：展示知识图谱在问答系统中的价值
- 📚 **RAG 系统开发**：作为 RAG 系统的参考实现
- 🎓 **教学演示**：适合作为教学 Demo 和二次开发起点

---

## 🛠️ 开发与扩展指南

### 🚀 快速开始

1. **🔧 环境准备**
   ```bash
   # 安装依赖
   pip install -r requirements.txt
   
   # 配置环境变量
   export OPENROUTER_API_KEY="your_key"
   export NEO4J_URI="bolt://localhost:7687"
   export NEO4J_PASSWORD="your_password"
   ```

2. **🔍 模式推断和图谱构建**
   ```bash
   # 推断模式
   python scripts/infer_schema.py data/raw/your_data.jsonl --domain your_domain --version 1.0
   
   # 构建图谱
   python scripts/build_graph.py config/schemas/your_domain_schema_v1.0.json data/raw/your_data.jsonl
   ```

3. **▶️ 一键启动**
   ```bash
   chmod +x start.sh
   ./start.sh
   ```

4. **🌐 访问系统**
   - 🖥️ 前端界面：http://localhost:8103/
   - 📚 API 文档：http://localhost:8103/docs

### 🔨 扩展开发

#### 📊 新增数据源
1. 📝 准备数据文件（JSONL 格式）
2. 🔍 运行模式推断脚本生成图模式
3. 🏗️ 运行图谱构建脚本构建知识图谱
4. ✨ 系统自动适配新的图模式

#### 🤖 替换/新增 LLM
1. 📦 在 `core/models/llm.py` 中封装新模型
2. ⚙️ 在 `config/settings.py` 中添加配置
3. 🔄 在 Agent 逻辑中切换或路由

#### 🎯 自定义图模式
1. ✏️ 手动编辑 `config/schemas/` 下的模式配置文件
2. 🤖 或使用模式推断脚本自动生成
3. 🔄 系统会自动加载并使用新的图模式

### 💡 最佳实践

- 📦 **依赖管理**：使用虚拟环境，避免系统 Python 冲突
- ⚙️ **配置管理**：优先使用环境变量，不在代码中硬编码
- 🐛 **错误处理**：查看 `storage/logs/` 中的日志文件
- 📋 **代码规范**：遵循模块化设计，保持职责清晰

### 📝 文档维护

如在使用过程中新增模块或流程，建议：

- 📚 在对应模块目录下补充或更新 `README.md`
- 📖 在 `docs/architecture/` 中补充技术文档
- ✏️ 更新本 README 的相关章节
- 📝 如有重大改动，可在 `CHANGELOG.md` 中记录

---

## 📋 项目信息

- 📦 **项目名称**：GraphRAG
- 🎯 **项目类型**：通用知识图谱问答系统 / RAG 系统
- 🛠️ **技术栈**：Python + FastAPI + Neo4j + Milvus + Redis + OpenRouter
- 📜 **许可证**：MIT (待定)
- 🔄 **维护状态**：积极维护中

## 🔗 相关资源

- 📖 [技术流程文档](./architecture/technical_workflow.md)
- 💬 [对话记录系统](./architecture/conversation_history_system.md)
- 🧠 [上下文增强系统](./architecture/context_enhancement.md)
- 🎯 [通用知识图谱构建框架](../core/framework/README.md)
- 📦 [项目根目录](../)

---
