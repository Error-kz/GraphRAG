# 通用知识图谱构建框架

这是一个通用的知识图谱构建框架，可以自动推断数据文件的图模式并构建知识图谱。

## 功能特性

1. **自动模式推断**：使用大模型分析数据结构，自动识别节点、属性和关系
2. **多格式支持**：支持 JSONL、JSON、CSV 等数据格式
3. **模式管理**：自动保存和加载图模式配置
4. **动态图谱构建**：根据模式配置文件动态构建知识图谱
5. **领域无关**：可适配任意领域的数据

## 快速开始

### 第一步：模式推断

使用 `infer_schema.py` 脚本自动推断数据文件的图模式：

```bash
python scripts/infer_schema.py data/raw/medical.jsonl --domain medical --version 1.0
```

### 第二步：构建图谱

使用 `build_graph.py` 脚本根据模式构建知识图谱：

```bash
python scripts/build_graph.py config/schemas/medical_schema_v1.0.json data/raw/medical.jsonl
```

## 工作流程

### 模式推断流程

```
1. 读取数据文件第一行
   ↓
2. 调用大模型分析数据结构
   ↓
3. 解析LLM返回的图模式
   ↓
4. 生成 GraphSchema 对象
   ↓
5. 保存模式到配置文件
```

### 图谱构建流程

```
1. 加载推断出的图模式
   ↓
2. 读取完整数据文件
   ↓
3. 根据模式动态解析数据
   - 识别主实体（如：Disease）
   - 识别关联实体（如：Drug, Food）
   - 识别关系（如：recommand_drug）
   ↓
4. 批量创建节点和关系
   ↓
5. 验证图谱完整性
```

## 使用示例

### Python API 使用

```python
from core.framework import SchemaConfig, GraphBuilder
from core.graph.neo4j_client import Neo4jClient

# 1. 加载模式
config_manager = SchemaConfig()
schema = config_manager.load_schema("medical", "1.0")

# 2. 创建构建器
builder = GraphBuilder(schema)

# 3. 构建图谱
builder.build_graph(
    data_file="data/raw/medical.jsonl",
    batch_size=100,
    clear_existing=False  # 是否清空现有图谱
)
```

## 架构说明

### 核心模块

1. **DataReader** (`data_reader.py`)
   - 读取数据文件的第一行或前N行
   - 支持 JSONL、JSON、CSV 格式

2. **SchemaInferrer** (`schema_inferrer.py`)
   - 调用大模型分析数据结构
   - 识别节点类型、属性和关系

3. **SchemaGenerator** (`schema_generator.py`)
   - 将推断结果转换为 GraphSchema 对象
   - 验证模式的有效性

4. **SchemaConfig** (`schema_config.py`)
   - 保存和加载图模式配置
   - 支持版本管理

5. **GraphBuilder** (`graph_builder.py`)
   - 根据模式动态解析数据
   - 批量创建节点和关系
   - 验证图谱完整性

## 配置文件格式

生成的配置文件保存在 `config/schemas/` 目录下，格式如下：

```json
{
  "version": "1.0",
  "domain": "medical",
  "nodes": [
    {
      "label": "Disease",
      "properties": {
        "name": "string",
        "desc": "string"
      }
    }
  ],
  "relationships": [
    {
      "type": "has_symptom",
      "from_node": "Disease",
      "to_node": "Symptom",
      "properties": {}
    }
  ]
}
```

## 字段映射规则

框架会自动推断数据字段到图模式的映射：

- `symptom` → `has_symptom` → `Symptom`
- `category` → `belongs_to_category` → `Category`
- `acompany` → `has_acompany` → `Acompany`
- `cure_way` → `cured_by` → `CureWay`
- `check` → `needs_check` → `Check`
- `cure_department` → `treated_in` → `Department`

## 注意事项

1. 确保已配置 `OPENROUTER_API_KEY` 环境变量
2. 确保 Neo4j 数据库已启动并配置正确
3. 数据文件的第一行应该包含完整的字段结构
4. LLM 推断结果可能需要人工验证和调整
5. 生成的模式配置文件可以手动编辑

## 下一步

完成模式推断和图谱构建后，可以：
1. 使用推断出的模式生成 NL2Cypher 提示词
2. 验证和优化推断出的模式
3. 扩展框架支持更多数据格式和关系类型
