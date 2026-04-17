# Status
Baseline reuse is already resolved: `nvrc-local-source` remains the accepted upstream asset.

Current stage: `experiment_prep`

Current judgment:
- The active child line is `Querybank-Normalized Teacher-Anchor Packet Interface After Hubness Diagnosis`.
- The current widened failure is treated as retrieval-time teacher-anchor hub collapse, not as total loss of packet-side signal.
- The bounded hypothesis is that querybank-normalized teacher-anchor scoring should beat the current raw global-bank retrieval and reduce concentration on anchors `0009/0010/0011` without retraining.
- The next experiment keeps the frozen `16`-frame teacher-packet bundles and evaluation surface fixed; only the retrieval-time scoring rule is allowed to change.
- The planned first comparison surface is `raw global-bank` vs `QB-Norm` vs `Dynamic Inverted Softmax` vs `CSLS`; hard shortlist pruning is only an optional secondary control.
- This pass is still a local feasibility smoke on reused `16`-frame bundle chunks and is not paper-comparable to the UVG coding metrics.
- The remaining immediate work is experiment control sync, dedicated run-branch preparation, and the bounded smoke implementation.
