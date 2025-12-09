# 🚀 GraphRAG 快速启动

欢迎使用 GraphRAG！本指南将帮助您快速启动系统。

## ⚡ 一键启动（推荐）

```bash
# 1. 赋予执行权限（首次使用）
chmod +x start_full.sh

# 2. 一键启动（使用默认配置）
./start_full.sh
```

**默认配置**：
- 数据文件: `data/raw/medical.jsonl`
- 领域: `medical`
- 版本: `1.0`

**自定义参数**：
```bash
./start_full.sh \
  --data-file data/raw/your_data.jsonl \
  --domain your_domain \
  --version 1.0 \
  --clear
```

## 📋 前置准备

1. **安装依赖**
   ```bash
   pip install -r requirements.txt
   ```

2. **配置环境变量**
   ```bash
   cp .env.example .env
   # 编辑 .env 文件，填写 OPENROUTER_API_KEY 和 Neo4j 配置
   ```

3. **准备数据文件**
   - 将数据文件放在 `data/raw/` 目录下
   - 支持格式：JSONL、JSON、CSV

## 🎯 启动流程

脚本会自动执行：
1. ✅ 环境检查
2. 🔍 模式推断（自动分析数据结构）
3. 🏗️ 图谱构建（创建知识图谱）
4. 🚀 启动服务（Agent + Graph）
5. 🌐 打开浏览器

## 🌐 访问服务

启动成功后访问：
- **前端界面**: http://localhost:8103/
- **API 文档**: http://localhost:8103/docs

## 🛑 停止服务

```bash
./stop.sh
```

## 📚 详细文档

- 📖 [完整快速启动指南](docs/QUICK_START.md) - 详细教程和故障排除
- 📖 [主文档](docs/README.md) - 项目完整说明
- 📖 [图谱构建框架](docs/framework/README.md) - 框架详细说明

## ❓ 需要帮助？

查看 [快速启动指南](docs/QUICK_START.md) 中的常见问题部分。

---

**祝您使用愉快！** 🎉

