#!/usr/bin/env python3
"""Re-prep Video-MME long+motion manifest — keep ALL questions per video + real
task_type + domain (fixes G11). The per-video codec is question-independent, so one
trained codec answers every question -> stratified read-out for free.

qa.json per video now holds a `questions` LIST (each: question/options/expected_letter/
task_type/bucket). Bucket = detail | temporal | gist(control). Also writes a flat
`questions.jsonl` for harvest_stratified.py. video_idx = videoID (codec lookup unchanged).

Usage: python tools/vmme_prep.py --out-dir outputs/datasets/vmme_long_motion
"""
import argparse, json, os
from pathlib import Path
import pandas as pd
LETTERS = list("ABCDE")
BUCKET = {  # Video-MME task_type -> 3 buckets
    "Object Recognition":"detail","Object Reasoning":"detail","Attribute Perception":"detail",
    "OCR Problems":"detail","Counting Problem":"detail","Spatial Reasoning":"detail","Spatial Perception":"detail",
    "Action Recognition":"temporal","Action Reasoning":"temporal","Temporal Reasoning":"temporal","Temporal Perception":"temporal",
    "Information Synopsis":"gist",
}

def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--parquet", default="/tmp/vmme_meta/videomme/test-00000-of-00001.parquet")
    ap.add_argument("--video-dir", default="/mnt/nas/xinyizheng/VideoMME/videos")
    ap.add_argument("--out-dir", default="outputs/datasets/vmme_long_motion")
    args = ap.parse_args()
    df = pd.read_parquet(args.parquet)
    have = {os.path.splitext(f)[0] for f in os.listdir(args.video_dir) if f.endswith(".mp4")}
    df = df[df.videoID.isin(have)]
    out = Path(args.out_dir); out.mkdir(parents=True, exist_ok=True)
    mf = (out / "manifest.jsonl").open("w")
    qf = (out / "questions.jsonl").open("w")
    nv = nq = 0
    from collections import Counter
    bc = Counter()
    for vid, g in df.groupby("videoID"):
        mp4 = os.path.join(args.video_dir, f"{vid}.mp4")
        if not (os.path.exists(mp4) and os.path.getsize(mp4) > 1e6):
            continue
        qs = []
        for _, r in g.iterrows():
            opts = [str(o)[3:].strip() if str(o)[:2].strip().rstrip('.') in LETTERS else str(o) for o in r.options]
            ans = str(r.answer).strip().upper()
            if ans not in LETTERS[:len(opts)]:
                continue
            bkt = BUCKET.get(str(r.task_type), "detail")
            q = {"qid": str(r.question_id), "question": r.question, "options": opts,
                 "expected_letter": ans, "task_type": str(r.task_type), "bucket": bkt,
                 "domain": str(r.domain), "sub": str(r.sub_category)}
            qs.append(q); bc[bkt] += 1
            qf.write(json.dumps({"video_idx": vid, "mp4": mp4, **q}, ensure_ascii=False) + "\n"); nq += 1
        if not qs:
            continue
        # manifest record: video-level; qa.json keeps the FULL question list + a default (first) for legacy units
        rec0 = {"video_idx": vid, "mp4": mp4, "question": qs[0]["question"], "options": qs[0]["options"],
                "expected_letter": qs[0]["expected_letter"], "n_options": len(qs[0]["options"]),
                "task": qs[0]["sub"], "questions": qs}
        mf.write(json.dumps(rec0, ensure_ascii=False) + "\n")
        vdir = out / vid; vdir.mkdir(exist_ok=True)
        (vdir / "qa.json").write_text(json.dumps(rec0, indent=2, ensure_ascii=False))
        nv += 1
    mf.close(); qf.close()
    print(f"[vmme_prep] {nv} videos, {nq} questions -> {out}")
    print(f"[vmme_prep] bucket counts: {dict(bc)}")

if __name__ == "__main__":
    main()
