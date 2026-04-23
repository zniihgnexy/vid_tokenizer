"""Command construction and execution for NVRC pipeline runs."""

from __future__ import annotations

import json
import shlex
import subprocess
import sys
from argparse import Namespace
from dataclasses import asdict
from pathlib import Path
from typing import Any

from .io import write_json
from .paths import (
    DEFAULT_COMPRESS_MODEL_CONFIG,
    DEFAULT_DATA_CONFIG,
    DEFAULT_EXP_CONFIG,
    DEFAULT_MODEL_CONFIG,
    default_output_root,
    find_repo_root,
    nvrc_root,
    smoke_script,
)
from .profiles import Profile, task_config_path
from .results import parse_results_file


def quoted(command: list[str]) -> str:
    return shlex.join(str(part) for part in command)


def run_streaming(command: list[str], cwd: Path, dry_run: bool) -> None:
    print(f"[command] {quoted(command)}")
    print(f"[cwd] {cwd}")
    if dry_run:
        return
    subprocess.run(command, cwd=cwd, check=True)


def run_json_command(command: list[str], cwd: Path, dry_run: bool) -> dict[str, Any]:
    print(f"[command] {quoted(command)}")
    print(f"[cwd] {cwd}")
    if dry_run:
        return {"dry_run": True, "command": command, "cwd": str(cwd)}
    completed = subprocess.run(
        command,
        cwd=cwd,
        check=True,
        text=True,
        capture_output=True,
    )
    if completed.stdout:
        print(completed.stdout)
    if completed.stderr:
        print(completed.stderr, file=sys.stderr)
    return json.loads(completed.stdout)


def build_smoke_command(repo_root: Path, profile: Profile, extra_args: list[str]) -> list[str]:
    return [sys.executable, str(smoke_script(repo_root)), *profile.smoke_args, *extra_args]


def maybe_append(command: list[str], flag: str, value: Any) -> None:
    if value is None:
        return
    if isinstance(value, (list, tuple)):
        command.append(flag)
        command.extend(str(item) for item in value)
        return
    command.extend([flag, str(value)])


def build_nvrc_command(args: Namespace, profile: Profile) -> list[str]:
    command = [
        sys.executable,
        "main_nvrc.py",
        "--exp-config",
        args.exp_config,
        "--train-data-config",
        args.train_data_config,
        "--eval-data-config",
        args.eval_data_config or args.train_data_config,
        "--train-task-config",
        args.train_task_config or str(task_config_path(profile)),
        "--eval-task-config",
        args.eval_task_config or args.train_task_config or str(task_config_path(profile)),
        "--compress-model-config",
        args.compress_model_config,
        "--model-config",
        args.model_config,
        "--output",
        str(args.output_root),
        "--exp-name",
        args.exp_name,
    ]

    maybe_append(command, "--train-dataset-dir", args.dataset_dir)
    maybe_append(command, "--eval-dataset-dir", args.dataset_dir)
    maybe_append(command, "--train-dataset", args.dataset)
    maybe_append(command, "--eval-dataset", args.dataset)
    maybe_append(command, "--train-video-size", args.video_size)
    maybe_append(command, "--eval-video-size", args.video_size)
    maybe_append(command, "--train-patch-size", args.patch_size)
    maybe_append(command, "--eval-patch-size", args.patch_size)
    maybe_append(command, "--epochs", args.epochs)
    maybe_append(command, "--warmup-epochs", args.warmup_epochs)
    maybe_append(command, "--eval-epochs", args.eval_epochs)
    maybe_append(command, "--rate-steps", args.rate_steps)
    maybe_append(command, "--num-frames", args.num_frames)
    maybe_append(command, "--start-frame", args.start_frame)
    maybe_append(command, "--intra-period", args.intra_period)
    maybe_append(command, "--seed", args.seed)
    maybe_append(command, "--workers", args.workers)
    maybe_append(command, "--train-batch-size", args.train_batch_size)
    maybe_append(command, "--eval-batch-size", args.eval_batch_size)
    maybe_append(command, "--teacher-type", args.teacher_type)
    if args.eval_only:
        command.extend(["--eval-only", "true"])
    command.extend(args.nvrc_arg)
    return command


def run_profile(args: Namespace, profile: Profile) -> dict[str, Any] | None:
    repo_root = find_repo_root(args.repo_root)
    args.output_root = Path(args.output_root).expanduser().resolve()
    args.output_root.mkdir(parents=True, exist_ok=True)
    experiment_dir = args.output_root / args.exp_name

    smoke_summary: dict[str, Any] | None = None
    if args.smoke_first:
        smoke_summary = run_json_command(
            build_smoke_command(repo_root, profile, args.smoke_arg),
            cwd=repo_root,
            dry_run=args.dry_run,
        )

    nvrc_command = build_nvrc_command(args, profile)
    run_streaming(nvrc_command, cwd=nvrc_root(repo_root), dry_run=args.dry_run)

    if args.dry_run:
        return None

    results_path = experiment_dir / "results" / "all.txt"
    if not results_path.exists():
        raise FileNotFoundError(
            f"Run completed but aggregated results were not found at {results_path}"
        )

    summary = {
        "profile": asdict(profile),
        "smoke_summary": smoke_summary,
        "experiment_dir": str(experiment_dir),
        "results_path": str(results_path),
        "metrics": parse_results_file(results_path),
        "nvrc_command": nvrc_command,
    }
    write_json(experiment_dir / "pipeline_summary.json", summary)
    print(json.dumps(summary, indent=2, sort_keys=True))
    return summary


def default_run_output_root(repo_root_arg: str | None = None) -> str:
    return str(default_output_root(find_repo_root(repo_root_arg)))


def default_exp_config() -> str:
    return str(DEFAULT_EXP_CONFIG)


def default_data_config() -> str:
    return str(DEFAULT_DATA_CONFIG)


def default_compress_model_config() -> str:
    return str(DEFAULT_COMPRESS_MODEL_CONFIG)


def default_model_config() -> str:
    return str(DEFAULT_MODEL_CONFIG)
