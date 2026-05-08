# NVRC 代码深度理解 - 详细解读

这是给想真正理解 NVRC 工作原理的人的完整代码流程图。

---

## 🔄 代码执行流程

### 总体流程图

```
用户命令
  ↓
main_nvrc.py:main()
  ├─ parse_args() → 读取 YAML 配置
  ├─ get_accelerator_logger() → 设置 GPU/分布式训练
  ├─ create_encoding_decoding_videos() → 加载视频数据
  ├─ create_overfit_dataset() → 创建数据集对象
  ├─ create_overfit_task() → 创建编码/解码任务
  │
  └─ for intra_idx in range(intra_idx_max):  # 循环每个 GOP
     ├─ 【第1阶段】编码器训练
     │  ├─ create_codec() → 创建 NVRC 编码器
     │  ├─ create_optimizer_scheduler() → 优化器
     │  ├─ 360 epoch 循环：
     │  │  ├─ forward pass: x → encoder → z
     │  │  ├─ loss = λ*L_rate + (1-λ)*L_recon
     │  │  ├─ backward() → 梯度下降
     │  │  └─ 验证集评估
     │  └─ 保存最优模型
     │
     └─ 【第2阶段】量化器训练
        ├─ 加载第1阶段权重
        ├─ 冻结编码器，只训练量化器
        ├─ 30 epoch 循环：
        │  ├─ forward pass: 计算熵损失
        │  ├─ loss = L_entropy
        │  └─ backward() → 量化器优化
        └─ 编码：参数 → 比特流

最后：
  ├─ 解码：比特流 → 参数 → x_hat
  ├─ 计算指标：PSNR, MS-SSIM, 压缩率
  └─ 保存结果
```

---

## 📝 关键文件深度解析

### 1. main_nvrc.py - 主循环

```python
def main():
    # ========== 初始化 ==========
    args = parse_args()  # 从命令行读取参数
    accelerator, logger, output_dir = get_accelerator_logger(args)

    # ========== 数据准备 ==========
    # 创建输入视频对象（用于读取 PNG/YUV）
    train_video_in, train_video_out = create_encoding_decoding_videos(...)
    eval_video_in, eval_video_out = create_encoding_decoding_videos(...)

    # 创建数据集（抽象 PNG 文件目录的接口）
    train_dataset = create_overfit_dataset(...)  # → datasets.py
    eval_dataset = create_overfit_dataset(...)

    # 创建任务（定义编码/解码目标）
    train_task = create_overfit_task(...)  # → tasks.py
    eval_task = create_overfit_task(...)

    # ========== 主循环 - 按 GOP 处理 ==========
    intra_period = 360  # 每个 GOP 多少帧
    num_frames = train_dataset.get_video_size()[0]  # 总帧数
    intra_idx_max = (num_frames + intra_period - 1) // intra_period

    for intra_idx in range(intra_idx_max):  # 对每个 GOP
        # --- 第1阶段：编码器训练 ---
        model = create_codec(...)  # → compress_models/nvrc.py
        optimizer, scheduler = create_optimizer_scheduler(...)

        # 360 epoch 的训练循环
        for epoch in range(args.epochs):  # epochs=360
            for batch_idx, batch_data in enumerate(train_loader):
                # Forward
                frames = batch_data['frames']  # (B, T, H, W, 3)
                recon, loss_dict = model(frames)  # 调用 NVRC.forward()

                # 计算损失
                loss_rate = loss_dict['rate']  # 速率损失
                loss_recon = loss_dict['recon']  # 失真损失
                loss = args.lambda * loss_rate + (1-args.lambda) * loss_recon

                # Backward
                accelerator.backward(loss)
                optimizer.step()
                optimizer.zero_grad()

            # 验证
            if epoch % eval_epochs == 0:
                validate(eval_loader, model, eval_task)

        # --- 第2阶段：量化器训练 ---
        # 加载第1阶段最优权重
        model.load_state_dict(checkpoint['model'])

        # 冻结编码器参数
        for name, param in model.named_parameters():
            if 'quantizer' not in name:
                param.requires_grad = False

        # 30 epoch 的量化训练
        for epoch in range(args.warmup_epochs):  # warmup_epochs=30
            for batch_idx, batch_data in enumerate(train_loader):
                # 只计算熵损失
                loss_entropy = model.entropy_loss()
                loss_entropy.backward()
                optimizer.step()

        # --- 编码：参数 → 比特流 ---
        bitstream = model.encode(eval_dataset)  # 熵编码

        # --- 验证：检查解码是否正确 ---
        decoded_frames = model.decode(bitstream)
        assert torch.allclose(decoded_frames, recon)  # 无损解码验证
```

**关键点：**

- `args.lambda` 控制速率-失真权衡
- 两个阶段：先学编码器，再学量化器
- 每个 GOP 独立处理（per-video fitting）

---

### 2. compress_models/nvrc.py - 编码器定义

```python
class NVRC(nn.Module):
    """NVRC 编码器+解码器"""

    def __init__(self, config):
        self.encoder = HiNeRV(config.model)  # 【关键】INR 编码器
        self.grid_em = GridEntropyModel(...)  # 网格特征熵模型
        self.weight_em = WeightEntropyModel(...)  # 权重熵模型
        self.quantizer = RoundQuantizer(...)  # 量化器

    def forward(self, frames):
        """
        Input:  frames (B, T, H, W, 3) - RGB 视频帧
        Output: recon (B, T, H, W, 3) - 重建视频
                loss_dict - 各种损失值
        """
        # ===== 编码阶段 =====
        # 1. 编码器前向传播：计算编码器网络的参数
        z_encoder = self.encoder.encode(frames)  # 编码器生成的隐空间表示

        # 2. 使用熵模型编码编码器参数
        bits_encoder, z_encoder_encoded = self.grid_em.encode(z_encoder)

        # 3. 编码网络权重
        bits_weight = self.weight_em.encode(self.encoder.weight_dict())

        # ===== 解码阶段 =====
        # 4. 量化解码（从比特流恢复参数）
        z_recovered = self.grid_em.decode(z_encoder_encoded)
        weights_recovered = self.weight_em.decode(bits_weight)

        # 5. 更新解码器网络权重
        self.encoder.load_weight_dict(weights_recovered)

        # 6. 解码器前向传播：参数 → 视频
        recon = self.encoder.decode(z_recovered)  # (B, T, H, W, 3)

        # ===== 损失计算 =====
        # 重建损失（失真）
        loss_recon = F.mse_loss(recon, frames)  # 或 ms_ssim_loss

        # 速率损失（比特成本）
        loss_rate = (bits_encoder + bits_weight) / (B*T*H*W)  # bits/pixel

        return recon, {
            'recon': loss_recon,
            'rate': loss_rate,
            'bits_total': bits_encoder + bits_weight,
        }

    def encode(self, frames):
        """完整编码：帧 → 比特流"""
        # ... 编码器推理、量化、算术编码 ...
        return bitstream  # 二进制数据

    def decode(self, bitstream):
        """完整解码：比特流 → 帧"""
        # ... 算术解码、反量化、解码器推理 ...
        return frames  # (B, T, H, W, 3)
```

**关键理解：**

```
【编码器网络的作用】
  输入：视频帧
  学习内容：MLP 权重 w 和隐变量 z
  输出：参数（w 和 z）

【解码器网络的作用】
  输入：参数（恢复后的 w 和 z）
  输出：重建视频帧

【为什么需要熵模型？】
  直接存储浮点参数太大
  → 学习参数分布 p(z)
  → 用熵编码压缩：bits = -log(p(z))
  → 比特流远小于原始参数
```

---

### 3. models/hinerv.py - INR 架构

```python
class HiNeRV(nn.Module):
    """分层神经表征 - 视频压缩的编码器网络"""

    def __init__(self, dim_base=256, depth=6, n_freq_time=4, n_freq_space=10):
        # 位置编码：将坐标转为高维特征
        self.pos_encoder = PositionalEncoding(n_freq_time, n_freq_space)

        # 主 MLP：坐标 → RGB 像素值
        self.mlp = nn.Sequential(
            nn.Linear(pos_encoder.out_dim, dim_base),
            nn.ReLU(),
            nn.Linear(dim_base, dim_base),
            nn.ReLU(),
            # ... 多层 ...
            nn.Linear(dim_base, 3),  # 输出 RGB
        )

    def forward(self, t, h, w):
        """
        输入：坐标 (t, h, w)
            - t ∈ [0, T-1] 时间坐标
            - h ∈ [0, H-1] 高坐标
            - w ∈ [0, W-1] 宽坐标

        输出：RGB 像素值 (3,)
        """
        # 位置编码
        pos_encoded = self.pos_encoder(t, h, w)  # (D_enc,)

        # MLP 前向
        rgb = self.mlp(pos_encoded)  # (3,)

        return torch.sigmoid(rgb)  # 值域 [0, 1]

    def encode(self, frames):
        """
        学习表示：找到最优的参数 θ 使得 INR(θ) ≈ frames
        """
        # 1. 初始化参数
        theta = self.initialize_parameters()

        # 2. 优化参数（梯度下降）
        optimizer = torch.optim.Adam(theta, lr=0.001)
        for iter in range(1000):
            # 在所有像素位置评估 INR
            recon = self.forward_batch(frames)

            # 最小化重建误差
            loss = F.mse_loss(recon, frames)
            loss.backward()
            optimizer.step()

        # 3. 返回学到的参数
        return theta

    def decode(self, z):
        """
        重建：用参数 θ 生成完整视频"""
        # 设置 INR 参数为 z
        self.set_parameters(z)

        # 在所有坐标上评估 INR
        frames = []
        for t in range(T):
            frame = []
            for h in range(H):
                row = []
                for w in range(W):
                    rgb = self.forward(t, h, w)  # 标量前向通过
                    row.append(rgb)
                frame.append(torch.stack(row))  # (W, 3)
            frames.append(torch.stack(frame))  # (H, W, 3)

        return torch.stack(frames)  # (T, H, W, 3)
```

**HiNeRV 的核心思想：**

```
视频帧可以看作函数：f: (t, h, w) → (r, g, b)

传统编码：存储每个像素值
  大小：T × H × W × 8 bits = 超大

神经表示：用 MLP 参数表示函数
  大小：MLP 参数数量（通常 100M 左右）

压缩率来自：
  1. 离散化：参数→低精度
  2. 熵编码：参数分布不均匀 → 可压缩
```

---

### 4. entropy_models/ - 熵编码

```python
class GridEntropyModel(nn.Module):
    """为网格特征（编码器输出）编码/解码"""

    def forward(self, z):
        """
        学习 z 的分布：p(z) = Normal(μ(context), σ(context))
        """
        # 1. 上下文建模：周围特征 → μ, σ
        context = self.context_net(z)  # 自适应上下文
        mu = self.mu_net(context)      # 均值
        sigma = self.sigma_net(context)  # 方差

        # 2. 分布参数化
        distribution = Normal(mu, sigma)

        # 3. 计算比特成本：-log(p(z))
        log_prob = distribution.log_prob(z)
        bits = -log_prob / np.log(2)  # 转为 bits

        return bits, distribution

    def encode(self, z):
        """训练时：计算熵损失"""
        bits, distribution = self.forward(z)
        return bits.mean()  # 平均每个元素的 bits

    def arithmetic_encode(self, z):
        """实际编码：生成比特流"""
        bits, distribution = self.forward(z)

        # 算术编码：利用概率分布压缩
        bitstream = arithmetic_encode(
            z.cpu().numpy(),
            distribution.mean.cpu().numpy(),
            distribution.stddev.cpu().numpy()
        )

        return bitstream  # 二进制数据


class WeightEntropyModel(nn.Module):
    """为网络权重编码/解码"""

    def forward(self, weights):
        """
        假设权重来自高斯分布，学习其参数
        """
        # 统计权重分布
        weight_mean = weights.mean()
        weight_std = weights.std()

        # 计算比特成本
        distribution = Normal(weight_mean, weight_std)
        bits = -distribution.log_prob(weights) / np.log(2)

        return bits, distribution
```

---

## 🎯 如何修改代码进行你的实验

### 场景 1: 添加 Tokenizer 分支

**目标：** 在 NVRC 的输出上计算 `L_tok`

```python
# 在 compress_models/nvrc.py 中修改 forward()

from your_tokenizer import CLIPTokenizer  # 导入你的 tokenizer

class NVRC(nn.Module):
    def __init__(self, config):
        # ... 原有代码 ...
        self.tokenizer = CLIPTokenizer()  # 添加 tokenizer

    def forward(self, frames):
        # ... 原有代码（计算 recon） ...

        # 【新增】计算 tokenizer 一致性损失
        with torch.no_grad():  # tokenizer 冻结
            y = self.tokenizer(frames)      # (B, T, D)
            y_hat = self.tokenizer(recon)   # (B, T, D)

        loss_tok = F.mse_loss(y_hat, y)  # tokenizer 损失

        # 修改损失函数
        loss = (args.lambda_rate * loss_rate +
                args.lambda_rec * loss_recon +
                args.lambda_tok * loss_tok)

        return recon, {
            'recon': loss_recon,
            'rate': loss_rate,
            'tok': loss_tok,  # 新增
            'total': loss,
        }
```

---

### 场景 2: 修改 HiNeRV 架构

**目标：** 改进 INR 网络结构

```python
# 在 models/hinerv.py 中修改 HiNeRV 类

class HiNeRV(nn.Module):
    def __init__(self, dim_base=256, depth=6, **kwargs):
        # 原始架构
        self.pos_encoder = PositionalEncoding(...)
        self.mlp = nn.Sequential(...)

        # 【新增】添加额外的分支（例如）
        self.residual_branch = nn.Sequential(
            nn.Linear(pos_encoder.out_dim, dim_base),
            nn.ReLU(),
            nn.Linear(dim_base, 3),
        )

    def forward(self, t, h, w):
        pos_encoded = self.pos_encoder(t, h, w)

        # 主分支
        main_rgb = self.mlp(pos_encoded)

        # 【新增】残差分支
        residual = self.residual_branch(pos_encoded)

        # 合并
        rgb = main_rgb + 0.1 * residual

        return torch.sigmoid(rgb)
```

---

### 场景 3: 调整损失函数

**目标：** 从 MSE 改为 MS-SSIM

```python
# 在 compress_models/nvrc.py 或 losses.py 中

def forward(self, frames):
    # ... 编码/解码代码 ...

    # 替换损失函数
    from lpips import LPIPS

    # 方案 A: 使用 MS-SSIM（感知损失）
    loss_recon = 1 - ms_ssim(recon, frames)  # MS-SSIM 通常 0-1

    # 方案 B: 使用 LPIPS（学习感知损失）
    lpips_model = LPIPS(pretrained=True).eval()
    loss_recon = lpips_model(recon, frames).mean()

    # 方案 C: 混合损失
    loss_recon = 0.5 * F.mse_loss(recon, frames) + \
                 0.5 * lpips_model(recon, frames).mean()

    return recon, {...}
```

---

## 🔍 调试技巧

### 打印中间值

```python
# 在 forward() 中添加
def forward(self, frames):
    print(f"Input frames shape: {frames.shape}")  # (B, T, H, W, 3)

    z_encoder = self.encoder.encode(frames)
    print(f"Encoder output shape: {z_encoder.shape}")

    bits_encoder, _ = self.grid_em.encode(z_encoder)
    print(f"Bits per element: {bits_encoder.mean().item():.4f}")

    recon = self.decoder.decode(z_encoder)
    print(f"Reconstruction shape: {recon.shape}")
    print(f"Reconstruction loss: {F.mse_loss(recon, frames).item():.6f}")
```

---

### 保存中间激活

```python
# 用于分析 INR 是否学到有意义的特征
import torch

def save_activations(model, frames, save_dir="activations"):
    with torch.no_grad():
        # 钩子：捕获每层的输出
        activations = {}
        def hook(name):
            def _hook(m, inp, out):
                activations[name] = out.detach()
            return _hook

        for name, module in model.named_modules():
            if isinstance(module, nn.Linear):
                module.register_forward_hook(hook(name))

        model(frames)

        # 保存
        for name, act in activations.items():
            print(f"{name}: {act.shape}, range [{act.min():.3f}, {act.max():.3f}]")
```

---

## 📊 关键数据流总结

```
【输入】RGB 视频 (1, 360, 1080, 1920, 3)
  ↓
【HiNeRV 编码】
  - 训练优化：找参数 θ 使 f_θ(x,y,t) ≈ RGB[t,y,x]
  - 输出：θ 的参数集合
  ↓
【参数量化+熵编码】
  - 将 θ 量化为低精度
  - 用熵模型压缩：θ → bits
  ↓
【重建】
  - 恢复 θ'（可能有量化误差）
  - HiNeRV 解码：f_{θ'}(x,y,t) → RGB[t,y,x]
  - 输出：重建视频 (1, 360, 1080, 1920, 3)
  ↓
【评估】
- PSNR(原, 重建)
- MS-SSIM(原, 重建)
- 压缩率 = 原大小 / 比特流大小
- L_tok = ||tokenizer(原) - tokenizer(重建)||²
```

---

**现在你应该理解 NVRC 的整个流程了！准备好修改代码实现你的 tokenizer 分支吗？**
