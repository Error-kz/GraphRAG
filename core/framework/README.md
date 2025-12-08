# 通用知识图谱构建框架

这是一个通用的知识图谱构建框架，可以自动推断数据文件的图模式并构建知识图谱。

## 功能特性

1. **自动模式推断**：使用大模型分析数据结构，自动识别节点、属性和关系
2. **多格式支持**：支持 JSONL、JSON、CSV 等数据格式
3. **模式管理**：自动保存和加载图模式配置
4. **领域无关**：可适配任意领域的数据

## 快速开始

### 1. 模式推断

使用 `infer_schema.py` 脚本自动推断数据文件的图模式：

```bash
python scripts/infer_schema.py data/raw/medical.jsonl --domain medical --version 1.0
```

参数说明：
- `data_file`: 数据文件路径（支持 JSONL/JSON/CSV）
- `--domain`: 领域名称（如：medical, finance）
- `--version`: 版本号（默认：1.0）
- `--output-dir`: 输出目录（默认：config/schemas）

### 2. 使用示例

```python
from core.framework import DataReader, SchemaInferrer, SchemaGenerator, SchemaConfig

# 1. 读取数据
reader = DataReader("data/raw/medical.jsonl")
first_line = reader.read_first_line()

# 2. 推断模式
inferrer = SchemaInferrer()
inferred_schema = inferrer.infer_schema(first_line)

# 3. 生成GraphSchema
generator = SchemaGenerator()
schema = generator.generate_schema(inferred_schema)

# 4. 保存配置
config_manager = SchemaConfig()
config_file = config_manager.save_schema(schema, domain="medical", version="1.0")
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

## 工作流程

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

## 注意事项

1. 确保已配置 `OPENROUTER_API_KEY` 环境变量
2. 数据文件的第一行应该包含完整的字段结构
3. LLM 推断结果可能需要人工验证和调整
4. 生成的模式配置文件可以手动编辑

## 下一步

完成模式推断后，可以：
1. 使用推断出的模式构建知识图谱
2. 基于模式生成 NL2Cypher 提示词
3. 验证和优化推断出的模式

