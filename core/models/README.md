# models 模块说明

`models` 模块封装了项目中使用的各种模型，包括 Embedding 模型和大语言模型（LLM），提供统一的接口和便捷的使用方式。

## 目录结构

```
models/
├── __init__.py
├── embeddings.py    # Embedding 模型封装
└── llm.py          # 大语言模型封装
```

## 主要功能

### Embedding 模型

- **统一接口**：封装智谱 AI Embedding 模型，提供与 LangChain 兼容的接口
- **批量处理**：支持批量生成文档向量和单条查询向量
- **自动配置**：自动从配置中读取 API Key

### 大语言模型

- **客户端管理**：提供 DeepSeek 等 LLM 客户端的创建方法
- **答案生成**：封装答案生成流程，包括格式清理
- **配置管理**：统一管理模型参数和配置

## 主要文件

### embeddings.py

#### `ZhipuAIEmbeddings` 类

智谱 AI Embedding 模型的封装类，继承自 `langchain.embeddings.base.Embeddings`。

**初始化**：
```python
embeddings = ZhipuAIEmbeddings(client=None)
```

**参数**：
- `client`：ZhipuAiClient 实例，如果为 `None` 则自动创建

**主要方法**：

##### `embed_documents(texts: list) -> list`

批量生成文档的嵌入向量。

**参数**：
- `texts`：文本列表

**返回**：嵌入向量列表，每个向量对应一个输入文本

**使用场景**：用于批量处理文档，构建向量索引

##### `embed_query(text: str) -> list`

生成查询文本的嵌入向量。

**参数**：
- `text`：查询文本

**返回**：嵌入向量（列表）

**使用场景**：用于将用户查询转换为向量，进行相似度检索

**技术细节**：
- 使用智谱 AI 的 `embedding-3` 模型
- 自动从 `config.settings.ZHIPU_API_KEY` 读取 API Key

### llm.py

#### `create_deepseek_client() -> OpenAI`

创建 DeepSeek 客户端。

**返回**：配置好的 OpenAI 客户端实例（使用 DeepSeek API）

**配置**：
- API Key：从 `config.settings.DEEPSEEK_API_KEY` 读取
- Base URL：`https://api.deepseek.com/v1`
- 兼容 OpenAI SDK 接口

#### `generate_deepseek_answer(client: OpenAI, question: str) -> str`

使用 DeepSeek 生成答案。

**参数**：
- `client`：DeepSeek 客户端实例
- `question`：问题文本

**返回**：生成的答案（已清理 Markdown 格式）

**功能特性**：
- 自动清理 Markdown 格式标记（粗体、斜体、标题、代码块等）
- 移除 HTML 标签
- 规范化换行符
- 返回纯文本格式

**模型配置**：
- 模型：`deepseek-chat`
- Temperature：0.7
- Max Tokens：2048
- Stream：False

**系统提示词**：要求模型使用纯文本格式回答，不使用 Markdown 格式。

## 使用示例

### Embedding 模型使用

```python
from core.models.embeddings import ZhipuAIEmbeddings

# 创建 Embedding 模型实例
embeddings = ZhipuAIEmbeddings()

# 批量生成文档向量
documents = ["文档1", "文档2", "文档3"]
doc_vectors = embeddings.embed_documents(documents)

# 生成查询向量
query = "用户查询"
query_vector = embeddings.embed_query(query)
```

### LLM 使用

```python
from core.models.llm import create_deepseek_client, generate_deepseek_answer

# 创建客户端
client = create_deepseek_client()

# 生成答案
question = "什么是高血压？"
answer = generate_deepseek_answer(client, question)
print(answer)
```

### 在向量检索中使用

```python
from core.models.embeddings import ZhipuAIEmbeddings
from langchain_milvus import Milvus

# 创建 Embedding 模型
embeddings = ZhipuAIEmbeddings()

# 创建向量存储
vectorstore = Milvus.from_documents(
    documents=docs,
    embedding=embeddings,
    # ... 其他配置
)

# 进行相似度检索
results = vectorstore.similarity_search(query, k=5)
```

## 配置要求

### Embedding 模型配置

需要在 `config/settings.py` 中配置：
```python
ZHIPU_API_KEY = "your-zhipu-api-key"
```

### LLM 配置

需要在 `config/settings.py` 中配置：
```python
DEEPSEEK_API_KEY = "your-deepseek-api-key"
```

## 设计优势

1. **统一接口**：避免在业务代码中直接操作底层模型类
2. **配置集中**：所有模型配置统一管理
3. **易于扩展**：可以轻松添加新的模型支持
4. **格式处理**：自动处理模型输出的格式问题
5. **LangChain 兼容**：Embedding 类兼容 LangChain 生态

## 注意事项

1. **API Key 安全**：确保 API Key 不会泄露到代码仓库
2. **速率限制**：注意 API 调用速率限制，必要时实现重试机制
3. **错误处理**：在实际使用中应添加适当的错误处理和重试逻辑
4. **成本控制**：Embedding 和 LLM 调用都会产生费用，注意控制调用频率

