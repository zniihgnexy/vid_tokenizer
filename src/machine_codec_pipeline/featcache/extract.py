"""Frozen-VLM token cache for a video: every cached frame through InternViT + pixel-shuffle + mlp1."""

from __future__ import annotations

import os

import torch

from machine_codec_pipeline.vlm.internvl_backend import _list_frames, extract_internvit_tokens, load_image

VIT_BATCH = 32


@torch.no_grad()
def video_tokens(model, frame_dir: str, batch: int = VIT_BATCH) -> torch.Tensor:
    """All frames in ``frame_dir`` (sorted) -> [T, 256, 4096] float16 on cpu."""
    frames = _list_frames(frame_dir)
    if not frames:
        raise FileNotFoundError(f"no frames in {frame_dir}")
    out = []
    for i in range(0, len(frames), batch):
        tiles = torch.cat([load_image(str(p), max_num=1) for p in frames[i:i + batch]], dim=0)
        out.append(extract_internvit_tokens(model, tiles).to(torch.float16).cpu())
    return torch.cat(out, dim=0)


def query_frame_rows(num_frames: int, sample_count: int) -> list[int]:
    """Same 8-frame grid as qa_from_raw_frames / harvest_stratified (honours QA_SAMPLE_OFFSET)."""
    if sample_count >= num_frames:
        return list(range(num_frames))
    step = num_frames / sample_count
    off = int(os.environ.get("QA_SAMPLE_OFFSET", "0"))
    return [min(int(i * step) + off, num_frames - 1) for i in range(sample_count)]


def frame_dir_of(out_root: str, dataset: str, uuid: str) -> str:
    return f"{out_root}/_videos/{dataset}/{uuid}_256_uniform"
