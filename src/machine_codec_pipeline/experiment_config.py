"""Experiment-bundle config: load a ``configs/experiments/*.yaml`` parameter
bundle, expose it to Python runners, save a resolved copy into each run's output
directory, and provide a small CLI so bash runners can read fields too.

One YAML file == one experiment == one reproducible parameter bundle. See
``configs/experiments/_schema.md`` for the full schema. Runners read only the
subset of keys relevant to their execution path; unknown keys are preserved and
copied into the run's ``resolved_config.yaml`` so nothing is silently dropped.
"""

from __future__ import annotations

import argparse
import json
import subprocess
import sys
from pathlib import Path
from typing import Any

import yaml

from .paths import find_repo_root


def load(path: str | Path) -> dict[str, Any]:
    """Load and lightly validate an experiment bundle YAML."""
    p = Path(path)
    if not p.is_absolute():
        # allow passing either a full path or a bundle name under configs/experiments
        repo = find_repo_root()
        if not p.exists():
            cand = repo / "configs" / "experiments" / p.name
            if cand.exists():
                p = cand
    if not p.exists():
        raise SystemExit(f"experiment config not found: {path}")
    with p.open() as fh:
        cfg = yaml.safe_load(fh) or {}
    if not isinstance(cfg, dict):
        raise SystemExit(f"experiment config is not a mapping: {p}")
    cfg.setdefault("name", p.stem)
    cfg["_config_path"] = str(p)
    return cfg


def _git_commit(repo_root: Path) -> str | None:
    try:
        out = subprocess.run(
            ["git", "rev-parse", "HEAD"],
            cwd=repo_root,
            capture_output=True,
            text=True,
            check=True,
        )
        return out.stdout.strip()
    except Exception:
        return None


def save_resolved(cfg: dict[str, Any], output_dir: str | Path) -> Path:
    """Write a copy of the resolved config (plus git commit) into a run's output
    directory, so the exact parameters of a run are always recoverable."""
    out = Path(output_dir)
    out.mkdir(parents=True, exist_ok=True)
    repo = find_repo_root()
    snapshot = dict(cfg)
    snapshot["_git_commit"] = _git_commit(repo)
    dest = out / "resolved_config.yaml"
    with dest.open("w") as fh:
        yaml.safe_dump(snapshot, fh, sort_keys=False, allow_unicode=True)
    return dest


def get(cfg: dict[str, Any], dotted_key: str, default: Any = None) -> Any:
    """Fetch a nested value by ``a.b.c`` dotted path."""
    node: Any = cfg
    for part in dotted_key.split("."):
        if isinstance(node, dict) and part in node:
            node = node[part]
        else:
            return default
    return node


# ── CLI (used by bash runners) ──────────────────────────────────────────────


def _cli(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="cmd", required=True)

    p_get = sub.add_parser("get", help="print a dotted-key scalar (for bash)")
    p_get.add_argument("config")
    p_get.add_argument("key")
    p_get.add_argument("--default", default="")

    p_vids = sub.add_parser(
        "list-videos", help="print 'tag<TAB>path' lines from videos[] (for bash)"
    )
    p_vids.add_argument("config")

    p_save = sub.add_parser("save", help="write resolved_config.yaml into a dir")
    p_save.add_argument("config")
    p_save.add_argument("output_dir")

    p_show = sub.add_parser("show", help="dump the loaded config as JSON")
    p_show.add_argument("config")

    args = parser.parse_args(argv)
    cfg = load(args.config)

    if args.cmd == "get":
        val = get(cfg, args.key, args.default)
        print("" if val is None else val)
    elif args.cmd == "list-videos":
        for v in cfg.get("videos", []):
            tag = v.get("name") or v.get("tag")
            path = v.get("path", "")
            if tag and path:
                print(f"{tag}\t{path}")
    elif args.cmd == "save":
        print(save_resolved(cfg, args.output_dir))
    elif args.cmd == "show":
        printable = {k: v for k, v in cfg.items() if not k.startswith("_")}
        print(json.dumps(printable, indent=2, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(_cli())
