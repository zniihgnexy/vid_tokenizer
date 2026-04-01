# 快速开始 - vid_tokenizer Agent 系统

5分钟快速了解如何使用这个项目的 Claude Code 工作流系统。

## 系统包含了什么？

```
.claude/
├── SYSTEM.md                    # 工作流哲学
├── WORKFLOW.md                  # 日常工作流规范
├── MEMORY_POLICY.md             # 记忆系统说明
├── MISTAKE_POLICY.md            # 错误处理和恢复
├── MULTI_AGENT_GUIDE.md         # 多 Agent 协作指南
├── QUICKSTART.md                # 本文件
└── memory/                      # 项目记忆库
    ├── MEMORY.md                # 记忆索引
    ├── user_research_background.md
    ├── feedback_experiment_standards.md
    ├── feedback_data_handling.md
    ├── project_core_constraints.md
    ├── project_research_progress.md
    └── reference_resources.md
```

## 核心概念 (1分钟)

### 三层工作流

1. **CLAUDE.md** — 项目规范和约束（已在根目录创建）
2. **.claude/** — AI 助手的工作流系统（本目录）
3. **memory/** — 跨实验的知识积累

### 四种记忆类型

- **User** — 关于你的信息
- **Feedback** — 已验证的最佳实践和陷阱
- **Project** — 项目状态和进度
- **Reference** — 资源位置

## 使用场景 (2分钟)

### 场景 1: 规划一个新实验

```
1. 向 Claude 说："我想尝试用 ViT 作为 tokenizer"
2. Claude 自动读取：
   - CLAUDE.md（项目规范）
   - memory/project_core_constraints.md（核心约束）
   - memory/feedback_experiment_standards.md（实验规范）
3. Claude 提出设计建议和注意事项
4. 讨论、同意后，Claude 帮你规划实验
```

### 场景 2: 遇到问题

```
1. 说："我的 L_tok 没有下降"
2. Claude 查阅：
   - memory/feedback_data_handling.md（数据问题）
   - MISTAKE_POLICY.md（问题分类）
3. Claude 帮助诊断和解决
4. 记录学到的东西到记忆
```

### 场景 3: 新人加入项目

```
1. 新人阅读：CLAUDE.md → .claude/SYSTEM.md → .claude/WORKFLOW.md
2. Claude 概述项目、约束、当前进度（从记忆读取）
3. 新人可以快速上手，避免重复错误
```

## 关键文件导航

### 了解项目 (必读)
1. **根目录 CLAUDE.md** — 项目简介、架构、命令
2. **.claude/SYSTEM.md** — 设计哲学
3. **memory/project_core_constraints.md** — 不能改变什么

### 开始工作
1. **.claude/WORKFLOW.md** — 日常工作流
2. **memory/feedback_experiment_standards.md** — 实验规范
3. **memory/reference_resources.md** — 数据和资源位置

### 遇到问题
1. **.claude/MISTAKE_POLICY.md** — 错误分类和恢复
2. **memory/** — 查找相关的已知陷阱

### 多人协作
1. **.claude/MULTI_AGENT_GUIDE.md** — Agent 角色和协作
2. **memory/MEMORY.md** — 记忆索引

## 命令参考

```bash
# 查看项目规范
cat CLAUDE.md

# 查看工作流
cat .claude/WORKFLOW.md

# 查看记忆系统
cat .claude/memory/MEMORY.md
```

## 第一次运行实验的检查清单

- [ ] 理解了项目的机器理解焦点（见 CLAUDE_readme.md）
- [ ] 确认了数据集位置（见 memory/reference_resources.md）
- [ ] 设计好了实验假设
- [ ] 创建了 configs/exp_XXX.yaml
- [ ] 固定了所有随机种子
- [ ] 验证了数据分割无重叠

## 常见问题

**Q: 我应该何时更新记忆？**
A: 当你发现新的陷阱、学到关键经验、或项目状态改变时。

**Q: 我可以改变项目定义吗？**
A: 不建议。核心定义见 memory/project_core_constraints.md。如果必须改，需要明确的讨论和批准。

**Q: 我应该使用单 Agent 还是多 Agent？**
A: 简单实验用单 Agent。复杂项目（>3 个并行任务）考虑 MULTI_AGENT_GUIDE.md。

**Q: 实验结果应该记录在哪？**
A: 创建 experiments.md（参考模板在 CLAUDE_TEMPLATE/templates/），或简单地记录到 memory/project_research_progress.md。

## 下一步

1. 读 **memory/project_core_constraints.md** — 理解项目的固定原则
2. 读 **WORKFLOW.md** — 学习日常工作流
3. 阅读 **feedback_experiment_standards.md** — 了解实验规范
4. 开始你的第一个实验！

## 获取更多帮助

- **系统哲学** → .claude/SYSTEM.md
- **工作流规范** → .claude/WORKFLOW.md
- **记忆系统** → .claude/MEMORY_POLICY.md
- **错误处理** → .claude/MISTAKE_POLICY.md
- **多 Agent 协作** → .claude/MULTI_AGENT_GUIDE.md
- **项目记忆** → .claude/memory/

---

**本系统会自动在你的每次 Claude Code 对话中被加载，帮助你保持一致、高效的研究工作流！**

最后更新：2026-04-01
