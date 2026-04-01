# .claude 系统 - vid_tokenizer 项目

这个目录包含了 Claude Code 在 vid_tokenizer 项目中的完整工作流系统。它会被自动加载到每次对话中，帮助保持一致、高效的研究开发过程。

## 📖 快速导航

### 首次使用？从这里开始
1. 读 **QUICKSTART.md** (5分钟)
2. 读 **SYSTEM.md** 了解哲学 (10分钟)
3. 读 **WORKFLOW.md** 了解日常流程 (15分钟)

### 开始工作
- **memory/** — 项目的知识库，会被自动读取
- 参考 **MEMORY_POLICY.md** 了解如何使用记忆系统

### 遇到问题
- **MISTAKE_POLICY.md** — 错误分类、诊断和恢复流程
- **memory/** 中的各个 feedback_*.md 文件

### 多人协作
- **MULTI_AGENT_GUIDE.md** — 多个 Claude Agent 如何协作

## 📁 文件结构

```
.claude/
│
├── 核心工作流文件 (必读)
│   ├── SYSTEM.md                    ← 系统哲学和架构
│   ├── WORKFLOW.md                  ← 日常工作流规范
│   ├── MEMORY_POLICY.md             ← 记忆系统说明
│   ├── MISTAKE_POLICY.md            ← 错误处理机制
│   └── MULTI_AGENT_GUIDE.md         ← 多 Agent 协作
│
├── 快速参考
│   ├── QUICKSTART.md                ← 新人入门指南
│   ├── README.md                    ← 本文件
│   └── experiments_template.md       ← 实验记录模板
│
└── memory/                          ← 项目知识库
    ├── MEMORY.md                    ← 记忆索引
    ├── user_research_background.md
    ├── feedback_experiment_standards.md
    ├── feedback_data_handling.md
    ├── project_core_constraints.md
    ├── project_research_progress.md
    └── reference_resources.md
```

## 🎯 核心概念

### 三层记忆系统

```
┌─────────────────────────────────────┐
│  会话记忆                            │ 当前对话的实验细节
├─────────────────────────────────────┤
│  项目记忆 (CLAUDE.md)               │ 项目规范、约束、架构
├─────────────────────────────────────┤
│  团队记忆 (memory/)                 │ 跨实验的经验、陷阱、最佳实践
└─────────────────────────────────────┘
```

### 四种Agent角色

1. **Planner** — 规划实验、设计方案
2. **Coder** — 实现代码、运行训练
3. **Researcher** — 分析结果、调查论文
4. **Verifier** — 验证正确性、检查质量

使用场景：
- 简单实验：单个 Agent 就够了
- 复杂项目：多个 Agent 并行协作（见 MULTI_AGENT_GUIDE.md）

## 🚀 使用场景

### 场景 1: 规划新实验

```
用户: "我想用 ViT 替换 CLIP tokenizer"
     ↓
Claude 自动读取:
  - CLAUDE.md (项目规范)
  - memory/project_core_constraints.md (核心约束)
  - memory/feedback_experiment_standards.md (实验规范)
     ↓
Claude 提出:
  - 设计建议
  - 需要注意的事项
  - 预期成本和时间
     ↓
讨论 → 同意 → Claude 帮助规划和实现
```

### 场景 2: 遇到问题

```
用户: "我的 L_tok 没有下降"
     ↓
Claude 查阅:
  - memory/feedback_data_handling.md
  - MISTAKE_POLICY.md
  - memory/feedback_experiment_standards.md
     ↓
Claude 诊断:
  - 数据泄漏？
  - Tokenizer 冻结了吗？
  - 损失权重配置对吗？
     ↓
分步修复 → 验证 → 记录经验
```

### 场景 3: 新人加入

```
新人: "我怎么开始这个项目？"
    ↓
Claude 建议:
  1. 读 QUICKSTART.md
  2. 读 memory/project_core_constraints.md
  3. 读 WORKFLOW.md
    ↓
  然后 Claude 可以:
  - 解释项目定义
  - 回顾当前进度
  - 指导第一个实验
```

## 📋 关键特点

### ✅ 自动化

- Claude 在每次对话中自动读取这些文件
- 不需要手动告诉 Claude 项目约束或历史经验
- 记忆系统自动积累知识

### ✅ 一致性

- 所有工作遵循相同的规范（WORKFLOW.md）
- 所有实验遵循相同的标准（feedback_experiment_standards.md）
- 避免重复的错误（通过记忆陷阱）

### ✅ 可追踪性

- 每个决策都有记录（MISTAKE_POLICY.md）
- 所有经验都保存（memory/）
- 项目进度清晰（project_research_progress.md）

### ✅ 适应性

- 可以针对你的项目自定义
- 记忆系统会随着工作演进
- 反馈机制帮助改进工作流

## 🔄 工作流概览

### 典型的实验周期

```
1. 规划 (30 min)
   读取约束 → 设计实验 → 确认假设

2. 配置 (30 min)
   写 config.yaml → 检查所有参数

3. 执行 (几小时)
   训练 → 监控损失 → 完全收敛

4. 分析 (1 小时)
   计算指标 → 与 baseline 对比 → 分析原因

5. 记录 (30 min)
   更新 experiments.md → 更新记忆 → 规划下一步
```

### 多 Agent 工作流

```
Planner: 规划 (2h)
  ↓
Coder: 实现 (8h, 可并行多个)
  ↓
Verifier: 验证 (1h)
  ↓
Researcher: 分析 (2h)
  ↓
结果总结和下一步规划
```

## 📚 文件使用指南

| 文件 | 何时读 | 何时更新 |
|------|--------|---------|
| SYSTEM.md | 第一次用时 | 不需要（固定） |
| WORKFLOW.md | 开始新工作 | 如果流程改变 |
| MEMORY_POLICY.md | 第一周 | 不需要（固定） |
| MISTAKE_POLICY.md | 遇到错误时 | 添加新的错误类型时 |
| MULTI_AGENT_GUIDE.md | 需要多 Agent 时 | 不需要（固定） |
| memory/MEMORY.md | 每天 | 每当创建新记忆时 |
| experiments_template.md | 第一个实验前 | 每个实验后 |

## ⚙️ 自定义和扩展

### 添加新的记忆

```bash
# 1. 在 memory/ 中创建新文件
cat > memory/feedback_your_topic.md << 'EOF'
---
name: 你的记忆标题
type: feedback  # 或 user/project/reference
---

[内容]
EOF

# 2. 在 memory/MEMORY.md 中添加索引
# - [你的标题](feedback_your_topic.md) — 一句话描述
```

### 更新工作流

如果你发现某些流程需要改变：
1. 在 WORKFLOW.md 中记录新的步骤
2. 在 MISTAKE_POLICY.md 中记录相关的错误处理
3. 如有常见陷阱，在 feedback_*.md 中记录

### 添加新的 Agent 角色

如果项目需要新的角色（如数据工程师、论文编辑等）：
1. 在 MULTI_AGENT_GUIDE.md 中定义新角色
2. 创建相应的 feedback_role_specific.md 文件

## 🔗 与其他文件的关系

```
根目录的重要文件：
├── CLAUDE.md               ← 项目规范（主文档）
├── CLAUDE_readme.md        ← 项目定义（不改）
│
.claude/ 目录：
├── 工作流文件 ← 自动被加载和使用
├── memory/ ← 自动被读取和更新
└── 本 README

src/ 代码目录：
└── 实现代码（遵循 CLAUDE.md 中的规范）

experiments.md 或 results/:
└── 实验记录（使用 experiments_template.md）
```

## 📖 完整阅读清单

### 第一天 (1小时)
- [ ] QUICKSTART.md
- [ ] SYSTEM.md

### 第一周 (3小时)
- [ ] WORKFLOW.md
- [ ] MEMORY_POLICY.md
- [ ] memory/project_core_constraints.md
- [ ] memory/feedback_experiment_standards.md

### 需要时
- [ ] MISTAKE_POLICY.md — 遇到错误
- [ ] MULTI_AGENT_GUIDE.md — 多人协作
- [ ] memory/feedback_data_handling.md — 数据问题
- [ ] 其他 memory/*.md — 具体问题时查阅

## 💡 关键要点

1. **Claude 会自动读取这些文件** — 不需要手动告诉 Claude 项目信息
2. **记忆会自动积累** — 每个实验学到的东西都可以保存，后续使用
3. **一致性很重要** — 所有人遵循相同的规范，工作更高效
4. **约束是保护** — 项目的核心定义（memory/project_core_constraints.md）保护研究方向

## 🆘 获取帮助

- **系统不清楚** → 读 SYSTEM.md
- **不知道该做什么** → 读 WORKFLOW.md
- **遇到错误** → 读 MISTAKE_POLICY.md
- **多人协作** → 读 MULTI_AGENT_GUIDE.md
- **找不到信息** → 查阅 memory/MEMORY.md 索引
- **有新发现** → 在 memory/ 中添加反馈记忆

---

**本系统采用自适应设计** — 随着项目进展，你可以根据需要更新和扩展它！

**最后更新：** 2026-04-01
**维护者：** Claude Code 系统
**相关：** 根目录 CLAUDE.md, CLAUDE_readme.md
