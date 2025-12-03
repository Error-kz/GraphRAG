# 数据目录说明

## 目录结构

```
data/
├── raw/          # 原始数据文件（不提交到 Git）
├── processed/    # 处理后的数据文件（不提交到 Git）
└── dict/         # 字典文件（不提交到 Git）
```

## 数据文件说明

### raw/ 目录
存放原始数据文件，包括：
- `medical.json` - 医疗知识图谱原始数据
- `data.jsonl` - 训练数据
- `dev.jsonl` - 开发集数据
- `dialog.jsonl` - 对话数据
- `train.jsonl` - 训练集数据

**注意**：这些文件较大（约 615MB），已被 `.gitignore` 忽略，不会提交到 Git。

### processed/ 目录
存放处理后的数据文件，由数据处理脚本生成。

### dict/ 目录
存放字典文件，包括：
- `disease.txt` - 疾病字典
- `symptom.txt` - 症状字典
- `drug.txt` - 药品字典
- `food.txt` - 食物字典
- `check.txt` - 检查项字典
- `department.txt` - 科室字典
- `producer.txt` - 生产商字典
- `deny.txt` - 否定词字典

## 如何获取数据

1. **原始数据**：需要从数据源获取，或联系项目维护者
2. **处理后的数据**：运行数据处理脚本生成
3. **字典文件**：可以从原始数据中提取，或使用项目提供的脚本生成

## 数据生成

如果需要重新生成数据，可以运行：

```bash
# 生成知识图谱数据
python utils/create_graph.py

# 生成向量数据库
python utils/create_vector.py
```

