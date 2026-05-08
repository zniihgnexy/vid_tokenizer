import torch
import torch.nn as nn
import torch.nn.functional as F


class FrozenTeacherAdapter(nn.Module):
    def __init__(self, teacher_type='mean_pool', detach_target=True):
        super().__init__()
        self.teacher_type = teacher_type
        self.detach_target = detach_target

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
            self.register_buffer(
                'norm_mean',
                torch.tensor([0.485, 0.456, 0.406], dtype=torch.float32).view(1, 3, 1, 1),
            )
            self.register_buffer(
                'norm_std',
                torch.tensor([0.229, 0.224, 0.225], dtype=torch.float32).view(1, 3, 1, 1),
            )
        else:
            raise ValueError(f'Unknown teacher_type: {self.teacher_type}')

    def extract_features(self, x):
        assert x.ndim == 5, 'inputs are expected to have 5D ([N, C, T, H, W])'
        if self.teacher_type == 'mean_pool':
            return x.float().mean(dim=(3, 4)).permute(0, 2, 1).contiguous()
        if self.teacher_type == 'resnet18_imagenet':
            return self._extract_resnet18_features(x)
        raise ValueError(f'Unknown teacher_type: {self.teacher_type}')

    def _extract_resnet18_features(self, x):
        assert x.shape[1] == 3, 'resnet18_imagenet expects RGB inputs'

        n, c, t, h, w = x.shape
        frames = x.float().permute(0, 2, 1, 3, 4).reshape(n * t, c, h, w)
        frames = frames.clamp(0.0, 1.0)
        frames = F.interpolate(frames, size=(224, 224), mode='bilinear', align_corners=False)

        self.backbone.to(frames.device)
        self.backbone.eval()

        norm_mean = self.norm_mean.to(frames.device)
        norm_std = self.norm_std.to(frames.device)
        frames = (frames - norm_mean) / norm_std
        features = self.backbone(frames)
        return features.view(n, t, -1).contiguous()

    def consistency_map(self, pred, target):
        pred_feat = self.extract_features(pred)
        if self.detach_target:
            with torch.no_grad():
                target_feat = self.extract_features(target)
        else:
            target_feat = self.extract_features(target)
        return F.mse_loss(pred_feat, target_feat, reduction='none').mean(dim=2)


def build_teacher_adapter(enable=False, teacher_type='mean_pool', detach_target=True):
    if not enable:
        return None
    return FrozenTeacherAdapter(teacher_type=teacher_type, detach_target=detach_target)
