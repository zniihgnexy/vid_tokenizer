"""Command-line interface for machine-oriented NVRC pipeline orchestration."""

from __future__ import annotations

import argparse
import json
from dataclasses import asdict
from pathlib import Path

from .commands import (
    build_smoke_command,
    default_compress_model_config,
    default_data_config,
    default_exp_config,
    default_model_config,
    default_run_output_root,
    run_json_command,
    run_chunked_profile,
    run_profile,
)
from .demo import run_demo
from .io import write_json
from .paths import find_repo_root
from .profiles import PROFILES, ensure_profile
from .results import compare_results
from .data.video_data import prepare_video_window, split_png_video_chunks
from .evaluation.video_qa import (
    generate_openai_chunked_video_qa_report,
    generate_openai_video_qa_report,
)


def command_list_profiles(_args: argparse.Namespace) -> int:
    payload = {name: asdict(profile) for name, profile in sorted(PROFILES.items())}
    print(json.dumps(payload, indent=2, sort_keys=True))
    return 0


def command_smoke(args: argparse.Namespace) -> int:
    repo_root = find_repo_root(args.repo_root)
    profile = ensure_profile(args.profile)
    payload = run_json_command(
        build_smoke_command(repo_root, profile, args.smoke_arg),
        cwd=repo_root,
        dry_run=args.dry_run,
    )
    if args.summary_json and not args.dry_run:
        write_json(Path(args.summary_json).expanduser().resolve(), payload)
    return 0


def command_run(args: argparse.Namespace) -> int:
    run_profile(args, ensure_profile(args.profile))
    return 0


def command_run_chunked(args: argparse.Namespace) -> int:
    run_chunked_profile(args, ensure_profile(args.profile))
    return 0


def command_compare(args: argparse.Namespace) -> int:
    print(json.dumps(compare_results(args.results), indent=2, sort_keys=True))
    return 0


def command_demo(args: argparse.Namespace) -> int:
    comparison = run_demo(Path(args.output_root).expanduser().resolve())
    print(json.dumps(comparison, indent=2, sort_keys=True))
    return 0


def command_prepare_video(args: argparse.Namespace) -> int:
    summary = prepare_video_window(
        video_path=Path(args.video_path),
        output_dir=Path(args.output_dir),
        start_frame=args.start_frame,
        num_frames=args.num_frames,
        width=args.width,
        height=args.height,
        overwrite=args.overwrite,
        chunk_size=args.chunk_size,
        chunk_output_root=Path(args.chunk_output_root) if args.chunk_output_root else None,
        chunk_prefix=args.chunk_prefix,
        sampling=args.sampling,
    )
    if args.summary_json:
        write_json(Path(args.summary_json).expanduser().resolve(), summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def command_split_chunks(args: argparse.Namespace) -> int:
    summary = split_png_video_chunks(
        source_dir=Path(args.source_dir),
        output_root=Path(args.output_root),
        chunk_size=args.chunk_size,
        prefix=args.prefix,
        overwrite=args.overwrite,
    )
    if args.summary_json:
        write_json(Path(args.summary_json).expanduser().resolve(), summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return 0


def command_video_qa_report(args: argparse.Namespace) -> int:
    if args.provider != "openai":
        raise ValueError(f"Unsupported provider: {args.provider}")
    comparison = generate_openai_video_qa_report(
        repo_root=find_repo_root(args.repo_root),
        report_root=Path(args.report_root).expanduser().resolve(),
        model=args.model,
        sample_count=args.sample_count,
        output_dir=Path(args.output_dir).expanduser().resolve() if args.output_dir else None,
    )
    print(json.dumps(comparison, indent=2, sort_keys=True))
    return 0


def command_video_qa_chunked_report(args: argparse.Namespace) -> int:
    if args.provider != "openai":
        raise ValueError(f"Unsupported provider: {args.provider}")
    comparison = generate_openai_chunked_video_qa_report(
        repo_root=find_repo_root(args.repo_root),
        chunked_summary_path=Path(args.chunked_summary).expanduser().resolve(),
        question=args.question,
        options=args.option,
        answer_index=args.answer_index,
        model=args.model,
        sample_count=args.sample_count,
        output_dir=Path(args.output_dir).expanduser().resolve() if args.output_dir else None,
        use_embedding_mode=args.use_embedding_mode,
        n_trials=args.n_trials,
        temperature=args.temperature,
    )
    print(json.dumps(comparison, indent=2, sort_keys=True))
    return 0


def add_repo_root(parser: argparse.ArgumentParser) -> None:
    parser.add_argument(
        "--repo-root",
        type=str,
        default=None,
        help="Outer repository root. Auto-detected when omitted.",
    )


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(
        description="Unified launcher for the machine-oriented NVRC pipeline."
    )
    subparsers = parser.add_subparsers(dest="command", required=True)

    list_parser = subparsers.add_parser(
        "list-profiles", help="Print the built-in experiment profile registry."
    )
    list_parser.set_defaults(func=command_list_profiles)

    smoke_parser = subparsers.add_parser(
        "smoke", help="Run the teacher-path smoke test for one built-in profile."
    )
    add_repo_root(smoke_parser)
    smoke_parser.add_argument("--profile", required=True, choices=sorted(PROFILES))
    smoke_parser.add_argument(
        "--smoke-arg",
        action="append",
        default=[],
        help="Additional argument forwarded to tools/smoke_teacher_loss.py.",
    )
    smoke_parser.add_argument("--summary-json", type=str, default=None)
    smoke_parser.add_argument("--dry-run", action="store_true")
    smoke_parser.set_defaults(func=command_smoke)

    prepare_parser = subparsers.add_parser(
        "prepare-video",
        help="Extract one bounded video window into PNG frames and optionally split it into chunks.",
    )
    prepare_parser.add_argument("--video-path", required=True)
    prepare_parser.add_argument("--output-dir", required=True)
    prepare_parser.add_argument("--start-frame", type=int, default=0)
    prepare_parser.add_argument("--num-frames", type=int, required=True)
    prepare_parser.add_argument("--width", type=int, default=32)
    prepare_parser.add_argument("--height", type=int, default=32)
    prepare_parser.add_argument("--sampling", type=str, default="contiguous",
                                choices=["contiguous", "uniform"],
                                help="contiguous = first N frames; uniform = N frames evenly spaced across the whole clip")
    prepare_parser.add_argument("--chunk-size", type=int, default=None)
    prepare_parser.add_argument("--chunk-output-root", type=str, default=None)
    prepare_parser.add_argument("--chunk-prefix", type=str, default=None)
    prepare_parser.add_argument("--summary-json", type=str, default=None)
    prepare_parser.add_argument("--overwrite", action="store_true")
    prepare_parser.set_defaults(func=command_prepare_video)

    split_parser = subparsers.add_parser(
        "split-chunks",
        help="Split an existing PNG frame directory into chunk datasets.",
    )
    split_parser.add_argument("--source-dir", required=True)
    split_parser.add_argument("--output-root", required=True)
    split_parser.add_argument("--chunk-size", type=int, required=True)
    split_parser.add_argument("--prefix", type=str, default=None)
    split_parser.add_argument("--summary-json", type=str, default=None)
    split_parser.add_argument("--overwrite", action="store_true")
    split_parser.set_defaults(func=command_split_chunks)

    run_parser = subparsers.add_parser(
        "run",
        help="Run one NVRC experiment profile through the full main_nvrc.py pipeline.",
    )
    add_repo_root(run_parser)
    run_parser.add_argument("--profile", required=True, choices=sorted(PROFILES))
    run_parser.add_argument("--exp-name", required=True)
    run_parser.add_argument(
        "--output-root",
        type=str,
        default=default_run_output_root(),
        help="Directory whose children become per-run experiment folders.",
    )
    run_parser.add_argument("--dataset-dir", type=str, default=None)
    run_parser.add_argument("--dataset", type=str, default=None)
    run_parser.add_argument("--video-size", type=int, nargs="+", default=None)
    run_parser.add_argument("--patch-size", type=int, nargs="+", default=None)
    run_parser.add_argument("--num-frames", type=int, default=None)
    run_parser.add_argument("--start-frame", type=int, default=None)
    run_parser.add_argument("--intra-period", type=int, default=None)
    run_parser.add_argument("--epochs", type=int, default=None)
    run_parser.add_argument("--warmup-epochs", type=int, default=None)
    run_parser.add_argument("--eval-epochs", type=int, default=None)
    run_parser.add_argument("--rate-steps", type=int, default=None)
    run_parser.add_argument("--seed", type=int, default=None)
    run_parser.add_argument("--workers", type=int, default=None)
    run_parser.add_argument("--train-batch-size", type=int, default=None)
    run_parser.add_argument("--eval-batch-size", type=int, default=None)
    run_parser.add_argument("--teacher-type", type=str, default=None)
    run_parser.add_argument(
        "--train-enable-log",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Ask NVRC to export training-side visual outputs.",
    )
    run_parser.add_argument(
        "--eval-enable-log",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Ask NVRC to export evaluation/decoded PNG outputs.",
    )
    run_parser.add_argument("--eval-only", action="store_true")
    run_parser.add_argument("--exp-config", type=str, default=default_exp_config())
    run_parser.add_argument("--train-data-config", type=str, default=default_data_config())
    run_parser.add_argument("--eval-data-config", type=str, default=None)
    run_parser.add_argument("--train-task-config", type=str, default=None)
    run_parser.add_argument("--eval-task-config", type=str, default=None)
    run_parser.add_argument(
        "--compress-model-config",
        type=str,
        default=default_compress_model_config(),
    )
    run_parser.add_argument("--model-config", type=str, default=default_model_config())
    run_parser.add_argument(
        "--smoke-first",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Run the matching smoke test before the main NVRC command.",
    )
    run_parser.add_argument(
        "--smoke-arg",
        action="append",
        default=[],
        help="Additional argument forwarded to tools/smoke_teacher_loss.py.",
    )
    run_parser.add_argument(
        "--nvrc-arg",
        action="append",
        default=[],
        help="Additional argument forwarded directly to third_party/NVRC/main_nvrc.py.",
    )
    run_parser.add_argument("--dry-run", action="store_true")
    run_parser.set_defaults(func=command_run)

    run_chunked_parser = subparsers.add_parser(
        "run-chunked",
        help="Run one NVRC profile over every dataset chunk listed in a chunk index.",
    )
    add_repo_root(run_chunked_parser)
    run_chunked_parser.add_argument("--profile", required=True, choices=sorted(PROFILES))
    run_chunked_parser.add_argument("--chunk-index", required=True)
    run_chunked_parser.add_argument("--exp-name-prefix", required=True)
    run_chunked_parser.add_argument(
        "--output-root",
        type=str,
        default=default_run_output_root(),
        help="Directory whose children become per-run experiment folders.",
    )
    run_chunked_parser.add_argument("--limit-chunks", type=int, default=None)
    run_chunked_parser.add_argument("--video-size", type=int, nargs="+", default=None)
    run_chunked_parser.add_argument("--patch-size", type=int, nargs="+", default=None)
    run_chunked_parser.add_argument("--num-frames", type=int, default=None)
    run_chunked_parser.add_argument("--start-frame", type=int, default=None)
    run_chunked_parser.add_argument("--intra-period", type=int, default=None)
    run_chunked_parser.add_argument("--epochs", type=int, default=None)
    run_chunked_parser.add_argument("--warmup-epochs", type=int, default=None)
    run_chunked_parser.add_argument("--eval-epochs", type=int, default=None)
    run_chunked_parser.add_argument("--rate-steps", type=int, default=None)
    run_chunked_parser.add_argument("--seed", type=int, default=None)
    run_chunked_parser.add_argument("--workers", type=int, default=None)
    run_chunked_parser.add_argument("--train-batch-size", type=int, default=None)
    run_chunked_parser.add_argument("--eval-batch-size", type=int, default=None)
    run_chunked_parser.add_argument("--teacher-type", type=str, default=None)
    run_chunked_parser.add_argument(
        "--train-enable-log",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Ask NVRC to export training-side visual outputs for every chunk.",
    )
    run_chunked_parser.add_argument(
        "--eval-enable-log",
        action=argparse.BooleanOptionalAction,
        default=None,
        help="Ask NVRC to export evaluation/decoded PNG outputs for every chunk.",
    )
    run_chunked_parser.add_argument("--eval-only", action="store_true")
    run_chunked_parser.add_argument("--exp-config", type=str, default=default_exp_config())
    run_chunked_parser.add_argument(
        "--train-data-config", type=str, default=default_data_config()
    )
    run_chunked_parser.add_argument("--eval-data-config", type=str, default=None)
    run_chunked_parser.add_argument("--train-task-config", type=str, default=None)
    run_chunked_parser.add_argument("--eval-task-config", type=str, default=None)
    run_chunked_parser.add_argument(
        "--compress-model-config",
        type=str,
        default=default_compress_model_config(),
    )
    run_chunked_parser.add_argument(
        "--model-config", type=str, default=default_model_config()
    )
    run_chunked_parser.add_argument(
        "--smoke-first",
        action=argparse.BooleanOptionalAction,
        default=True,
        help="Run the matching smoke test once before the chunk loop.",
    )
    run_chunked_parser.add_argument(
        "--smoke-arg",
        action="append",
        default=[],
        help="Additional argument forwarded to tools/smoke_teacher_loss.py.",
    )
    run_chunked_parser.add_argument(
        "--nvrc-arg",
        action="append",
        default=[],
        help="Additional argument forwarded directly to third_party/NVRC/main_nvrc.py.",
    )
    run_chunked_parser.add_argument("--dry-run", action="store_true")
    run_chunked_parser.set_defaults(func=command_run_chunked)

    compare_parser = subparsers.add_parser(
        "compare",
        help="Compare one or more historical results/all.txt files.",
    )
    compare_parser.add_argument(
        "results",
        nargs="+",
        help="Result files or experiment directories that contain results/all.txt.",
    )
    compare_parser.set_defaults(func=command_compare)

    demo_parser = subparsers.add_parser(
        "demo",
        help="Create and compare a tiny synthetic output-contract demo.",
    )
    demo_parser.add_argument(
        "--output-root",
        type=str,
        default="outputs/demo",
        help="Where to write the demo run folders.",
    )
    demo_parser.set_defaults(func=command_demo)

    video_qa_parser = subparsers.add_parser(
        "video-qa-report",
        help="Run an OpenAI visual QA comparison over a single-video analysis bundle.",
    )
    add_repo_root(video_qa_parser)
    video_qa_parser.add_argument(
        "--report-root",
        required=True,
        help="Path to an existing single-video report bundle that contains single_video_report.json.",
    )
    video_qa_parser.add_argument(
        "--provider",
        default="openai",
        choices=["openai"],
        help="Downstream VLM provider. Only OpenAI is implemented in this example.",
    )
    video_qa_parser.add_argument(
        "--model",
        default="gpt-4.1-mini",
        help="OpenAI Responses API model name used for the visual multiple-choice comparison.",
    )
    video_qa_parser.add_argument(
        "--sample-count",
        type=int,
        default=8,
        help="How many evenly spaced frames to include in each contact sheet.",
    )
    video_qa_parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Optional destination for the generated contact sheets and report files.",
    )
    video_qa_parser.set_defaults(func=command_video_qa_report)

    video_qa_chunked_parser = subparsers.add_parser(
        "video-qa-chunked-report",
        help="Run an OpenAI visual QA comparison over a chunked full-video summary.",
    )
    add_repo_root(video_qa_chunked_parser)
    video_qa_chunked_parser.add_argument(
        "--chunked-summary",
        required=True,
        help="Path to one run-chunked aggregate summary JSON.",
    )
    video_qa_chunked_parser.add_argument(
        "--provider",
        default="openai",
        choices=["openai"],
        help="Downstream LLM provider.",
    )
    video_qa_chunked_parser.add_argument("--model", default="gpt-4.1-mini")
    video_qa_chunked_parser.add_argument(
        "--question",
        required=True,
        help="Multiple-choice question to ask about the sampled full-video contact sheet.",
    )
    video_qa_chunked_parser.add_argument(
        "--option",
        action="append",
        required=True,
        help="Repeat once per answer option.",
    )
    video_qa_chunked_parser.add_argument(
        "--answer-index",
        type=int,
        required=True,
        help="Zero-based index of the official answer within --option values.",
    )
    video_qa_chunked_parser.add_argument(
        "--sample-count",
        type=int,
        default=8,
        help="How many evenly spaced frames across the available chunked-video coverage to show.",
    )
    video_qa_chunked_parser.add_argument(
        "--output-dir",
        type=str,
        default=None,
        help="Optional destination for the generated contact sheets and report files.",
    )
    video_qa_chunked_parser.add_argument(
        "--use-embedding-mode",
        action="store_true",
        default=False,
        help="Use ResNet18 embedding visualization instead of pixel contact sheets for VLM input.",
    )
    video_qa_chunked_parser.add_argument(
        "--n-trials",
        type=int,
        default=1,
        help="Number of independent VLM trials per view. >1 enables majority-vote and disagreement reporting.",
    )
    video_qa_chunked_parser.add_argument(
        "--temperature",
        type=float,
        default=None,
        help="OpenAI 'temperature' (0 = greedy / deterministic). Omit to use API default.",
    )
    video_qa_chunked_parser.set_defaults(func=command_video_qa_chunked_report)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
