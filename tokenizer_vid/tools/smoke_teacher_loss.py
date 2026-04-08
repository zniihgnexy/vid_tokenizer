#!/usr/bin/env python3
import argparse
import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1] / 'third_party' / 'NVRC'
sys.path.insert(0, str(ROOT))

import torch

from tasks import OverfitTask


class NullLogger:
    def info(self, _message):
        return None


class DummyVideo:
    def get_num_channels(self):
        return 3

    def get_bit_depth(self):
        return 8

    def get_path(self):
        return 'synthetic://teacher-smoke'


def parse_args():
    parser = argparse.ArgumentParser(description='Smoke test the NVRC teacher-loss path.')
    parser.add_argument('--teacher-type', type=str, default='mean_pool',
                        help='Teacher adapter type to validate.')
    return parser.parse_args()


def main():
    args = parse_args()

    task = OverfitTask(
        logger=NullLogger(),
        video=DummyVideo(),
        loss_cfg=[1.0, 'l1'],
        metric_cfg=['psnr', 'teacher-mse'],
        lamb=[1.0],
        enable_log=False,
        training=True,
        device='cpu',
        teacher_enable=True,
        teacher_type=args.teacher_type,
        teacher_loss_weight=0.2,
        teacher_detach_target=True,
    )

    pred = torch.rand(2, 3, 4, 8, 8)
    target = torch.rand_like(pred)
    loss = task.compute_d_loss(pred, target, torch.tensor([1.0]))
    metrics = task.compute_metrics(pred, target)
    features = task.teacher_adapter.extract_features(pred)

    summary = {
        'run': 'teacher-loss-smoke',
        'teacher_type': args.teacher_type,
        'loss_value': float(loss.item()),
        'feature_shape': list(features.shape),
        'teacher_mse_shape': list(metrics['teacher-mse'].shape),
        'psnr_shape': list(metrics['psnr'].shape),
    }
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
