# Long Video And Custom Data Guide

这份文档专门解决后续操作问题：

- 如果你想在更长的视频上继续试，怎么开始
- 如果你想用自己的数据集，怎么把当前 pipeline 套过去
- 如果你想继续测 consumer 或 bridge，应该走哪条路径

这里的原则很简单：

- 只引用当前目录里真实存在的脚本
- 先保留当前 bounded pipeline 的结构
- 优先做“可比较的扩展”，而不是一上来把所有东西都改掉

## 1. 当前已有的最小可操作 pipeline

从已有脚本看，当前 pipeline 可以拆成四段：

1. 准备 bounded video frames
2. 跑 frozen upstream export
3. 导出 machine-facing interface bundle
4. 做 downstream eval

对应脚本分别是：

- `experiments/main/scripts/extract_bounded_video_frames.py`
- `experiments/main/scripts/run_shared_gating_export_ego4d16f_smoke.sh`
- `experiments/main/scripts/export_reconstructed_interface.py`
- `experiments/main/scripts/export_teacher_feature_interface.py`
- `experiments/main/scripts/run_frozen_consumer_eval.py`
- `experiments/main/scripts/run_delta_packet_bridge_eval.py`

## 2. 如果你想试更长视频，建议怎么做

### 推荐策略

不要直接从 `16` 帧一下跳到非常长的视频端到端完整重跑。更稳妥的做法是：

1. 先从同一条视频里提更长的 contiguous window
2. 保持 frame resolution 和 pipeline 结构不变
3. 先验证 export 与 bundle 这层有没有坏
4. 再做 downstream eval

### Step 1: 从原视频抽更长的窗口

当前现成脚本：

```bash
python experiments/main/scripts/extract_bounded_video_frames.py \
  --video-path /path/to/your_video.mp4 \
  --output-dir /path/to/output_dataset \
  --start-frame 0 \
  --num-frames 32 \
  --width 32 \
  --height 32 \
  --overwrite
```

这一步会产出一个 PNG 数据目录和 `extraction_manifest.json`。

当前脚本的默认假设仍然偏向 bounded local bridge pipeline，所以更长视频建议先试：

- `num_frames = 32`
- 再试 `48`
- 最后再看是否值得继续往上加

### Step 2: 跑 frozen upstream export

现成 launcher：

```bash
DATASET_DIR=/path/to/data \
DATASET_NAME=your_dataset_name \
NUM_FRAMES=32 \
FRAME_HEIGHT=32 \
FRAME_WIDTH=32 \
OUTPUT_ROOT=/path/to/experiments/main \
EXP_NAME=shared_gating_interface_export_yourdataset_32f_smoke_r1 \
./experiments/main/scripts/run_shared_gating_export_ego4d16f_smoke.sh
```

这个 launcher 的关键点：

- 它会调用 vendored `NVRC/main_nvrc.py`
- 走的是 frozen shared-gating export 路线
- 默认依赖一个已有 `RESUME_ROOT`

所以如果你换更长视频，最稳妥的做法是：

- 先保持 backbone / config 不变
- 只改 `DATASET_DIR`、`DATASET_NAME`、`NUM_FRAMES`
- 把它当成“结构迁移测试”，而不是“全新训练实验”

### Step 3: 导出 interface bundle

如果你先只关心 reconstructed interface，可以用：

```bash
python experiments/main/scripts/export_reconstructed_interface.py \
  --source-run-dir /path/to/completed_run \
  --dataset-dir /path/to/png_dataset \
  --output-dir /path/to/interface_bundle
```

如果你要保留 teacher feature / packet 层，可以用：

```bash
python experiments/main/scripts/export_teacher_feature_interface.py \
  --source-run-dir /path/to/completed_run \
  --dataset-dir /path/to/png_dataset \
  --output-dir /path/to/interface_bundle \
  --teacher-type resnet18_imagenet \
  --device auto
```

导出后，bundle 一般会包含：

- `original/`
- `reconstructed/`
- `packets/`
- `manifest.json`
- `metadata/args.yaml`
- `metadata/aggregate_results.csv`

### Step 4: 在更长视频 bundle 上跑 downstream eval

先跑最稳妥的 frozen consumer：

```bash
python experiments/main/scripts/run_frozen_consumer_eval.py \
  --bundle-dir /path/to/interface_bundle \
  --output-dir /path/to/output_eval \
  --model resnet18 \
  --mode smoke \
  --batch-size 16 \
  --device auto
```

如果这一步还有正信号，再继续试 delta bridge：

```bash
python experiments/main/scripts/run_delta_packet_bridge_eval.py \
  --bundle-dir /path/to/interface_bundle \
  --output-dir /path/to/output_eval \
  --mode smoke \
  --delta-weight 8.0 \
  --ridge-lambda 1.0
```

## 3. 如果你想用自己的数据集，最小改动方式是什么

### 当前 pipeline 对数据的最小要求

从现有脚本来看，你自己的数据最好先整理成：

- 一个目录
- 里面是连续编号的 PNG 帧
- 帧尺寸先尽量和当前 bounded pipeline 保持一致，例如 `32x32`

原因不是因为最终只能用这么小，而是因为：

- 现在这条线的重点是先验证 pipeline 结构能不能稳定迁移
- 不是一开始就把分辨率、时长、任务复杂度一起改掉

### 推荐的两种接入方式

#### 方式 A: 你手里已经有 `.mp4`

直接先用：

```bash
python experiments/main/scripts/extract_bounded_video_frames.py ...
```

把它切成一个 bounded PNG 数据目录。

#### 方式 B: 你已经有逐帧图像

那就直接整理成当前脚本能识别的 PNG dataset 目录结构，然后从 export 那一步开始。

## 4. 继续做你自己的数据时，建议保留哪些不变量

为了让新结果还能和当前线对话，建议先保留：

- teacher type 不变：`resnet18_imagenet`
- export 路线不变：先沿用 frozen shared-gating export
- eval 顺序不变：先 frozen consumer，再 delta bridge
- bundle 结构不变：保留 `manifest.json + original/reconstructed/packets`

如果你一开始同时改：

- teacher
- video length
- resolution
- consumer
- bridge

那结果很容易解释不清。

## 5. 一条更实际的推进路线

如果我是按“最小可验证增量”继续做，我会建议：

### Phase 1: 先把 bounded pipeline 搬到你自己的短视频

- 先抽一个 `16` 或 `32` 帧窗口
- 跑 export
- 导 bundle
- 跑 frozen consumer eval

目标：

- 验证当前 repo 不是只对现有 smoke 数据有效

### Phase 2: 再把同一视频窗口拉长

- 从 `16 -> 32 -> 48`
- 观察 export 是否稳定
- 看 consumer 指标有没有快速塌掉

目标：

- 找到当前 pipeline 的时长敏感性

### Phase 3: 再决定要不要重训或换 consumer

只有在下面两件事已经成立时，才建议往前走：

1. 更长视频上 export/bundle/eval 这条链还是通的
2. frozen consumer 至少还有一些正信号

不然更可能应该先修接口，而不是急着上更大模型。

## 6. 如果你只是想复现当前 paper 线，不想扩展

最短路径如下：

### 6.1 跑 bounded teacher-anchor smoke

```bash
./experiments/main/scripts/run_querybank_teacher_anchor_smoke.sh
```

它默认会从：

- `experiments/main/evals/shared_gating_query_collapse_localization_smoke_r1/summary.json`

里读取 bundle 路径，再调用：

- `experiments/main/scripts/run_teacher_anchor_packet_eval.py`

### 6.2 看输出

看：

- `experiments/main/evals/querybank_teacher_anchor_smoke_r1/report.md`
- `experiments/main/evals/querybank_teacher_anchor_smoke_r1/summary.json`

### 6.3 对照 paper

再回去对照：

- `paper/draft.md`
- `paper/evidence_ledger.json`

确认 manuscript 里的数字是不是和脚本输出一致。

## 7. 当前最现实的注意事项

- 这条线现在还是 smoke / bounded evaluation 主导，不是完整 benchmark pipeline
- 更长视频和自定义数据在工程上已经有入口，但还没有被包装成 one-click full pipeline
- 如果你想把这条线做成更 public 的 GitHub repo，下一步重点会是：
  - 清理和固定环境依赖
  - 把 DeepScientist 生成的过程性材料进一步压缩成更标准的 repo 文档
  - 给 export / bundle / eval 做更稳定的 config 入口

## 8. 你现在最该怎么用这份仓库

如果你的目标是：

### 先 review 再决定交不交

先看：

- `PR_LOCAL_REVIEW.md`
- `paper/draft.md`
- `paper/review/review.md`

### 继续推进工程

直接从：

- `extract_bounded_video_frames.py`
- `run_shared_gating_export_ego4d16f_smoke.sh`
- `export_teacher_feature_interface.py`
- `run_frozen_consumer_eval.py`

这四步往下走。

### 测你自己的数据

先做最小版本：

- 一段短视频
- 一个 bounded frame window
- 一次 export
- 一次 bundle
- 一次 frozen consumer eval

先确认这条链能迁移，再谈更长视频和更强 consumer。

