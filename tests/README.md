# 测试文档

本目录包含 MedGraphRAG 项目的测试用例。

## 📁 目录结构

```
tests/
├── unit/              # 单元测试
│   └── test_redis_write.py    # Redis 写入功能测试
├── integration/       # 集成测试
│   └── test_conversation_history.py  # 对话历史功能测试
├── performance/       # 性能测试
│   └── README.md      # 性能测试文档
└── README.md          # 本文件
```

## 🧪 测试分类

### 单元测试 (unit/)

单元测试针对单个函数或模块进行测试，不依赖外部服务。

- **test_redis_write.py**：测试 Redis 数据库的写入功能

### 集成测试 (integration/)

集成测试测试多个模块或服务之间的协作。

- **test_conversation_history.py**：测试对话历史的存储和读取功能

### 性能测试 (performance/)

性能测试用于评估系统的性能指标和进行基准对比。

- **benchmark_retrieval.py**：检索策略性能对比测试
- **benchmark_context.py**：上下文增强效果测试
- **benchmark_cache.py**：缓存性能测试
- **benchmark_concurrent.py**：并发性能测试
- **benchmark_end_to_end.py**：端到端性能测试

详细说明请参考 [性能测试文档](./performance/README.md)

## 🚀 运行测试

### 运行所有测试

```bash
# 从项目根目录运行
python -m pytest tests/
```

### 运行单元测试

```bash
python -m pytest tests/unit/
```

### 运行集成测试

```bash
python -m pytest tests/integration/
```

### 运行性能测试

```bash
python -m pytest tests/performance/
```

### 运行特定测试文件

```bash
python -m pytest tests/unit/test_redis_write.py
python -m pytest tests/integration/test_conversation_history.py
```

## 📝 测试说明

### 前置条件

部分测试需要外部服务支持：

- **Redis 测试**：需要 Redis 服务运行
- **对话历史测试**：需要 Redis 服务运行

### 测试环境

建议在测试环境中运行测试，避免影响生产数据。

## 🔗 相关链接

- [主文档](../docs/README.md)
- [对话记录系统文档](../docs/architecture/conversation_history_system.md)

