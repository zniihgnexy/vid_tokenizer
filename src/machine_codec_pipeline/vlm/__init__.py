"""Pluggable VLM backbones for Pathway B-mid.

Each backbone wraps one frozen vision-language model behind a single uniform
interface (see ``base.VLMBackbone``), so the codec / adapter / loss / QA
orchestration never has to know which VLM it is talking to. The only
per-model differences live in ``internvl.py`` / ``instructblip.py``.

Two usage sides share the same backbone object:
  * align side (training, inside NVRC): vision encoder + projector, no LLM.
  * eval side (root runners): full model for QA + token injection.
"""

from __future__ import annotations

from .base import VLMBackbone, run_self_judge, run_mcq, sample_frame_indices


def build_backbone(name: str, **kwargs) -> VLMBackbone:
    """Construct a backbone by short name. Lazy imports keep heavy deps out of
    the import path until a model is actually requested."""
    key = name.lower().replace("-", "").replace("_", "")
    if key in ("internvl", "internvit", "internvl25", "internvl258b"):
        from .internvl import InternVLBackbone
        return InternVLBackbone(**kwargs)
    if key in ("instructblip", "instructblipvicuna7b", "evaclip"):
        from .instructblip import InstructBlipBackbone
        return InstructBlipBackbone(**kwargs)
    if key in ("llavavideo", "llavavideoqwen2", "llavaqwen", "llava"):
        from .llava_video import LlavaVideoBackbone
        return LlavaVideoBackbone(**kwargs)
    if key in ("qwen25vl", "qwen2vl", "qwen25vl7b", "qwen"):
        from .qwen25vl import Qwen25VLBackbone
        return Qwen25VLBackbone(**kwargs)
    raise ValueError(f"Unknown VLM backbone: {name!r}")


__all__ = [
    "VLMBackbone",
    "build_backbone",
    "run_self_judge",
    "run_mcq",
    "sample_frame_indices",
]
