# PromptGenerator 动态提示词生成器

## 概述

`PromptGenerator` 是一个智能的、领域无关的动态提示词生成器，专门用于为 NL2Cypher（自然语言转 Cypher 查询）任务生成系统提示词。它能够根据任意图数据库模式自动生成包含图模式描述、语义映射规则和查询示例的完整提示词。

## 核心特性

### 🎯 领域无关设计
- **无需硬编码**：不依赖特定领域或节点类型
- **自动适配**：根据图模式自动生成适配的提示词
- **通用规则**：基于命名模式自动推断语义

### 🧠 智能语义推断
- **关系语义推断**：自动识别否定关系（not_eat）、推荐关系（recommend_xxx）、拥有关系（has_xxx）等
- **节点描述推断**：基于节点标签命名模式自动生成中文描述
- **动作词提取**：从关系名称中自动提取动作词（eat → 吃，take → 服用等）

### 📝 动态内容生成
- **图模式描述**：自动构建节点类型和关系类型的描述
- **中文语义映射**：按目标节点分组，自动生成关系类型与中文表达的映射
- **查询示例**：为主实体和每个关系自动生成自然语言到 Cypher 的查询示例

### 🔧 高度可扩展
- **模式匹配**：基于命名模式自动识别，无需维护映射表
- **规则驱动**：使用通用规则而非硬编码列表
- **易于扩展**：新增节点或关系类型时自动适配

## 快速开始

### 基本使用

```python
from core.framework.prompt_generator import PromptGenerator
from core.framework.schema_config import SchemaConfig

# 1. 加载图模式
config_manager = SchemaConfig()
schema = config_manager.load_schema("medical", "2.0")

# 2. 创建提示词生成器
generator = PromptGenerator(schema)

# 3. 生成系统提示词
system_prompt = generator.generate_system_prompt()
print(system_prompt)
```

### 在 NL2Cypher 服务中使用

```python
from core.framework.nl2cypher_service import NL2CypherService

# 方式1：使用领域和版本
service = NL2CypherService(domain="medical", version="2.0")

# 方式2：直接使用 GraphSchema 对象
from core.framework.schema_config import SchemaConfig
config_manager = SchemaConfig()
schema = config_manager.load_schema("medical", "2.0")
service = NL2CypherService(schema=schema)

# 生成 Cypher 查询
result = service.generate_cypher("感冒有什么忌口的吗")
print(result["cypher_query"])
```

## API 文档

### PromptGenerator 类

#### `__init__(schema: GraphSchema)`

初始化提示词生成器。

**参数：**
- `schema` (GraphSchema): 图模式对象，包含节点和关系定义

**示例：**
```python
from core.graph.schemas import GraphSchema
generator = PromptGenerator(schema)
```

#### `generate_system_prompt() -> str`

生成完整的系统提示词，包含：
- 图数据库模式描述
- Cypher 查询规则
- 中文语义映射说明
- 查询示例

**返回：**
- `str`: 完整的系统提示词字符串

**示例：**
```python
prompt = generator.generate_system_prompt()
```

#### `generate_validation_prompt(cypher_query: str) -> str`

生成用于验证 Cypher 查询的提示词。

**参数：**
- `cypher_query` (str): 需要验证的 Cypher 查询语句

**返回：**
- `str`: 验证提示词

**示例：**
```python
validation_prompt = generator.generate_validation_prompt(
    "MATCH (d:Disease)-[:not_eat]->(f:Food) RETURN f.name"
)
```

## 工作原理

### 1. 图模式描述构建

`_build_schema_description()` 方法会：
- 遍历所有节点类型，列出每个节点的属性
- 遍历所有关系类型，展示关系的起点、类型和终点
- 生成结构化的模式描述

**示例输出：**
```
## 节点类型
- Disease: name (string), desc (string), prevent (string), ...
- Food: name (string)
- Drug: name (string)

## 关系类型
- Disease --[not_eat]--> Food
- Disease --[recommand_drug]--> Drug
```

### 2. 中文语义映射生成

`_generate_semantic_mapping()` 方法会：
- 按目标节点类型分组关系
- 为每个关系自动推断中文语义和关键词
- 生成通用映射规则

**示例输出：**
```
## 食物相关关系
- **not_eat关系**：不能吃的食物（忌口）
  - 中文表达：'忌'、'不能'、'禁止'、'避免'、'忌口'、'忌吃'、'不能吃'、'禁止吃'
  - 查询示例：'Disease有什么忌口的吗' 或 'Disease不能吃什么' → 使用 not_eat 关系

## 通用映射规则
1. **否定关系识别**：当关系名称包含 'not'、'no'、'avoid' 等否定词时...
2. **推荐关系识别**：当关系名称包含 'recommend'、'suggest' 等词时...
```

### 3. 查询示例生成

`_generate_examples()` 方法会：
- 识别主实体（属性最多的节点）
- 为主实体生成基本查询示例
- 为每个关系生成关系查询示例
- 生成属性查询和聚合查询示例

**示例输出：**
```
自然语言: "Disease有什么忌口的吗" 或 "Disease不能吃什么"
Cypher: "MATCH (d:Disease)-[r:not_eat]->(f:Food) WHERE d.name CONTAINS '示例' RETURN f.name"
```

### 4. 智能语义推断

#### 关系语义推断 (`_infer_relationship_semantic`)

基于关系名称模式自动推断：
- **否定关系**：`not_eat`, `not_use`, `avoid_xxx` → "不能吃的食物"
- **推荐关系**：`recommend_drug`, `suggest_xxx` → "推荐药物"
- **拥有关系**：`has_symptom`, `have_xxx` → "拥有症状"
- **动作关系**：自动提取动作词（eat → 吃）

#### 节点描述推断 (`_infer_node_description_from_label`)

基于节点标签命名模式自动推断：
- **直接匹配**：`Food` → "食物"
- **部分匹配**：`UserProfile` → 识别 `User` → "用户"
- **PascalCase 处理**：`AcompanyDisease` → 识别 `Disease` → "疾病"
- **中文标签**：直接返回中文标签

#### 动作词提取 (`_extract_action_from_rel`)

从关系名称中提取动作词：
- `eat` → "吃"
- `take` → "服用"
- `use` → "使用"
- `visit` → "访问"

## 设计理念

### 1. 通用性优先

不硬编码特定领域或节点类型，而是基于命名模式和通用规则自动推断：

```python
# ❌ 不这样做（硬编码）
node_desc_map = {
    'Food': '食物',
    'Drug': '药物',
    # ... 需要维护大量映射
}

# ✅ 这样做（模式匹配）
if 'food' in label_lower:
    return '食物'
if 'drug' in label_lower or 'medicine' in label_lower:
    return '药物'
```

### 2. 规则驱动

使用通用规则而非特定映射：

```python
# 否定关系识别规则
if any(neg in rel_lower for neg in ['not', 'no', 'avoid', '禁止', '忌']):
    # 自动识别为否定关系
    keywords.extend(['忌', '不能', '禁止', '避免'])
```

### 3. 自动适配

新增节点或关系类型时，系统自动适配，无需修改代码：

```python
# 新增关系类型 not_drink
# 系统自动识别：
# - 包含 'not' → 否定关系
# - 包含 'drink' → 动作词 "喝"
# - 目标节点 Food → "食物"
# 自动生成：不能喝的食物
```

## 使用示例

### 示例 1：医疗领域

```python
from core.framework.prompt_generator import PromptGenerator
from core.framework.schema_config import SchemaConfig

# 加载医疗领域模式
config_manager = SchemaConfig()
schema = config_manager.load_schema("medical", "2.0")

# 生成提示词
generator = PromptGenerator(schema)
prompt = generator.generate_system_prompt()

# 生成的提示词包含：
# - Disease、Food、Drug 等节点描述
# - not_eat、recommand_drug 等关系映射
# - "感冒有什么忌口的吗" → not_eat 关系的示例
```

### 示例 2：电商领域

```python
# 假设有电商领域的图模式
# 节点：Product, Category, User, Order
# 关系：belongs_to, purchased_by, recommended_for

schema = load_ecommerce_schema()
generator = PromptGenerator(schema)
prompt = generator.generate_system_prompt()

# 系统自动：
# - 识别 Product → "产品"
# - 识别 belongs_to → "属于分类"
# - 生成相应的查询示例
```

### 示例 3：自定义图模式

```python
from core.graph.schemas import GraphSchema, NodeSchema, RelationshipSchema

# 创建自定义图模式
nodes = [
    NodeSchema(label="Article", properties={"title": "string", "content": "string"}),
    NodeSchema(label="Tag", properties={"name": "string"}),
]
relationships = [
    RelationshipSchema(type="has_tag", from_node="Article", to_node="Tag", properties={}),
]
schema = GraphSchema(nodes=nodes, relationships=relationships)

# 生成提示词
generator = PromptGenerator(schema)
prompt = generator.generate_system_prompt()

# 系统自动：
# - 识别 Article → "文章"（基于 article 词根）
# - 识别 Tag → "标签"（基于 tag 词根）
# - 识别 has_tag → "拥有标签"
```

## 扩展和自定义

### 扩展节点描述映射

如果需要支持新的节点类型，可以在 `_infer_node_description_from_label` 方法中添加词根映射：

```python
word_mappings = {
    'food': '食物',
    'drug': '药物',
    # 添加新的映射
    'recipe': '食谱',
    'ingredient': '食材',
}
```

### 扩展动作词映射

在 `_extract_action_from_rel` 方法中添加新的动作词：

```python
action_map = {
    'eat': '吃',
    'take': '服用',
    # 添加新的动作词
    'cook': '烹饪',
    'prepare': '准备',
}
```

### 自定义关系语义规则

可以在 `_infer_relationship_semantic` 方法中添加新的关系模式识别规则：

```python
# 添加新的关系模式
elif 'contain' in rel_lower or 'include' in rel_lower:
    description = f"包含{target_desc}"
```

## 最佳实践

### 1. 节点命名规范

使用清晰的英文命名，便于自动推断：

```python
# ✅ 推荐
- Food, Drug, Symptom, Disease
- UserProfile, OrderItem, ProductCategory

# ❌ 不推荐
- F, D, S, D  # 太简短，无法推断
- 食物, 药物  # 中文命名，虽然支持但不利于国际化
```

### 2. 关系命名规范

使用语义明确的关系名称：

```python
# ✅ 推荐
- not_eat, recommand_drug, has_symptom
- belongs_to, purchased_by, recommended_for

# ❌ 不推荐
- rel1, rel2, r1, r2  # 无语义
- 不能吃, 推荐药物  # 中文命名
```

### 3. 模式设计建议

- **主实体明确**：确保有一个属性最多的节点作为主实体
- **关系语义清晰**：使用有意义的动词和方向
- **属性命名一致**：使用 `name` 作为标识属性（如果可能）

## 常见问题

### Q: 如何支持新的节点类型？

A: 系统会自动识别。如果无法识别，可以在 `_infer_node_description_from_label` 方法中添加词根映射，或者使用更明确的命名（如 `ProductItem` 而不是 `Item`）。

### Q: 如何自定义关系的中文表达？

A: 系统基于命名模式自动推断。如果需要特定表达，可以：
1. 使用更明确的命名（如 `recommend_drug` 而不是 `drug`）
2. 在 `_infer_relationship_keywords` 方法中添加特定规则

### Q: 生成的提示词太长怎么办？

A: 提示词长度取决于图模式的复杂度。可以：
1. 优化图模式，减少不必要的节点和关系
2. 只为主实体生成示例（当前实现）
3. 自定义 `_generate_examples` 方法，限制示例数量

### Q: 如何处理中文节点标签？

A: 系统支持中文标签，会直接返回中文标签作为描述。但建议使用英文命名，便于国际化。

## 技术细节

### 依赖关系

```python
from core.graph.schemas import GraphSchema, NodeSchema, RelationshipSchema
```

### 内部方法

- `_build_schema_description()`: 构建图模式描述
- `_generate_semantic_mapping()`: 生成中文语义映射
- `_generate_examples()`: 生成查询示例
- `_infer_relationship_semantic()`: 推断关系语义
- `_infer_relationship_keywords()`: 推断关系关键词
- `_get_node_description()`: 获取节点描述
- `_infer_node_description_from_label()`: 基于标签推断描述
- `_extract_action_from_rel()`: 提取动作词

## 更新日志

### v1.0 (当前版本)
- ✅ 基础功能：图模式描述、语义映射、查询示例生成
- ✅ 智能推断：关系语义、节点描述、动作词提取
- ✅ 通用设计：领域无关、规则驱动、自动适配

## 相关文档

- [GraphSchema 文档](../../core/graph/README.md)
- [Framework 框架文档](./README.md)
- [图模式配置文档](../../core/framework/schema_config.py)

## 贡献指南

欢迎贡献代码和提出建议！主要改进方向：
1. 扩展节点描述词根映射
2. 扩展动作词映射
3. 优化提示词生成逻辑
4. 支持多语言提示词生成

