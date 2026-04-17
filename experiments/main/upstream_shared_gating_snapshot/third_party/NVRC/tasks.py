from utils import *
from io_utils import *
from losses import *
from teacher_utils import build_teacher_adapter


def _parse_int_list(value):
    if value is None:
        return tuple()
    if isinstance(value, str):
        items = [item.strip() for item in value.split(',') if item.strip()]
        return tuple(int(item) for item in items)
    if isinstance(value, (list, tuple)):
        return tuple(int(item) for item in value)
    return (int(value),)


class OverfitTask:
    def __init__(self, logger, video, loss_cfg, metric_cfg, lamb,
                 channel_scale=None, channel_shift=None,
                 enable_log=True, training=True, device=None,
                 teacher_enable=False, teacher_type='mean_pool',
                 teacher_loss_weight=0.0, teacher_detach_target=True,
                 teacher_semantic_blueprint=False,
                 teacher_semantic_blueprint_rank=16,
                 teacher_relation_consistency=False,
                 teacher_relation_mode='cosine',
                 teacher_relation_weight=1.0,
                 teacher_temporal_delta_consistency=False,
                 teacher_temporal_delta_weight=1.0,
                 teacher_temporal_delta_semantic_gating=False,
                 teacher_semantic_change_weighting=False,
                 teacher_semantic_change_floor=0.25,
                 teacher_semantic_change_gamma=1.0,
                 teacher_pred_variance_weight=0.0,
                 teacher_pred_variance_margin=0.1,
                 teacher_pred_delta_variance_weight=0.0,
                 teacher_pred_delta_variance_margin=0.1,
                 teacher_function_readout_consistency=False,
                 teacher_function_readout_weight=1.0,
                 teacher_function_readout_bank_size=4,
                 teacher_function_readout_hidden_dim=64,
                 teacher_function_readout_out_dim=16,
                 teacher_function_readout_seed=0,
                 teacher_function_readout_seeds=''):
        self.logger = logger
        self.video = video
        self.channels = self.video.get_num_channels()

        self.loss_cfg = [1.0, loss_cfg[0]] if len(loss_cfg) == 1 else loss_cfg
        self.metric_cfg = metric_cfg

        assert channel_scale is None or channel_shift is None or \
            (len(channel_scale) == self.channels and len(channel_shift) == self.channels)
        self.channel_scale, self.channel_shift = \
            compute_scale_shift(self.channels, self.video.get_bit_depth(), channel_scale, channel_shift)

        self.enable_log = enable_log
        self.training = training
        self.device = device
        self.metrics_buffer = {}
        self.teacher_enable = teacher_enable
        self.teacher_type = teacher_type
        self.teacher_loss_weight = float(teacher_loss_weight)
        self.teacher_detach_target = teacher_detach_target
        self.teacher_semantic_blueprint = teacher_semantic_blueprint
        self.teacher_semantic_blueprint_rank = int(teacher_semantic_blueprint_rank)
        self.teacher_relation_consistency = teacher_relation_consistency
        self.teacher_relation_mode = teacher_relation_mode
        self.teacher_relation_weight = float(teacher_relation_weight)
        self.teacher_temporal_delta_consistency = teacher_temporal_delta_consistency
        self.teacher_temporal_delta_weight = float(teacher_temporal_delta_weight)
        self.teacher_temporal_delta_semantic_gating = teacher_temporal_delta_semantic_gating
        self.teacher_semantic_change_weighting = teacher_semantic_change_weighting
        self.teacher_semantic_change_floor = float(teacher_semantic_change_floor)
        self.teacher_semantic_change_gamma = float(teacher_semantic_change_gamma)
        self.teacher_pred_variance_weight = float(teacher_pred_variance_weight)
        self.teacher_pred_variance_margin = float(teacher_pred_variance_margin)
        self.teacher_pred_delta_variance_weight = float(teacher_pred_delta_variance_weight)
        self.teacher_pred_delta_variance_margin = float(teacher_pred_delta_variance_margin)
        self.teacher_function_readout_consistency = teacher_function_readout_consistency
        self.teacher_function_readout_weight = float(teacher_function_readout_weight)
        self.teacher_function_readout_bank_size = int(teacher_function_readout_bank_size)
        self.teacher_function_readout_hidden_dim = int(teacher_function_readout_hidden_dim)
        self.teacher_function_readout_out_dim = int(teacher_function_readout_out_dim)
        self.teacher_function_readout_seed = int(teacher_function_readout_seed)
        self.teacher_function_readout_seeds = _parse_int_list(teacher_function_readout_seeds)
        self.teacher_adapter = build_teacher_adapter(
            enable=self.teacher_enable,
            teacher_type=self.teacher_type,
            detach_target=self.teacher_detach_target,
        )
        if self.teacher_adapter is not None and self.device is not None:
            self.teacher_adapter = self.teacher_adapter.to(self.device)

        if isinstance(lamb, (int, float)):
            lamb_values = [float(lamb)]
        else:
            assert isinstance(lamb, (list, tuple)) and len(lamb) == 1, \
                'lamb should be a scalar or a list/tuple with a single value'
            lamb_values = [float(v) for v in lamb]
        self.lamb = torch.tensor(sorted(lamb_values), dtype=torch.float32, device=self.device)

        logger.info(f'OverfitTask:')
        logger.info(f'     Root: {self.video.get_path()}')
        logger.info(f'     Training: {self.training}')
        logger.info(f'     Losses: {self.loss_cfg}    Metrics: {self.metric_cfg}')
        logger.info(f'     Lamb: {self.lamb.tolist()}')
        logger.info(f'     Enable log: {self.enable_log}')
        if self.teacher_enable:
            logger.info(
                f'     Teacher: enabled={self.teacher_enable} type={self.teacher_type} '
                f'weight={self.teacher_loss_weight:.4f} detach_target={self.teacher_detach_target} '
                f'semantic_blueprint={self.teacher_semantic_blueprint} '
                f'semantic_blueprint_rank={self.teacher_semantic_blueprint_rank} '
                f'relation_consistency={self.teacher_relation_consistency} '
                f'relation_mode={self.teacher_relation_mode} '
                f'relation_weight={self.teacher_relation_weight:.4f} '
                f'temporal_delta_consistency={self.teacher_temporal_delta_consistency} '
                f'temporal_delta_weight={self.teacher_temporal_delta_weight:.4f} '
                f'temporal_delta_semantic_gating={self.teacher_temporal_delta_semantic_gating} '
                f'semantic_change_weighting={self.teacher_semantic_change_weighting} '
                f'semantic_change_floor={self.teacher_semantic_change_floor:.4f} '
                f'semantic_change_gamma={self.teacher_semantic_change_gamma:.4f} '
                f'pred_variance_weight={self.teacher_pred_variance_weight:.4f} '
                f'pred_variance_margin={self.teacher_pred_variance_margin:.4f} '
                f'pred_delta_variance_weight={self.teacher_pred_delta_variance_weight:.4f} '
                f'pred_delta_variance_margin={self.teacher_pred_delta_variance_margin:.4f} '
                f'function_readout_consistency={self.teacher_function_readout_consistency} '
                f'function_readout_weight={self.teacher_function_readout_weight:.4f} '
                f'function_readout_bank_size={self.teacher_function_readout_bank_size} '
                f'function_readout_hidden_dim={self.teacher_function_readout_hidden_dim} '
                f'function_readout_out_dim={self.teacher_function_readout_out_dim} '
                f'function_readout_seed={self.teacher_function_readout_seed} '
                f'function_readout_seeds={list(self.teacher_function_readout_seeds) if self.teacher_function_readout_seeds else []}'
            )

    def get_metrics(self):
        return self.metric_cfg

    def get_video_size(self):
        return tuple(v + sum(p) for v, p in zip(self.video.get_video_size(), self.video.get_padding()))

    def get_patch_size(self):
        return self.video.get_patch_size()

    def get_start_frame(self):
        return self.video.get_start_frame()

    def get_num_frames(self):
        return self.video.get_num_frames()

    def set_frames(self, start_frame, num_frames):
        self.video.set_frames(start_frame, num_frames)

    def create_cache(self):
        self.video.create_cache(enable=self.enable_log)

    def parse_batch(self, batch):
        """
        Parse the input and output batch during training/evaluation step
        """
        idx, x = batch
        idx_max = self.video.get_idx_max()
        assert idx.ndim == 2, \
            'idx should have 2 dimensions with shape [N, 3], where each row is the 3D patch coordinate'
        assert x.ndim == 5,  \
            'x should have 5 dimensions with shape [N, C, T, H, W], where each sample is a 3D patch'

        inputs = {
            'vidx': torch.zeros(idx.shape[0], dtype=torch.int32, device=idx.device),
            'vidx_max': 1,
            'idx': idx,
            'idx_max': idx_max,
            'x': x if self.training else None,
            'lamb': self.lamb,
            'rp': None,
            'rel_batch_size': x.shape[0] * x.shape[2] * \
                math.prod(self.get_patch_size()[1:]) / math.prod(self.get_video_size()[1:]),
            'video_size': (self.get_num_frames(),) + self.get_video_size()[1:],
            'patch_size': self.get_patch_size(),
            'channels': self.video.get_num_channels()
        }

        return inputs, x

    def parse_output(self, output):
        """
        Parse the output from the model during training/evaluation step
        """
        return output.contiguous()

    def variance_floor_penalty(self, features, margin):
        flat_features = features.reshape(-1, features.shape[-1])
        if flat_features.shape[0] <= 1:
            return flat_features.new_zeros(())
        channel_std = torch.sqrt(flat_features.var(dim=0, unbiased=False) + 1e-6)
        return F.relu(float(margin) - channel_std).mean()

    def compute_d_loss(self, x, y, lamb):
        loss = 0.
        for i in range(len(self.loss_cfg) // 2):
            weight = float(self.loss_cfg[i * 2])
            loss_type = self.loss_cfg[i * 2 + 1]
            loss += weight * lamb * compute_loss(loss_type, x, y).mean()
        if self.teacher_adapter is not None and self.teacher_loss_weight > 0:
            pred_feat, target_feat = self.teacher_adapter.consistency_features(x, y)
            loss_pred_feat = pred_feat
            loss_target_feat = target_feat
            teacher_weights = None

            if self.teacher_semantic_blueprint:
                loss_pred_feat, loss_target_feat, _ = self.teacher_adapter.blueprint_consistency_features(
                    pred_feat=pred_feat,
                    target_feat=target_feat,
                    rank=self.teacher_semantic_blueprint_rank,
                )

            teacher_consistency = F.mse_loss(loss_pred_feat, loss_target_feat, reduction='none').mean(dim=2)
            if self.teacher_semantic_change_weighting:
                teacher_weights = self.teacher_adapter.semantic_change_weights(
                    floor=self.teacher_semantic_change_floor,
                    gamma=self.teacher_semantic_change_gamma,
                    target_feat=target_feat,
                )
                teacher_consistency = teacher_consistency * teacher_weights
            loss += self.teacher_loss_weight * lamb * teacher_consistency.mean()
            if self.teacher_pred_variance_weight > 0:
                pred_variance_penalty = self.variance_floor_penalty(
                    pred_feat,
                    margin=self.teacher_pred_variance_margin,
                )
                loss += (
                    self.teacher_loss_weight
                    * self.teacher_pred_variance_weight
                    * lamb
                    * pred_variance_penalty
                )
            pred_delta = None
            target_delta = None
            if self.teacher_pred_delta_variance_weight > 0 or self.teacher_temporal_delta_consistency:
                pred_delta, target_delta = self.teacher_adapter.temporal_delta_consistency_features(
                    pred_feat=pred_feat,
                    target_feat=target_feat,
                )
            if self.teacher_pred_delta_variance_weight > 0:
                pred_delta_variance_penalty = self.variance_floor_penalty(
                    pred_delta,
                    margin=self.teacher_pred_delta_variance_margin,
                )
                loss += (
                    self.teacher_loss_weight
                    * self.teacher_pred_delta_variance_weight
                    * lamb
                    * pred_delta_variance_penalty
                )
            if self.teacher_function_readout_consistency:
                pred_readout, target_readout = self.teacher_adapter.function_readout_consistency_features(
                    pred_feat=pred_feat,
                    target_feat=target_feat,
                    bank_size=self.teacher_function_readout_bank_size,
                    hidden_dim=self.teacher_function_readout_hidden_dim,
                    out_dim=self.teacher_function_readout_out_dim,
                    seed=self.teacher_function_readout_seed,
                    seeds=self.teacher_function_readout_seeds,
                )
                function_readout_consistency = F.mse_loss(pred_readout, target_readout, reduction='none')
                function_readout_consistency = function_readout_consistency.mean(dim=3).mean(dim=2)
                loss += (
                    self.teacher_loss_weight
                    * self.teacher_function_readout_weight
                    * lamb
                    * function_readout_consistency.mean()
                )
            if self.teacher_relation_consistency:
                pred_rel, target_rel = self.teacher_adapter.relation_consistency_features(
                    pred_feat=pred_feat,
                    target_feat=target_feat,
                    mode=self.teacher_relation_mode,
                )
                relation_consistency = F.mse_loss(pred_rel, target_rel, reduction='none').mean(dim=(1, 2))
                loss += self.teacher_loss_weight * self.teacher_relation_weight * lamb * relation_consistency.mean()
            if self.teacher_temporal_delta_consistency:
                temporal_delta_consistency = F.mse_loss(pred_delta, target_delta, reduction='none').mean(dim=2)
                if (
                    self.teacher_temporal_delta_semantic_gating
                    and self.teacher_semantic_change_weighting
                    and teacher_weights is not None
                ):
                    temporal_delta_consistency = temporal_delta_consistency * teacher_weights
                loss += self.teacher_loss_weight * self.teacher_temporal_delta_weight * lamb * temporal_delta_consistency.mean()
        return loss

    def compute_r_loss(self, r):
        return r

    def compute_metrics(self, x, y):
        metrics = {}
        with torch.no_grad():
            for metric_type in self.metric_cfg:
                metrics[metric_type] = compute_metric(metric_type, x, y, teacher_adapter=self.teacher_adapter)
        return metrics

    def d_step(self, model, batch):   
        inputs, target = self.parse_batch(batch)
        output = model(inputs, compute_outputs=True, compute_rates=False)
        output = self.parse_output(output)
        loss = self.compute_d_loss(output, target, inputs['lamb'])
        metrics = self.compute_metrics(output, target)
        return inputs, target, output, loss, metrics

    def r_step(self, model, batch, sub_step=0, num_sub_steps=1):
        inputs, _ = self.parse_batch(batch)
        inputs['r_sub_step'] = sub_step
        inputs['r_num_sub_steps'] = num_sub_steps
        rate, rate_loss = model(inputs, compute_outputs=False, compute_rates=True)
        rate = rate / math.prod(inputs['video_size'])
        rate_loss = self.compute_r_loss(rate_loss / math.prod(inputs['video_size']))
        return rate, rate_loss

    def log_outputs(self, inputs, outputs, metrics):
        """
        Log the outputs
        """
        if self.enable_log:
            N, _, _, _, _ = outputs.shape
            idx = inputs['idx']
            outputs = outputs.detach()
            metrics = {k: v.detach() for k, v in metrics.items()}

            scale = self.channel_scale.to(outputs.device)
            shift = self.channel_shift.to(outputs.device)

            # Loop over all samples
            for n in range(N):
                # Save the patch
                if isinstance(self.video, PNGVideo):
                    self.video.write_patch(idx[n].cpu().numpy(),
                                           ((outputs[n] - shift.view(self.channels, 1, 1, 1)) \
                                            / scale.view(self.channels, 1, 1, 1)) \
                                           .permute(1, 2, 3, 0).round().cpu().numpy())
                else:
                    yuv420_patch = yuv444_to_yuv420(outputs[n].permute(1, 0, 2, 3), mode='avg_pool')
                    self.video.write_patch(idx[n].cpu().numpy(),
                                           [((patch_i - shift[i]) / scale[i]).round().cpu().numpy() \
                                            for i, patch_i in enumerate(yuv420_patch)])

                # Save the averge metrics for each patch
                idx_str = '(' + ' '.join([str(i) for i in idx[n].tolist()]) + ')'
                self.metrics_buffer[idx_str] = \
                    ','.join([idx_str] + \
                             [f'{k}: {v[n].mean().item():.4f}' for k, v in metrics.items() if k in self.metric_cfg])

    def flush(self, dir):
        """
        Flush the outputs to the disk
        """
        if self.enable_log:
            # Save video outputs
            self.video.flush(dir)

            # Save metrics
            with open(os.path.join(dir, 'metrics.txt'), 'w') as f:
                f.write('\n'.join(self.metrics_buffer.values()))
            self.metrics_buffer = {}


def create_overfit_task(args, logger, video, channel_scale=None, channel_shift=None, training=True, device=None):
    # Create task
    if training:
        config = args.train_task
    else:
        config = args.eval_task

    task = OverfitTask(logger, video, loss_cfg=config.loss, metric_cfg=config.metric,
                       lamb=config.lamb, channel_scale=channel_scale, channel_shift=channel_shift,
                       enable_log=config.enable_log, training=training, device=device,
                       teacher_enable=config.teacher_enable, teacher_type=config.teacher_type,
                       teacher_loss_weight=config.teacher_loss_weight,
                       teacher_detach_target=config.teacher_detach_target,
                       teacher_semantic_blueprint=config.teacher_semantic_blueprint,
                       teacher_semantic_blueprint_rank=config.teacher_semantic_blueprint_rank,
                       teacher_relation_consistency=config.teacher_relation_consistency,
                       teacher_relation_mode=config.teacher_relation_mode,
                       teacher_relation_weight=config.teacher_relation_weight,
                       teacher_temporal_delta_consistency=config.teacher_temporal_delta_consistency,
                       teacher_temporal_delta_weight=config.teacher_temporal_delta_weight,
                       teacher_temporal_delta_semantic_gating=config.teacher_temporal_delta_semantic_gating,
                       teacher_semantic_change_weighting=config.teacher_semantic_change_weighting,
                       teacher_semantic_change_floor=config.teacher_semantic_change_floor,
                       teacher_semantic_change_gamma=config.teacher_semantic_change_gamma,
                       teacher_pred_variance_weight=config.teacher_pred_variance_weight,
                       teacher_pred_variance_margin=config.teacher_pred_variance_margin,
                       teacher_pred_delta_variance_weight=config.teacher_pred_delta_variance_weight,
                       teacher_pred_delta_variance_margin=config.teacher_pred_delta_variance_margin,
                       teacher_function_readout_consistency=config.teacher_function_readout_consistency,
                       teacher_function_readout_weight=config.teacher_function_readout_weight,
                       teacher_function_readout_bank_size=config.teacher_function_readout_bank_size,
                       teacher_function_readout_hidden_dim=config.teacher_function_readout_hidden_dim,
                       teacher_function_readout_out_dim=config.teacher_function_readout_out_dim,
                       teacher_function_readout_seed=config.teacher_function_readout_seed,
                       teacher_function_readout_seeds=config.teacher_function_readout_seeds)
    return task
