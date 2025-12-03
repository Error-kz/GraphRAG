# vector_store 模块说明

`vector_store` 模块封装了 Milvus 向量数据库的操作，提供向量存储和检索功能。

## 目录结构

```
vector_store/
├── __init__.py
└── milvus_client.py
```

## 主要功能

### 向量存储管理

- **混合索引**：支持稠密向量（Dense）和稀疏向量（Sparse/BM25）混合索引
- **批量处理**：支持批量添加文档，优化插入性能
- **自动向量化**：自动使用 Embedding 模型将文本转换为向量

### 向量检索

- **相似度搜索**：基于向量相似度进行文档检索
- **多字段检索**：支持稠密向量和稀疏向量的混合检索

## 主要文件

### milvus_client.py

#### `MilvusVectorStore` 类

Milvus 向量存储封装类，用于创建和管理 Milvus 向量数据库。

**初始化**：
```python
vector_store = MilvusVectorStore(embedding_model=None, uri=None)
```

**参数**：
- `embedding_model`：`ZhipuAIEmbeddings` 实例，如果为 `None` 则自动创建
- `uri`：Milvus 数据库 URI，如果为 `None` 则使用 `config.settings.MILVUS_AGENT_DB`

**索引配置**：

1. **稠密索引（Dense）**：
   - Metric Type：`IP`（内积）
   - Index Type：`IVF_FLAT`

2. **稀疏索引（Sparse/BM25）**：
   - Metric Type：`BM25`
   - Index Type：`SPARSE_INVERTED_INDEX`

**主要方法**：

##### `create_vector_store(docs: list) -> Milvus`

创建向量存储并添加文档。

**参数**：
- `docs`：文档列表（`langchain_core.documents.Document` 对象）

**返回**：Milvus 向量存储实例

**工作流程**：
1. 使用前 10 个文档初始化向量存储
2. 批量添加剩余文档（每批 5 个）
3. 显示插入进度
4. 返回可用的向量存储实例

**特性**：
- 使用 `BM25BuiltInFunction()` 进行稀疏向量生成
- 支持双向量字段（`dense` 和 `sparse`）
- 一致性级别：`Bounded`
- 不删除旧数据（`drop_old=False`）

## 使用示例

### 创建向量存储

```python
from core.vector_store.milvus_client import MilvusVectorStore
from langchain_core.documents import Document

# 准备文档
documents = [
    Document(page_content="文档内容1", metadata={"source": "doc1"}),
    Document(page_content="文档内容2", metadata={"source": "doc2"}),
    # ... 更多文档
]

# 创建向量存储
vector_store = MilvusVectorStore()
milvus_store = vector_store.create_vector_store(documents)
```

### 检索文档

```python
# 使用 LangChain 的检索器进行相似度搜索
from langchain.retrievers import ContextualCompressionRetriever

# 创建检索器
retriever = milvus_store.as_retriever(search_kwargs={"k": 5})

# 检索相关文档
query = "用户查询"
results = retriever.get_relevant_documents(query)
```

### 在 Agent 服务中使用

```python
from core.vector_store.milvus_client import MilvusVectorStore
from core.models.embeddings import ZhipuAIEmbeddings
from langchain_milvus import Milvus

# 创建 Embedding 模型
embeddings = ZhipuAIEmbeddings()

# 直接使用 LangChain 的 Milvus 集成
vectorstore = Milvus.from_documents(
    documents=docs,
    embedding=embeddings,
    builtin_function=BM25BuiltInFunction(),
    index_params=[dense_index, sparse_index],
    vector_field=['dense', 'sparse'],
    connection_args={'uri': settings.MILVUS_AGENT_DB},
    consistency_level='Bounded',
    drop_old=False,
)

# 进行检索
results = vectorstore.similarity_search(query, k=5)
```

## 配置要求

### Milvus 配置

需要在 `config/settings.py` 中配置：
```python
MILVUS_AGENT_DB = "path/to/milvus/database"  # 本地 Milvus 数据库路径
```

### Embedding 配置

需要配置智谱 AI API Key（见 `core/models/README.md`）。

## 技术细节

### 混合检索

- **稠密向量（Dense）**：使用 Embedding 模型生成的语义向量，适合语义相似度检索
- **稀疏向量（Sparse/BM25）**：使用 BM25 算法生成的词频向量，适合关键词匹配

混合使用两种索引可以同时利用语义理解和关键词匹配的优势。

### 索引参数

- **IVF_FLAT**：倒排文件索引，适合中等规模数据
- **SPARSE_INVERTED_INDEX**：稀疏倒排索引，专门用于 BM25 向量

### 一致性级别

- **Bounded**：有界一致性，在性能和一致性之间取得平衡

## 性能优化

1. **批量插入**：使用批量插入减少网络开销
2. **进度显示**：使用 `tqdm` 显示插入进度
3. **延迟控制**：在批量插入之间添加延迟，避免过载

## 注意事项

1. **数据库路径**：确保 Milvus 数据库路径正确且有写权限
2. **内存使用**：大量文档插入时注意内存使用情况
3. **索引构建**：首次创建索引需要一定时间，取决于文档数量
4. **数据持久化**：确保 Milvus 数据库路径稳定，避免数据丢失

## 扩展建议

1. **检索优化**：可以根据业务需求调整检索参数（如 `k` 值、相似度阈值）
2. **元数据过滤**：利用 Milvus 的元数据过滤功能进行更精确的检索
3. **索引优化**：根据数据规模选择合适的索引类型和参数
4. **监控告警**：添加向量存储的监控和告警机制

