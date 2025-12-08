# 迁移到 OpenRouter API 指南

## 概述

本项目已将所有大模型调用（包括 DeepSeek 和 ZhipuAI）统一迁移到 OpenRouter API。OpenRouter 是一个统一的 API 网关，可以访问多个大模型提供商。

## 配置更改

### 1. 环境变量配置

在 `.env` 文件中添加以下配置：

```bash
# OpenRouter API Key（必需）
OPENROUTER_API_KEY=your_openrouter_api_key_here

# 模型选择（可选，有默认值）
OPENROUTER_LLM_MODEL=deepseek/deepseek-chat
OPENROUTER_EMBEDDING_MODEL=zhipuai/glm-4-embedding
```

### 2. 获取 OpenRouter API Key

1. 访问 [OpenRouter 官网](https://openrouter.ai)
2. 注册并登录账号
3. 进入 "API Keys" 页面
4. 生成新的 API 密钥
5. 将密钥添加到 `.env` 文件中

### 3. 支持的模型

OpenRouter 支持多种模型，您可以根据需要选择：

**LLM 模型（用于文本生成）：**
- `deepseek/deepseek-chat` - DeepSeek Chat（默认）
- `openai/gpt-4` - GPT-4
- `openai/gpt-3.5-turbo` - GPT-3.5 Turbo
- `anthropic/claude-3-opus` - Claude 3 Opus
- `google/gemini-pro` - Google Gemini Pro
- 更多模型请查看 [OpenRouter 模型列表](https://openrouter.ai/models)

**Embedding 模型（用于向量化）：**
- `zhipuai/glm-4-embedding` - 智谱 GLM-4 Embedding（默认）
- `openai/text-embedding-ada-002` - OpenAI Embedding
- `cohere/embed-english-v3.0` - Cohere Embedding
- 更多模型请查看 [OpenRouter Embedding 模型](https://openrouter.ai/models?supported_parameters=embedding)

## 代码更改说明

### 1. LLM 客户端

**之前：**
```python
from core.models.llm import create_deepseek_client, generate_deepseek_answer

client = create_deepseek_client()
answer = generate_deepseek_answer(client, question)
```

**现在：**
```python
from core.models.llm import create_openrouter_client, generate_answer

client = create_openrouter_client()
answer = generate_answer(client, question)
```

**向后兼容：**
```python
# 仍然支持旧的函数名（内部使用 OpenRouter）
from core.models.llm import create_deepseek_client, generate_deepseek_answer

client = create_deepseek_client()  # 内部使用 OpenRouter
answer = generate_deepseek_answer(client, question)  # 内部使用 OpenRouter
```

### 2. Embedding 客户端

**之前：**
```python
from zai import ZhipuAiClient
from core.models.embeddings import ZhipuAIEmbeddings

client = ZhipuAiClient(api_key=settings.ZHIPU_API_KEY)
embeddings = ZhipuAIEmbeddings(client)
```

**现在：**
```python
from core.models.embeddings import ZhipuAIEmbeddings

# 自动使用 OpenRouter API
embeddings = ZhipuAIEmbeddings()
```

### 3. 模型调用

所有模型调用现在都通过 OpenRouter API，模型名称格式为 `provider/model-name`：

```python
# 之前
response = client.chat.completions.create(
    model="deepseek-chat",
    ...
)

# 现在
response = client.chat.completions.create(
    model=settings.OPENROUTER_LLM_MODEL,  # 默认: "deepseek/deepseek-chat"
    ...
)
```

## 已修改的文件

### 核心模块
- `config/settings.py` - 添加 OpenRouter 配置
- `core/models/llm.py` - 迁移到 OpenRouter API
- `core/models/embeddings.py` - 迁移到 OpenRouter API

### 服务层
- `services/graph_service.py` - 更新 LLM 调用
- `services/agent_service.py` - 更新 LLM 和 Embedding 调用
- `services/streaming_handler.py` - 更新流式 LLM 调用

### 上下文增强
- `core/context/enhancer.py` - 更新 LLM 调用

### 框架模块
- `core/framework/schema_inferrer.py` - 更新 LLM 调用

### 工具模块
- `utils/create_vector.py` - 更新 Embedding 调用
- `core/vector_store/milvus_client.py` - 更新 Embedding 调用

## 迁移步骤

1. **备份现有配置**
   ```bash
   cp .env .env.backup
   ```

2. **添加 OpenRouter API Key**
   在 `.env` 文件中添加：
   ```bash
   OPENROUTER_API_KEY=your_key_here
   ```

3. **（可选）自定义模型**
   如果需要使用其他模型，添加：
   ```bash
   OPENROUTER_LLM_MODEL=openai/gpt-4
   OPENROUTER_EMBEDDING_MODEL=openai/text-embedding-ada-002
   ```

4. **测试配置**
   ```bash
   python -c "from config.settings import settings; print(f'OpenRouter API Key: {settings.OPENROUTER_API_KEY[:10]}...')"
   ```

## 优势

1. **统一管理**：所有大模型调用通过一个 API
2. **灵活切换**：可以轻松切换不同的模型提供商
3. **成本优化**：OpenRouter 提供统一的计费和管理
4. **向后兼容**：旧的函数名仍然可用

## 注意事项

1. **API Key 安全**：请妥善保管 OpenRouter API Key，不要提交到代码仓库
2. **模型可用性**：某些模型可能在某些地区不可用，请查看 OpenRouter 文档
3. **成本控制**：OpenRouter 按使用量计费，请注意控制使用量
4. **Embedding 支持**：不是所有模型都支持 embedding，请确认选择的模型支持该功能

## 故障排除

### 错误：OPENROUTER_API_KEY 未配置

**解决方案**：在 `.env` 文件中添加 `OPENROUTER_API_KEY`

### 错误：模型不支持 embedding

**解决方案**：更换为支持 embedding 的模型，例如：
```bash
OPENROUTER_EMBEDDING_MODEL=openai/text-embedding-ada-002
```

### 错误：API 调用失败

**解决方案**：
1. 检查 API Key 是否正确
2. 检查网络连接
3. 查看 OpenRouter 服务状态
4. 检查模型名称是否正确

## 更多信息

- [OpenRouter 官方文档](https://openrouter.ai/docs)
- [OpenRouter 模型列表](https://openrouter.ai/models)
- [OpenRouter API 参考](https://openrouter.ai/docs/api-reference)

