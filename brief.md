# Quest Brief

## Goal

Project Bootstrap
- Project title: vid_tokenizer with foundation model
- Project id: 002
- User language: English

Primary Research Request
# Next Quest Bootstrap

## 先说结论

建议把下一步作为 **新的 quest** 来开，而不是继续挂在当前 quest 下面。

原因很简单：

1. 当前 quest 已经完成了它该完成的事，核心结论和边界已经收住。
2. 你下一步想做的事情已经不是“继续证明当前 tokenizer/compression 线路是否成立”，而是把它接到 **更完整的 machine pipeline / 大模型接口 / downstream 验证** 上。
3. 这个新目标会引入新的输入输出接口、新的评测方式、甚至新的数据组织方式；如果继续塞回旧 quest，会把已经收好的结论重新打散。

所以更合理的做法是：

- **保留当前 quest 作为已完成的前置研究**
- **新开一个 quest，明确研究目标变成“从已验证的 machine-oriented compression 模块，走向完整 pipeline 与下游 machine use”**

---

## 当前 quest 已经提供了什么

新 quest 不应该从零开始，它应该把下面这些内容视为已经成立的前置资产：

1. `nvrc-local-source` baseline 已确认可用。
2. 当前比较稳定、适合承接论文故事的主线是 **shared semantic-gated dual-path** 这一类 machine-oriented tokenizer interface 方案。
3. readout 主线已经被降级，不应作为下一步默认承接对象。
4. DINOv2 richer-teacher 方向目前只能算旁证，不足以单独替换当前主线。
5. 当前 quest 更像是在回答：
   - “machine-oriented compression 这件事能不能成立？”
   - “tokenizer / teacher consistency 作为压缩目标有没有研究价值？”

它**还没有真正完成**的是：

- 把这个模块接成一个更完整的 downstream machine pipeline
- 证明压缩表示对更高层的 machine understanding / interface 使用是否仍然有效
- 设计更贴近未来系统形态的输入输出协议

这正是新 quest 该做的事。

---

## 新 quest 的核心定位

下一条线建议固定成下面这个定位：

> 在已经验证过的 machine-oriented egocentric video compression 模块之上，构建一个面向下游 machine understanding 的完整接口与最小可执行 pipeline，验证压缩表示是否能稳定服务于更高层的视觉/视频理解模型。

这句话里有两个关键词：

1. **在已经验证过的模块之上**
   - 意味着新 quest 默认继承当前 quest 的压缩主线，而不是重新打一轮“shared-gating 到底行不行”。

2. **完整接口与最小可执行 pipeline**
   - 重点不是一开始就堆很大的系统，而是先定义清楚：
     - 下游模型到底接什么输入
     - 原视频 / 重建视频 / 压缩表示之间如何对齐
     - 最小验证任务是什么

---

## 新 quest 要回答的核心问题

建议把问题收敛成下面 4 个，而不是一开始铺太大：

1. 当前已验证的 compression + tokenizer interface，能否稳定导出一个对下游模型可消费的表示或输入协议？
2. 用压缩后重建视频，或者压缩相关中间表示，去做下游 machine task 时，相比原视频会损失多少？
3. 这种损失是否在一个可以接受的范围内，足以支持“machine-oriented compression is useful beyond the teacher loss”？
4. 如果要进一步接大模型接口，最合理的承接层应该是：
   - reconstructed video
   - tokenizer/teacher features
   - 更抽象的 compressed packet / semantic packet

---

## 推荐的主路线

### 推荐路线 A：先做接口化，再接一个最小下游任务

这是我最推荐的路线。

做法：

1. 冻结当前最佳 compression 主线，不再重新优化它。
2. 定义统一导出接口，例如每个视频样本能导出：
   - 原视频标识
   - 压缩表示或可恢复的中间产物
   - 重建视频
   - teacher/tokenizer 表征
   - 对齐后的 metadata
3. 先接一个 **最小但真实** 的 downstream task，验证“压缩后是否仍可供机器使用”。

为什么推荐：

- 它最干净地承接当前 quest
- 它不会一上来就被“大模型 API 调通细节”拖死
- 它能先把“接口到底该长什么样”这个真正关键的问题定下来

### 备选路线 B：直接接大模型/VLM 接口做 end-to-end demo

这个路线可以做，但我不推荐作为第一步主线。

问题在于：

- 一旦直接接大模型，变量会突然变很多
- 你最后很难判断问题到底出在：
  - compression 本身
  - 接口设计
  - prompt / API / sampling
  - 下游任务定义

所以更适合把它放到新 quest 的第二阶段，而不是第一阶段。

### 不推荐路线 C：继续在当前 quest 里加层

不推荐。

因为这会把“已经收好的 research answer”和“下一阶段新问题”混在一起。

---

## 新 quest 的建议边界

### 应该做的

- 把当前 compression 主线视为 frozen upstream module
- 明确下游接口长什么样
- 选一个最小的 downstream 机器任务做验证
- 建立原视频 vs 重建视频 vs 压缩相关表示的对比框架
- 为后续更大模型接口留出清晰扩展位

### 暂时不要一开始就做的

- 不要先重新打 shared-gating / readout / DINOv2 谁更强
- 不要一上来做很多下游任务
- 不要一上来就做多模型、多 API、多数据集的大而全系统
- 不要过早把故事改写成“通用大模型视频系统”

---

## 新 quest 的最小可执行目标

建议把第一阶段目标压成下面 3 个交付：

1. **一个固定的上游输入输出协议**
   - 明确当前 compression 模块产出什么
   - 明确下游模块消费什么

2. **一个最小 end-to-end pipeline**
   - 从输入视频到压缩/重建，再到下游 machine consumer，整条链条能跑通

3. **一个最小对比实验**
   - 至少比较：
     - original video input
     - reconstructed video input
     - 如果可行，再加 compressed-side interface input

如果这 3 个交付都落地了，新 quest 就已经是 solid 的开始。

---

## 建议的第一阶段实验包

### Phase 1: 冻结当前上游模块

目标：

- 明确当前继承的是哪条已验证线路
- 固定 checkpoint / 配置 / 数据子集

成功标准：

- 不再对上游 compression 方法做新的研究性改动
- 所有人都知道“这条 quest 继承的输入模块”到底是什么

### Phase 2: 定义 machine-facing interface

目标：

- 定义下游消费的最小对象

候选对象可以是：

1. reconstructed video
2. tokenizer feature packet
3. compressed semantic packet

推荐顺序：

1. 先从 `reconstructed video + teacher-aligned metadata` 开始
2. 再尝试更抽象的 feature / packet 接口

原因：

- 第一种最容易先跑通
- 也最容易与原视频输入做公平比较

### Phase 3: 接一个最小下游任务

推荐先选：

- 一个轻量、稳定、评价明确的任务

例如可优先考虑：

1. retrieval / matching 类任务
2. clip-level classification / probing
3. 一个简单的视频理解代理任务

不建议第一步就上：

- 开放式生成问答
- 很长链条的 agent workflow
- 高度依赖 prompt 工程的大模型 demo

### Phase 4: 再决定是否接更大模型接口

这一步才适合回答：

- 是否需要真正引入 VLM / LLM API
- 接入点该放在视频、feature，还是中间语义包上
- 是否值得把“machine-oriented compression”推进到更系统级的 story

---

## 这个新 quest 的成功标准

如果我是给这个 quest 设验收，我会用下面这些标准：

1. 新 quest 能清楚说明它继承了什么，而不是重新做上一条线。
2. 有一个明确的 machine-facing interface，而不是只有“压缩重建结果”。
3. 有一个最小 end-to-end pipeline 可以稳定跑通。
4. 有至少一个下游任务能对比 original vs reconstructed 的机器可用性差异。
5. 能回答“下一步是否值得接更大的模型接口”，而不是只堆了更多工程。

---

## 建议的新 quest 标题

你可以从下面两个里选一个风格：

### 版本 1：偏研究标题

**Machine-Facing Downstream Interface for Egocentric Video Compression**

### 版本 2：偏工程研究结合

**From Machine-Oriented Video Compression to a Usable Downstream Pipeline**

我个人更推荐第二个，因为它更贴合你现在真正想做的“往完整 pipeline 走”。

---

## 可直接复制到新项目里的请求模板

下面这段就是我建议你直接复制到新 quest 里的启动文档或 request：

```md
# New Quest Bootstrap

## Project Goal

This quest is a follow-up to a completed research line on machine-oriented egocentric video compression.

The previous quest already established a stable upstream compression/tokenizer interface line. This new quest should **not** reopen that question by default. Instead, it should treat the current upstream module as a frozen starting point and focus on building a **usable downstream machine pipeline** on top of it.

The core goal of this quest is:

> Build a minimal but real downstream pipeline on top of the validated machine-oriented video compression module, and test whether compressed/reconstructed video or compression-related machine-facing representations remain useful for downstream machine understanding.

## What This Quest Inherits

- A completed prior line showing that machine-oriented compression with teacher/tokenizer consistency is a valid research direction.
- A stable paper-facing upstream line centered on a shared semantic-gated dual-path style interface.
- A trusted baseline contract from the previous quest.
- A clear conclusion that the previous quest should be treated as closed rather than further extended in-place.

## What This Quest Should Do

1. Freeze the inherited upstream compression line instead of re-optimizing it.
2. Define a machine-facing downstream interface.
3. Build a minimal end-to-end pipeline from compressed input to downstream machine usage.
4. Evaluate at least one minimal downstream task comparing original vs reconstructed inputs, and optionally a more abstract compression-side interface.
5. Decide whether a larger VLM/LLM interface is justified after the minimal pipeline is stable.

## What This Quest Should Not Do First

- Do not reopen the old question of which upstream compression variant wins unless new evidence forces it.
- Do not start with a huge end-to-end LLM system.
- Do not launch many downstream tasks at once.
- Do not turn the project into a generic large-model demo without preserving the original machine-oriented compression story.

## Recommended First-Stage Plan

### Stage 1: Freeze and package the upstream module

- Identify the inherited best line, checkpoint, config, and data subset.
- Make the inherited input/output contract explicit.

### Stage 2: Define the downstream-facing interface

Possible interfaces:
- reconstructed video
- teacher/tokenizer feature packet
- compressed semantic packet

Recommended starting point:
- reconstructed video plus aligned teacher-side metadata

### Stage 3: Build one minimal downstream task

Prefer a stable and low-variance task such as:
- retrieval / matching
- clip-level classification / probing
- another lightweight video-understanding proxy task

Avoid starting with:
- open-ended generative QA
- multi-model agent pipelines
- prompt-heavy demos

### Stage 4: Decide whether to connect a larger model interface

Only after the minimal pipeline is stable, decide:
- whether to add a VLM/LLM API
- where that interface should attach
- whether the new story is strong enough to broaden the system scope

## Success Criteria

This quest is successful if it delivers:

1. a frozen inherited upstream module,
2. a clear machine-facing interface,
3. a runnable minimal downstream pipeline,
4. at least one original-vs-reconstructed downstream comparison,
5. an evidence-based decision on whether to scale toward a larger model interface.

## Communication Rule

Always preserve the original project identity:
- this is still machine-oriented egocentric video compression
- the downstream pipeline is an extension of that story, not a replacement of it

Do not silently turn this into a generic human-video or generic large-model project.
```

---

## 一句话建议

这次最合理的开法是：

**新开一个 quest，把当前 quest 当作已经完成并冻结的上游研究；新 quest 专注于“machine-facing downstream interface + 最小完整 pipeline”，不要继续在旧 quest 里加层。**

Research Goals
- find a link between the current comression layer and build the large model layers to make the whole pipelien runnable and prove the feasibilty. see if you can use a model as example and form a full version of experiment version of the whole design and get a first version of result batch for me to see what the output can be and whether this direction is worth doing.
- make the major innovation to be more focused on the pipeline building, focus on the output result but it can be trade-off a bit innovation level by the pipeline building.
- build a full vversion of Github repo with code and can be rerun locally and shared through the github link

Baseline Context
Runtime will attach and confirm baseline_id nvrc-local-source (variant tiny-local-teacher-pilot-r3) before the project starts. Treat it as the pre-bound baseline unless you find a concrete incompatibility, corruption, or missing-evidence problem.

Reference Papers / Repositories / Local Paths
- None provided

Operational Constraints
No explicit runtime, privacy, dataset, or hardware constraints were provided.

Research Delivery Mode
- A research paper is required for this project.
- The project should normally continue through baseline, literature-grounded idea selection, implementation, main experiments, necessary analysis, paper outline, drafting, revision, and paper bundle preparation.
- Do not stop after obtaining only one improved algorithm or one promising run.
- After each `artifact.record_main_experiment(...)`, first interpret the measured result, then decide whether to improve further, run necessary follow-up analysis, or move into writing.
- The idea stage only creates or revises a candidate direction; the round is not complete until a main experiment result is recorded and routed.
- Unless the user explicitly changes scope, do not terminate the project before at least one paper-like deliverable exists.

Decision Handling Mode
- Autonomous decision mode is active.
- Do not hand ordinary route, branch, cost, baseline-reuse, or experiment-selection decisions back to the user.
- Report chosen routes through threaded progress or milestone updates, and keep moving unless you are explicitly requesting final completion approval.

Launch Mode
- Standard launch mode is active.
- Standard profile: canonical research workflow.
- Start from the canonical research graph unless durable state later proves that a non-standard entry path is better.

Research Contract
- Launch mode: Standard mode: start from the ordinary canonical research loop and let the default stage graph drive the first round.
- Standard entry type: Canonical research workflow: follow the ordinary research graph from baseline and idea selection through experiment, analysis, and paper work when justified.
- Research intensity: Balanced: secure a trustworthy baseline and probe one justified direction without overcommitting.
- Decision policy: Autonomous: decide ordinary route choices yourself, keep the user informed through threaded updates, and do not hand routine decisions back to the user.
- Research paper required: Yes
- Scope: Baseline + direction: secure the baseline, then test one promising improvement direction.
- Baseline policy: Use existing baseline: trust the selected reusable baseline first and let runtime attach and confirm it before the project begins.
- Review follow-up policy: Not applicable outside the Review custom task type.
- Baseline execution policy: Standard baseline handling from the ordinary research loop.
- Manuscript edit mode: No manuscript-facing custom edit contract requested.
- Resource policy: Balanced: keep progress steady while still controlling cost and risk.
- Git strategy: Semantic head + controlled integration: keep a cleaner main line and merge only reviewed branches.
- Time budget per research round: 24 hour(s)

Mandatory Working Rules
- Keep all durable files inside the project root.
- Reuse existing baseline artifacts whenever possible before rebuilding them.
- Standard launch mode is active here: use the canonical research graph unless later durable evidence justifies a different entry path.
- Emit explicit milestone updates after each meaningful step.
- Every decision must include reasons, evidence, and the next recommended action.
- If the startup contract already fixes the delivery mode and baseline policy, follow it without asking the user again unless cost, safety, or scope changes materially.
- If manuscript edits are required, make the section-level deltas explicit and keep the replacement wording copy-ready.
- Autonomous mode is the default contract here: decide the route yourself and continue unless you are requesting explicit completion approval.

## Initial Notes

- Establish or attach a baseline.
- Capture the first concrete decision with explicit reasons.
