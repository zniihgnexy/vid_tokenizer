"""Raw-video preparation helpers for bounded and chunked NVRC runs."""

from __future__ import annotations

import json
import shutil
import subprocess
from pathlib import Path
from typing import Any

from PIL import Image

from ..io import write_json


def read_probe(video_path: Path) -> dict[str, Any]:
    """Read basic frame metadata from one source video."""

    probe_cmd = [
        "ffprobe",
        "-v",
        "error",
        "-select_streams",
        "v:0",
        "-count_frames",
        "-show_entries",
        "stream=width,height,avg_frame_rate,nb_read_frames,nb_frames,duration",
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


def _coerce_frame_count(probe: dict[str, Any]) -> int | None:
    for key in ("nb_read_frames", "nb_frames"):
        raw_value = probe.get(key)
        if raw_value in {None, "", "N/A"}:
            continue
        try:
            frame_count = int(raw_value)
        except (TypeError, ValueError):
            continue
        if frame_count > 0:
            return frame_count
    return None


def _probe_fps(video_path: Path) -> float | None:
    """Average frame rate via ffprobe (parses 'num/den'). Used to map uniform
    frame indices -> seek timestamps for fast long-video extraction."""
    try:
        out = subprocess.run(
            ["ffprobe", "-v", "error", "-select_streams", "v:0",
             "-show_entries", "stream=avg_frame_rate", "-of",
             "default=noprint_wrappers=1:nokey=1", str(video_path)],
            capture_output=True, text=True, check=True).stdout.strip()
        num, _, den = out.partition("/")
        n, d = float(num), float(den) if den else 1.0
        return n / d if d else None
    except Exception:
        return None


def _ensure_clean_output_dir(output_dir: Path, overwrite: bool) -> None:
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
        for artifact_name in ("extraction_manifest.json", "prepare_video_summary.json"):
            artifact_path = output_dir / artifact_name
            if artifact_path.exists():
                artifact_path.unlink()


def _normalize_frame_shape(raw_value: Any) -> list[int] | None:
    if not isinstance(raw_value, (list, tuple)) or len(raw_value) != 2:
        return None
    try:
        height = int(raw_value[0])
        width = int(raw_value[1])
    except (TypeError, ValueError):
        return None
    if height <= 0 or width <= 0:
        return None
    return [height, width]


def _read_json_if_exists(path: Path) -> dict[str, Any] | None:
    if not path.exists():
        return None
    return json.loads(path.read_text(encoding="utf-8"))


def _uniform_indices(total: int, num_frames: int, start_frame: int = 0) -> list[int]:
    """Evenly-spaced, distinct frame indices across [start_frame, total-1]."""
    hi = total - 1
    if num_frames == 1:
        return [start_frame]
    step = (hi - start_frame) / (num_frames - 1)
    raw = [round(start_frame + i * step) for i in range(num_frames)]
    seen: set[int] = set()
    out: list[int] = []
    for v in raw:
        v = max(start_frame, min(v, hi))
        while v in seen and v < hi:
            v += 1
        while v in seen and v > start_frame:
            v -= 1
        seen.add(v)
        out.append(v)
    return sorted(out)


def _extract_frames(
    *,
    video_path: Path,
    output_dir: Path,
    start_frame: int,
    num_frames: int,
    width: int,
    height: int,
    overwrite: bool,
    sampling: str = "contiguous",
    total_frames: int | None = None,
) -> list[Path]:
    if sampling == "uniform" and total_frames and total_frames > num_frames:
        # N evenly-spaced frames across the whole clip (long-form coverage).
        # Decoding every frame (select=eq(n,..)) is O(total_frames) -- crippling on
        # 30-60min videos (~100k frames). Instead use input SEEKING (-ss BEFORE -i)
        # once per target frame: O(num_frames) fast keyframe seeks.
        idx = _uniform_indices(total_frames, num_frames, start_frame)
        fps = _probe_fps(video_path) or 25.0
        # Keep seeks strictly inside the file: the very last frame index can land
        # at/after EOF and yield no PNG. Cap a few frames before the end.
        safe_last = max(start_frame, total_frames - 3)
        for k, fi in enumerate(idx):
            ts = min(fi, safe_last) / fps
            out_png = output_dir / f"{k:04d}.png"
            seek_cmd = [
                "ffmpeg", "-hide_banner", "-loglevel", "error",
                "-ss", f"{ts:.3f}", "-i", str(video_path),
                "-vf", f"scale={width}:{height}:flags=lanczos",
                "-frames:v", "1", "-y" if overwrite else "-n",
                str(out_png),
            ]
            subprocess.run(seek_cmd, check=True)
            # Robustness: if a seek produced nothing (EOF/corrupt), copy the prev frame.
            if not out_png.exists():
                prev = output_dir / f"{max(0, k-1):04d}.png"
                if prev.exists():
                    import shutil
                    shutil.copyfile(prev, out_png)
    else:
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


def extract_bounded_video_frames(
    *,
    video_path: Path,
    output_dir: Path,
    start_frame: int,
    num_frames: int,
    width: int = 32,
    height: int = 32,
    overwrite: bool = False,
    sampling: str = "contiguous",
) -> dict[str, Any]:
    """Extract a PNG dataset directory: contiguous first-N frames, or N frames
    uniformly spaced across the whole clip (``sampling='uniform'``)."""

    if start_frame < 0:
        raise ValueError("--start-frame must be >= 0")
    if num_frames <= 0:
        raise ValueError("--num-frames must be > 0")
    if width <= 0 or height <= 0:
        raise ValueError("--width and --height must be > 0")

    resolved_video_path = video_path.expanduser().resolve()
    resolved_output_dir = output_dir.expanduser().resolve()
    if not resolved_video_path.exists():
        raise FileNotFoundError(f"Video path does not exist: {resolved_video_path}")

    probe = read_probe(resolved_video_path)
    total_frames = _coerce_frame_count(probe)
    # The contiguous mode requires the window to fit; uniform spans the whole clip.
    if (
        sampling != "uniform"
        and total_frames is not None
        and start_frame + num_frames > total_frames
    ):
        raise ValueError(
            f"Requested frames [{start_frame}, {start_frame + num_frames - 1}] "
            f"but source only has {total_frames} frames."
        )

    _ensure_clean_output_dir(resolved_output_dir, overwrite=overwrite)
    written_frames = _extract_frames(
        video_path=resolved_video_path,
        output_dir=resolved_output_dir,
        start_frame=start_frame,
        num_frames=num_frames,
        width=width,
        height=height,
        overwrite=overwrite,
        sampling=sampling,
        total_frames=total_frames,
    )

    manifest = {
        "video_path": str(resolved_video_path),
        "output_dir": str(resolved_output_dir),
        "dataset_name": resolved_output_dir.name,
        "start_frame": start_frame,
        "num_frames": num_frames,
        "sampling": sampling,
        "width": width,
        "height": height,
        "source_frame_count": total_frames,
        "written_frame_count": len(written_frames),
        "written_frames": [path.name for path in written_frames],
        "source_probe": probe,
    }
    manifest_path = resolved_output_dir / "extraction_manifest.json"
    write_json(manifest_path, manifest)

    summary = {
        "dataset_dir": str(resolved_output_dir.parent),
        "dataset_name": resolved_output_dir.name,
        "frame_count": len(written_frames),
        "frame_shape": [height, width],
        "start_frame": start_frame,
        "manifest_path": str(manifest_path),
        "source_frame_count": total_frames,
        "video_path": str(resolved_video_path),
    }
    write_json(resolved_output_dir / "prepare_video_summary.json", summary)
    return summary


def split_png_video_chunks(
    *,
    source_dir: Path,
    output_root: Path,
    chunk_size: int,
    prefix: str | None = None,
    overwrite: bool = False,
) -> dict[str, Any]:
    """Split one PNG frame directory into fixed-size chunk datasets."""

    resolved_source_dir = source_dir.expanduser().resolve()
    resolved_output_root = output_root.expanduser().resolve()
    chunk_prefix = prefix or resolved_source_dir.name

    if not resolved_source_dir.is_dir():
        raise FileNotFoundError(f"Source frame directory not found: {resolved_source_dir}")
    if chunk_size <= 0:
        raise ValueError("--chunk-size must be positive")

    frames = sorted(resolved_source_dir.glob("*.png"))
    if not frames:
        raise FileNotFoundError(f"No PNG frames found in {resolved_source_dir}")

    resolved_output_root.mkdir(parents=True, exist_ok=True)
    chunk_manifests: list[dict[str, Any]] = []
    source_manifest_path = resolved_source_dir / "extraction_manifest.json"
    source_manifest = _read_json_if_exists(source_manifest_path)
    source_frame_shape = None
    source_video_path = None
    if source_manifest is not None:
        source_frame_shape = _normalize_frame_shape(
            [source_manifest.get("height"), source_manifest.get("width")]
        )
        source_video_path = source_manifest.get("video_path")

    for chunk_index, start in enumerate(range(0, len(frames), chunk_size)):
        chunk_frames = frames[start : start + chunk_size]
        chunk_name = f"{chunk_prefix}_chunk{chunk_index:02d}"
        chunk_dir = resolved_output_root / chunk_name

        if chunk_dir.exists():
            if not overwrite:
                raise FileExistsError(f"Chunk directory already exists: {chunk_dir}")
            shutil.rmtree(chunk_dir)
        chunk_dir.mkdir(parents=True, exist_ok=True)

        manifest = {
            "source_dir": str(resolved_source_dir),
            "chunk_name": chunk_name,
            "chunk_index": chunk_index,
            "chunk_size": len(chunk_frames),
            "original_start_index": start,
            "original_end_index": start + len(chunk_frames) - 1,
            "frame_shape": source_frame_shape,
            "source_manifest_path": str(source_manifest_path) if source_manifest is not None else None,
            "source_video_path": source_video_path,
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
        write_json(manifest_path, manifest)
        chunk_manifests.append(
            {
                "chunk_name": chunk_name,
                "chunk_dir": str(chunk_dir),
                "manifest_path": str(manifest_path),
                "frame_count": len(chunk_frames),
                "frame_shape": source_frame_shape,
            }
        )

    index_payload = {
        "source_dir": str(resolved_source_dir),
        "chunk_size": chunk_size,
        "chunk_count": len(chunk_manifests),
        "source_manifest_path": str(source_manifest_path) if source_manifest is not None else None,
        "source_video_path": source_video_path,
        "source_frame_shape": source_frame_shape,
        "chunks": chunk_manifests,
    }
    index_path = resolved_output_root / f"{chunk_prefix}_chunk_index.json"
    write_json(index_path, index_payload)
    return index_payload


def prepare_video_window(
    *,
    video_path: Path,
    output_dir: Path,
    start_frame: int,
    num_frames: int,
    width: int = 32,
    height: int = 32,
    overwrite: bool = False,
    chunk_size: int | None = None,
    chunk_output_root: Path | None = None,
    chunk_prefix: str | None = None,
    sampling: str = "contiguous",
) -> dict[str, Any]:
    """Extract one bounded video window and optionally split it into chunks."""

    extraction_summary = extract_bounded_video_frames(
        video_path=video_path,
        output_dir=output_dir,
        start_frame=start_frame,
        num_frames=num_frames,
        width=width,
        height=height,
        overwrite=overwrite,
        sampling=sampling,
    )

    payload: dict[str, Any] = {
        "video_path": str(video_path.expanduser().resolve()),
        "dataset": extraction_summary,
    }
    if chunk_size is not None:
        resolved_chunk_output_root = (
            chunk_output_root.expanduser().resolve()
            if chunk_output_root is not None
            else output_dir.expanduser().resolve().parent
            / f"{output_dir.expanduser().resolve().name}_chunks"
        )
        payload["chunks"] = split_png_video_chunks(
            source_dir=output_dir,
            output_root=resolved_chunk_output_root,
            chunk_size=chunk_size,
            prefix=chunk_prefix,
            overwrite=overwrite,
        )
    return payload


def load_chunk_index(path: Path) -> dict[str, Any]:
    """Load one chunk-index manifest written by ``split_png_video_chunks``."""

    resolved_path = path.expanduser().resolve()
    payload = json.loads(resolved_path.read_text(encoding="utf-8"))
    if "chunks" not in payload or not isinstance(payload["chunks"], list):
        raise ValueError(f"Invalid chunk index at {resolved_path}")
    payload["chunk_index_path"] = str(resolved_path)
    return payload


def infer_chunk_video_settings(chunk_index: dict[str, Any], chunk: dict[str, Any]) -> dict[str, list[int]] | None:
    """Infer per-chunk video and patch sizes from generated manifests."""

    frame_shape = _normalize_frame_shape(chunk.get("frame_shape"))
    if frame_shape is None:
        frame_shape = _normalize_frame_shape(chunk_index.get("source_frame_shape"))

    if frame_shape is None:
        source_manifest_path = chunk_index.get("source_manifest_path")
        if source_manifest_path:
            source_manifest = _read_json_if_exists(Path(source_manifest_path))
            if source_manifest is not None:
                frame_shape = _normalize_frame_shape(
                    [source_manifest.get("height"), source_manifest.get("width")]
                )

    if frame_shape is None:
        chunk_dir = Path(chunk["chunk_dir"]).expanduser().resolve()
        first_frame = next(iter(sorted(chunk_dir.glob("*.png"))), None)
        if first_frame is not None:
            with Image.open(first_frame) as image:
                frame_shape = [image.height, image.width]

    frame_count = int(chunk.get("frame_count", 0))
    if frame_count <= 0 or frame_shape is None:
        return None

    height, width = frame_shape
    return {
        "video_size": [frame_count, height, width],
        "patch_size": [1, height, width],
    }
