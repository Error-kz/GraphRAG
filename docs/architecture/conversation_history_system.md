# 对话记录系统技术文档

## 1. 概述

对话记录系统是一个基于 Redis 的会话管理功能，用于在医疗问答助手中实现多轮对话的上下文记忆和历史记录管理。系统支持自动会话管理、历史记录存储、会话列表展示等功能。

### 1.1 核心功能

- **会话标识管理**：为每个聊天窗口生成唯一的会话ID（session_id）
- **对话历史存储**：将每次问答对保存到 Redis 数据库
- **自动会话切换**：当对话达到10条时，自动创建新会话并保存旧会话到历史记录
- **手动创建会话**：支持用户手动创建新会话
- **历史记录展示**：在右侧边栏显示所有历史会话列表
- **会话详情查看**：点击历史记录可查看完整的对话内容

### 1.2 技术栈

- **后端**：Python + FastAPI
- **数据库**：Redis
- **前端**：HTML + JavaScript (原生)
- **存储结构**：Redis List + Sorted Set

## 2. 架构设计

### 2.1 系统架构图

```
┌─────────────────┐
│   前端界面      │
│  (index.html)   │
└────────┬────────┘
         │ HTTP/SSE
         ▼
┌─────────────────┐
│  FastAPI 服务   │
│ (agent_service) │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Redis 客户端   │
│ (redis_client)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│   Redis 数据库  │
└─────────────────┘
```

### 2.2 数据流

1. **用户发送消息** → 前端携带 `session_id` 发送请求
2. **后端处理** → 生成回答并保存对话历史到 Redis
3. **检查限制** → 如果达到10条，自动创建新会话
4. **返回结果** → 返回回答和新的 `session_id`（如果创建了新会话）
5. **前端更新** → 刷新历史记录列表

## 3. 数据结构设计

### 3.1 Redis 存储结构

#### 3.1.1 对话历史记录（List）

**Key 格式**：`chat:history:{session_id}`

**数据结构**：Redis List，每个元素是 JSON 格式的对话记录

**示例**：
```json
{
  "question": "感冒了有什么症状？",
  "answer": "感冒的常见症状包括流鼻涕、打喷嚏、咳嗽、头痛等。",
  "timestamp": "2024-01-01 12:00:00"
}
```

**特点**：
- 使用 `RPUSH` 追加新记录
- 最多保留10条记录（达到10条后自动创建新会话）
- 过期时间：24小时（86400秒）

#### 3.1.2 会话列表（Sorted Set）

**Key**：`chat:sessions:list`

**数据结构**：Redis Sorted Set，按时间戳排序

**Value 格式**（JSON）：
```json
{
  "session_id": "uuid-string",
  "title": "第一个问题（最多50字符）",
  "update_time": "2024-01-01 12:00:00",
  "message_count": 10
}
```

**特点**：
- 使用时间戳作为 score，实现按时间倒序排列
- 最多保留50个会话
- 过期时间：30天（2592000秒）

### 3.2 前端数据结构

#### 3.2.1 会话列表

```javascript
let allSessions = [
  {
    session_id: "uuid-string",
    title: "感冒了有什么症状？",
    update_time: "2024-01-01 12:00:00",
    message_count: 10
  },
  // ...
];
```

#### 3.2.2 当前会话状态

```javascript
let activeSessionId = null;      // 当前使用的会话ID
let currentSessionId = null;     // 当前选中的历史会话ID（用于高亮显示）
```

## 4. API 接口文档

### 4.1 创建新会话

**接口**：`POST /api/new_session`

**请求参数**：
```json
{
  "old_session_id": "旧的会话ID（可选）"
}
```

**响应**：
```json
{
  "status": 200,
  "session_id": "新的会话ID",
  "message": "新会话创建成功"
}
```

**功能**：
- 如果提供了 `old_session_id`，将其保存到历史记录
- 生成新的 `session_id` 并返回

### 4.2 获取历史会话列表

**接口**：`GET /api/sessions`

**响应**：
```json
{
  "status": 200,
  "sessions": [
    {
      "session_id": "uuid-string",
      "title": "第一个问题",
      "update_time": "2024-01-01 12:00:00",
      "message_count": 10
    }
  ],
  "count": 1
}
```

**功能**：
- 返回所有历史会话列表
- 按时间倒序排列（最新的在前）
- 最多返回50个会话

### 4.3 获取会话详情

**接口**：`GET /api/sessions/{session_id}`

**响应**：
```json
{
  "status": 200,
  "session_id": "uuid-string",
  "conversations": [
    {
      "question": "问题1",
      "answer": "答案1",
      "timestamp": "2024-01-01 12:00:00"
    }
  ],
  "count": 10
}
```

**功能**：
- 返回指定会话的所有对话记录
- 按时间顺序排列

### 4.4 问答接口（已扩展）

**接口**：`POST /`

**请求参数**：
```json
{
  "question": "用户问题",
  "session_id": "会话ID（可选，首次请求可不传）",
  "stream": true
}
```

**响应**（流式）：
- `session_id` 事件：返回当前会话ID
- `new_session_created` 事件：如果达到10条，返回新会话ID
- `answer_complete` 事件：包含 `new_session_id` 字段（如果创建了新会话）

**响应**（非流式）：
```json
{
  "response": "回答内容",
  "status": 200,
  "time": "2024-01-01 12:00:00",
  "session_id": "当前会话ID",
  "new_session_id": "新会话ID（如果创建了新会话）",
  "new_session_created": true,
  "search_path": [...],
  "search_stages": {...}
}
```

## 5. 核心函数说明

### 5.1 后端函数

#### 5.1.1 `generate_session_id()`

**位置**：`services/agent_service.py`

**功能**：生成唯一的会话ID（UUID格式）

**返回**：`str` - 会话ID字符串

#### 5.1.2 `get_or_create_session_id(json_post_list)`

**位置**：`services/agent_service.py`

**功能**：从请求中获取session_id，如果不存在则生成新的

**参数**：
- `json_post_list`: 请求的JSON数据字典

**返回**：`str` - 会话ID

#### 5.1.3 `save_conversation_history(r, session_id, question, answer, expire)`

**位置**：`core/cache/redis_client.py`

**功能**：保存对话历史到Redis

**参数**：
- `r`: Redis客户端实例
- `session_id`: 会话ID
- `question`: 用户问题
- `answer`: 助手回答
- `expire`: 过期时间（秒），默认86400

**返回**：`tuple` - `(new_session_id, should_create_new)`
- `new_session_id`: 如果达到10条，返回新的session_id，否则返回None
- `should_create_new`: 是否需要创建新会话（达到10条时为True）

**逻辑**：
1. 构建对话记录（包含question、answer、timestamp）
2. 使用 `RPUSH` 追加到列表
3. 检查是否达到10条
4. 如果达到10条，生成新session_id并保存当前会话到历史记录
5. 设置过期时间

#### 5.1.4 `save_session_to_history(r, session_id, first_question)`

**位置**：`core/cache/redis_client.py`

**功能**：将会话保存到历史记录列表中

**参数**：
- `r`: Redis客户端实例
- `session_id`: 会话ID
- `first_question`: 会话的第一个问题（用作标题）

**逻辑**：
1. 从Redis获取会话的所有对话记录
2. 提取第一个问题作为标题（最多50字符）
3. 获取最后一条记录的时间作为更新时间
4. 构建会话信息并保存到Sorted Set
5. 限制最多保留50个会话

#### 5.1.5 `get_conversation_history_list(r, limit)`

**位置**：`core/cache/redis_client.py`

**功能**：获取历史会话列表

**参数**：
- `r`: Redis客户端实例
- `limit`: 返回的最大数量，默认50

**返回**：`list` - 会话信息列表，按时间倒序排列

#### 5.1.6 `get_session_conversations(r, session_id)`

**位置**：`core/cache/redis_client.py`

**功能**：获取指定会话的所有对话记录

**参数**：
- `r`: Redis客户端实例
- `session_id`: 会话ID

**返回**：`list` - 对话记录列表，每个元素包含 question, answer, timestamp

### 5.2 前端函数

#### 5.2.1 `loadHistory()`

**功能**：从Redis加载对话历史列表

**流程**：
1. 调用 `GET /api/sessions` API
2. 更新 `allSessions` 数组
3. 调用 `renderHistory()` 渲染

#### 5.2.2 `renderHistory()`

**功能**：渲染对话历史列表到右侧边栏

**流程**：
1. 根据过滤条件选择要渲染的会话列表
2. 如果为空，显示空状态
3. 遍历会话列表，创建DOM元素
4. 格式化时间显示
5. 绑定点击事件

#### 5.2.3 `loadHistoryItem(sessionId)`

**功能**：加载指定会话的详细对话记录

**流程**：
1. 调用 `GET /api/sessions/{sessionId}` API
2. 清空当前聊天界面
3. 遍历对话记录，重新渲染到聊天界面
4. 更新 `currentSessionId` 用于高亮显示

#### 5.2.4 `createNewSession()`

**功能**：创建新会话

**流程**：
1. 调用 `POST /api/new_session` API，传递当前 `activeSessionId`
2. 获取新的 `session_id`
3. 更新 `activeSessionId` 并保存到 localStorage
4. 清空当前聊天界面
5. 刷新历史记录列表

#### 5.2.5 `refreshHistory()`

**功能**：刷新对话历史列表（对话后调用）

**流程**：
1. 调用 `loadHistory()` 重新加载历史记录

## 6. 工作流程

### 6.1 首次对话流程

```
1. 用户打开页面
   ↓
2. 前端检查 localStorage 是否有 session_id
   ↓
3. 如果没有，发送请求时不带 session_id
   ↓
4. 后端生成新的 session_id
   ↓
5. 返回 session_id 给前端
   ↓
6. 前端保存 session_id 到 localStorage
   ↓
7. 保存对话历史到 Redis
   ↓
8. 刷新历史记录列表
```

### 6.2 继续对话流程

```
1. 用户发送消息
   ↓
2. 前端从 localStorage 获取 session_id
   ↓
3. 发送请求时携带 session_id
   ↓
4. 后端保存对话历史
   ↓
5. 检查是否达到10条
   ↓
6. 如果达到10条：
   - 保存当前会话到历史记录
   - 生成新的 session_id
   - 返回新 session_id
   ↓
7. 前端更新 activeSessionId
   ↓
8. 刷新历史记录列表
```

### 6.3 手动创建新会话流程

```
1. 用户点击"创建新会话"按钮
   ↓
2. 前端调用 createNewSession()
   ↓
3. 发送 POST /api/new_session 请求
   - 携带当前 activeSessionId
   ↓
4. 后端保存旧会话到历史记录
   ↓
5. 生成新的 session_id
   ↓
6. 返回新 session_id
   ↓
7. 前端更新 activeSessionId
   ↓
8. 清空聊天界面
   ↓
9. 刷新历史记录列表
```

### 6.4 查看历史记录流程

```
1. 用户点击历史记录项
   ↓
2. 前端调用 loadHistoryItem(sessionId)
   ↓
3. 发送 GET /api/sessions/{sessionId} 请求
   ↓
4. 后端从 Redis 获取会话的所有对话记录
   ↓
5. 返回对话记录列表
   ↓
6. 前端清空当前聊天界面
   ↓
7. 遍历对话记录，重新渲染到聊天界面
   ↓
8. 更新 currentSessionId 用于高亮显示
```

## 7. 配置说明

### 7.1 Redis 配置

**位置**：`config/settings.py`

**配置项**：
```python
REDIS_HOST: str = "0.0.0.0"          # Redis 主机地址
REDIS_PORT: int = 6379                # Redis 端口
REDIS_DB: int = 0                     # Redis 数据库编号
REDIS_PASSWORD: Optional[str] = None  # Redis 密码
REDIS_MAX_CONNECTIONS: int = 10       # 最大连接数
```

### 7.2 系统参数

**对话历史限制**：
- 每个会话最多保留：10条对话记录
- 历史会话列表最多保留：50个会话

**过期时间**：
- 对话历史记录：24小时（86400秒）
- 会话列表：30天（2592000秒）

## 8. 错误处理

### 8.1 后端错误处理

- **Redis 连接失败**：打印错误日志，不影响主流程
- **保存对话历史失败**：打印错误日志，不中断请求处理
- **获取会话列表失败**：返回空列表，状态码500

### 8.2 前端错误处理

- **API 请求失败**：显示错误信息，不影响其他功能
- **数据解析失败**：使用默认值，确保界面正常显示
- **时间格式化失败**：使用原始时间字符串

## 9. 性能优化

### 9.1 数据限制

- 每个会话最多10条记录，避免数据过大
- 历史会话列表最多50个，自动删除旧记录
- 使用过期时间自动清理数据

### 9.2 前端优化

- 使用异步加载，不阻塞界面
- 按需加载会话详情，不一次性加载所有数据
- 使用 localStorage 缓存当前会话ID

## 10. 使用示例

### 10.1 前端调用示例

```javascript
// 创建新会话
async function createNewSession() {
    const response = await fetch('/api/new_session', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ old_session_id: activeSessionId })
    });
    const data = await response.json();
    activeSessionId = data.session_id;
}

// 获取历史会话列表
async function loadHistory() {
    const response = await fetch('/api/sessions');
    const data = await response.json();
    allSessions = data.sessions || [];
}

// 获取会话详情
async function loadHistoryItem(sessionId) {
    const response = await fetch(`/api/sessions/${sessionId}`);
    const data = await response.json();
    // 渲染对话记录
}
```

### 10.2 后端调用示例

```python
from core.cache.redis_client import (
    get_redis_client,
    save_conversation_history,
    get_conversation_history_list
)

# 保存对话历史
redis_client = get_redis_client()
new_session_id, should_create_new = save_conversation_history(
    redis_client, 
    session_id, 
    question, 
    answer
)

# 获取历史会话列表
sessions = get_conversation_history_list(redis_client)
```

## 11. 测试说明

### 11.1 功能测试

1. **会话创建测试**：验证能否正确生成和保存 session_id
2. **对话保存测试**：验证对话记录是否正确保存到 Redis
3. **自动切换测试**：验证达到10条时是否自动创建新会话
4. **历史记录测试**：验证历史会话列表是否正确显示
5. **会话详情测试**：验证能否正确加载和显示会话详情

### 11.2 测试文件

- `tests/test_session_id.py`：测试会话ID生成
- `tests/integration/test_conversation_history.py`：测试对话历史存储

## 12. 未来改进方向

1. **会话搜索功能**：支持按关键词搜索历史会话
2. **会话重命名**：允许用户自定义会话标题
3. **会话删除功能**：支持删除不需要的历史会话
4. **会话导出功能**：支持导出会话为多种格式（JSON、TXT、PDF等）
5. **会话分享功能**：支持分享会话链接
6. **数据持久化**：考虑将重要会话持久化到数据库
7. **多用户支持**：为不同用户隔离会话数据

## 13. 版本历史

- **v1.0** (2024-01-01)
  - 初始版本
  - 实现基本的会话管理和历史记录功能
  - 支持自动和手动创建新会话
  - 支持历史记录查看

## 14. 相关文件

### 14.1 后端文件

- `core/cache/redis_client.py`：Redis 客户端和对话历史相关函数
- `services/agent_service.py`：主服务，包含会话管理和API接口
- `services/streaming_handler.py`：流式处理，包含会话管理逻辑

### 14.2 前端文件

- `web/index.html`：前端界面，包含所有JavaScript代码

### 14.3 配置文件

- `config/settings.py`：Redis 配置

### 14.4 测试文件

- `tests/test_session_id.py`：会话ID测试
- `tests/integration/test_conversation_history.py`：对话历史测试

## 15. 联系与支持

如有问题或建议，请联系开发团队。

---

**文档版本**：v1.0  
**最后更新**：2024-01-01  
**维护者**：MedGraphRAG 开发团队

