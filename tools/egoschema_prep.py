#!/usr/bin/env python3
"""Build an EgoSchema multiple-choice eval manifest from the Subset parquet.

The **Subset** split (500 Q) carries PUBLIC ground-truth answers, so it is what we
use for local accuracy. The full **MC** split (5031 Q) has answers held out (the
official leaderboard scores those) -- do not use it for local accuracy.

We keep only videos whose ``<video_idx>.mp4`` exists under ``videos_dir``, take the
first N, strip the leading "A. "/"B. " prefixes from the option strings, and emit:

  <out_dir>/manifest.jsonl        one JSON record per (video, question)
  <out_dir>/<video_idx>/qa.json   per-video sidecar read by the unit scripts

Record fields: video_idx, mp4, question, options[5], answer_idx, expected_letter.

Usage:
  python tools/egoschema_prep.py --dataset-config configs/datasets/egoschema.yaml \
      --n 5 --out-dir outputs/datasets/egoschema
"""
import argparse
import json
import re
import sys
from pathlib import Path

import yaml
import pandas as pd

_PREFIX = re.compile(r'^\s*[A-Ea-e]\s*[.)]\s*')


def strip_prefix(opt: str) -> str:
    return _PREFIX.sub('', str(opt)).strip()


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--dataset-config', default='configs/datasets/egoschema.yaml')
    ap.add_argument('--n', type=int, default=None,
                    help='max videos to keep (overrides n_videos in the config)')
    ap.add_argument('--out-dir', default=None,
                    help='output dir (overrides manifest_dir in the config)')
    args = ap.parse_args()

    cfg = yaml.safe_load(Path(args.dataset_config).read_text())
    cols = cfg['columns']
    letters = cfg.get('letters', list('ABCDE'))
    videos_dir = Path(cfg['videos_dir'])
    n = args.n if args.n is not None else cfg.get('n_videos')
    out = Path(args.out_dir or cfg.get('manifest_dir', 'outputs/datasets/egoschema'))
    out.mkdir(parents=True, exist_ok=True)

    df = pd.read_parquet(cfg['parquet'])
    manifest = (out / 'manifest.jsonl').open('w')
    kept = 0
    for _, row in df.iterrows():
        if n is not None and kept >= n:
            break
        uid = str(row[cols['uuid']])
        mp4 = videos_dir / f'{uid}.mp4'
        if not mp4.exists():
            continue
        ans = row[cols['answer']]
        if ans is None or (isinstance(ans, float) and pd.isna(ans)):
            continue  # held-out (MC split); only the Subset carries answers
        opts = [strip_prefix(o) for o in list(row[cols['options']])]
        ai = int(ans)
        rec = {
            'video_idx': uid,
            'mp4': str(mp4),
            'question': str(row[cols['question']]),
            'options': opts,
            'answer_idx': ai,
            'expected_letter': letters[ai],
        }
        manifest.write(json.dumps(rec, ensure_ascii=False) + '\n')
        vdir = out / uid
        vdir.mkdir(exist_ok=True)
        (vdir / 'qa.json').write_text(json.dumps(rec, indent=2, ensure_ascii=False))
        kept += 1
    manifest.close()

    print(f'[egoschema_prep] kept {kept} videos -> {out}/manifest.jsonl')
    if kept == 0:
        print('  WARNING: 0 videos matched. Check that videos_dir holds <video_idx>.mp4 '
              'files and that the parquet is the Subset split (non-null answers).',
              file=sys.stderr)
        sys.exit(1)


if __name__ == '__main__':
    main()
