# START HERE - NVRC 项目完整指南

## ✨ 你现在拥有什么

你的项目里现在有 **NVRC** — 一个完整的、可工作的神经视频压缩框架。

```
你的项目
├── CLAUDE.md (项目规范)
├── CLAUDE_readme.md (核心定义)
├── third_party/NVRC/
│   ├── 模型代码 (HiNeRV INR)
│   ├── 熵编码 (压缩核心)
│   ├── 训练脚本
│   └── 配置文件
│
└── .claude/ (工作流系统)
    ├── NVRC_SETUP_GUIDE.md ← 【详细安装和原理】
    ├── NVRC_QUICK_COMMANDS.md ← 【一步步命令】
    ├── NVRC_CODE_DEEP_DIVE.md ← 【深度代码理解】
    └── NVRC_README_START_HERE.md ← 【本文件】
```

---

## 🎯 3 个学习层级

### 级别 1: 快速启动 (今天)

**目标：** 让代码跑起来，理解输入输出

**需要阅读：**
- `.claude/NVRC_QUICK_COMMANDS.md` — 复制粘贴命令

**需要做：**
1. 安装环境 (30分钟)
2. 运行测试 (5分钟)
3. 观察输出

**成果：** "我的代码能跑！"

---

### 级别 2: 理解原理 (第 1-2 天)

**目标：** 理解 NVRC 为什么这样设计、数据如何流动

**需要阅读：**
- `.claude/NVRC_SETUP_GUIDE.md` → 深层逻辑部分
- `.claude/NVRC_CODE_DEEP_DIVE.md` → 数据流部分

**需要做：**
1. 跑多个实验，改变参数
2. 查看输出文件，理解各个指标
3. 读 main_nvrc.py 和 compress_models/nvrc.py

**成果：** "我理解 NVRC 做什么了"

---

### 级别 3: 深度修改 (第 3-7 天)

**目标：** 集成 tokenizer，修改架构，做研究实验

**需要阅读：**
- 完整的 `.claude/NVRC_CODE_DEEP_DIVE.md`
- 阅读 `models/hinerv.py` 源代码
- 阅读 `entropy_models/` 的实现

**需要做：**
1. 添加 tokenizer 分支
2. 修改损失函数
3. 尝试不同的 INR 架构

**成果：** "我能修改代码做自己的实验"

---

## 📚 4 份详细文档说明

| 文档 | 长度 | 内容 | 何时读 |
|------|------|------|--------|
| **NVRC_SETUP_GUIDE.md** | 长 (30 min) | 完整安装、背景知识、参数详解 | 第1天 |
| **NVRC_QUICK_COMMANDS.md** | 短 (5 min) | 逐命令执行，快速上手 | 现在就读 |
| **NVRC_CODE_DEEP_DIVE.md** | 长 (30 min) | 代码流程、如何修改 | 第2天 |
| **NVRC_README_START_HERE.md** | 短 (5 min) | 总览和快速链接 | 现在 |

---

## ⚡ 快速行动计划

### 👉 现在 (5 分钟)

```bash
# 1. 检查 GPU
nvidia-smi

# 2. 如果有 GPU，执行这个
cat ~/.cuda_version 2>/dev/null || echo "Installing..."

# 3. 阅读这个文件的下一部分
```

### 👉 接下来 (1 小时)

1. **打开 `.claude/NVRC_QUICK_COMMANDS.md`**
2. **按顺序执行第 1-2 步骤的所有命令**
3. **遇到问题，查看文档里的"常见问题"部分**

### 👉 第一次成功 (1-2 小时)

1. **跑完第一个实验**
2. **查看 `output/` 目录的结果**
3. **记录数字和观察**（压缩率、质量等）

### 👉 理解原理 (第 2 天)

1. **深入读 `NVRC_SETUP_GUIDE.md` 的"深层逻辑"部分**
2. **改变参数重新运行，观察结果如何变化**
3. **画出数据流程图在纸上**

### 👉 开始研究 (第 3 天+)

1. **读 `NVRC_CODE_DEEP_DIVE.md`**
2. **在 NVRC 代码里添加你的 tokenizer 分支**
3. **尝试第一个改进实验**

---

## 🗂️ 文件导航速查

### 安装和环境问题？
→ **NVRC_QUICK_COMMANDS.md** 第 1 步 + 常见问题诊断

### 想快速跑一个实验？
→ **NVRC_QUICK_COMMANDS.md** 第 3 步

### 想理解 NVRC 的工作原理？
→ **NVRC_SETUP_GUIDE.md** 的"深层逻辑"部分

### 想修改代码？
→ **NVRC_CODE_DEEP_DIVE.md** 的"如何修改代码"部分

### 想了解数据流？
→ **NVRC_CODE_DEEP_DIVE.md** 的"代码执行流程"部分

### 遇到 CUDA 错误？
→ **NVRC_QUICK_COMMANDS.md** 的"常见问题" → 问题 1

### 遇到导入错误？
→ **NVRC_QUICK_COMMANDS.md** 的"常见问题" → 问题 2

---

## 🔑 核心概念速查

### NVRC 做什么？

```
输入：视频帧 (T, H, W, 3)
  ↓
HiNeRV：学习一个 MLP 网络
  - 学到什么：隐函数 f(t, h, w) → RGB
  - 用什么优化：重建损失 + 速率损失
  ↓
压缩：参数 → 比特流（熵编码）
  ↓
输出：
  - 比特流（极小，可存储和传输）
  - 重建视频（从比特流解码得到）
```

### 为什么分两个阶段？

```
第1阶段 (360 epoch)：编码器训练
  - 学习最优的编码网络参数
  - 目标：平衡压缩率和重建质量
  - 输出：最优的参数集

第2阶段 (30 epoch)：量化器训练
  - 冻结编码器，只学量化器
  - 目标：进一步压缩参数（离散化）
  - 输出：量化后的比特流
```

### Lambda 是什么？

```
lambda ∈ [0, 1]：速率-失真权衡

λ = 0：只优化质量（MSE 最小）
  → 压缩率低，文件很大
  ← 不推荐，浪费空间

λ = 0.01：质量优先（常用）
  → 好的视频质量，还是有压缩
  ← 推荐用这个

λ = 0.1：平衡
  → 压缩更强，质量尚可
  ← 可以试试

λ = 1：压缩优先
  → 极限压缩，质量会下降
  ← 不推荐
```

---

## ⚠️ 常见陷阱

### 陷阱 1: 显存不足

**症状：** `RuntimeError: out of memory`

**快速修复：**
```bash
BATCH_SIZE=32     # 从 144 改为 32
SCALE=xs          # 从 s 改为 xs
```

---

### 陷阱 2: 数据找不到

**症状：** `FileNotFoundError: data/YOUR_VIDEO/`

**快速修复：**
```bash
# 检查数据路径
ls -la data/YOUR_VIDEO/

# 应该看到 0001.png, 0002.png 等
```

---

### 陷阱 3: 导入错误

**症状：** `ModuleNotFoundError: No module named 'compressai'`

**快速修复：**
```bash
cd /home/xinyizheng/vid_tokenizer/third_party/NVRC
pip install --upgrade compressai accelerate
```

---

### 陷阱 4: 训练很慢

**症状：** 每个 epoch 需要很久

**可能原因 + 解决：**
```bash
# 原因1：在 CPU 上运行
nvidia-smi  # 应该看到你的进程用 GPU

# 原因2：设置太大
BATCH_SIZE=64     # 改小
SCALE=xs          # 改小

# 原因3：数据集太大
# → 用小视频（8-10帧）测试流程
```

---

## 🎓 学习路径建议

### 如果你：有 ML 背景

```
第1天：
  ✓ 跑一个快速测试 (NVRC_QUICK_COMMANDS.md)
  ✓ 理解 lambda 参数的含义
  ✓ 修改 lambda 重新运行

第2天：
  ✓ 读 NVRC_CODE_DEEP_DIVE.md 的"代码执行流程"
  ✓ 理解两阶段训练的区别
  ✓ 理解熵编码的作用

第3天+：
  ✓ 添加 tokenizer 分支
  ✓ 修改损失函数
  ✓ 开始实验
```

### 如果你：新手，想深入学

```
第1天：
  ✓ 跑一个快速测试
  ✓ 阅读 NVRC_SETUP_GUIDE.md（慢慢读，理解原理）
  ✓ 查看输出文件，理解各个指标

第2天：
  ✓ 改变 lambda/scale 参数重新运行
  ✓ 观察结果如何变化
  ✓ 试着预测一下"如果我改这个参数，压缩率会怎样？"

第3-4天：
  ✓ 深入读代码（NVRC_CODE_DEEP_DIVE.md）
  ✓ 在纸上画出数据流程
  ✓ 理解每个模块的职责

第5+天：
  ✓ 修改代码做自己的实验
```

---

## ✅ 检查清单

### 环境检查

- [ ] GPU 可用（`nvidia-smi` 能看到）
- [ ] PyTorch 装好（`python -c "import torch; print(torch.cuda.is_available())"`）
- [ ] 依赖装好（`python -c "import compressai; import accelerate"` 不报错）

### 第一次实验前

- [ ] 有训练数据（PNG 或 YUV 文件）
- [ ] 知道数据路径
- [ ] 知道 lambda 值的含义
- [ ] 知道 scale 参数的含义
- [ ] 有地方保存输出（output/ 目录）

### 运行后

- [ ] 能找到输出文件
- [ ] 能看到日志信息
- [ ] 能理解输出的 PSNR/MS-SSIM 等指标
- [ ] 能画出参数和性能的关系

---

## 🚀 第一句话行动

```bash
cd /home/xinyizheng/vid_tokenizer/third_party/NVRC
cat NVRC_QUICK_COMMANDS.md | head -20
```

这会显示前 20 行，让你知道要做什么。

然后一步步执行命令。

---

## 📞 遇到问题？

### 快速查询

1. **Bash 错误信息** → 复制错误到 `.claude/NVRC_QUICK_COMMANDS.md` 的"常见问题"查找
2. **不理解某个概念** → 在 `.claude/NVRC_SETUP_GUIDE.md` 搜索关键词
3. **想修改代码** → 查看 `.claude/NVRC_CODE_DEEP_DIVE.md` 的"如何修改代码"

### 深层问题

1. **理论细节** → 查看 NVRC 原论文（在 README.md 里有链接）
2. **架构设计** → 看 HiNeRV 论文
3. **熵编码** → 看 CompressAI 文档

---

## 📖 推荐阅读顺序

```
Day 1:
  1. 本文件（10 分钟）
  2. NVRC_QUICK_COMMANDS.md（执行命令，20 分钟）
  3. 看结果和日志（10 分钟）

Day 2:
  4. NVRC_SETUP_GUIDE.md（深层逻辑部分，30 分钟）
  5. 改参数重新运行（30 分钟）

Day 3+:
  6. NVRC_CODE_DEEP_DIVE.md（30 分钟）
  7. 开始修改代码（自由时间）
```

---

## 🎉 成功标志

✅ **第1级成功：** "我能运行 NVRC"
  - 环境搭好了
  - 训练脚本能跑
  - 看到了输出结果

✅ **第2级成功：** "我理解 NVRC 的工作原理"
  - 知道 lambda 的含义和影响
  - 能解释 PSNR 和 MS-SSIM
  - 能预测参数改变的效果

✅ **第3级成功：** "我能修改和扩展 NVRC"
  - 添加了 tokenizer 分支
  - 修改了损失函数或架构
  - 跑了自己的实验

---

## 📋 最后检查

你是否：

- [ ] 理解了 NVRC 是什么？
- [ ] 知道下一步要做什么？（运行 NVRC_QUICK_COMMANDS.md）
- [ ] 知道有 4 个详细文档可以查阅？
- [ ] 知道遇到问题去哪找答案？

**如果都是 ✅，那就开始吧！** 👇

```bash
# 打开快速命令指南
cd /home/xinyizheng/vid_tokenizer
cat .claude/NVRC_QUICK_COMMANDS.md
```

---

**祝你研究顺利！** 🚀
