# Scripts 模块说明

`scripts` 目录存放的是**服务启动、图谱构建和维护脚本**，主要用于简化开发、部署和系统维护。

## 📁 目录结构

```
scripts/
├── __init__.py
├── start_agent.py          # 启动 Agent 服务
├── start_graph_service.py  # 启动图服务
├── infer_schema.py         # 模式推断脚本
└── build_graph.py          # 图谱构建脚本
```

---

## 🚀 服务启动脚本

### start_agent.py

- **作用**：启动主 Agent 服务（问答服务）
- **端口**：从 `config.settings.AGENT_SERVICE_PORT` 读取（默认 `8103`）
- **关键点**
  - 把项目根目录加入 `sys.path`，确保包导入正常
  - 从 `services.agent_service` 导入 `app`
  - 使用 `uvicorn.run(app, host="0.0.0.0", port=settings.AGENT_SERVICE_PORT, workers=1)` 启动服务
  - 提供前端页面（`web/index.html`）和问答 API 接口

**使用方式**：
```bash
python scripts/start_agent.py
```

> 💡 一般不单独调用，更多通过根目录下的 `start.sh` 间接启动。

---

### start_graph_service.py

- **作用**：启动图服务（NL2Cypher + Neo4j 查询）
- **端口**：从 `config.settings.GRAPH_SERVICE_PORT` 读取（默认 `8101`）
- **关键点**
  - 同样通过 `uvicorn.run` 启动 FastAPI 应用
  - 对外提供以下接口：
    - `POST /generate`：生成 Cypher 查询
    - `POST /generate-dynamic`：动态模式生成 Cypher 查询
    - `POST /validate`：验证 Cypher 查询
    - `POST /execute`：执行 Cypher 查询
    - `GET /schema`：获取图模式
  - 供 Agent 服务通过 HTTP 调用

**使用方式**：
```bash
python scripts/start_graph_service.py
```

> 💡 一般不单独调用，更多通过根目录下的 `start.sh` 间接启动。

---

## 🔍 图谱构建脚本

### infer_schema.py

- **作用**：自动推断数据文件的图模式并保存配置
- **功能**：使用大模型分析数据结构，自动识别节点、属性和关系

**使用方法**：
```bash
python scripts/infer_schema.py data/raw/your_data.jsonl --domain your_domain --version 1.0
```

**参数说明**：
- `data_file`（必需）：数据文件路径（支持 JSONL、JSON、CSV）
- `--domain`（必需）：领域名称（如：medical、finance）
- `--version`（可选）：版本号，默认为 "1.0"
- `--output-dir`（可选）：输出目录，默认为 `config/schemas/`

**工作流程**：
1. 读取数据文件第一行
2. 调用大模型分析数据结构
3. 解析 LLM 返回的图模式
4. 生成 `GraphSchema` 对象
5. 保存模式到配置文件（`config/schemas/{domain}_schema_v{version}.json`）

**输出示例**：
```
================================================================================
开始模式推断流程
================================================================================

[步骤1] 读取数据文件第一行...
✅ 成功读取第一行数据，包含 15 个字段

[步骤2] 调用大模型分析数据结构...
✅ 模式推断完成

[步骤3] 生成 GraphSchema 对象...
✅ 模式生成完成
  节点类型: 7 个
  关系类型: 6 个

[步骤4] 保存模式到配置文件...
✅ 模式已保存到: config/schemas/your_domain_schema_v1.0.json
```

> 📖 详细文档：[通用知识图谱构建框架](../docs/framework/README.md)

---

### build_graph.py

- **作用**：根据推断出的图模式构建知识图谱
- **功能**：动态解析数据，批量创建节点和关系

**使用方法**：
```bash
python scripts/build_graph.py config/schemas/your_domain_schema_v1.0.json data/raw/your_data.jsonl
```

**参数说明**：
- `schema_file`（必需）：模式配置文件路径
  - 格式：`config/schemas/{domain}_schema_v{version}.json`
- `data_file`（必需）：数据文件路径
  - 支持格式：JSONL (.jsonl)、JSON (.json)、CSV (.csv)
- `--clear`（可选）：清空现有图谱
  - 使用此选项会删除所有现有节点和关系
  - **谨慎使用**，建议先备份数据
- `--batch-size`（可选）：批量处理大小
  - 默认值：100
  - 控制批量创建节点和关系的大小

**工作流程**：
1. 加载推断出的图模式
2. 读取完整数据文件
3. 根据模式动态解析数据
   - 识别主实体（如：Entity）
   - 识别关联实体（如：Category）
   - 识别关系（如：belongs_to）
4. 批量创建节点和关系
5. 验证图谱完整性

**输出示例**：
```
================================================================================
开始图谱构建流程
================================================================================

[步骤1] 加载推断出的图模式...
✅ 模式加载成功
  领域: your_domain
  版本: 1.0
  节点类型: 7 个
  关系类型: 6 个

[步骤2] 读取完整数据文件: data/raw/your_data.jsonl
✅ 数据读取完成，共 1000 条记录

[步骤3] 数据解析完成
  识别到的主实体: Entity (1000 个)
  识别到的关联实体: Category (50 个)

[步骤4] 批量创建节点和关系...
✅ 节点创建完成
✅ 关系创建完成

[步骤5] 验证图谱完整性...
✅ 图谱构建完成！
```

**使用示例**：
```bash
# 基本构建（不清空现有数据）
python scripts/build_graph.py config/schemas/your_domain_schema_v1.0.json data/raw/your_data.jsonl

# 清空现有图谱后重新构建
python scripts/build_graph.py config/schemas/your_domain_schema_v1.0.json data/raw/your_data.jsonl --clear

# 使用自定义批量大小
python scripts/build_graph.py config/schemas/your_domain_schema_v1.0.json data/raw/your_data.jsonl --batch-size 200
```

> 📖 详细文档：[图谱构建脚本使用说明](../docs/README_build_graph.md)

---

## 🔧 一键启动脚本

### 根目录 start.sh 与 scripts 的关系

根目录的 `start.sh` 是"一键启动脚本"，内部会：

1. **自动选择 Python 解释器**
   - 默认使用 `python3.11`
   - 可通过环境变量 `PYTHON_CMD` 覆盖

2. **后台启动服务**
   - 启动 `scripts/start_agent.py`（Agent 服务）
   - 启动 `scripts/start_graph_service.py`（图服务）

3. **监测端口就绪**
   - 等待服务启动完成
   - 检查端口是否可用

4. **自动打开浏览器**（macOS）
   - 自动打开浏览器访问 `http://localhost:8103/`

5. **进程管理**
   - 监控服务进程
   - 脚本退出时尝试清理子进程

**使用方式**：
```bash
chmod +x start.sh        # 第一次使用需要赋予执行权限
./start.sh
```

> 💡 **推荐在开发和体验时优先使用**：  
> `./start.sh`  
> 这样可以同时启动前后端，并直接打开浏览器。

---

## 📋 完整工作流程示例

### 第一次使用系统

```bash
# 1. 推断图模式
python scripts/infer_schema.py data/raw/your_data.jsonl --domain your_domain --version 1.0

# 2. 构建知识图谱
python scripts/build_graph.py config/schemas/your_domain_schema_v1.0.json data/raw/your_data.jsonl

# 3. 启动服务
./start.sh
```

### 日常开发

```bash
# 直接启动服务（如果图谱已构建）
./start.sh

# 或分别启动服务（用于调试）
python scripts/start_agent.py
python scripts/start_graph_service.py
```

---

## ⚠️ 注意事项

1. **环境要求**
   - 确保已配置 `OPENROUTER_API_KEY` 环境变量
   - 确保 Neo4j 数据库已启动并配置正确
   - 确保 Python 版本 >= 3.8

2. **端口冲突**
   - Agent 服务默认端口：`8103`
   - 图服务默认端口：`8101`
   - 如果端口被占用，可在 `.env` 文件中修改

3. **数据文件格式**
   - 模式推断脚本支持：JSONL、JSON、CSV
   - 图谱构建脚本支持：JSONL、JSON、CSV
   - 确保数据文件格式正确且包含完整字段

4. **日志输出**
   - Agent 服务日志：`storage/logs/agent_service_simple.log`
   - 图服务日志：`storage/logs/graph_service_simple.log`
   - 图谱查询日志：`storage/logs/graph_query.log`

---

## 🔗 相关文档

- [通用知识图谱构建框架](../docs/framework/README.md)
- [图谱构建脚本使用说明](../docs/README_build_graph.md)
- [服务层文档](../services/README.md)
- [配置管理](../config/README.md)
