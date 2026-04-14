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


def parse_int_list(value):
    if not value:
        return tuple()
    return tuple(int(item.strip()) for item in value.split(',') if item.strip())


def parse_args():
    parser = argparse.ArgumentParser(description='Smoke test the NVRC teacher-loss path.')
    parser.add_argument('--teacher-type', type=str, default='mean_pool',
                        help='Teacher adapter type to validate.')
    parser.add_argument('--semantic-blueprint', action='store_true',
                        help='Enable frozen semantic-blueprint supervision during the teacher-loss smoke.')
    parser.add_argument('--semantic-blueprint-rank', type=int, default=16,
                        help='Low-rank dimension used by the frozen semantic-blueprint target.')
    parser.add_argument('--relation-consistency', action='store_true',
                        help='Enable relation-preserving supervision during the teacher-loss smoke.')
    parser.add_argument('--relation-mode', type=str, default='cosine',
                        help='Relation mode used by relation-consistency supervision.')
    parser.add_argument('--relation-weight', type=float, default=1.0,
                        help='Relative auxiliary weight used by relation-consistency supervision.')
    parser.add_argument('--temporal-delta-consistency', action='store_true',
                        help='Enable temporal-delta supervision during the teacher-loss smoke.')
    parser.add_argument('--temporal-delta-weight', type=float, default=1.0,
                        help='Relative auxiliary weight used by temporal-delta supervision.')
    parser.add_argument('--temporal-delta-semantic-gating', action='store_true',
                        help='Share semantic-change weights with temporal-delta supervision during the teacher-loss smoke.')
    parser.add_argument('--semantic-change-weighting', action='store_true',
                        help='Enable semantic-change weighting during the teacher-loss smoke.')
    parser.add_argument('--semantic-change-floor', type=float, default=0.25,
                        help='Minimum normalized floor used by semantic-change weighting.')
    parser.add_argument('--semantic-change-gamma', type=float, default=1.0,
                        help='Power-law gain applied to semantic-change weights.')
    parser.add_argument('--function-readout-consistency', action='store_true',
                        help='Enable frozen function-readout supervision during the teacher-loss smoke.')
    parser.add_argument('--function-readout-weight', type=float, default=1.0,
                        help='Relative auxiliary weight used by function-readout supervision.')
    parser.add_argument('--function-readout-bank-size', type=int, default=4,
                        help='Number of frozen readout heads used by function-readout supervision.')
    parser.add_argument('--function-readout-hidden-dim', type=int, default=64,
                        help='Hidden dimension of each frozen readout head.')
    parser.add_argument('--function-readout-out-dim', type=int, default=16,
                        help='Output dimension of each frozen readout head.')
    parser.add_argument('--function-readout-seed', type=int, default=0,
                        help='Seed used to build the frozen function-readout bank.')
    parser.add_argument('--function-readout-seeds', type=str, default='',
                        help='Comma-separated list of seeds used to build a multi-seed frozen function-readout ensemble.')
    return parser.parse_args()


def main():
    args = parse_args()
    function_readout_seeds = parse_int_list(args.function_readout_seeds)

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
        teacher_semantic_blueprint=args.semantic_blueprint,
        teacher_semantic_blueprint_rank=args.semantic_blueprint_rank,
        teacher_relation_consistency=args.relation_consistency,
        teacher_relation_mode=args.relation_mode,
        teacher_relation_weight=args.relation_weight,
        teacher_temporal_delta_consistency=args.temporal_delta_consistency,
        teacher_temporal_delta_weight=args.temporal_delta_weight,
        teacher_temporal_delta_semantic_gating=args.temporal_delta_semantic_gating,
        teacher_semantic_change_weighting=args.semantic_change_weighting,
        teacher_semantic_change_floor=args.semantic_change_floor,
        teacher_semantic_change_gamma=args.semantic_change_gamma,
        teacher_function_readout_consistency=args.function_readout_consistency,
        teacher_function_readout_weight=args.function_readout_weight,
        teacher_function_readout_bank_size=args.function_readout_bank_size,
        teacher_function_readout_hidden_dim=args.function_readout_hidden_dim,
        teacher_function_readout_out_dim=args.function_readout_out_dim,
        teacher_function_readout_seed=args.function_readout_seed,
        teacher_function_readout_seeds=function_readout_seeds,
    )

    pred = torch.rand(2, 3, 4, 8, 8)
    target = torch.rand_like(pred)
    loss = task.compute_d_loss(pred, target, torch.tensor([1.0]))
    metrics = task.compute_metrics(pred, target)
    features = task.teacher_adapter.extract_features(pred)

    summary = {
        'run': 'teacher-loss-smoke',
        'teacher_type': args.teacher_type,
        'semantic_blueprint': args.semantic_blueprint,
        'relation_consistency': args.relation_consistency,
        'relation_mode': args.relation_mode,
        'relation_weight': args.relation_weight,
        'temporal_delta_consistency': args.temporal_delta_consistency,
        'temporal_delta_weight': args.temporal_delta_weight,
        'temporal_delta_semantic_gating': args.temporal_delta_semantic_gating,
        'semantic_change_weighting': args.semantic_change_weighting,
        'function_readout_consistency': args.function_readout_consistency,
        'function_readout_weight': args.function_readout_weight,
        'function_readout_seeds': list(function_readout_seeds),
        'loss_value': float(loss.item()),
        'feature_shape': list(features.shape),
        'teacher_mse_shape': list(metrics['teacher-mse'].shape),
        'psnr_shape': list(metrics['psnr'].shape),
    }
    if args.semantic_blueprint:
        pred_feat, target_feat = task.teacher_adapter.consistency_features(pred, target)
        pred_blueprint, target_blueprint, blueprint = task.teacher_adapter.blueprint_consistency_features(
            pred_feat=pred_feat,
            target_feat=target_feat,
            rank=args.semantic_blueprint_rank,
        )
        summary.update({
            'semantic_blueprint_rank': int(blueprint['rank']),
            'semantic_blueprint_basis_shape': list(blueprint['basis'].shape),
            'semantic_blueprint_target_shape': list(target_blueprint.shape),
            'semantic_blueprint_pred_shape': list(pred_blueprint.shape),
        })
    if args.semantic_change_weighting:
        weights = task.teacher_adapter.semantic_change_weights(
            target,
            floor=args.semantic_change_floor,
            gamma=args.semantic_change_gamma,
        )
        summary.update({
            'semantic_weight_shape': list(weights.shape),
            'semantic_weight_min': float(weights.min().item()),
            'semantic_weight_max': float(weights.max().item()),
            'semantic_weight_mean': float(weights.mean().item()),
            'semantic_weight_gamma': float(args.semantic_change_gamma),
        })
    if args.relation_consistency:
        pred_feat, target_feat = task.teacher_adapter.consistency_features(pred, target)
        pred_rel, target_rel = task.teacher_adapter.relation_consistency_features(
            pred_feat=pred_feat,
            target_feat=target_feat,
            mode=args.relation_mode,
        )
        summary.update({
            'relation_shape': list(pred_rel.shape),
            'relation_target_shape': list(target_rel.shape),
            'relation_min': float(pred_rel.min().item()),
            'relation_max': float(pred_rel.max().item()),
        })
    if args.temporal_delta_consistency:
        pred_feat, target_feat = task.teacher_adapter.consistency_features(pred, target)
        pred_delta, target_delta = task.teacher_adapter.temporal_delta_consistency_features(
            pred_feat=pred_feat,
            target_feat=target_feat,
        )
        summary.update({
            'temporal_delta_shape': list(pred_delta.shape),
            'temporal_delta_target_shape': list(target_delta.shape),
            'temporal_delta_abs_mean': float(pred_delta.abs().mean().item()),
            'temporal_delta_target_abs_mean': float(target_delta.abs().mean().item()),
        })
    if args.function_readout_consistency:
        pred_feat, target_feat = task.teacher_adapter.consistency_features(pred, target)
        pred_readout, target_readout = task.teacher_adapter.function_readout_consistency_features(
            pred_feat=pred_feat,
            target_feat=target_feat,
            bank_size=args.function_readout_bank_size,
            hidden_dim=args.function_readout_hidden_dim,
            out_dim=args.function_readout_out_dim,
            seed=args.function_readout_seed,
            seeds=function_readout_seeds,
        )
        summary.update({
            'function_readout_shape': list(pred_readout.shape),
            'function_readout_target_shape': list(target_readout.shape),
            'function_readout_abs_mean': float(pred_readout.abs().mean().item()),
            'function_readout_target_abs_mean': float(target_readout.abs().mean().item()),
            'function_readout_bank_size': int(args.function_readout_bank_size),
            'function_readout_hidden_dim': int(args.function_readout_hidden_dim),
            'function_readout_out_dim': int(args.function_readout_out_dim),
            'function_readout_seed': int(args.function_readout_seed),
            'function_readout_seeds': list(function_readout_seeds),
        })
    print(json.dumps(summary, indent=2))


if __name__ == '__main__':
    main()
