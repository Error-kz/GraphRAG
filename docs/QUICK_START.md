# GraphRAG 快速启动指南

本指南将帮助您从零开始，完成从数据读取到服务启动的完整流程。

## 📋 目录

- [前置准备](#前置准备)
- [一键启动（推荐）](#一键启动推荐)
- [分步执行](#分步执行)
- [常见问题](#常见问题)
- [高级配置](#高级配置)

---

## 🔧 前置准备

### 1. 环境要求

- **Python**: 3.8+ （推荐 3.11）
- **Neo4j**: 已安装并运行
- **OpenRouter API Key**: 用于大模型调用

### 2. 安装依赖

```bash
# 进入项目目录
cd /path/to/GraphRAG

# 创建虚拟环境（推荐）
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# 安装依赖
pip install -r requirements.txt
```

### 3. 配置环境变量

创建 `.env` 文件（如果不存在）：

```bash
cp .env.example .env
```

编辑 `.env` 文件，填写必要的配置：

```bash
# 必需：OpenRouter API Key
OPENROUTER_API_KEY=your_openrouter_api_key_here

# Neo4j 配置
NEO4J_URI=bolt://localhost:7687
NEO4J_USER=neo4j
NEO4J_PASSWORD=your_password

# 可选：Redis 配置（用于缓存和对话历史）
REDIS_HOST=localhost
REDIS_PORT=6379
```

### 4. 准备数据文件

确保您的数据文件位于 `data/raw/` 目录下，支持格式：
- JSONL (`.jsonl`) - 推荐
- JSON (`.json`)
- CSV (`.csv`)

**数据文件示例** (`data/raw/your_data.jsonl`):
```json
{"name": "实体1", "category": "分类1", "description": "描述1"}
{"name": "实体2", "category": "分类2", "description": "描述2"}
```

---

## 🚀 一键启动（推荐）

### 基本用法

```bash
# 赋予执行权限（首次使用）
chmod +x start_full.sh

# 一键启动（使用默认配置）
./start_full.sh
```

默认配置：
- 数据文件: `data/raw/medical.jsonl`
- 领域: `medical`
- 版本: `1.0`

### 自定义参数

```bash
# 指定数据文件和领域
./start_full.sh \
  --data-file data/raw/your_data.jsonl \
  --domain your_domain \
  --version 1.0

# 清空现有图谱后重新构建
./start_full.sh --clear

# 仅启动服务（跳过模式推断和图谱构建）
./start_full.sh --skip-infer --skip-build
```

### 完整参数说明

| 参数 | 说明 | 默认值 |
|------|------|--------|
| `--data-file FILE` | 数据文件路径 | `data/raw/medical.jsonl` |
| `--domain DOMAIN` | 领域名称 | `medical` |
| `--version VERSION` | 版本号 | `1.0` |
| `--skip-infer` | 跳过模式推断 | `false` |
| `--skip-build` | 跳过图谱构建 | `false` |
| `--clear` | 清空现有图谱 | `false` |
| `--batch-size SIZE` | 批量处理大小 | `100` |
| `--help` | 显示帮助信息 | - |

### 启动流程

脚本会自动执行以下步骤：

1. **环境检查** ✅
   - 检查 Python 环境
   - 检查 `.env` 文件
   - 检查 Python 依赖

2. **模式推断** 🔍
   - 读取数据文件第一行
   - 调用大模型分析数据结构
   - 生成图模式配置
   - 保存到 `config/schemas/{domain}_schema_v{version}.json`

3. **图谱构建** 🏗️
   - 加载图模式配置
   - 读取完整数据文件
   - 动态解析数据
   - 批量创建节点和关系
   - 验证图谱完整性

4. **启动服务** 🚀
   - 启动 Agent 服务（端口 8103）
   - 启动 Graph 服务（端口 8101）
   - 等待服务就绪
   - 自动打开浏览器

---

## 📝 分步执行

如果您想了解每个步骤的详细过程，可以手动执行：

### 步骤1: 模式推断

```bash
python scripts/infer_schema.py \
  data/raw/your_data.jsonl \
  --domain your_domain \
  --version 1.0
```

**输出**：
- 模式配置文件: `config/schemas/your_domain_schema_v1.0.json`
- 控制台输出：节点类型、关系类型等信息

### 步骤2: 图谱构建

```bash
python scripts/build_graph.py \
  config/schemas/your_domain_schema_v1.0.json \
  data/raw/your_data.jsonl \
  --clear \
  --batch-size 100
```

**参数说明**：
- `--clear`: 清空现有图谱（首次构建建议使用）
- `--batch-size`: 批量处理大小（大数据集建议增大）

### 步骤3: 启动服务

**方式一：使用一键启动脚本**
```bash
./start.sh
```

**方式二：分别启动**
```bash
# 终端1: 启动 Agent 服务
python scripts/start_agent.py

# 终端2: 启动 Graph 服务
python scripts/start_graph_service.py
```

---

## 🌐 访问服务

启动成功后，访问以下地址：

- **前端界面**: http://localhost:8103/
- **API 文档**: http://localhost:8103/docs
- **Graph 服务**: http://localhost:8101/

### 测试 API

```bash
# 测试问答接口
curl -X POST "http://localhost:8103/" \
  -H "Content-Type: application/json" \
  -d '{"question": "你的问题"}'

# 测试 Graph 服务
curl "http://localhost:8101/"
```

---

## ❓ 常见问题

### 1. 模式推断失败

**问题**: 提示 "无法读取数据文件" 或 "大模型调用失败"

**解决方案**:
- 检查数据文件路径是否正确
- 检查 `.env` 文件中的 `OPENROUTER_API_KEY` 是否配置
- 检查数据文件格式是否正确（JSONL/JSON/CSV）

### 2. 图谱构建失败

**问题**: 提示 "Neo4j 连接失败" 或 "模式文件不存在"

**解决方案**:
- 确保 Neo4j 数据库已启动
- 检查 `.env` 文件中的 Neo4j 配置
- 确保模式文件已生成（先运行模式推断）

### 3. 服务启动失败

**问题**: 端口被占用或服务无法启动

**解决方案**:
```bash
# 检查端口占用
lsof -i :8103
lsof -i :8101

# 修改端口（在 .env 文件中）
AGENT_SERVICE_PORT=8104
GRAPH_SERVICE_PORT=8102
```

### 4. 浏览器未自动打开

**问题**: 脚本执行完成但浏览器未打开

**解决方案**:
- macOS: 脚本会自动打开浏览器
- Linux: 需要安装 `xdg-open`
- Windows: 手动访问 http://localhost:8103/

---

## ⚙️ 高级配置

### 环境变量配置

通过环境变量覆盖默认值：

```bash
# 设置数据文件
export DATA_FILE="data/raw/your_data.jsonl"

# 设置领域和版本
export DOMAIN="your_domain"
export VERSION="1.0"

# 设置批量大小
export BATCH_SIZE=200

# 执行启动脚本
./start_full.sh
```

### 使用不同的 Python 版本

```bash
# 指定 Python 版本
PYTHON_CMD=python3.11 ./start_full.sh
```

### 后台运行

修改 `start_full.sh` 脚本，注释掉最后的 `wait` 命令，服务将在后台运行。

### 查看日志

```bash
# 实时查看日志
tail -f storage/logs/agent_service_simple.log
tail -f storage/logs/graph_service_simple.log

# 查看图谱查询日志
tail -f storage/logs/graph_query.log
```

### 停止服务

```bash
# 方式1: 使用 PID 文件（如果存在 stop.sh）
./stop.sh

# 方式2: 手动停止
kill $(cat storage/pids/agent_service.pid)
kill $(cat storage/pids/graph_service.pid)

# 方式3: 查找并停止
lsof -ti:8103 | xargs kill
lsof -ti:8101 | xargs kill
```

---

## 📚 下一步

完成启动后，您可以：

1. **查看图谱**: 使用 Neo4j Browser 查看构建的知识图谱
2. **测试问答**: 在前端界面或通过 API 测试问答功能
3. **自定义模式**: 手动编辑模式配置文件以优化图谱结构
4. **扩展功能**: 参考 [开发文档](../README.md) 进行二次开发

---

## 🔗 相关文档

- [主 README](../README.md) - 项目总体介绍
- [通用图谱构建框架](../core/framework/README.md) - 框架详细说明
- [图谱构建脚本说明](./README_build_graph.md) - 构建脚本使用说明
- [服务层文档](../services/README.md) - 服务接口说明

---

## 💡 提示

- **首次使用**: 建议使用 `--clear` 选项清空现有图谱
- **大数据集**: 建议增大 `--batch-size` 参数（如 200-500）
- **开发调试**: 使用 `--skip-infer --skip-build` 快速启动服务
- **生产环境**: 建议分别执行各步骤，便于监控和排查问题

---

**祝您使用愉快！** 🎉

