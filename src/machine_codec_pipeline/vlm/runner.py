"""Shared CLI for the per-model root runners (run_internvl.py / run_instructblip.py).

Both root scripts call ``run_cli(default_backbone)``; the only thing that
differs between them is which backbone/config they default to. All actual
logic lives here and in the backbone classes, so the runners stay 3 lines.

Actions:
  smoke       -- load full model, caption one image (sanity).
  self-judge  -- free-form QA: oracle(raw frames) vs codec(tokens), VLM judges.
  mcq         -- multiple-choice QA on codec tokens.
"""

from __future__ import annotations

import argparse
from pathlib import Path

import yaml

from . import build_backbone
from .base import run_self_judge, run_mcq, write_json


def _load_cfg(path):
    return yaml.safe_load(Path(path).read_text())


def run_cli(default_backbone: str, argv=None):
    ap = argparse.ArgumentParser(description=f"{default_backbone} VLM runner")
    ap.add_argument("--config", required=True, help="configs/vlm/<model>.yaml")
    ap.add_argument("--action", required=True,
                    choices=["smoke", "self-judge", "mcq"])
    ap.add_argument("--qa-tokens", default=None)
    ap.add_argument("--raw-chunk-dir", default=None)
    ap.add_argument("--questions-file", default=None)
    ap.add_argument("--output-json", default=None)
    ap.add_argument("--sample-count", type=int, default=4)
    ap.add_argument("--image", default=None, help="image path for smoke")
    ap.add_argument("--question", default=None)
    ap.add_argument("--option", action="append", default=None)
    ap.add_argument("--expected-letter", default=None)
    args = ap.parse_args(argv)

    cfg = _load_cfg(args.config)
    backbone = build_backbone(
        cfg.get("backbone", default_backbone),
        model_path=cfg["model_path"],
        device=cfg.get("device", "cuda"),
        align_layer=int(cfg.get("align_layer", 12)),
        input_size=int(cfg.get("input_size", 448)),
    )

    if args.action == "smoke":
        backbone.load_full()
        img = args.image or cfg.get("smoke_image")
        if not img:
            raise SystemExit("smoke needs --image or cfg.smoke_image")
        ans = backbone.answer_pixels([img], args.question or "Describe this image in one sentence.")
        print(f"[{backbone.name}] smoke answer: {ans}")
        return

    if args.action == "self-judge":
        if not (args.qa_tokens and args.raw_chunk_dir and args.questions_file):
            raise SystemExit("self-judge needs --qa-tokens --raw-chunk-dir --questions-file")
        backbone.load_full()
        questions = [l.strip() for l in Path(args.questions_file).read_text().splitlines() if l.strip()]
        result = run_self_judge(backbone, args.qa_tokens, args.raw_chunk_dir,
                                questions, sample_count=args.sample_count)
        if args.output_json:
            print(f"[{backbone.name}] wrote {write_json(args.output_json, result)}")
        print(f"[{backbone.name}] agreement_rate = {result['agreement_rate']:.3f} "
              f"({result['num_agree']}/{result['num_questions']})")
        return

    if args.action == "mcq":
        if not args.qa_tokens:
            raise SystemExit("mcq needs --qa-tokens")
        backbone.load_full()
        question = args.question or "What outdoor or agricultural task is the camera wearer performing?"
        options = list(args.option) if args.option else [
            "Mowing a lawn.", "Constructing a building.", "Digging or tilling soil.",
            "Painting an outdoor surface.", "Cleaning an outdoor area."]
        result = run_mcq(backbone, args.qa_tokens, question, options,
                         expected_letter=args.expected_letter)
        if args.output_json:
            print(f"[{backbone.name}] wrote {write_json(args.output_json, result)}")
        print(f"[{backbone.name}] answer={result['model_answer']!r} "
              f"parsed={result['parsed_letter']} correct={result['correct']}")
        return
