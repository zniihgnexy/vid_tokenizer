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
    run_profile,
)
from .demo import run_demo
from .io import write_json
from .paths import find_repo_root
from .profiles import PROFILES, ensure_profile
from .results import compare_results


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


def command_compare(args: argparse.Namespace) -> int:
    print(json.dumps(compare_results(args.results), indent=2, sort_keys=True))
    return 0


def command_demo(args: argparse.Namespace) -> int:
    comparison = run_demo(Path(args.output_root).expanduser().resolve())
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
        default="runs/demo",
        help="Where to write the demo run folders.",
    )
    demo_parser.set_defaults(func=command_demo)

    return parser


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    raise SystemExit(main())
