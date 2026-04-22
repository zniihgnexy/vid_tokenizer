# Learning Path

这份文档是给“第一次认真看这条线”的人准备的。目标不是把所有历史都倒出来，而是帮你用最短路径看懂：

- 这条线想解决什么
- 现在有哪些已经可信的结论
- 这些结论分别落在什么文件里
- 如果你要继续做，应该从哪一层接手

## 1. 先用一句话抓住这条线

这条线研究的是：

`冻结的 teacher-anchor packet surface` 能不能通过一个更聪明的 downstream route，在不重训上游压缩模块的情况下，恢复出更多 retrieval signal。

当前答案是：

- 在一个 bounded widened surface 上，可以
- 但这个结论还不够宽，不能直接推广到更长视频、更复杂 consumer 或通用 machine-facing interface

## 2. 最短阅读路径

### Step 1: 先看 manuscript

看：

- `paper/draft.md`

重点看三件事：

1. Abstract
2. 第 4 节 `Bounded Query-Adaptive Evaluation`
3. 第 5 节 `Outcome Interpretation and Next Route`

如果你只想快速判断“这条线有没有东西”，这三处就够了。

### Step 2: 再看 claim 和 evidence 有没有对齐

看：

- `paper/claim_evidence_map.json`
- `paper/evidence_ledger.json`

你可以把它理解成：

- `draft.md` 负责把故事讲出来
- `claim_evidence_map.json` 负责回答“每个 claim 到底靠什么撑着”
- `evidence_ledger.json` 负责回答“这些证据具体是什么实验/分析结果”

### Step 3: 再看 skeptical review

看：

- `paper/review/review.md`
- `paper/review/revision_log.md`

这两份文件的作用是帮你跳过很多隐藏风险。它们已经把最容易被质疑的点列出来了，比如：

- 为什么现在只能叫 bounded feasibility note
- 为什么 broader retrieval validation 不能被写成 uniform dominance
- 为什么 downstream consumer bridge 现在还不能当正面结果

## 3. 再往下读代码和实验

如果你已经接受“paper 的说法大体可信”，下一层就看代码和结果产物。

### 3.1 Baseline 层

看：

- `baselines/imported/nvrc-local-source/verification.md`

你要确认的是：

- baseline 是什么
- 为什么它可以继续复用
- 哪些数字是 paper-facing comparator
- 哪些数字只是 local feasibility signal

### 3.2 Experiment script 层

重点脚本如下：

- `experiments/main/scripts/run_querybank_teacher_anchor_smoke.sh`
  当前 bounded smoke 的最直接入口
- `experiments/main/scripts/run_teacher_anchor_packet_eval.py`
  teacher-anchor packet eval 的主逻辑
- `experiments/main/scripts/run_query_collapse_localization.py`
  collapse 定位分析
- `experiments/main/scripts/run_frozen_consumer_eval.py`
  原图 vs reconstructed 的 frozen consumer 对比
- `experiments/main/scripts/run_delta_packet_bridge_eval.py`
  delta packet bridge 的轻量评估

建议顺序：

1. 先看 shell launcher
2. 再看 Python entrypoint
3. 最后再看 `experiments/main/evals/` 里的产物

### 3.3 Interface bundle 层

看：

- `experiments/main/interface_bundles/`

这里是把“模型跑完的结果”变成“可被下游继续消费的 bundle”。

当前你最值得先看的 bundle 是：

- `shared_gating_blueprint_repair_teacher_packet_smoke_r1`

因为它同时包含：

- `original/*.png`
- `reconstructed/*.png`
- `packets/*.pt`
- `manifest.json`
- `metadata/args.yaml`
- `metadata/aggregate_results.csv`

这会让你直观看到：当前 repo 并不只是 paper 文本，已经有一套 machine-facing intermediate asset。

## 4. 当前最值得记住的结果

### 主正结果

来自：

- `paper/draft.md`
- `paper/evidence_ledger.json`

结论：

- query-adaptive 在 bounded surface 上把 `top1_accuracy` 提到 `0.15625`
- raw-global 是 `0.125`
- temporal-context 是 `0.09375`

### 主边界

来自：

- `paper/draft.md` 第 5 节
- `paper/claim_evidence_map.json`

结论：

- broader three-bundle follow-up 还不支持“全面压制所有 parent route”
- temporal-context 在一些 ranking/chunk 指标上仍更强

### 主负结果

来自：

- manuscript 第 5 节里的 consumer bridge note
- `paper/review/review.md`

结论：

- 低容量 downstream-consumer bridge smoke 还是负的
- 所以现在不能说“packet surface 已经自然迁移到更强 consumer 上”

## 5. 如果你要继续接手，推荐从哪里开始

### 情况 A: 你主要想审 paper

从这 4 个文件开始：

1. `paper/draft.md`
2. `paper/claim_evidence_map.json`
3. `paper/evidence_ledger.json`
4. `paper/review/review.md`

### 情况 B: 你主要想审代码/实验可复现性

从这 5 个位置开始：

1. `experiments/main/scripts/run_querybank_teacher_anchor_smoke.sh`
2. `experiments/main/scripts/run_teacher_anchor_packet_eval.py`
3. `experiments/main/interface_bundles/`
4. `experiments/main/evals/`
5. `baselines/imported/nvrc-local-source/verification.md`

### 情况 C: 你准备继续推进下一阶段

那就直接看：

- `docs/LONG_VIDEO_CUSTOM_DATA_GUIDE.md`

因为下一阶段最实际的问题不是“paper 还能不能写”，而是：

- 怎么把 bounded surface 扩到更长视频
- 怎么把当前 pipeline 套到你自己的数据集
- 怎么把 frozen consumer / bridge eval 继续往前推

## 6. 学完以后你应该能回答的几个问题

如果你已经把这份 guide 走完，应该能回答：

1. 当前这条线在 big picture 里处于哪个阶段
2. 现在到底已经证明了什么
3. 现在明确没有证明什么
4. repo 里哪些文件是 paper，哪些文件是 evidence，哪些文件是 code entrypoint
5. 下一步如果继续做长视频或自定义数据，应该从哪个脚本开始

