#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

REPO_ROOT = Path(__file__).resolve().parents[3]
if str(REPO_ROOT / "src") not in sys.path:
    sys.path.insert(0, str(REPO_ROOT / "src"))

from machine_codec_pipeline.video_data import split_png_video_chunks


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Split a PNG frame directory into fixed-size chunk datasets."
    )
    parser.add_argument("--source-dir", type=Path, required=True, help="Directory containing source PNG frames.")
    parser.add_argument(
        "--output-root",
        type=Path,
        required=True,
        help="Directory where chunk datasets will be created.",
    )
    parser.add_argument("--chunk-size", type=int, required=True, help="Number of frames per chunk.")
    parser.add_argument(
        "--prefix",
        type=str,
        default=None,
        help="Optional dataset-name prefix. Defaults to the source directory name.",
    )
    parser.add_argument(
        "--overwrite",
        action="store_true",
        help="Delete any existing chunk datasets before writing new ones.",
    )
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    summary = split_png_video_chunks(
        source_dir=args.source_dir,
        output_root=args.output_root,
        chunk_size=args.chunk_size,
        prefix=args.prefix,
        overwrite=args.overwrite,
    )
    print(json.dumps(summary, indent=2, sort_keys=True))


if __name__ == "__main__":
    main()
