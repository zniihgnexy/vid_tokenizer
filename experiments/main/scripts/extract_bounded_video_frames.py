#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from machine_codec_pipeline.video_data import extract_bounded_video_frames


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description=(
            "Extract a bounded contiguous frame window from one source video "
            "into a PNG dataset directory that matches the frozen local bridge pipeline."
        )
    )
    parser.add_argument("--video-path", type=Path, required=True, help="Source .mp4 path")
    parser.add_argument("--output-dir", type=Path, required=True, help="Target PNG dataset directory")
    parser.add_argument("--start-frame", type=int, default=0, help="Inclusive start frame index")
    parser.add_argument("--num-frames", type=int, required=True, help="Number of frames to extract")
    parser.add_argument("--width", type=int, default=32, help="Output frame width")
    parser.add_argument("--height", type=int, default=32, help="Output frame height")
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Overwrite an existing dataset directory if PNG frames are already present",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = extract_bounded_video_frames(
        video_path=args.video_path,
        output_dir=args.output_dir,
        start_frame=args.start_frame,
        num_frames=args.num_frames,
        width=args.width,
        height=args.height,
        overwrite=args.overwrite,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
