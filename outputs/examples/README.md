# Example Outputs

Tracked example artifacts live here so the repository includes at least one
concrete reference for the current pipeline shape without dragging full local
run payloads into Git.

Keep example bundles lightweight. A good tracked example usually contains:

- a short README with the scenario and headline result
- a compact public summary JSON or Markdown report
- a few images that make the result easy to inspect
- optional small raw response files when they help interpret the result

Do not keep full chunk-level training payloads here. Large artifacts such as
checkpoints, decoded-frame dumps, bitstreams, and rank logs should stay under
the ignored `outputs/runs/` area.

Current curated example:

- `ego4d_real_full_video_openai/`
