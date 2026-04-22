# Local PR Review Draft

## PR Title

`paper line packaging: bounded query-adaptive teacher-anchor arbitration with repo-facing docs`

## 这次 PR 想解决什么

这次不是再补一个新实验，而是把当前已经完成到 paper-ready 的那条主线，整理成一个可以人工 review、后续也方便提交到 GitHub 的本地版本。

具体目标有三件事：

1. 把这条线的研究故事说清楚
2. 把支撑这条线的代码、实验结果和 paper 证据链串起来
3. 给后续继续扩展到长视频和自定义数据，留下可直接操作的入口

## Big Picture 里的位置

这个项目的大方向是：

`foundation model -> machine-oriented video compression / packet interface -> downstream machine usage`

当前这条线处在中间偏后的一个关键阶段：

- 上游 compression / packet export 已经能跑
- 现在要回答的不是“codec 能不能训练”，而是“冻结下来的 packet surface 里还有没有 downstream 可恢复的结构”
- 这条 paper 线给出的回答是：有，但目前只在一个 bounded teacher-anchor retrieval surface 上被证明，不能过度外推

所以这条线的意义不是终局，而是把“这个方向可能成立”从 vague idea 变成了一个有明确证据边界的 deliverable。

## 这条线当前最可信的贡献

### 1. 一个明确且保守的主结论

在不改上游 packet bundle 的前提下，`query-adaptive arbitration` 在 bounded widened surface 上：

- `top1_accuracy` 从 `0.125` / `0.09375` 提高到 `0.15625`
- `hub-cluster share` 从 `0.59375` 降到 `0.28125`

这说明冻结 packet surface 本身包含可被进一步读出的 downstream structure。

### 2. 一个可信的边界

这条线没有声称：

- 更广义的 machine-facing adapter 已经完成
- 更长视频或更多 surface 上已经普遍有效
- 下游 consumer transfer 已经被证明

相反，这些边界都已经被明确写进：

- `paper/draft.md`
- `paper/claim_evidence_map.json`
- `paper/review/review.md`

### 3. 一个已经可读、可审、可继续扩展的 repo 形态

这次整理后，repo 里已经有：

- manuscript
- claim/evidence ledger
- baseline verification
- review/proofing
- 真实实验脚本
- interface bundle
- 后续操作手册

## 主要文件和它们的作用

### Review 入口

- `README.md`
  总入口，给第一次打开仓库的人看
- `PR_LOCAL_REVIEW.md`
  这份本地 PR 说明

### 论文和证据

- `paper/draft.md`
  主 manuscript
- `paper/selected_outline.json`
  这条 paper 线的正式 story contract
- `paper/claim_evidence_map.json`
  claim 对应到哪些实验
- `paper/evidence_ledger.json`
  当前 paper 真的用了哪些 evidence
- `paper/review/review.md`
  skeptical review 结果
- `paper/proofing/proofing_report.md`
  proofing 记录

### 基线和实验

- `baselines/imported/nvrc-local-source/verification.md`
  baseline 为什么可信
- `experiments/main/scripts/run_teacher_anchor_packet_eval.py`
  teacher-anchor packet eval 的主要 Python 入口
- `experiments/main/scripts/run_querybank_teacher_anchor_smoke.sh`
  当前 bounded smoke 的 shell 入口
- `experiments/main/scripts/export_reconstructed_interface.py`
  导出 reconstructed interface bundle
- `experiments/main/scripts/export_teacher_feature_interface.py`
  导出 teacher-feature packet bundle
- `experiments/main/scripts/run_frozen_consumer_eval.py`
  冻结 consumer 的对比评估
- `experiments/main/scripts/run_delta_packet_bridge_eval.py`
  delta packet bridge 的评估

### 面向继续操作的文档

- `docs/LEARNING_PATH.md`
  怎么学习和观察当前已有内容
- `docs/LONG_VIDEO_CUSTOM_DATA_GUIDE.md`
  怎么继续跑更长视频和你自己的数据

## 推荐 review 顺序

1. 先看 `README.md`，确认 repo 现在在讲什么
2. 再看 `paper/draft.md`，确认 manuscript 的叙事和数字
3. 再看 `paper/claim_evidence_map.json` 与 `paper/evidence_ledger.json`
4. 最后看 `paper/review/review.md`

如果你是从“能不能继续做工程扩展”这个角度 review，就再补看：

5. `docs/LEARNING_PATH.md`
6. `docs/LONG_VIDEO_CUSTOM_DATA_GUIDE.md`

## Review 时建议重点盯的点

### A. 叙事有没有 overclaim

重点核对：

- manuscript 是否始终把结论限制在 bounded surface
- broader retrieval validation 是否只被当作 boundary note
- downstream consumer bridge negative result 是否被诚实保留

### B. 代码入口是否足够真实

重点核对：

- 文档里提到的脚本是否都存在
- 文档里推荐的运行路径是否真能对上当前目录里的 assets

### C. 这份 repo 是否已经足够做下一阶段

重点核对：

- 如果要试长视频，现有抽帧 / export / eval 路径是否够用
- 如果要换你自己的数据，当前手册是否已经把最小可操作路径讲清楚

## 当前已知限制

- 现在还是 markdown-first paper bundle，不是 venue-format 的 LaTeX/PDF 包
- 大部分结果仍然是 bounded smoke，而不是大规模 benchmark
- 自定义数据与长视频的支持已经有脚本入口，但还没有做成“一键完整 pipeline”

## 我对这次本地 PR 的建议判断

建议先按“可人工 review 的研究/工程 handoff 包”来 review，而不是按“已经是最终 public repo”来要求它。

原因很简单：

- 研究主线已经成形
- 代码和证据也已经真实存在
- 当前最缺的是 repo-facing packaging，而不是 scientific core

这次补的文档，正是在补这一层。

