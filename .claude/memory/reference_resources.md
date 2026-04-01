---
name: 资源位置和外部系统
type: reference
---

## 数据集和预训练模型

### Egocentric 视频数据集

| 名称 | 位置 | 状态 | 备注 |
|------|------|------|------|
| [待配置] | `/data/egocentric_*` | ⚠️ 待确认 | 具体数据集需要根据项目确定 |

### 预训练 Tokenizer 模型

| 名称 | 位置 | 用途 |
|------|------|------|
| CLIP | `~/.cache/huggingface/hub/` | 视觉特征提取 |
| ViT | `~/.cache/huggingface/hub/` | 补丁级别特征 |
| [自监督] | 待确认 | 可选的特征提取器 |

## 计算资源

### GPU 资源

- **设备** — 需根据实际环境配置
- **CUDA** — 版本需与 PyTorch 匹配
- **内存** — 监控 GPU 内存使用，防止 OOM

### 存储

- **训练输出** — `./results/` （配置、检查点、日志）
- **数据缓存** — `./data_cache/` （预处理后的数据）
- **模型检查点** — `./checkpoints/` （保留所有关键实验的）

## 项目输出位置

| 内容 | 位置 | 备注 |
|------|------|------|
| 实验配置 | `configs/` | YAML 格式 |
| 训练脚本 | `src/train.py` | 主训练入口 |
| 评估脚本 | `src/evaluate.py` | 评估和对比 |
| 实验记录 | `experiments.md` | 在这里记录所有结果 |
| 论文输出 | `papers/` | 草稿和最终版本 |

## 代码提交规范

**Repository:** [待配置] — 可以考虑 GitHub、GitLab 等

**分支策略：**
- `main` — 稳定的 baseline 版本
- `exp/XXX` — 实验分支
- `paper` — 论文最终版本代码

**提交信息：**
```
feat/exp-XXX: [实验名称]

[详细描述实验目标和配置]

Co-Authored-By: Claude Haiku 4.5 <noreply@anthropic.com>
```

## 相关论文和资源

### 核心论文

| 名称 | 作者 | 关键贡献 | 备注 |
|------|------|---------|------|
| [待补充] | - | INR-based 视频压缩基础 | 需要识别关键 baseline 论文 |

### 技术文档

- **CLAUDE_readme.md** — 项目定义（必读！）
- **CLAUDE.md** — 项目规范和约束
- **.claude/SYSTEM.md** — 工作流哲学

## 外部集成

### 实验追踪（可选）

如果使用：
- Wandb 项目：[待配置]
- TensorBoard 日志：`./logs/`

### 论文写作工具

- LaTeX 编译：[待确认]
- 图表生成：Python (matplotlib, seaborn)
- 参考文献：BibTeX

## 更新日期

- **最后更新：** 2026-04-01
- **状态：** 大部分待实际项目环境补充

## 下一步

项目初始化时需要：
- [ ] 确认数据集路径
- [ ] 测试 GPU/CUDA 环境
- [ ] 设置代码仓库
- [ ] 配置结果输出目录
- [ ] （可选）配置 Wandb 项目
