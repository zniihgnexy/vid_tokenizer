# NVRC 快速命令参考

**按照这个顺序一步步执行。每个命令执行完再执行下一个。**

---

## 📋 第1步：环境准备 (5-10分钟)

### 1.1 检查 GPU

```bash
nvidia-smi
```

**预期输出：** 显示你的 GPU 信息（型号、显存等）

---

### 1.2 创建虚拟环境

```bash
# 使用 conda (推荐)
conda create -n nvrc python=3.10
conda activate nvrc
```

或者：

```bash
# 使用 venv
python3.10 -m venv ~/nvrc_env
source ~/nvrc_env/bin/activate
```

**验证：** 你的终端提示符应该显示 `(nvrc)` 或 `(nvrc_env)`

---

### 1.3 安装 PyTorch

选择一个（根据你的 CUDA 版本）：

```bash
# CUDA 11.8（大多数 RTX 4000 系列）
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118 -q
```

或：

```bash
# CUDA 12.1
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu121 -q
```

或：

```bash
# CPU 版（无 GPU，会很慢）
pip install torch torchvision torchaudio -q
```

**验证：**

```bash
python -c "import torch; print(f'PyTorch {torch.version.__version__}'); print(f'CUDA: {torch.cuda.is_available()}')"
```

---

### 1.4 安装依赖

```bash
# 导航到 NVRC 目录
cd /home/xinyizheng/vid_tokenizer/third_party/NVRC

# 安装基础包
pip install accelerate pyyaml pillow tqdm numpy -q

# 安装 CompressAI
pip install compressai -q

# (可选) 安装 DeepSpeed
pip install deepspeed -q

# (可选) 安装 Wandb
pip install wandb -q
```

**验证：**

```bash
python << 'EOF'
import sys
import torch
import datasets
import compress_models
import entropy_models
import models

checks = [
    ("PyTorch", lambda: torch.__version__),
    ("CUDA available", lambda: torch.cuda.is_available()),
    ("CompressAI", lambda: True),
    ("Datasets", lambda: True),
    ("Models", lambda: True),
]

print("✓ Setup Check:")
for name, check in checks:
    try:
        result = check()
        print(f"  ✓ {name}: OK")
    except Exception as e:
        print(f"  ✗ {name}: FAILED - {e}")
        sys.exit(1)

print("\n✓ All checks passed!")
EOF
```

---

## 📁 第2步：数据准备 (10-30分钟)

### 2.1 创建数据目录

```bash
# 创建目录结构
mkdir -p ~/vid_tokenizer_data/uvg
cd ~/vid_tokenizer_data/uvg

# 检查是否有 YUV 视频文件
ls -lh *.yuv 2>/dev/null || echo "No YUV files found yet"
```

### 2.2 转换 YUV 为 PNG（如果你有 YUV 文件）

```bash
# 安装 FFmpeg（如果没装）
# Ubuntu/Debian:
sudo apt-get install ffmpeg

# macOS:
brew install ffmpeg

# 转换单个视频
VIDEO_ID=Beauty
HEIGHT=1080
WIDTH=1920

# 创建输出目录
mkdir -p $VIDEO_ID

# 转换（从 YUV420p 到 PNG）
ffmpeg -video_size ${WIDTH}x${HEIGHT} -pixel_format yuv420p -i ${VIDEO_ID}.yuv ${VIDEO_ID}/%04d.png

# 验证
ls -1 $VIDEO_ID/ | head -5
echo "Total frames: $(ls -1 $VIDEO_ID/ | wc -l)"
```

### 2.3 创建小型测试视频（如果你想快速测试）

```bash
# 方法 A: 用 synthetic 数据创建测试视频
cd /home/xinyizheng/vid_tokenizer/third_party/NVRC

mkdir -p data/test_video

# 生成 10 帧测试视频
python << 'EOF'
import os
from PIL import Image
import numpy as np

os.makedirs("data/test_video", exist_ok=True)

# 生成 10 帧随机视频（1280x720）
for i in range(10):
    # 生成随机 RGB 图像
    img_data = np.random.randint(0, 256, (720, 1280, 3), dtype=np.uint8)
    img = Image.fromarray(img_data, 'RGB')

    # 保存
    img.save(f"data/test_video/{i+1:04d}.png")

print(f"✓ Generated 10 test frames in data/test_video/")
EOF

# 验证
ls -1 data/test_video/ | head -5
```

---

## 🚀 第3步：运行你的第一个实验

### 3.1 快速可行性测试 (5分钟)

最小化参数，只验证代码能否运行：

```bash
cd /home/xinyizheng/vid_tokenizer/third_party/NVRC

# 运行快速测试（10帧，1个epoch）
bash scripts/train/overfitting_uvg_nvrc.sh \
  0 \
  test_video \
  0.01 \
  xs \
  2e-3 \
  1e-4 \
  1 \
  32
```

**预期：** 应该开始训练，显示进度条。如果失败，检查错误信息。

---

### 3.2 标准单视频实验 (1-2小时)

用真实参数训练：

```bash
cd /home/xinyizheng/vid_tokenizer/third_party/NVRC

# 参数设置
VIDEO_ID=Beauty              # 改成你的视频名
LAMBDA=0.01                  # 速率-失真权重：越小越追求质量
SCALE=s                      # 模型大小：xs < s < m < l
LR_S1=2e-3                   # 阶段1学习率（初始化）
LR_S2=1e-4                   # 阶段2学习率（精化）
GRAD_ACCUM=1                 # 梯度累积（显存紧张时增大）
BATCH_SIZE=144               # 批大小（显存紧张时减小）

# 执行
bash scripts/train/overfitting_uvg_nvrc.sh \
  0 \
  $VIDEO_ID \
  $LAMBDA \
  $SCALE \
  $LR_S1 \
  $LR_S2 \
  $GRAD_ACCUM \
  $BATCH_SIZE

echo "✓ Training complete!"
```

**输出位置：** `output/`

---

### 3.3 监控训练进度（在另一个终端）

```bash
cd /home/xinyizheng/vid_tokenizer/third_party/NVRC

# 实时查看日志
tail -f output/logs/*/train.log

# 或查看完整日志
cat output/logs/*/train.log | tail -50
```

---

## 📊 第4步：查看结果

### 4.1 检查输出文件

```bash
cd /home/xinyizheng/vid_tokenizer/third_party/NVRC

# 查看目录结构
tree output/ -L 2

# 或
find output/ -type f | sort
```

### 4.2 查看最终结果

```bash
# 查看结果摘要（如果存在）
cat output/result_summary.json 2>/dev/null | python -m json.tool

# 或查看日志文件
grep -E "(psnr|ms_ssim|bitrate|compression)" output/logs/*/eval.log | tail -10
```

### 4.3 查看模型大小

```bash
# 查看压缩后的比特流大小
du -h output/encoded_bitstream/*

# 与原始视频对比
du -h data/test_video/
```

---

## 🔧 常见问题快速诊断

### 问题 1: `CUDA out of memory`

**解决：** 减小批大小或模型大小

```bash
# 改为：
BATCH_SIZE=64      # 从 144 改为 64
SCALE=xs           # 从 s 改为 xs
```

---

### 问题 2: `ModuleNotFoundError: No module named 'compressai'`

**解决：** 重新安装依赖

```bash
pip install --upgrade compressai accelerate -q
```

---

### 问题 3: 找不到数据文件

**解决：** 检查数据路径

```bash
# 数据必须在这个路径：
ls -la data/YOUR_VIDEO_NAME/

# 应该看到：
# 0001.png
# 0002.png
# ...
```

---

### 问题 4: 训练速度很慢

**可能的原因：**

```bash
# 检查是否在用 GPU
nvidia-smi          # 应该看到你的进程用 GPU

# 如果没用 GPU，检查 PyTorch
python -c "import torch; print(torch.cuda.is_available())"

# 尝试增大批大小（如果显存允许）
BATCH_SIZE=256
```

---

## 📈 实验变种参数组合

### 快速测试（5分钟）

```bash
LAMBDA=0.01 SCALE=xs BATCH_SIZE=32 LR_S1=2e-3
```

### 质量优先（1小时）

```bash
LAMBDA=0.001 SCALE=m BATCH_SIZE=144 LR_S1=1e-3
```

### 压缩优先（1小时）

```bash
LAMBDA=0.1 SCALE=m BATCH_SIZE=144 LR_S1=2e-3
```

### 高质量基准（2小时）

```bash
LAMBDA=0.001 SCALE=l BATCH_SIZE=144 LR_S1=1e-3
```

---

## 🎯 下一步：与 Tokenizer 集成

当你的 NVRC 能成功运行后，下一步是：

```
1. 获取重建视频 x_hat
2. 加载 CLIP/ViT tokenizer
3. 计算：
   y = tokenizer(x)         # 原始视频特征
   y_hat = tokenizer(x_hat) # 重建视频特征
4. 优化 L_tok = ||y_hat - y||²
```

---

## 💾 保存常用命令

为了方便，创建一个脚本文件：

```bash
cat > ~/run_nvrc_experiment.sh << 'EOF'
#!/bin/bash

cd /home/xinyizheng/vid_tokenizer/third_party/NVRC

VIDEO_ID=${1:-test_video}
LAMBDA=${2:-0.01}
SCALE=${3:-s}
BATCH_SIZE=${4:-144}

echo "Running NVRC on $VIDEO_ID..."
bash scripts/train/overfitting_uvrc_nvrc.sh 0 $VIDEO_ID $LAMBDA $SCALE 2e-3 1e-4 1 $BATCH_SIZE

echo "Done! Results in output/"
EOF

chmod +x ~/run_nvrc_experiment.sh

# 使用:
~/run_nvrc_experiment.sh Beauty 0.01 m 144
```

---

**现在就执行第1步吧！** 👇

```bash
nvidia-smi
```
