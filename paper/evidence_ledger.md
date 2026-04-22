# Paper Evidence Ledger

- Selected outline: `outline-002`
- Item count: `3`
- Updated at: `2026-04-22T07:35:00+00:00`

| Item | Kind | Section | Role | Status | Metrics | Source |
|---|---|---|---|---|---|---|
| `query_adaptive_teacher_anchor_arbitration_smoke_r1` | main_experiment | bounded-packet-adapter-evaluation | main_text | completed | query_adaptive_top1=0.15625; raw_global_top1=0.125; temporal_context_top1=0.09375; query_adaptive_hub_share=0.28125; raw_global_hub_share=0.59375 | `experiments/main/query_adaptive_teacher_anchor_arbitration_smoke_r1/RUN.md`, `experiments/main/query_adaptive_teacher_anchor_arbitration_smoke_r1/RESULT.json` |
| `query_adaptive_broader_retrieval_validation_smoke_r1` | analysis_result | outcome-interpretation-and-next-route | main_text | completed | query_adaptive_top1=0.125; raw_global_top1=0.10417; temporal_context_top1=0.10417; temporal_mean_rank=7.8125; query_adaptive_mean_rank=8.47917 | local comparator repair note and contract under the repaired broader three-bundle surface |
| `AC-01` | analysis_result | sec_teacher_anchor_adapter | appendix | completed | qb_norm_top1=0.0625; raw_top1=0.0625; qb_norm_max_anchor_share=0.25; raw_max_anchor_share=0.5 | `experiments/analysis-results/analysis-8e2b0428/chunked_16f_qbnorm_revalidation.md`, `experiments/analysis/chunked_16f_qbnorm_revalidation/report.md`, `experiments/analysis/chunked_16f_qbnorm_revalidation/summary.json` |

## query_adaptive_teacher_anchor_arbitration_smoke_r1

- Title: Query-adaptive teacher-anchor arbitration smoke on the widened multibundle surface
- Kind: `main_experiment`
- Section: `bounded-packet-adapter-evaluation`
- Role: `main_text`
- Status: `completed`
- Claims: `C1`, `C2`

### Setup

Reused the frozen widened two-bundle teacher-anchor packet interface and compared the new query-adaptive arbitration rule against the same raw-global and temporal predicted-chunk parent routes on the same bounded local surface.

### Result Summary

Positive bounded retrieval signal on the widened teacher-anchor surface: query-adaptive arbitration raised top1_accuracy to `0.15625` from raw-global `0.125` and temporal-context `0.09375`, matched the best-of-two oracle top1, and cut hub-cluster share from `0.59375` to `0.28125`.

### Claim Links

- `C1`: Query-adaptive arbitration improves headline retrieval top-1 accuracy on the bounded widened teacher-anchor surface.
- `C2`: The frozen teacher-anchor packet surface contains downstream-recoverable structure that static routing underuses on that same surface.

### Key Metrics

- `query_adaptive_raw_hub_risk_disagreement_teacher_anchor_to_target_feat_top1_accuracy`: `0.15625`
- `raw_global_bank_to_target_feat_top1_accuracy`: `0.125`
- `temporal_context_predicted_chunk_teacher_anchor_to_target_feat_top1_accuracy`: `0.09375`
- `query_adaptive_raw_hub_risk_disagreement_teacher_anchor_to_target_feat_hub_cluster_share_0009_0010_0011`: `0.28125`
- `raw_global_bank_to_target_feat_hub_cluster_share_0009_0010_0011`: `0.59375`

### Source Paths

- `experiments/main/query_adaptive_teacher_anchor_arbitration_smoke_r1/RUN.md`
- `experiments/main/query_adaptive_teacher_anchor_arbitration_smoke_r1/RESULT.json`

## query_adaptive_broader_retrieval_validation_smoke_r1

- Title: Repaired broader three-bundle validation for the query-adaptive route
- Kind: `analysis_result`
- Section: `outcome-interpretation-and-next-route`
- Role: `main_text`
- Status: `completed`
- Claims: `C1`, `C2`

### Setup

Reused the query-adaptive arbitration rule on a repaired legal three-bundle surface built from the relation-repair packet set, the blueprint-repair packet set, and one recovered chunked `16`-sample teacher-packet bundle, while keeping route definitions fixed.

### Result Summary

On the repaired broader surface, query-adaptive keeps the best non-oracle top-1 accuracy at `0.125`, while raw-global and temporal-context both sit at `0.10416666666666667`. The broader follow-up therefore preserves the headline advantage, but temporal-context still keeps the best `mean_match_rank` (`7.8125`) and `chunk_top1_accuracy` (`0.3333333333333333`), so the broader claim boundary remains intentionally partial.

### Claim Links

- `C1`: Query-adaptive keeps a headline top-1 edge on a repaired broader surface.
- `C2`: The packet surface still carries downstream-recoverable structure, but the broader follow-up shows that static temporal routing remains the harder guardrail on ranking diagnostics.

### Key Metrics

- `query_adaptive_raw_hub_risk_disagreement_teacher_anchor_to_target_feat_top1_accuracy`: `0.125`
- `raw_global_bank_to_target_feat_top1_accuracy`: `0.10416666666666667`
- `temporal_context_predicted_chunk_teacher_anchor_to_target_feat_top1_accuracy`: `0.10416666666666667`
- `query_adaptive_raw_hub_risk_disagreement_teacher_anchor_to_target_feat_mean_match_rank`: `8.479166666666666`
- `temporal_context_predicted_chunk_teacher_anchor_to_target_feat_mean_match_rank`: `7.8125`
- `query_adaptive_raw_hub_risk_disagreement_teacher_anchor_to_target_feat_chunk_top1_accuracy`: `0.25`
- `temporal_context_predicted_chunk_teacher_anchor_to_target_feat_chunk_top1_accuracy`: `0.3333333333333333`

### Source Paths

- `/home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/idea-idea-748a9357/baselines/local/querybank-teacher-anchor-broader-retrieval-local/verification.md`
- `/home/xinyizheng/vid_tokenizer/DeepScientist/quests/002/.ds/worktrees/idea-idea-748a9357/baselines/local/querybank-teacher-anchor-broader-retrieval-local/json/metric_contract.json`

## AC-01

- Title: Chunked 16-frame QB-Norm revalidation on the wider existing teacher-packet surface
- Kind: `analysis_result`
- Section: `sec_teacher_anchor_adapter`
- Role: `appendix`
- Status: `completed`
- Claims: `C2`

### Result Summary

QB-Norm regularized geometry on the wider surface but did not improve headline retrieval over the raw route, so it remains appendix-only robustness evidence rather than a claim-strengthening main-text result.
