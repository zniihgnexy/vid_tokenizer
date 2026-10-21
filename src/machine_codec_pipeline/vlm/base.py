"""VLMBackbone interface + model-agnostic QA orchestration.

A backbone is used on two sides:

  align side (training, inside NVRC) -- vision encoder + projector, no LLM:
    load_align(); vit_dims(); oracle_hidden(); codec_hidden(); codec_to_llm_tokens()

  eval side (root runners) -- full model:
    load_full(); answer_pixels(); answer_codec_tokens(); judge()

The free functions at the bottom (run_self_judge / run_mcq) are identical for
every model -- they only call the abstract methods, so adding a new VLM never
touches the orchestration.
"""

from __future__ import annotations

import json
from abc import ABC, abstractmethod
from pathlib import Path

import torch


class VLMBackbone(ABC):
    """One frozen vision-language model behind a uniform interface."""

    #: short, human name used in logs / configs (e.g. "internvl").
    name: str = "vlm"

    def __init__(self, model_path: str, device: str = "cuda",
                 dtype: torch.dtype = torch.bfloat16, align_layer: int = 12,
                 input_size: int = 448, **kwargs):
        self.model_path = model_path
        self.device = device
        self.dtype = dtype
        self.align_layer = int(align_layer)
        self.input_size = int(input_size)
        self.extra = kwargs
        self.model = None      # set by load_align / load_full
        self.tokenizer = None
        self._mode = None      # "align" | "full"

    # ------------------------------------------------------------------ #
    # align side (training)
    # ------------------------------------------------------------------ #
    @abstractmethod
    def load_align(self) -> "VLMBackbone":
        """Load the frozen vision encoder (+ projector), drop the LLM."""

    @abstractmethod
    def vit_dims(self) -> dict:
        """{grid, num_patches, hidden_dim, num_layers} for sizing CodecAdapter."""

    @abstractmethod
    def preprocess_for_vit(self, x_5d: torch.Tensor) -> torch.Tensor:
        """[N,C,T,H,W] in [0,1] -> [N*T, 3, S, S] normalised to the ViT input."""

    @abstractmethod
    def oracle_hidden(self, x_5d: torch.Tensor, layer_idx: int) -> torch.Tensor:
        """Real frames -> ViT first ``layer_idx`` layers. [N, T, tok, dim], no_grad."""

    @abstractmethod
    def codec_hidden(self, patch_embeds: torch.Tensor, layer_idx: int) -> torch.Tensor:
        """CodecAdapter patch embeddings -> +CLS/pos -> ViT first ``layer_idx``
        layers. [B, tok, dim]. Gradient flows back to the adapter."""

    @abstractmethod
    def codec_to_llm_tokens(self, patch_embeds: torch.Tensor) -> torch.Tensor:
        """CodecAdapter patch embeddings -> full vision tower + projector ->
        [B, n_llm_tokens, llm_hidden] ready to inject into the LLM."""

    # ------------------------------------------------------------------ #
    # eval side (runners)
    # ------------------------------------------------------------------ #
    @abstractmethod
    def load_full(self) -> "VLMBackbone":
        """Load the full model (vision + projector + LLM) for QA."""

    @abstractmethod
    def answer_pixels(self, frame_paths: list[str], prompt: str,
                      max_new_tokens: int = 128) -> str:
        """Oracle path: real frames -> full VLM -> answer text."""

    @abstractmethod
    def answer_codec_tokens(self, token_rows: torch.Tensor, prompt: str,
                            max_new_tokens: int = 128) -> str:
        """Codec path: precomputed LLM-space tokens injected -> answer text.
        ``token_rows``: [N_frames, n_llm_tokens, llm_hidden]."""

    @abstractmethod
    def judge(self, prompt: str, max_new_tokens: int = 8) -> str:
        """Text-only generation (used as the equivalence judge)."""


# ====================================================================== #
# Model-agnostic QA orchestration (calls only the abstract methods)
# ====================================================================== #
def sample_frame_indices(idx, sample_count):
    """Uniformly sample frame ids from a codec-token ``idx`` tensor [M, 3]."""
    frames = sorted({int(v) for v in idx[:, 0].tolist()})
    if sample_count >= len(frames):
        return frames
    step = len(frames) / sample_count
    return [frames[int(i * step)] for i in range(sample_count)]


def _codec_rows_for_frames(idx, tokens, frame_ids):
    first_row = {}
    for row in range(idx.shape[0]):
        f = int(idx[row, 0])
        first_row.setdefault(f, row)
    rows = [first_row[f] for f in frame_ids]
    return tokens[rows]


def _frame_paths(raw_chunk_dir, frame_ids):
    paths = []
    for fid in frame_ids:
        p = Path(raw_chunk_dir) / f"{fid:04d}.png"
        if not p.exists():
            p = Path(raw_chunk_dir) / f"{fid:06d}.png"
        if not p.exists():
            raise FileNotFoundError(f"No frame file for id {fid} in {raw_chunk_dir}")
        paths.append(str(p))
    return paths


def _judge_prompt(question, oracle_answer, codec_answer):
    return (
        "Two answers were given to the same question. Decide if they convey "
        "substantially the same information.\n"
        f"Question: {question}\n"
        f"Answer A (oracle, from the real video): {oracle_answer.strip()}\n"
        f"Answer B (compressed-codec output): {codec_answer.strip()}\n"
        'Reply with exactly "Yes" or "No".'
    )


@torch.no_grad()
def run_self_judge(backbone: VLMBackbone, tokens_path, raw_chunk_dir, questions,
                   sample_count=4, max_new_tokens=128):
    """Free-form QA: oracle (raw frames) vs codec (injected tokens), VLM judges.
    Backbone-agnostic -- works for any VLMBackbone in 'full' mode."""
    payload = torch.load(tokens_path, map_location="cpu")
    idx, tokens = payload["idx"], payload["tokens"]
    frame_ids = sample_frame_indices(idx, sample_count)
    codec_rows = _codec_rows_for_frames(idx, tokens, frame_ids)
    frame_paths = _frame_paths(raw_chunk_dir, frame_ids)

    records, agree_count = [], 0
    for q in questions:
        codec_ans = backbone.answer_codec_tokens(codec_rows, q, max_new_tokens)
        oracle_ans = backbone.answer_pixels(frame_paths, q, max_new_tokens)
        judge_raw = backbone.judge(_judge_prompt(q, oracle_ans, codec_ans))
        agree = judge_raw.strip().lower().startswith("yes")
        records.append({
            "question": q, "oracle_answer": oracle_ans,
            "codec_answer": codec_ans, "judge_raw": judge_raw, "agree": bool(agree),
        })
        agree_count += int(agree)
        print(f"  Q: {q[:80]}")
        print(f"    oracle: {oracle_ans[:100]}")
        print(f"    codec : {codec_ans[:100]}")
        print(f"    judge : {judge_raw.strip()[:30]} -> agree={agree}")
    rate = (agree_count / len(questions)) if questions else None
    return {
        "backbone": backbone.name,
        "sample_frame_ids": frame_ids,
        "agreement_rate": rate,
        "num_questions": len(questions),
        "num_agree": agree_count,
        "records": records,
    }


@torch.no_grad()
def run_mcq(backbone: VLMBackbone, tokens_path, question, options,
            expected_letter=None, sample_count=8, max_new_tokens=64):
    """Multiple-choice QA straight from saved codec tokens (backbone-agnostic)."""
    payload = torch.load(tokens_path, map_location="cpu")
    idx, tokens = payload["idx"], payload["tokens"]
    frame_ids = sample_frame_indices(idx, sample_count)
    codec_rows = _codec_rows_for_frames(idx, tokens, frame_ids)
    option_lines = "\n".join(f"{chr(65 + i)}. {o}" for i, o in enumerate(options))
    prompt = (f"{question}\nOptions:\n{option_lines}\n"
              "Answer with the option letter only.")
    answer = backbone.answer_codec_tokens(codec_rows, prompt, max_new_tokens)
    parsed = next((c for c in answer.upper() if c in "ABCDE"), None)
    correct = (parsed == expected_letter.upper()) if expected_letter else None
    return {
        "backbone": backbone.name, "question": question, "options": options,
        "expected_letter": expected_letter, "model_answer": answer,
        "parsed_letter": parsed, "correct": correct, "tokens_path": str(tokens_path),
    }


def write_json(path, obj):
    p = Path(path)
    p.parent.mkdir(parents=True, exist_ok=True)
    p.write_text(json.dumps(obj, indent=2, ensure_ascii=False))
    return str(p)
