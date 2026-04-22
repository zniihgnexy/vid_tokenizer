# vid_tokenizer with foundation model

这是当前这条主线的本地可 review 版本。它把一条已经完成到论文交付就绪状态的研究线，重新整理成一个更像正常 GitHub 仓库的入口：

- 你可以先看清楚这条线在 big picture 里解决什么问题
- 你可以沿着真实存在的代码、实验结果和 paper 证据往下读
- 你也可以从这里继续做复现、长视频测试，或者替换成你自己的数据集

当前这条线的核心结论很克制：

- 上游 machine-oriented compression / packet pipeline 已经能稳定导出可用接口
- 在冻结 packet surface 不变的前提下，`query-adaptive arbitration` 能在一个 bounded widened teacher-anchor retrieval surface 上，把 headline `top1_accuracy` 提到 `0.15625`
- 这说明 frozen packet surface 里确实还有 downstream-recoverable structure
- 但这还不是“广义 machine-facing adapter 已经完成”的结论，长视频、更大 consumer、你自己的数据还属于下一阶段工作

## 这份仓库里最重要的内容

- `paper/draft.md`
  当前 manuscript 主体，适合先快速理解“这条线到底证明了什么”
- `paper/claim_evidence_map.json`
  每个 claim 对应哪些证据，适合 review 时核对有没有 overclaim
- `paper/evidence_ledger.json`
  当前 paper 线真正引用了哪些实验/分析结果
- `paper/review/review.md`
  独立审稿式 review，总结这条线目前最可信的说法和边界
- `baselines/imported/nvrc-local-source/verification.md`
  基线验证记录，说明这条线是建立在哪个可复用 baseline 上
- `experiments/main/scripts/`
  关键入口脚本，负责 export interface、packet eval、frozen consumer eval、delta bridge eval
- `experiments/main/evals/`
  已经跑出来的主要评估结果
- `experiments/main/interface_bundles/`
  已经导出的 interface bundle，可直接拿来观察 packet/original/reconstructed 数据

## 建议的阅读顺序

1. `PR_LOCAL_REVIEW.md`
   先看这次本地 PR 想交什么、为什么值得 review。
2. `paper/draft.md`
   看方法、结果、边界。
3. `paper/review/review.md`
   看目前最可能被质疑的点和已经收住的边界。
4. `docs/LEARNING_PATH.md`
   按代码和数据资产往下追，理解 repo 结构。
5. `docs/LONG_VIDEO_CUSTOM_DATA_GUIDE.md`
   如果你要继续动手，这里是下一步操作手册。

## Repo 结构速览

```text
.
├── baselines/
│   └── imported/nvrc-local-source/        # 当前确认过的 baseline 及验证记录
├── experiments/
│   └── main/
│       ├── scripts/                       # 真正可复用的实验入口脚本
│       ├── interface_bundles/             # 已导出的 machine-facing bundle
│       └── evals/                         # 各条线的评估输出
├── paper/
│   ├── draft.md                           # 当前 manuscript
│   ├── claim_evidence_map.json            # claim -> evidence 映射
│   ├── evidence_ledger.json               # paper 使用的证据总账
│   ├── review/                            # skeptical review 与 revision log
│   └── proofing/                          # proofing 记录
├── docs/
│   ├── LEARNING_PATH.md                   # 如何学习和观察当前已有内容
│   └── LONG_VIDEO_CUSTOM_DATA_GUIDE.md    # 如何继续跑更长视频和自己的数据
└── PR_LOCAL_REVIEW.md                     # 本地 GitHub PR 说明
```

## 现在这条线最值得看的几个结果

- 主结果：
  `paper/draft.md` 第 4 节，以及 `paper/evidence_ledger.json` 里的 `query_adaptive_teacher_anchor_arbitration_smoke_r1`
- 更宽一点但仍然保守的补充验证：
  `paper/evidence_ledger.json` 里的 `query_adaptive_broader_retrieval_validation_smoke_r1`
- 明确的负结果边界：
  `paper/draft.md` 第 5 节里关于 downstream-consumer bridge smoke 的说明

## 快速复现入口

当前最直接的 bounded smoke 入口是：

```bash
./experiments/main/scripts/run_querybank_teacher_anchor_smoke.sh
```

它会默认读取已有的 collapse-localization summary，然后调用：

```bash
python experiments/main/scripts/run_teacher_anchor_packet_eval.py
```

如果你只是想先理解当前已有 bundle 和下游 consumer 的关系，建议按下面顺序试：

1. 观察已有 interface bundle
2. 跑 frozen consumer eval
3. 再跑 delta-packet bridge eval

具体步骤见 `docs/LONG_VIDEO_CUSTOM_DATA_GUIDE.md`。

## 当前状态

- baseline：已确认
- paper line：bundle ready
- manuscript：可人工 review
- 当前最合理的下一步：不是继续补“有没有结果”，而是把这条线 review 清楚，然后决定是否继续做更长视频 / 更大 consumer / 自定义数据集扩展

