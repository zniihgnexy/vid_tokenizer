---
name: 研究进度和里程碑
type: project
---

## 当前状态

**项目启动日期：** 2026-04-01
**当前阶段：** 初始化 - 建立工作流和实验框架

## 关键里程碑

### Phase 1: 基础设施搭建 (当前)
- [ ] 项目结构和配置确定
- [ ] 数据集准备和验证
- [ ] 开发环境配置（PyTorch、CLIP 等）
- [ ] 基础 Baseline 实现（简单 INR + CLIP tokenizer）

### Phase 2: Baseline 复现 (计划中)
- [ ] 选择关键论文和实现方案
- [ ] 复现 baseline 模型
- [ ] 验证结果（允许 ±2% 差异）
- [ ] 建立可信的性能标准

### Phase 3: 方法改进 (计划中)
- [ ] 探索不同 tokenizer 的效果
- [ ] 尝试新的损失函数设计
- [ ] 实验压缩率与机器理解性能的权衡
- [ ] 可能的：多 tokenizer 联合训练

### Phase 4: 论文准备 (后期)
- [ ] 完整的实验对比表
- [ ] 消融研究
- [ ] 下游任务验证
- [ ] 论文初稿和修改

## 已完成的工作

### 2026-04-01: 工作流框架
- ✓ 创建 CLAUDE.md 项目规范
- ✓ 建立 .claude/ 系统和记忆结构
- ✓ 编写 SYSTEM.md, WORKFLOW.md, 多 Agent 指南
- ✓ 初始化记忆系统（5 个核心记忆文件）

## 待实现的关键功能

| 功能 | 优先级 | 预计工作量 | 依赖 |
|------|--------|----------|------|
| 基础 INR 模型 | 高 | 2-3 天 | 环境准备 |
| CLIP tokenizer 集成 | 高 | 1 天 | INR 模型 |
| 数据加载和预处理 | 高 | 1-2 天 | 数据集确认 |
| 训练脚本 | 高 | 1 天 | INR + tokenizer |
| 评估和对比脚本 | 高 | 1 天 | 训练脚本 |
| 第一个 Baseline 实验 | 中 | 3-5 天 | 上述完成 |
| Tensorboard / Wandb 集成 | 低 | 0.5 天 | 可选 |

## 当前的未解决问题

| 问题 | 状态 | 下一步 |
|------|------|--------|
| [等待确认] 数据集位置 | ⚠️ 未确认 | 需要用户提供 |
| [等待确认] GPU 环境 | ⚠️ 未确认 | 验证 CUDA 版本 |
| Baseline 论文选择 | 📋 规划中 | 文献综述，选择关键实现 |
| 其他 Tokenizer 选项 | 📋 规划中 | 列出候选，设计对比 |

## 经验和学习

### 已学到的
- 项目的机器理解焦点很关键，决定了所有技术选择
- INR 的每视频拟合特性需要在评估时明确说明
- Tokenizer 选择对结果影响很大（需要对比实验）

### 待验证的假设
- CLIP 是最优的 tokenizer 吗？（需要对比 ViT, 自监督等）
- 简单的 MSE tokenizer 一致性损失足够吗？（可能需要感知损失）
- 多 tokenizer 训练能改进泛化吗？（推测，需要实验）

## 下次工作的建议

1. **优先完成**：数据集准备 → 环境配置 → 基础 INR 实现
2. **关键决策**：选择 Baseline 论文和 tokenizer
3. **快速验证**：用小数据集快速测试管道

## 相关的记忆文件

- [project_core_constraints.md](project_core_constraints.md) — 不应改变的约束
- [feedback_experiment_standards.md](feedback_experiment_standards.md) — 实验规范
- [reference_resources.md](reference_resources.md) — 资源位置

**最后更新：** 2026-04-01
