#!/usr/bin/env python3
"""Build a LongVideoBench multiple-choice eval manifest (long, VISUAL questions).

LongVideoBench (val = 1337 Q with public answers) mixes subtitle-dependent and
purely-visual referring-reasoning questions. Our pipeline feeds ONLY frames (no
subtitles), so we keep VISUAL questions (drop any whose text mentions
"subtitle") and, for the long-video thesis, the LONG duration groups.

Output mirrors the other prep scripts so the units consume it unchanged:
  <out_dir>/manifest.jsonl          one record per (video, question)
  <out_dir>/<uuid>/qa.json          per-item sidecar
Record fields: video_idx(=id), mp4, question, options[], answer_idx, expected_letter.

Only items whose <video_id>.mp4 exists under videos_dir are kept (so it works on a
partially-extracted subset). Items are interleaved across question_category.

Usage:
  python tools/longvideobench_prep.py --n 25 --min-duration-group 600 \
      --out-dir outputs/datasets/longvideobench
"""
import argparse, json
from collections import defaultdict
from pathlib import Path

LETTERS = list("ABCDE")


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__)
    ap.add_argument("--val-json", default="/mnt/nas/xinyizheng/LongVideoBench/lvb_val.json")
    ap.add_argument("--videos-dir", default="/mnt/nas/xinyizheng/lvb_videos/videos")
    ap.add_argument("--min-duration-group", type=int, default=600,
                    help="keep questions whose duration_group >= this (600 = ~10min)")
    ap.add_argument("--n", type=int, default=25, help="max videos to keep")
    ap.add_argument("--out-dir", default="outputs/datasets/longvideobench")
    args = ap.parse_args()

    vdir = Path(args.videos_dir)
    data = json.loads(Path(args.val_json).read_text())

    # visual (non-subtitle) + long + video present, one question per video
    by_cat = defaultdict(list)
    seen_vid = set()
    for x in data:
        if "subtitle" in x["question"].lower():
            continue
        if x.get("duration_group", 0) < args.min_duration_group:
            continue
        vid = x["video_id"]
        if vid in seen_vid:
            continue
        if not (vdir / f"{vid}.mp4").exists():
            continue
        cands = [str(c) for c in x["candidates"]]
        ai = int(x["correct_choice"])
        if ai < 0 or ai >= len(cands):
            continue
        seen_vid.add(vid)
        by_cat[x["question_category"]].append({
            "video_idx": x["id"],
            "mp4": str(vdir / f"{vid}.mp4"),
            "question": str(x["question"]),
            "options": cands,
            "answer_idx": ai,
            "expected_letter": LETTERS[ai],
            "category": x["question_category"],
            "duration": x.get("duration"),
        })

    # round-robin across categories for diversity
    cats = sorted(by_cat)
    out = Path(args.out_dir); out.mkdir(parents=True, exist_ok=True)
    manifest = (out / "manifest.jsonl").open("w")
    kept = 0; r = 0
    while kept < args.n and any(r < len(by_cat[c]) for c in cats):
        for c in cats:
            if kept >= args.n:
                break
            if r < len(by_cat[c]):
                rec = by_cat[c][r]
                manifest.write(json.dumps(rec, ensure_ascii=False) + "\n")
                vd = out / rec["video_idx"]; vd.mkdir(exist_ok=True)
                (vd / "qa.json").write_text(json.dumps(rec, indent=2, ensure_ascii=False))
                kept += 1
        r += 1
    manifest.close()
    print(f"[lvb_prep] kept {kept} videos -> {out}/manifest.jsonl "
          f"(present in {vdir})")
    if kept == 0:
        print("  WARNING: 0 kept -- extract more videos into videos_dir.", flush=True)


if __name__ == "__main__":
    main()
