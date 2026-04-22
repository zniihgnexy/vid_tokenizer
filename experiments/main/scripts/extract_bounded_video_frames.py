#!/usr/bin/env python3
from __future__ import annotations

import argparse
import json
import subprocess
from pathlib import Path


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


def read_probe(video_path: Path) -> dict:
    probe_cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-count_frames",
        "-show_entries",
        "stream=width,height,avg_frame_rate,nb_read_frames,duration",
        "-of",
        "json",
        str(video_path),
    ]
    completed = subprocess.run(probe_cmd, check=True, capture_output=True, text=True)
    payload = json.loads(completed.stdout)
    streams = payload.get("streams", [])
    if not streams:
        raise RuntimeError(f"No video stream found in {video_path}")
    return streams[0]


def ensure_output_dir(output_dir: Path, overwrite: bool) -> None:
    output_dir.mkdir(parents=True, exist_ok=True)
    existing_pngs = sorted(output_dir.glob("*.png"))
    if existing_pngs and not overwrite:
        raise FileExistsError(
            f"Output dir {output_dir} already has {len(existing_pngs)} PNG frames; "
            "use --overwrite to replace them."
        )
    if overwrite:
        for path in existing_pngs:
            path.unlink()
        manifest_path = output_dir / "extraction_manifest.json"
        if manifest_path.exists():
            manifest_path.unlink()


def extract_frames(
    video_path: Path,
    output_dir: Path,
    start_frame: int,
    num_frames: int,
    width: int,
    height: int,
    overwrite: bool,
) -> list[Path]:
    end_frame = start_frame + num_frames - 1
    vf = (
        f"select='between(n\\,{start_frame}\\,{end_frame})',"
        f"scale={width}:{height}:flags=lanczos"
    )
    ffmpeg_cmd = [
        "ffmpeg",
        "-hide_banner",
        "-loglevel",
        "error",
        "-y" if overwrite else "-n",
        "-i",
        str(video_path),
        "-vf",
        vf,
        "-vsync",
        "0",
        "-frames:v",
        str(num_frames),
        "-start_number",
        "0",
        str(output_dir / "%04d.png"),
    ]
    subprocess.run(ffmpeg_cmd, check=True)
    written = sorted(output_dir.glob("*.png"))
    if len(written) != num_frames:
        raise RuntimeError(
            f"Expected {num_frames} PNG frames in {output_dir}, found {len(written)}."
        )
    return written


def write_manifest(
    output_dir: Path,
    video_path: Path,
    probe: dict,
    start_frame: int,
    num_frames: int,
    width: int,
    height: int,
    written_frames: list[Path],
) -> Path:
    manifest = {
        "video_path": str(video_path),
        "output_dir": str(output_dir),
        "dataset_name": output_dir.name,
        "start_frame": start_frame,
        "num_frames": num_frames,
        "width": width,
        "height": height,
        "written_frame_count": len(written_frames),
        "written_frames": [path.name for path in written_frames],
        "source_probe": probe,
    }
    manifest_path = output_dir / "extraction_manifest.json"
    manifest_path.write_text(json.dumps(manifest, indent=2) + "\n", encoding="utf-8")
    return manifest_path


def main() -> None:
    args = parse_args()
    if args.start_frame < 0:
        raise ValueError("--start-frame must be >= 0")
    if args.num_frames <= 0:
        raise ValueError("--num-frames must be > 0")
    if args.width <= 0 or args.height <= 0:
        raise ValueError("--width and --height must be > 0")

    video_path = args.video_path.resolve()
    output_dir = args.output_dir.resolve()
    if not video_path.exists():
        raise FileNotFoundError(f"Video path does not exist: {video_path}")

    probe = read_probe(video_path)
    total_frames = int(probe.get("nb_read_frames", 0))
    if args.start_frame + args.num_frames > total_frames:
        raise ValueError(
            f"Requested frames [{args.start_frame}, {args.start_frame + args.num_frames - 1}] "
            f"but source only has {total_frames} frames."
        )

    ensure_output_dir(output_dir, overwrite=args.overwrite)
    written_frames = extract_frames(
        video_path=video_path,
        output_dir=output_dir,
        start_frame=args.start_frame,
        num_frames=args.num_frames,
        width=args.width,
        height=args.height,
        overwrite=args.overwrite,
    )
    manifest_path = write_manifest(
        output_dir=output_dir,
        video_path=video_path,
        probe=probe,
        start_frame=args.start_frame,
        num_frames=args.num_frames,
        width=args.width,
        height=args.height,
        written_frames=written_frames,
    )

    summary = {
        "dataset_dir": str(output_dir.parent),
        "dataset_name": output_dir.name,
        "frame_count": len(written_frames),
        "frame_shape": [args.height, args.width],
        "manifest_path": str(manifest_path),
    }
    print(json.dumps(summary, indent=2))


if __name__ == "__main__":
    main()
