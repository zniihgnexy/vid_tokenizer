# NVRC 项目集成与设置指南

## 📖 NVRC 是什么？

**NVRC (Neural Video Representation Compression)** — NeurIPS 2024 最新方法

- **第一个** INR-based 神经视频编码器，性能超越传统视频编码 VTM (RA)
- **基于** 神经表征（INR - Implicit Neural Representation）
- **目标** 压缩视频为紧凑的参数表示

### 核心原理

```
输入视频 x (RGB/YUV)
    ↓
HiNeRV 编码器 (INR网络)
    ↓ 学习参数
编码器参数 z (紧凑)
    ↓
HiNeRV 解码器
    ↓
重建视频 x_hat
```

### 关键特性

1. **Per-Video 拟合** — 每个视频单独训练一个 INR 网络
2. **分组编码** — 支持 GOP (Group of Pictures) 结构
3. **熵编码** — Grid 和 Weight 两种熵模型
4. **多质量等级** — 不同 lambda 值控制速率-失真权衡

---

## 📁 目录结构详解

```
third_party/NVRC/
│
├── main_nvrc.py              ← 【主入口】训练/编码脚本
├── main_utils.py             ← 配置、模型、数据加载的工厂函数
│
├── compress_models/          ← 【核心】压缩编解码器
│   ├── nvrc.py               ← NVRC 编码器/解码器定义
│   ├── codec_base.py         ← 基类
│   ├── utils.py
│   └── __init__.py
│
├── entropy_models/           ← 【重要】熵编码（压缩核心）
│   ├── entropy_model_base.py ← 基础熵模型
│   ├── grid_entropy_model.py ← 网格型熵模型（编码器参数）
│   ├── weight_entropy_model.py ← 权重型熵模型（权重参数）
│   ├── quantizer.py          ← 量化器
│   ├── distributions.py      ← 概率分布
│   └── ...
│
├── models/                   ← 【关键】INR 和上采样模块
│   ├── hinerv.py             ← HiNeRV（分层 INR 架构）
│   ├── encoding.py           ← 坐标编码（位置编码）
│   ├── upsample.py           ← 时间/空间上采样
│   ├── patch_utils.py        ← 补丁处理
│   └── ...
│
├── datasets.py               ← 数据加载器
├── tasks.py                  ← 任务定义（编码/解码任务）
├── losses.py                 ← 损失函数
├── io_utils.py               ← 视频 I/O
├── utils.py                  ← 通用工具
│
└── scripts/                  ← 【配置和脚本】
    ├── configs/
    │   ├── nvrc/
    │   │   ├── compress_models/   ← 压缩器配置
    │   │   ├── models/            ← INR 模型配置
    │   │   └── overfit/           ← 快速测试配置
    │   ├── data/                  ← 数据配置
    │   └── tasks/                 ← 损失函数配置
    │
    └── train/                ← 训练脚本
        └── overfitting_uvg_nvrc.sh
```

---

## 🔧 深层逻辑理解

### 1. 数据流 (Data Flow)

```
【输入】视频帧序列
    ↓
【数据集】datasets.py
  - 读取 PNG 或 YUV 文件
  - 分割成 Group of Frames (GOP)
  - 补丁化处理（可选）
    ↓
【任务】tasks.py
  - 定义编码/解码目标
  - 计算速率失真损失
    ↓
【模型】compress_models/nvrc.py + models/hinerv.py
  - 编码：视频 → INR 参数
  - 熵编码：参数 → 比特流
  - 解码：比特流 → 参数 → 视频
    ↓
【输出】压缩比特流 + 重建视频
```

### 2. 训练流程 (Training Pipeline)

```
第 1 阶段：编码器训练 (S1 - Stage 1)
  ├─ 训练 INR 编码器网络
  ├─ 优化目标：重建损失 + 速率损失
  ├─ 输出：压缩参数 z (编码器权重)
  └─ 轮数：360 epoch（可配置）

第 2 阶段：量化器适配 (S2 - Stage 2)
  ├─ 在 S1 参数基础上训练量化器
  ├─ 优化目标：熵损失（参数的比特成本）
  ├─ 输出：量化后的离散参数
  └─ 轮数：30 epoch

编码阶段：
  ├─ 解码器推理：参数 → 视频帧
  ├─ 熵编码：参数 → 比特流
  └─ 输出：最终压缩文件
```

### 3. 核心模块详解

#### A. HiNeRV (INR 架构)

```
输入：(B, T, H, W) 视频帧
  ↓
【时间编码】
  - 分层位置编码
  - 不同频率的时间特征
  ↓
【空间编码】
  - 坐标编码 (x, y)
  - 频率编码 + 周期编码
  ↓
【多层 MLP】
  - 隐藏维度 256 / 512 / ...
  - 激活函数 ReLU / GELU
  ↓
【输出头】
  - 输出像素值 (R, G, B) 或 (Y, U, V)
  ↓
输出：(B, T, H, W, 3) 重建视频
```

**关键参数** (models/hinerv.py):
- `dim_base`: 基础隐藏维度 (default: 256)
- `n_layers`: MLP 层数 (default: 6)
- `n_freq_space / n_freq_time`: 空间/时间频率数

#### B. 熵模型 (Entropy Models)

**Grid 型** (编码器参数本身):
```
编码器输出的特征图 (grid features)
  ↓
【Grid Entropy Model】
  - 学习特征分布 p(feature)
  - 使用上下文自适应算术编码
  - 输出：特征的比特成本
```

**Weight 型** (编码器网络权重):
```
编码器网络权重 w
  ↓
【Weight Entropy Model】
  - 学习权重分布 p(w)
  - 按轴或全局量化
  - 输出：权重的比特成本
```

#### C. 损失函数 (losses.py)

```
总损失 = λ × 速率损失 + (1-λ) × 失真损失

速率损失 (Rate Loss):
  - -log(p_z(z))  [图特征的熵]
  - -log(p_w(w))  [权重的熵]
  ← 越小 = 更可压缩

失真损失 (Distortion Loss):
  - MSE(视频, 重建视频)
  - 或 MS-SSIM（多尺度感知损失）
  ← 越小 = 重建质量越好

λ ∈ [0, 1]:
  - λ = 0: 优先质量
  - λ = 1: 优先压缩
  - λ = 0.01: 质量优先（常用）
```

### 4. 配置系统 (Configuration)

NVRC 使用 **YAML** 配置驱动：

```yaml
# 模型配置 (models/uvg_hinerv-v2-s_1920x1080.yaml)
model:
  arch: hinerv-v2
  dim_base: 192
  depth: 4

# 压缩器配置 (compress_models/nvrc_s1.yaml)
compress_model:
  grid_em:
    em: grid
    blk_size: [20, 5, 5]  # 空间-时间块大小
  weight_em:
    em: weight
    blk_size: [16, 32]

# 训练配置 (main_utils.py)
training:
  epochs: 360
  lr: 1e-4
  batch_size: 144
  lambda: 1.0  # 速率-失真权衡
```

---

## 📦 依赖和环境要求

### 必需的库

```
PyTorch >= 2.0          (深度学习框架)
accelerate >= 0.27      (多 GPU 训练加速)
Pillow                  (图像处理)
numpy                   (数值计算)
pyyaml                  (配置解析)
tqdm                    (进度条)
compressai              (压缩 AI 库，来自 InterDigital)
```

### 可选

```
deepspeed               (大规模分布式训练)
wandb                   (实验追踪 - 推荐)
tensorboard             (日志可视化)
```

### GPU 要求

- **最小**：6GB VRAM (slow)
- **推荐**：24GB+ VRAM (RTX 4090 / A100)
- **最优**：多 GPU + DeepSpeed

---

## ⚙️ 完整设置步骤

### 步骤 1: 创建虚拟环境

```bash
# 使用 conda (推荐)
conda create -n nvrc python=3.10
conda activate nvrc

# 或使用 venv
python3.10 -m venv nvrc_env
source nvrc_env/bin/activate
```

### 步骤 2: 安装 PyTorch

```bash
# 根据你的 GPU 选择 CUDA 版本
# 对于 NVIDIA GPU (CUDA 11.8)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118

# 对于 NVIDIA GPU (CUDA 12.1)
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121

# 验证
python -c "import torch; print(torch.cuda.is_available())"
```

### 步骤 3: 安装依赖

```bash
# 进入 NVRC 目录
cd /home/xinyizheng/vid_tokenizer/third_party/NVRC

# 安装必要的包
pip install accelerate pyyaml pillow tqdm numpy

# 安装 CompressAI
pip install compressai

# (可选) 安装 DeepSpeed
pip install deepspeed

# (可选) 安装 Wandb 用于实验追踪
pip install wandb
```

### 步骤 4: 准备数据

**选项 A: PNG 格式 (RGB)**

```bash
# 创建数据目录
mkdir -p data/uvg
cd data/uvg

# 使用 FFmpeg 将 YUV 视频转为 PNG
# 例：Beauty 视频 (1920x1080, YUV420P)
VIDEO_ID=Beauty
ffmpeg -video_size 1920x1080 -pixel_format yuv420p -i ${VIDEO_ID}.yuv ${VIDEO_ID}/%04d.png

# 输出：
# data/uvg/Beauty/0001.png
# data/uvg/Beauty/0002.png
# ...
```

**选项 B: 原始 YUV 格式**

```bash
# 只需重命名为标准格式
# 命名规则：${VIDEO_ID}_${WIDTH}x${HEIGHT}_yuv420p.yuv
mv input_video.yuv Beauty_1920x1080_yuv420p.yuv
```

### 步骤 5: 验证安装

```bash
# 进入 NVRC 目录
cd /home/xinyizheng/vid_tokenizer/third_party/NVRC

# 测试导入
python -c "
import torch
import datasets
import compress_models
import entropy_models
import models
print('✓ All imports successful!')
print(f'✓ CUDA available: {torch.cuda.is_available()}')
print(f'✓ GPU count: {torch.cuda.device_count()}')
"
```

---

## 🚀 运行你的第一个实验

### 简单快速测试 (单视频过拟合)

```bash
cd /home/xinyizheng/vid_tokenizer/third_party/NVRC

# 设置参数
VIDEO_ID=Beauty          # 视频名
LAMBDA=0.01              # 速率失真权衡 (越小越追求质量)
SCALE=s                  # 模型大小: xs, s, m, l (越大效果越好但更慢)
LR_S1=2e-3               # 第1阶段学习率
LR_S2=1e-4               # 第2阶段学习率
GRAD_ACCUM=1             # 梯度累积步数
BATCH_SIZE=144           # 批大小 (显存小可以降低)

# 运行训练脚本
bash scripts/train/overfitting_uvg_nvrc.sh 0 ${VIDEO_ID} ${LAMBDA} ${SCALE} ${LR_S1} ${LR_S2} ${GRAD_ACCUM} ${BATCH_SIZE}

# 结果输出在：
# output/
# ├── logs/
# ├── checkpoints/
# └── encoded_bitstream/
```

### 详细参数说明

| 参数 | 含义 | 例子 | 说明 |
|------|------|------|------|
| `VIDEO_ID` | 视频名 | `Beauty` | 必须在 `data/uvg/Beauty/` 有 PNG 文件 |
| `LAMBDA` | 速率权重 | `0.01` | 越小越追求质量；越大越追求压缩 |
| `SCALE` | 模型大小 | `s` | `xs/s/m/l` 从小到大；大更好但慢 |
| `LR_S1` | 第1阶段学习率 | `2e-3` | 编码器训练的学习率 |
| `LR_S2` | 第2阶段学习率 | `1e-4` | 量化器训练的学习率 |
| `GRAD_ACCUM` | 梯度累积 | `1` | 显存不足时增大 |
| `BATCH_SIZE` | 批大小 | `144` | 显存不足时减小 |

---

## 🔍 理解输出文件

运行完成后的输出结构：

```
output/
├── logs/                      # 训练日志
│   ├── gop_0000/
│   │   ├── train.log         # 训练进度
│   │   └── eval.log          # 验证结果
│   └── ...
│
├── checkpoints/              # 模型检查点
│   ├── gop_0000/
│   │   ├── stage1_latest.pth # 第1阶段最新权重
│   │   ├── stage1_best.pth   # 第1阶段最优权重
│   │   ├── stage2_latest.pth # 第2阶段最新权重
│   │   └── stage2_best.pth   # 第2阶段最优权重
│   └── ...
│
├── config.yaml              # 使用的配置
│
├── result_summary.json      # 最终结果摘要
│   {
│       "video": "Beauty",
│       "lambda": 0.01,
│       "compression_ratio": 123.45,
│       "psnr": 35.67,
│       "ms_ssim": 0.9876,
│       "bitrate": 0.0234,  # bpp (bits per pixel)
│       "time_s1": 3600.0,   # S1 耗时(秒)
│       "time_s2": 180.0     # S2 耗时(秒)
│   }
│
└── encoded_bitstream/       # 压缩后的比特流
    └── gop_0000.bin         # 实际压缩数据
```

### 关键指标含义

```
压缩率 (Compression Ratio)
  = 原始视频大小 / 压缩文件大小
  ← 越大越好

比特率 (BPP - Bits Per Pixel)
  = 压缩文件大小(bits) / (宽 × 高 × 帧数)
  ← 越小越好

PSNR (Peak Signal-to-Noise Ratio)
  = 20 * log10(255 / RMSE)
  ← 越大越好（通常 >30 dB 可接受）

MS-SSIM (Multi-Scale Structural Similarity)
  = 0 ~ 1 多尺度结构相似度
  ← 越接近 1 越好（>0.98 很好）
```

---

## 💡 与你的项目的结合点

### 当前状态

NVRC 是：
- ✓ **编码器** — 将视频压缩为紧凑参数表示
- ✓ **解码器** — 从参数重建视频
- ✗ **不包括** tokenizer 分支

### 集成计划

```
原始视频 x
  ↓
【NVRC 编码】
  ↓
压缩参数 z + 重建视频 x_hat
  ↓
【Tokenizer 分支】← 这是你需要添加的！
  x → CLIP/ViT → y
  x_hat → CLIP/ViT → y_hat
  ↓
L_tok = ||y_hat - y||²  ← 你的核心目标
```

---

## 🎯 下一步行动

### 立即执行的步骤

1. **验证环境**
   ```bash
   cd /home/xinyizheng/vid_tokenizer/third_party/NVRC
   python -c "import torch; print(torch.cuda.is_available())"
   ```

2. **准备小规模数据**
   - 找一个短视频（例如 8-10 帧）
   - 转换为 PNG 格式
   - 放在 `data/test_video/` 下

3. **运行测试**
   ```bash
   # 用小参数快速测试流程
   bash scripts/train/overfitting_uvg_nvrc.sh 0 test_video 0.01 xs 2e-3 1e-4 1 32
   ```

4. **检查日志**
   ```bash
   # 监控训练进度
   tail -f output/logs/*/train.log
   ```

### 遇到问题的诊断步骤

如果运行失败，按顺序检查：

1. **CUDA 问题** → 检查 GPU 可用性
   ```bash
   nvidia-smi
   ```

2. **导入问题** → 检查依赖安装
   ```bash
   python -c "import compressai; import accelerate"
   ```

3. **数据问题** → 检查路径和格式
   ```bash
   ls -la data/test_video/
   file data/test_video/*.png
   ```

4. **显存不足** → 减小批大小或模型大小
   ```bash
   # 改为：BATCH_SIZE=32, SCALE=xs
   ```

---

**准备好开始了吗？执行验证环节的第一个命令吧！**
