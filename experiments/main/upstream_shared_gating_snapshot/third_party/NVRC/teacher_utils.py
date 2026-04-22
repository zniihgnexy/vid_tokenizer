from pathlib import Path

import torch
import torch.nn as nn
import torch.nn.functional as F


_DINOV2_REPO = Path.home() / ".cache" / "torch" / "hub" / "facebookresearch_dinov2_main"
_DINOV2_CHECKPOINT_DIR = Path.home() / ".cache" / "torch" / "hub" / "checkpoints"
_DINOV2_CHECKPOINTS = {
    "dinov2_vits14_reg": "dinov2_vits14_reg4_pretrain.pth",
    "dinov2_vitb14_reg": "dinov2_vitb14_reg4_pretrain.pth",
}


def _load_local_dinov2_backbone(model_name):
    if model_name not in _DINOV2_CHECKPOINTS:
        raise ValueError(f"Unsupported local DINOv2 teacher_type: {model_name}")
    if not _DINOV2_REPO.exists():
        raise FileNotFoundError(
            f"Expected local DINOv2 hub repo at {_DINOV2_REPO}, but it was not found."
        )

    checkpoint_path = _DINOV2_CHECKPOINT_DIR / _DINOV2_CHECKPOINTS[model_name]
    if not checkpoint_path.exists():
        raise FileNotFoundError(
            f"Expected cached DINOv2 checkpoint at {checkpoint_path}, but it was not found."
        )

    backbone = torch.hub.load(str(_DINOV2_REPO), model_name, source="local", pretrained=True)
    backbone.eval()
    for param in backbone.parameters():
        param.requires_grad = False
    return backbone


class FrozenTeacherAdapter(nn.Module):
    def __init__(self, teacher_type='mean_pool', detach_target=True):
        super().__init__()
        self.teacher_type = teacher_type
        self.detach_target = detach_target
        self._function_readout_cache = {}

        if self.teacher_type == 'mean_pool':
            self.backbone = None
        elif self.teacher_type == 'resnet18_imagenet':
            from torchvision.models import ResNet18_Weights, resnet18

            backbone = resnet18(weights=ResNet18_Weights.DEFAULT)
            backbone.fc = nn.Identity()
            backbone.eval()
            for param in backbone.parameters():
                param.requires_grad = False

            self.backbone = backbone
            self._register_imagenet_norm_buffers()
        elif self.teacher_type in _DINOV2_CHECKPOINTS:
            self.backbone = _load_local_dinov2_backbone(self.teacher_type)
            self._register_imagenet_norm_buffers()
        else:
            raise ValueError(f'Unknown teacher_type: {self.teacher_type}')

    def _register_imagenet_norm_buffers(self):
        self.register_buffer(
            'norm_mean',
            torch.tensor([0.485, 0.456, 0.406], dtype=torch.float32).view(1, 3, 1, 1),
        )
        self.register_buffer(
            'norm_std',
            torch.tensor([0.229, 0.224, 0.225], dtype=torch.float32).view(1, 3, 1, 1),
        )

    def extract_features(self, x):
        assert x.ndim == 5, 'inputs are expected to have 5D ([N, C, T, H, W])'
        if self.teacher_type == 'mean_pool':
            return x.float().mean(dim=(3, 4)).permute(0, 2, 1).contiguous()
        if self.teacher_type == 'resnet18_imagenet':
            return self._extract_resnet18_features(x)
        if self.teacher_type in _DINOV2_CHECKPOINTS:
            return self._extract_dinov2_features(x)
        raise ValueError(f'Unknown teacher_type: {self.teacher_type}')

    def target_features(self, target):
        if self.detach_target:
            with torch.no_grad():
                return self.extract_features(target)
        return self.extract_features(target)

    def consistency_features(self, pred, target):
        pred_feat = self.extract_features(pred)
        target_feat = self.target_features(target)
        return pred_feat, target_feat

    def temporal_deltas(self, features):
        n, t, _ = features.shape
        if t <= 1:
            return torch.zeros_like(features)

        deltas = features[:, 1:] - features[:, :-1]
        return torch.cat([deltas[:, :1], deltas], dim=1)

    def temporal_delta_consistency_features(self, pred=None, target=None, pred_feat=None, target_feat=None):
        if pred_feat is None or target_feat is None:
            pred_feat, target_feat = self.consistency_features(pred, target)
        pred_delta = self.temporal_deltas(pred_feat)
        target_delta = self.temporal_deltas(target_feat)
        return pred_delta, target_delta

    def relation_matrix(self, features, mode='cosine', eps=1e-6):
        if mode == 'cosine':
            normalized = F.normalize(features, dim=2, eps=eps)
            return torch.matmul(normalized, normalized.transpose(1, 2))
        if mode == 'l2':
            distances = torch.cdist(features, features, p=2)
            scale = distances.mean(dim=(1, 2), keepdim=True).clamp_min(eps)
            return distances / scale
        raise ValueError(f'Unknown relation mode: {mode}')

    def relation_consistency_features(self, pred=None, target=None, mode='cosine', pred_feat=None, target_feat=None):
        if pred_feat is None or target_feat is None:
            pred_feat, target_feat = self.consistency_features(pred, target)
        pred_rel = self.relation_matrix(pred_feat, mode=mode)
        target_rel = self.relation_matrix(target_feat, mode=mode)
        return pred_rel, target_rel

    def fit_semantic_blueprint(self, target=None, rank=16, target_feat=None):
        if target_feat is None:
            assert target is not None, 'target or target_feat must be provided'
            target_feat = self.target_features(target)

        target_feat = target_feat.detach()
        _, t, f = target_feat.shape
        rank = max(int(rank), 1)
        rank = min(rank, max(min(t, f), 1))

        center = target_feat.mean(dim=1, keepdim=True)
        centered = target_feat - center
        _, _, vh = torch.linalg.svd(centered, full_matrices=False)
        basis = vh[:, :rank, :].contiguous()
        target_blueprint = torch.matmul(centered, basis.transpose(1, 2))

        return {
            'center': center,
            'basis': basis,
            'rank': rank,
            'target_blueprint': target_blueprint,
        }

    def project_semantic_blueprint(self, features, blueprint):
        center = blueprint['center'].to(features.device)
        basis = blueprint['basis'].to(features.device)
        centered = features - center
        return torch.matmul(centered, basis.transpose(1, 2))

    def blueprint_consistency_features(self, pred=None, target=None, rank=16, pred_feat=None, target_feat=None):
        if pred_feat is None or target_feat is None:
            pred_feat, target_feat = self.consistency_features(pred, target)

        blueprint = self.fit_semantic_blueprint(target_feat=target_feat, rank=rank)
        pred_blueprint = self.project_semantic_blueprint(pred_feat, blueprint)
        target_blueprint = blueprint['target_blueprint']
        return pred_blueprint, target_blueprint, blueprint

    def _function_readout_bank_params(self, feature_dim, bank_size, hidden_dim, out_dim, seed, device, dtype):
        key = (
            int(feature_dim),
            int(bank_size),
            int(hidden_dim),
            int(out_dim),
            int(seed),
            str(device),
            str(dtype),
        )
        if key not in self._function_readout_cache:
            generator = torch.Generator(device='cpu')
            generator.manual_seed(int(seed))

            w1 = torch.randn(bank_size, feature_dim, hidden_dim, generator=generator, dtype=torch.float32)
            b1 = 0.05 * torch.randn(bank_size, hidden_dim, generator=generator, dtype=torch.float32)
            w2 = torch.randn(bank_size, hidden_dim, out_dim, generator=generator, dtype=torch.float32)
            b2 = 0.05 * torch.randn(bank_size, out_dim, generator=generator, dtype=torch.float32)

            w1 = F.normalize(w1, dim=1)
            w2 = F.normalize(w2, dim=1)

            self._function_readout_cache[key] = tuple(
                tensor.to(device=device, dtype=dtype) for tensor in (w1, b1, w2, b2)
            )
        return self._function_readout_cache[key]

    def _apply_function_readout_bank(self, features, bank_size=4, hidden_dim=64, out_dim=16, seed=0):
        bank_size = max(int(bank_size), 1)
        hidden_dim = max(int(hidden_dim), 1)
        out_dim = max(int(out_dim), 1)

        features = F.layer_norm(features, (features.shape[-1],))
        w1, b1, w2, b2 = self._function_readout_bank_params(
            feature_dim=features.shape[-1],
            bank_size=bank_size,
            hidden_dim=hidden_dim,
            out_dim=out_dim,
            seed=seed,
            device=features.device,
            dtype=features.dtype,
        )
        hidden = torch.einsum('ntf,bfh->ntbh', features, w1) + b1.view(1, 1, bank_size, hidden_dim)
        hidden = F.gelu(hidden)
        return torch.einsum('ntbh,bho->ntbo', hidden, w2) + b2.view(1, 1, bank_size, out_dim)

    def function_readout_consistency_features(
        self,
        pred=None,
        target=None,
        bank_size=4,
        hidden_dim=64,
        out_dim=16,
        seed=0,
        seeds=None,
        pred_feat=None,
        target_feat=None,
    ):
        if pred_feat is None or target_feat is None:
            pred_feat, target_feat = self.consistency_features(pred, target)

        if isinstance(seeds, str):
            seeds = [int(item.strip()) for item in seeds.split(',') if item.strip()]
        elif seeds is not None:
            seeds = [int(item) for item in seeds]
        else:
            seeds = []

        if seeds:
            pred_readout = torch.cat([
                self._apply_function_readout_bank(
                    pred_feat,
                    bank_size=bank_size,
                    hidden_dim=hidden_dim,
                    out_dim=out_dim,
                    seed=current_seed,
                )
                for current_seed in seeds
            ], dim=2)
            target_readout = torch.cat([
                self._apply_function_readout_bank(
                    target_feat,
                    bank_size=bank_size,
                    hidden_dim=hidden_dim,
                    out_dim=out_dim,
                    seed=current_seed,
                )
                for current_seed in seeds
            ], dim=2)
        else:
            pred_readout = self._apply_function_readout_bank(
                pred_feat,
                bank_size=bank_size,
                hidden_dim=hidden_dim,
                out_dim=out_dim,
                seed=seed,
            )
            target_readout = self._apply_function_readout_bank(
                target_feat,
                bank_size=bank_size,
                hidden_dim=hidden_dim,
                out_dim=out_dim,
                seed=seed,
            )
        return pred_readout, target_readout

    def _prepare_imagenet_frames(self, x, teacher_label):
        assert x.shape[1] == 3, f'{teacher_label} expects RGB inputs'
        n, c, t, h, w = x.shape
        frames = x.float().permute(0, 2, 1, 3, 4).reshape(n * t, c, h, w)
        frames = frames.clamp(0.0, 1.0)
        frames = F.interpolate(frames, size=(224, 224), mode='bilinear', align_corners=False)

        self.backbone.to(frames.device)
        self.backbone.eval()

        norm_mean = self.norm_mean.to(frames.device)
        norm_std = self.norm_std.to(frames.device)
        frames = (frames - norm_mean) / norm_std
        return n, t, frames

    def _extract_resnet18_features(self, x):
        n, t, frames = self._prepare_imagenet_frames(x, 'resnet18_imagenet')
        features = self.backbone(frames)
        return features.view(n, t, -1).contiguous()

    def _extract_dinov2_features(self, x):
        n, t, frames = self._prepare_imagenet_frames(x, self.teacher_type)
        features = self.backbone(frames)
        return features.view(n, t, -1).contiguous()

    def consistency_map(self, pred, target, pred_feat=None, target_feat=None):
        if pred_feat is None or target_feat is None:
            pred_feat, target_feat = self.consistency_features(pred, target)
        return F.mse_loss(pred_feat, target_feat, reduction='none').mean(dim=2)

    def semantic_change_weights(self, target=None, floor=0.25, gamma=1.0, eps=1e-6, target_feat=None):
        if target_feat is None:
            assert target is not None, 'target or target_feat must be provided'
            target_feat = self.target_features(target)

        n, t, _ = target_feat.shape
        if t <= 1:
            return torch.ones((n, t), dtype=target_feat.dtype, device=target_feat.device)

        deltas = F.mse_loss(target_feat[:, 1:], target_feat[:, :-1], reduction='none').mean(dim=2)
        deltas = torch.cat([deltas[:, :1], deltas], dim=1).clamp_min(eps)
        weights = deltas / (deltas.mean(dim=1, keepdim=True) + eps)

        gamma = max(float(gamma), 0.0)
        if gamma != 1.0:
            weights = weights.clamp_min(eps).pow(gamma)

        floor = min(max(float(floor), 0.0), 1.0)
        if floor > 0.0:
            weights = floor + (1.0 - floor) * weights

        return weights / (weights.mean(dim=1, keepdim=True) + eps)


def build_teacher_adapter(enable=False, teacher_type='mean_pool', detach_target=True):
    if not enable:
        return None
    return FrozenTeacherAdapter(teacher_type=teacher_type, detach_target=detach_target)
