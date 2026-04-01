---
name: 数据处理和预处理陷阱
type: feedback
---

## 数据分割陷阱

**Problem:** 训练数据无意中混入了验证或测试集。

**Why:** 数据分割脚本中的 off-by-one 错误、模糊的分割逻辑、或手动拆分时的遗漏。
这会导致性能指标虚高，不可信。

**How to apply:**

1. **编写分割验证代码**
```python
# 检查没有重叠
train_ids = set(train_dataset['video_id'])
val_ids = set(val_dataset['video_id'])
test_ids = set(test_dataset['video_id'])

assert len(train_ids & val_ids) == 0, "Train-Val leak!"
assert len(train_ids & test_ids) == 0, "Train-Test leak!"
assert len(val_ids & test_ids) == 0, "Val-Test leak!"

# 检查覆盖完整
assert train_ids | val_ids | test_ids == all_video_ids, "Incomplete coverage!"
```

2. **手动抽查**
   - 随机选 10 个视频，检查它们确实只在一个集合中
   - 在 CLAUDE.md 中记录数据分割 ID，方便溯源

3. **记录数据分割方案**
   - 在 experiments.md 中记录：哪 80 个视频用于训练、哪 10 个用于验证等
   - 这样后续实验可以使用相同的分割，确保可比

## 数据预处理陷阱

### 归一化不一致
**Problem:** 训练和验证使用不同的归一化（或者用了全局统计量导致泄漏）。

**How to apply:**
```python
# ❌ 错误：使用全局统计量（包含 test 数据）
mean, std = data.mean(), data.std()

# ✅ 正确：只用训练集统计量
mean, std = train_data.mean(), train_data.std()
# 然后在 val/test 上应用相同的 mean, std
```

### 不同的预处理管道
**Problem:** 训练时进行数据增强，但在验证/测试时用不同的预处理。

**How to apply:**
- 清晰地定义：哪些预处理用于 train，哪些用于 val/test
- 通常：train 有增强，val/test 没有
- 但所有数据都应该有相同的基础预处理（缩放、归一化等）

## Tokenizer 特征对齐陷阱

### 维度不匹配
**Problem:** `y = T(x)` 和 `y_hat = T(x_hat)` 的维度不同。

**Why:** 可能是图像大小不一致（`x` 和 `x_hat` 分辨率不同）导致的。

**How to apply:**
```python
# 验证维度匹配
y = tokenizer(x)  # shape: (B, D)
y_hat = tokenizer(x_hat)  # shape: (B, D)

assert y.shape == y_hat.shape, f"Shape mismatch: {y.shape} vs {y_hat.shape}"
```

### 特征值范围差异
**Problem:** 由于压缩，重建的 `x_hat` 可能有值域变化，导致 `y_hat` 的特征范围不同。

**How to apply:**
- 如果 `x_hat` 的值域与 `x` 不同（例如 0-255 vs 0-1），手动调整
- 或在计算 L_tok 前对 y 和 y_hat 进行 L2 归一化

## 实验数据完整性检查

**在运行任何实验前的检查清单：**

- [ ] 数据分割有无重叠？已用代码验证
- [ ] train/val/test 大小合理吗？（通常 80/10/10 或类似）
- [ ] 数据质量正常吗？（无 NaN、无异常值）
- [ ] 预处理管道一致吗？（特别是归一化）
- [ ] Tokenizer 输出维度和 x_hat 输入维度对齐吗？
- [ ] 所有随机种子已固定吗？

## 记录位置

所有数据相关的决策应该记录在：
1. **CLAUDE.md** — 数据集描述、分割方案、预处理方式
2. **experiments.md** — 每个实验使用的具体数据分割 ID
3. **src/data.py** — 数据加载代码中有清晰的注释

## 故障排除

| 症状 | 可能原因 | 修复 |
|------|---------|------|
| 验证性能异常高 | 数据泄漏 | 检查分割，运行验证代码 |
| 训练不收敛 | 归一化错误 | 检查 mean/std 计算 |
| L_tok 不下降 | y_hat 维度错误 | 检查 x_hat 分辨率和 tokenizer 输入 |
| 模式重复 | 数据不足或重复 | 检查数据集大小和去重 |
