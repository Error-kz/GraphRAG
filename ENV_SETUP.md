# 环境变量配置指南

## 快速开始

### 1. 创建 .env 文件

```bash
# 复制模板文件
cp .env.example .env
```

### 2. 编辑 .env 文件

使用文本编辑器打开 `.env` 文件，填写您的配置：

```bash
# 必需：OpenRouter API Key
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxx

# Neo4j 配置
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password_here
```

### 3. 验证配置

```bash
# 测试配置是否正确加载
python -c "from config.settings import settings; print('✅ OpenRouter API Key:', settings.OPENROUTER_API_KEY[:20] + '...' if settings.OPENROUTER_API_KEY else '❌ 未配置')"
```

## 必需配置项

### OpenRouter API Key（必需）

1. 访问 [OpenRouter 官网](https://openrouter.ai)
2. 注册并登录账号
3. 进入 "API Keys" 页面
4. 生成新的 API 密钥
5. 将密钥添加到 `.env` 文件：

```bash
OPENROUTER_API_KEY=sk-or-v1-xxxxxxxxxxxxx
```

## 可选配置项

### 模型选择

如果需要使用其他模型，可以修改：

```bash
# LLM 模型（用于文本生成）
OPENROUTER_LLM_MODEL=openai/gpt-4

# Embedding 模型（用于向量化）
OPENROUTER_EMBEDDING_MODEL=openai/text-embedding-ada-002
```

### Neo4j 配置

```bash
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password
NEO4J_ENCRYPTED=False
```

### Redis 配置（可选）

```bash
REDIS_HOST=0.0.0.0
REDIS_PORT=6379
REDIS_DB=0
REDIS_PASSWORD=your_redis_password  # 如果设置了密码
```

### 服务端口

```bash
AGENT_SERVICE_PORT=8103
GRAPH_SERVICE_PORT=8101
```

## 注意事项

1. **安全提示**：
   - `.env` 文件包含敏感信息，已被 `.gitignore` 忽略
   - **不要**将 `.env` 文件提交到代码仓库
   - 建议定期更换 API Key

2. **配置优先级**：
   - 系统环境变量 > `.env` 文件 > 代码默认值

3. **向后兼容**：
   - 旧的 `DEEPSEEK_API_KEY` 和 `ZHIPU_API_KEY` 仍然支持
   - 但建议迁移到 `OPENROUTER_API_KEY`

## 故障排除

### 问题：配置未生效

**解决方案**：
1. 确认 `.env` 文件在项目根目录
2. 检查文件格式（不要有多余的空格）
3. 重启服务

### 问题：OpenRouter API Key 未配置

**解决方案**：
1. 检查 `.env` 文件中是否有 `OPENROUTER_API_KEY`
2. 确认 API Key 格式正确（以 `sk-or-v1-` 开头）
3. 验证 API Key 是否有效

### 问题：模型调用失败

**解决方案**：
1. 检查模型名称是否正确（格式：`provider/model-name`）
2. 确认该模型在 OpenRouter 上可用
3. 检查网络连接

## 更多信息

- 详细配置说明：`config/README.md`
- 迁移指南：`docs/migration_to_openrouter.md`
- OpenRouter 文档：https://openrouter.ai/docs

