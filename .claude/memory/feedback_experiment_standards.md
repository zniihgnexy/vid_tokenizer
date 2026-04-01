---
name: 实验规范和最佳实践
type: feedback
---

## 核心要求

所有实验必须满足可重复性标准。

**Why:** 研究的公信力和论文可发表性取决于结果的可重复性。

**How to apply:** 每个实验运行时必须：

### 随机种子固定
```python
torch.manual_seed(42)
np.random.seed(42)
torch.cuda.manual_seed_all(42)
torch.backends.cudnn.deterministic = True
```

### 配置完整记录
- 在 `configs/exp_XXX.yaml` 中明确所有参数
- 包括数据路径、模型大小、学习率等
- 配置文件是论文附录的一部分

### 实验结果标准化
- 运行 3 次，报告 mean ± std
- 允许的波动范围通常是 ±2%（取决于任务难度）

### 数据分割验证
- 在训练前验证 train/val/test 没有重叠
- 代码示例：
```python
assert len(train_ids & val_ids) == 0, "Data leak!"
```

### Tokenizer 约束
- tokenizer 必须冻结（no gradients）
- `T(x)` 和 `T(x_hat)` 的维度必须相同
- 不允许微调 tokenizer

### 指标报告
- **必须报告** L_tok（核心目标）
- **必须报告** 压缩率和重建质量
- **应该报告** 下游任务性能（如测试过）
- 不要单独报告 PSNR，这不是我们的主要目标

## 常见错误和修正

| 错误 | 现象 | 修正 |
|------|------|------|
| 随机种子不一致 | 同配置多次运行结果不同 | 固定所有随机源 |
| 数据泄漏 | 验证性能异常好 | 检查数据分割 |
| Tokenizer 微调 | L_tok 快速下降但不可靠 | 确保冻结 tokenizer |
| 配置不完整 | 无法复现 | 所有参数都写入 YAML |

## 实验周期清单

### 前
- [ ] 假设清晰
- [ ] 配置完整
- [ ] 随机种子设置
- [ ] 数据分割验证

### 中
- [ ] 监控 L_tok 和其他损失
- [ ] 定期保存检查点
- [ ] 记录完整日志

### 后
- [ ] 结果记录到 experiments.md
- [ ] 对比 baseline（报告差异原因）
- [ ] 运行 2 次以验证可重复性
