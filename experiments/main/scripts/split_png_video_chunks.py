#!/usr/bin/env python3
import argparse
import json
import shutil
from pathlib import Path


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
    source_dir = args.source_dir.resolve()
    output_root = args.output_root.resolve()
    prefix = args.prefix or source_dir.name

    if not source_dir.is_dir():
        raise FileNotFoundError(f"Source frame directory not found: {source_dir}")
    if args.chunk_size <= 0:
        raise ValueError("--chunk-size must be positive")

    frames = sorted(source_dir.glob("*.png"))
    if not frames:
        raise FileNotFoundError(f"No PNG frames found in {source_dir}")

    output_root.mkdir(parents=True, exist_ok=True)
    chunk_manifests = []

    for chunk_index, start in enumerate(range(0, len(frames), args.chunk_size)):
        chunk_frames = frames[start : start + args.chunk_size]
        chunk_name = f"{prefix}_chunk{chunk_index:02d}"
        chunk_dir = output_root / chunk_name

        if chunk_dir.exists():
            if not args.overwrite:
                raise FileExistsError(f"Chunk directory already exists: {chunk_dir}")
            shutil.rmtree(chunk_dir)
        chunk_dir.mkdir(parents=True, exist_ok=True)

        manifest = {
            "source_dir": str(source_dir),
            "chunk_name": chunk_name,
            "chunk_index": chunk_index,
            "chunk_size": len(chunk_frames),
            "original_start_index": start,
            "original_end_index": start + len(chunk_frames) - 1,
            "frames": [],
        }

        for local_index, frame_path in enumerate(chunk_frames):
            new_name = f"{local_index:04d}{frame_path.suffix}"
            new_path = chunk_dir / new_name
            shutil.copy2(frame_path, new_path)
            manifest["frames"].append(
                {
                    "original_index": start + local_index,
                    "source_name": frame_path.name,
                    "chunk_name": new_name,
                }
            )

        manifest_path = chunk_dir / "chunk_manifest.json"
        manifest_path.write_text(json.dumps(manifest, indent=2), encoding="utf-8")
        chunk_manifests.append(
            {
                "chunk_name": chunk_name,
                "chunk_dir": str(chunk_dir),
                "manifest_path": str(manifest_path),
                "frame_count": len(chunk_frames),
            }
        )

    index_payload = {
        "source_dir": str(source_dir),
        "chunk_size": args.chunk_size,
        "chunk_count": len(chunk_manifests),
        "chunks": chunk_manifests,
    }
    index_path = output_root / f"{prefix}_chunk_index.json"
    index_path.write_text(json.dumps(index_payload, indent=2), encoding="utf-8")
    print(json.dumps(index_payload, indent=2))


if __name__ == "__main__":
    main()
