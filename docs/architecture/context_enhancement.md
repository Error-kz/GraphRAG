# 上下文增强系统技术文档

## 1. 概述

上下文增强系统是一个基于大语言模型的智能对话理解模块，用于分析用户问题是否依赖对话历史中的上下文信息，并自动提取主题实体来增强问题，提高问答系统的准确性和用户体验。

### 1.1 核心功能

- **指代检测**：智能判断用户问题是否包含指代性词语，需要依赖上下文才能理解
- **主题提取**：从对话历史中提取核心主题实体（疾病、症状、药物等）
- **问题增强**：将提取的主题补充到问题中，生成完整、清晰的问题
- **智能判断**：使用大模型进行语义理解，而非简单的规则匹配

### 1.2 应用场景

**场景1：指代性问题**
```
用户：感冒了有什么症状？
助手：感冒的常见症状包括发热、咳嗽、流鼻涕等。

用户：有什么特效药？  ← 包含指代"有什么"
系统增强：感冒有什么特效药？  ← 自动补充主题"感冒"
```

**场景2：省略主题的问题**
```
用户：高血压患者饮食要注意什么？
助手：高血压患者应该低盐饮食，限制钠的摄入。

用户：怎么治疗？  ← 省略了主题"高血压"
系统增强：高血压怎么治疗？  ← 自动补充主题
```

### 1.3 技术栈

- **后端**：Python + FastAPI
- **大模型**：DeepSeek API
- **存储**：Redis（对话历史）
- **前端**：HTML + JavaScript

## 2. 架构设计

### 2.1 系统架构图

```
┌─────────────────┐
│   用户问题      │
│  "有什么特效药？"│
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  上下文增强模块  │
│ (enhancer.py)   │
└────────┬────────┘
         │
         ├─────────────────┐
         │                 │
         ▼                 ▼
┌─────────────────┐  ┌─────────────────┐
│  获取对话历史    │  │  大模型分析      │
│  (Redis)        │  │  (DeepSeek)     │
└─────────────────┘  └─────────────────┘
         │                 │
         └────────┬────────┘
                  │
                  ▼
         ┌─────────────────┐
         │  增强后的问题    │
         │ "感冒有什么特效药？"│
         └─────────────────┘
```

### 2.2 数据流

1. **用户发送问题** → 前端携带 `session_id` 发送请求
2. **获取对话历史** → 从 Redis 获取该会话的历史记录
3. **大模型分析** → 调用 DeepSeek API 分析问题和历史
4. **问题增强** → 生成增强后的问题
5. **继续处理** → 使用增强后的问题进行检索和生成

## 3. 核心模块

### 3.1 模块结构

```
core/context/
├── __init__.py          # 模块导出
├── enhancer.py          # 核心增强逻辑
└── README.md            # 模块说明
```

### 3.2 核心函数

#### 3.2.1 `extract_entities_from_history()`

**功能**：从对话历史中提取主题实体

**位置**：`core/context/enhancer.py`

**参数**：
- `history`: 对话历史列表，每个元素包含 `question`, `answer`, `timestamp`
- `max_history`: 最多使用最近几条历史记录，默认5条

**返回**：
```python
{
    'diseases': ['感冒', '高血压'],  # 疾病列表
    'symptoms': ['头痛', '发热'],    # 症状列表
    'drugs': ['布洛芬'],              # 药物列表
    'topics': ['感冒']                # 主题关键词列表
}
```

**实现方式**：
- 使用 DeepSeek 大模型分析对话历史
- 通过精心设计的提示词引导模型提取医学实体
- 返回结构化的 JSON 结果

**提示词示例**：
```
你是一个医学信息提取专家。请从对话历史中提取主要的医学主题实体。

要求：
1. 提取对话中讨论的主要疾病名称（如：感冒、高血压、糖尿病等）
2. 提取主要症状（如果有）
3. 提取主要药物（如果有）
4. 提取对话的核心主题关键词（通常是疾病或症状名称）

请以JSON格式返回结果...
```

#### 3.2.2 `enhance_query_with_context()`

**功能**：根据对话历史增强用户问题

**位置**：`core/context/enhancer.py`

**参数**：
- `query`: 用户当前问题
- `history`: 对话历史列表
- `max_history`: 最多使用最近几条历史记录，默认5条

**返回**：
```python
(enhanced_query, was_enhanced)
# enhanced_query: 增强后的问题
# was_enhanced: 是否进行了增强（True/False）
```

**实现方式**：
- 使用 DeepSeek 大模型智能判断是否需要增强
- 如果需要增强，从对话历史中提取主题并生成增强后的问题
- 如果大模型调用失败，回退到简单的规则判断逻辑

**提示词示例**：
```
你是一个医学对话理解专家。请分析用户当前问题是否依赖对话历史中的上下文信息。

任务：
1. 判断当前问题是否包含指代性词语，需要依赖上下文才能理解
2. 如果问题完整且不依赖上下文，返回原问题
3. 如果需要增强，从对话历史中提取核心主题，将主题补充到问题中

要求：
- 如果问题已经包含主题实体，不需要增强
- 如果问题包含指代但历史中没有明确主题，返回原问题
- 增强后的问题应该自然、完整、易于理解
```

#### 3.2.3 `has_reference_pronouns()`（回退函数）

**功能**：检测问题是否包含指代性词语

**位置**：`core/context/enhancer.py`

**用途**：当大模型调用失败时，作为回退策略使用

**检测的指代性词语**：
- "有什么"、"哪些"、"什么"
- "怎么"、"如何"、"怎样"
- "这个"、"那个"、"它"、"该"、"此"
- "还"、"也"、"又"、"再"、"继续"、"更多"、"其他"

## 4. 集成方式

### 4.1 在流式处理服务中集成

**位置**：`services/streaming_handler.py`

**集成点**：在 `chatbot_stream()` 函数开始时

```python
async def chatbot_stream(
    query: str,
    session_id: str,
    ...
):
    # 发送会话ID事件
    yield await send_event('session_id', {
        'session_id': session_id
    })
    
    # 上下文增强：从历史对话中提取信息，增强当前问题
    enhanced_query = query
    was_enhanced = False
    try:
        from core.cache.redis_client import get_redis_client, get_session_conversations
        from core.context.enhancer import enhance_query_with_context
        
        # 获取对话历史
        redis_client = get_redis_client()
        history = get_session_conversations(redis_client, session_id)
        
        # 如果有历史记录，尝试增强问题
        if history:
            enhanced_query, was_enhanced = enhance_query_with_context(query, history, max_history=5)
            
            if was_enhanced:
                print(f"✅ 问题已增强: {query} -> {enhanced_query}")
                # 发送问题增强事件（可选，用于前端显示）
                yield await send_event('query_enhanced', {
                    'original_query': query,
                    'enhanced_query': enhanced_query,
                    'message': '问题已根据对话历史增强'
                })
    except Exception as e:
        print(f"⚠️ 上下文增强失败，使用原问题: {str(e)}")
        enhanced_query = query
    
    # 使用增强后的问题进行后续处理
    # 1. 向量数据库检索
    recall_rerank_milvus = milvus_vectorstore.similarity_search(
        enhanced_query,  # 使用增强后的问题
        ...
    )
    
    # 2. 知识图谱查询
    graph_data = {'natural_language_query': enhanced_query}  # 使用增强后的问题
    
    # 3. LLM 生成回答
    USER_PROMPT = f"""
    <question>
    {enhanced_query}  # 使用增强后的问题
    </question>
    """
```

### 4.2 工作流程

```
1. 用户发送问题
   ↓
2. 获取对话历史（从 Redis）
   ↓
3. 调用 enhance_query_with_context()
   ↓
4. 大模型分析：
   - 判断是否需要增强
   - 提取主题实体
   - 生成增强后的问题
   ↓
5. 使用增强后的问题：
   - 向量数据库检索
   - 知识图谱查询
   - LLM 生成回答
   ↓
6. 保存对话历史（使用原始问题）
```

## 5. 使用示例

### 5.1 基本使用

```python
from core.context.enhancer import enhance_query_with_context
from core.cache.redis_client import get_redis_client, get_session_conversations

# 获取对话历史
redis_client = get_redis_client()
history = get_session_conversations(redis_client, session_id)

# 增强问题
enhanced_query, was_enhanced = enhance_query_with_context(
    query="有什么特效药？",
    history=history,
    max_history=5
)

if was_enhanced:
    print(f"问题已增强: {enhanced_query}")
    # 输出: 问题已增强: 感冒有什么特效药？
```

### 5.2 完整对话场景

```python
# 对话历史
history = [
    {
        'question': '感冒了有什么症状？',
        'answer': '感冒的常见症状包括发热、咳嗽、流鼻涕、头痛等。',
        'timestamp': '2024-01-01 10:00:00'
    },
    {
        'question': '感冒怎么治疗？',
        'answer': '感冒的治疗方法包括多休息、多喝水、服用感冒药等。',
        'timestamp': '2024-01-01 10:05:00'
    }
]

# 用户继续提问（包含指代）
query = "有什么特效药？"

# 增强问题
enhanced_query, was_enhanced = enhance_query_with_context(query, history)

# 结果
# enhanced_query = "感冒有什么特效药？"
# was_enhanced = True
```

## 6. 配置说明

### 6.1 参数配置

- **`max_history`**: 最多使用最近几条历史记录，默认5条
  - 影响：使用更多历史记录可能提取更准确的主题，但会增加处理时间
  - 建议：3-5条历史记录通常足够

- **`temperature`**: 大模型温度参数，默认0.1
  - 影响：较低温度提高准确性，较高温度增加创造性
  - 建议：0.1-0.3 适合信息提取任务

- **`max_tokens`**: 最大token数，默认500
  - 影响：限制模型输出的长度
  - 建议：500足够返回JSON结果

### 6.2 错误处理

系统实现了多层错误处理机制：

1. **大模型调用失败**：自动回退到规则判断逻辑
2. **JSON解析失败**：尝试多种方式提取JSON，如果都失败则返回原问题
3. **历史记录为空**：直接返回原问题，不进行增强

## 7. 性能优化

### 7.1 缓存策略

- 对话历史存储在 Redis 中，读取速度快
- 只使用最近5条历史记录，减少处理数据量
- 答案内容只取前100字，避免过长

### 7.2 异步处理

- 在流式处理中，上下文增强在发送第一个事件后立即执行
- 如果增强失败，不影响后续处理流程

### 7.3 超时控制

- 大模型调用设置合理的超时时间
- 如果超时，自动回退到规则判断

## 8. 测试

### 8.1 测试用例

参考 `tests/unit/test_enhancer_simple.py`：

```python
def test_enhancer_with_llm():
    """测试使用大模型增强问题"""
    history = [
        {
            'question': '感冒了有什么症状？',
            'answer': '感冒的常见症状包括发热、咳嗽等。',
            'timestamp': '2024-01-01 10:00:00'
        }
    ]
    
    # 测试指代性问题
    query = "有什么特效药？"
    enhanced_query, was_enhanced = enhance_query_with_context(query, history)
    
    assert was_enhanced == True
    assert "感冒" in enhanced_query
```

### 8.2 运行测试

```bash
cd /Users/qukaizhi/Desktop/MedGraphRAG
python tests/unit/test_enhancer_simple.py
```

## 9. 注意事项

### 9.1 使用限制

- 需要有效的 DeepSeek API Key
- 需要 Redis 连接正常
- 大模型调用需要网络连接

### 9.2 最佳实践

1. **历史记录管理**：定期清理过期的对话历史
2. **错误监控**：监控大模型调用失败率，及时发现问题
3. **性能监控**：监控上下文增强的耗时，优化性能瓶颈

### 9.3 常见问题

**Q: 为什么有时候问题没有被增强？**

A: 可能的原因：
- 问题已经包含主题实体，不需要增强
- 对话历史中没有明确的主题
- 大模型判断不需要增强

**Q: 增强后的问题不准确怎么办？**

A: 可以：
- 调整提示词，提高提取准确性
- 增加历史记录数量
- 检查对话历史的质量

**Q: 大模型调用失败怎么办？**

A: 系统会自动回退到规则判断逻辑，确保功能可用。

## 10. 未来改进

### 10.1 计划功能

- [ ] 支持多轮对话的上下文理解
- [ ] 支持更复杂的指代消解
- [ ] 支持主题实体的一致性检查
- [ ] 添加增强效果的评估指标

### 10.2 性能优化

- [ ] 实现结果缓存，减少重复调用
- [ ] 优化提示词，减少token消耗
- [ ] 批量处理多个问题，提高效率

## 11. 相关文档

- [对话历史系统文档](./conversation_history_system.md)
- [上下文增强模块 README](../../core/context/README.md)
- [流式处理服务文档](../technical_workflow.md)

## 12. 更新日志

### v1.0.0 (2024-01-01)
- 初始版本
- 实现基于大模型的上下文增强功能
- 支持指代检测和主题提取
- 集成到流式处理服务

---

**文档版本**: 1.0.0  
**最后更新**: 2024-01-01  
**维护者**: MedGraphRAG Team

