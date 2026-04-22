# Quest Summary

- Updated at: 2026-04-22T07:54:29+00:00
- Branch: `paper/run-querybank-teacher-anchor-smoke-r1`
- Head: `eb64f29ae87bc07f7e305770cf5d1d30cc8b6887`

- Refresh reason: Refresh summary after successful paper bundle submission and post-registration route decision into review.

## Recent runs
- `shared_gating_pred_variance_repair_ego4d16f_smoke_r1`: Main experiment `shared_gating_pred_variance_repair_ego4d16f_smoke_r1` recorded on `run/shared_gating_pred_variance_repair_ego4d16f_smoke_r1`. uvg_bd_rate_reduction_pct_vs_vtm_ra_psnr=24 vs baseline 24 (Δ 0)
- `run-6be2f60b`: You've hit your usage limit. Upgrade to Pro (https://chatgpt.com/explore/pro), visit https://chatgpt.com/codex/settings/usage to purchase more credits or try again at Apr 15th, 2026 2:12 AM.
- `run-97ad0d37`: You've hit your usage limit. Upgrade to Pro (https://chatgpt.com/explore/pro), visit https://chatgpt.com/codex/settings/usage to purchase more credits or try again at 2:12 AM.
- `teacher_anchored_packet_adapter_smoke_r1`: Main experiment `teacher_anchored_packet_adapter_smoke_r1` recorded on `run/teacher_anchored_packet_adapter_smoke_r1`. uvg_bd_rate_reduction_pct_vs_vtm_ra_psnr=24 vs baseline 24 (Δ 0)
- `run-b1e1505b`: 我先把这次 quest 里已经做过的尝试梳理成一个短摘要。先读一下最近的对话上下文和当前全局状态，避免把已经降级或已经确认的结论说错。
我已经把主线压缩成几个最关键的尝试点了。接下来先把这个短摘要作为直接答复发给你，然后我再继续沿当前 idea 线推进。
- 先把已经验证过的压缩上游模块冻结下来，搭了第一版完整 downstream pipeline，用重建视频做最小 retrieval/matching 验证。
- 第一轮结果说明 pipeline 能跑通，但 `reconstructed video` 作为机器接口太弱，检索只有大约 `0.25` top-1，所以这条接口被降级。
- 接着转去试 `teacher/tokenizer feature packet` 接口，不再只依赖重建视频，而是直接把中间特征导给下游。
- 在 packet 路线上比较了 plain feature、temporal delta、delta-dominant 几种设计；其中 `delta-first` 最好，最好一版到过大约 `0.75` top-1。
- 然后把验证面稍微放宽，做了 `chunk-aware` 检查，结果发现这个优势没有稳住，指标又掉回接近随机。
- 进一步诊断后，问题被收紧到 `query-side collapse`：也就是区分信息很可能在 packet repair 之前就已经丢了，不只是聚合器的问题。
- 现在最新的主线是在做 `query collapse localization`，先定位信息到底在哪一层丢掉，再决定下一版 packet/interface 怎么改。

一句话版：我已经依次试了 `重建视频接口 -> teacher feature packet -> delta-first packet -> chunk-aware 扩展验证 -> query collapse 定位`，当前最清楚的结论是“链条能跑，但真正的瓶颈在 query 侧表征保持”。
