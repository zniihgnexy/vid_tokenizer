"""OpenAI-backed video QA comparison for single-video and chunked-video bundles."""

from __future__ import annotations

import base64
import json
import mimetypes
import os
import shutil
import subprocess
import textwrap
import urllib.error
import urllib.request
from pathlib import Path
from typing import Any

from PIL import Image, ImageDraw, ImageOps

from .io import write_json
from .paths import find_repo_root

_RESAMPLE = Image.Resampling.LANCZOS if hasattr(Image, "Resampling") else Image.LANCZOS


def _load_json(path: Path) -> dict[str, Any]:
    return json.loads(path.read_text(encoding="utf-8"))


def _read_key_from_dotenv(path: Path, key: str) -> str | None:
    if not path.exists():
        return None
    for raw_line in path.read_text(encoding="utf-8").splitlines():
        line = raw_line.strip()
        if not line or line.startswith("#") or "=" not in line:
            continue
        left, _, right = line.partition("=")
        left = left.strip()
        if left.startswith("export "):
            left = left[len("export ") :].strip()
        if left != key:
            continue
        value = right.strip()
        if len(value) >= 2 and value[0] == value[-1] and value[0] in {"'", '"'}:
            value = value[1:-1]
        return value
    return None


def _resolve_openai_api_key(repo_root: Path) -> str:
    api_key = os.environ.get("OPENAI_API_KEY")
    if api_key:
        return api_key
    api_key = _read_key_from_dotenv(repo_root / ".env", "OPENAI_API_KEY")
    if api_key:
        return api_key
    raise RuntimeError(
        "OPENAI_API_KEY is not available in the process environment or repo .env file."
    )


def _resolve_source_video_path(report_root: Path, q_uid: str) -> Path:
    direct = report_root / "videos" / f"{q_uid}.mp4"
    if direct.exists():
        return direct
    candidates = sorted((report_root / "videos").glob("*.mp4"))
    if len(candidates) == 1:
        return candidates[0]
    raise FileNotFoundError(
        f"Could not resolve the source mp4 for q_uid={q_uid} under {report_root / 'videos'}."
    )


def _resolve_reconstructed_frame_paths(report_root: Path, q_uid: str) -> list[Path]:
    candidates = sorted(report_root.glob(f"runs/*log*/outputs/**/{q_uid}_mid*/*.png"))
    if not candidates:
        raise FileNotFoundError(
            f"Could not find reconstructed PNG frames for q_uid={q_uid} under {report_root / 'runs'}."
        )
    return candidates


def _sample_positions(frame_count: int, sample_count: int) -> list[int]:
    if frame_count <= 0:
        raise ValueError("frame_count must be positive.")
    if sample_count <= 0:
        raise ValueError("sample_count must be positive.")
    if sample_count >= frame_count:
        return list(range(frame_count))
    if sample_count == 1:
        return [frame_count // 2]
    return sorted(
        {
            round(index * (frame_count - 1) / (sample_count - 1))
            for index in range(sample_count)
        }
    )


def _extract_source_frames(
    video_path: Path,
    absolute_indices: list[int],
    output_dir: Path,
) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    paths: list[Path] = []
    for absolute_index in absolute_indices:
        frame_path = output_dir / f"{absolute_index:06d}.png"
        command = [
            "ffmpeg",
            "-hide_banner",
            "-loglevel",
            "error",
            "-y",
            "-i",
            str(video_path),
            "-vf",
            f"select=eq(n\\,{absolute_index})",
            "-vframes",
            "1",
            str(frame_path),
        ]
        subprocess.run(command, check=True, capture_output=True, text=True)
        if not frame_path.exists():
            raise FileNotFoundError(f"ffmpeg did not materialize {frame_path}.")
        paths.append(frame_path)
    return paths


def _copy_reconstructed_frames(
    frame_paths: list[Path],
    clip_positions: list[int],
    output_dir: Path,
) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    selected: list[Path] = []
    for clip_position in clip_positions:
        source = frame_paths[clip_position]
        target = output_dir / source.name
        if source.resolve() != target.resolve():
            shutil.copy2(source, target)
        selected.append(target)
    return selected


def _copy_selected_frames(frame_paths: list[Path], output_dir: Path) -> list[Path]:
    output_dir.mkdir(parents=True, exist_ok=True)
    selected: list[Path] = []
    for index, source in enumerate(frame_paths):
        target = output_dir / f"{index:04d}_{source.name}"
        if source.resolve() != target.resolve():
            shutil.copy2(source, target)
        selected.append(target)
    return selected


def _build_contact_sheet(
    image_paths: list[Path],
    output_path: Path,
    *,
    title: str,
    columns: int = 4,
    cell_size: tuple[int, int] = (256, 256),
) -> Path:
    if not image_paths:
        raise ValueError("image_paths must not be empty.")

    rows = (len(image_paths) + columns - 1) // columns
    header_height = 80
    gutter = 12
    width = columns * cell_size[0] + (columns + 1) * gutter
    height = header_height + rows * cell_size[1] + (rows + 1) * gutter
    sheet = Image.new("RGB", (width, height), color=(250, 248, 244))
    drawer = ImageDraw.Draw(sheet)
    drawer.text((gutter, 18), title, fill=(40, 40, 40))

    for index, image_path in enumerate(image_paths):
        row = index // columns
        column = index % columns
        x = gutter + column * (cell_size[0] + gutter)
        y = header_height + gutter + row * (cell_size[1] + gutter)
        with Image.open(image_path) as image:
            tile = ImageOps.contain(image.convert("RGB"), cell_size, _RESAMPLE)
        background = Image.new("RGB", cell_size, color=(233, 227, 217))
        offset = ((cell_size[0] - tile.width) // 2, (cell_size[1] - tile.height) // 2)
        background.paste(tile, offset)
        sheet.paste(background, (x, y))
        drawer.rectangle(
            [(x, y), (x + cell_size[0], y + cell_size[1])],
            outline=(176, 164, 150),
            width=2,
        )
        drawer.text((x + 8, y + 8), f"frame {index}", fill=(40, 40, 40))

    output_path.parent.mkdir(parents=True, exist_ok=True)
    sheet.save(output_path)
    return output_path


def _encode_image_as_data_url(path: Path) -> str:
    mime_type, _ = mimetypes.guess_type(path.name)
    mime_type = mime_type or "image/png"
    encoded = base64.b64encode(path.read_bytes()).decode("ascii")
    return f"data:{mime_type};base64,{encoded}"


def _build_prompt(question: str, options: list[str]) -> str:
    numbered_options = "\n".join(
        f"{index}. {option}" for index, option in enumerate(options)
    )
    return textwrap.dedent(
        f"""
        You are evaluating one egocentric-video contact sheet. Answer only from the visual evidence in the image.

        Return JSON only with this schema:
        {{
          "choice_index": <integer>,
          "choice_text": <string>,
          "confidence": <number between 0 and 1>,
          "rationale": <short string>
        }}

        Multiple-choice question:
        {question}

        Options:
        {numbered_options}
        """
    ).strip()


def _extract_output_text(payload: dict[str, Any]) -> str:
    output_text = payload.get("output_text")
    if isinstance(output_text, str) and output_text.strip():
        return output_text.strip()

    chunks: list[str] = []
    for item in payload.get("output", []):
        if not isinstance(item, dict):
            continue
        for content in item.get("content", []):
            if not isinstance(content, dict):
                continue
            if content.get("type") in {"output_text", "text"}:
                text = content.get("text") or content.get("value")
                if isinstance(text, str) and text.strip():
                    chunks.append(text.strip())
    if chunks:
        return "\n".join(chunks)
    raise RuntimeError("OpenAI response did not contain readable output text.")


def _parse_json_object(text: str) -> dict[str, Any]:
    candidate = text.strip()
    if candidate.startswith("```"):
        candidate = candidate.strip("`")
        candidate = candidate.replace("json\n", "", 1).strip()
    try:
        return json.loads(candidate)
    except json.JSONDecodeError:
        start = candidate.find("{")
        end = candidate.rfind("}")
        if start >= 0 and end > start:
            return json.loads(candidate[start : end + 1])
        raise


def _normalize_choice(choice_index: Any, option_count: int) -> int | None:
    if isinstance(choice_index, bool):
        return None
    if isinstance(choice_index, int) and 0 <= choice_index < option_count:
        return choice_index
    return None


def _call_openai_responses(
    *,
    api_key: str,
    model: str,
    prompt: str,
    image_path: Path,
) -> dict[str, Any]:
    payload = {
        "model": model,
        "input": [
            {
                "role": "user",
                "content": [
                    {"type": "input_text", "text": prompt},
                    {
                        "type": "input_image",
                        "image_url": _encode_image_as_data_url(image_path),
                    },
                ],
            }
        ],
    }
    request = urllib.request.Request(
        "https://api.openai.com/v1/responses",
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key}",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=180) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise RuntimeError(f"OpenAI API request failed: {exc.code} {body}") from exc


def _evaluate_view(
    *,
    api_key: str,
    model: str,
    question: str,
    options: list[str],
    answer_index: int,
    image_path: Path,
    label: str,
) -> dict[str, Any]:
    prompt = _build_prompt(question, options)
    raw_response = _call_openai_responses(
        api_key=api_key,
        model=model,
        prompt=prompt,
        image_path=image_path,
    )
    output_text = _extract_output_text(raw_response)
    parsed = _parse_json_object(output_text)
    predicted_index = _normalize_choice(parsed.get("choice_index"), len(options))
    predicted_text = parsed.get("choice_text")
    correct = predicted_index == answer_index if predicted_index is not None else None
    return {
        "label": label,
        "image_path": str(image_path),
        "prompt": prompt,
        "raw_response": raw_response,
        "output_text": output_text,
        "parsed": parsed,
        "predicted_index": predicted_index,
        "predicted_text": predicted_text,
        "correct": correct,
    }


def _comparison_verdict(original: dict[str, Any], reconstructed: dict[str, Any]) -> dict[str, str]:
    original_correct = bool(original.get("correct"))
    reconstructed_correct = bool(reconstructed.get("correct"))
    if original_correct and reconstructed_correct:
        return {
            "status": "parity_correct",
            "summary": "Both the original and reconstructed contact sheets answered the question correctly.",
        }
    if original_correct and not reconstructed_correct:
        return {
            "status": "degraded_after_compression",
            "summary": "The original contact sheet answered correctly, but the reconstructed contact sheet failed.",
        }
    if not original_correct and reconstructed_correct:
        return {
            "status": "reconstructed_only_correct",
            "summary": "The reconstructed contact sheet answered correctly while the original contact sheet missed it.",
        }
    return {
        "status": "both_failed",
        "summary": "Neither contact sheet produced the correct multiple-choice answer.",
    }


def _format_choice(index: int | None, options: list[str]) -> str:
    if index is None:
        return "unparsed"
    return f"[{index}] {options[index]}"


def _extract_retrieval_metrics(report_payload: dict[str, Any]) -> dict[str, Any]:
    compressed = (
        report_payload.get("downstream_retrieval", {})
        .get("compressed_feature_retrieval", {})
    )
    return {
        "top1_accuracy": compressed.get("top1_accuracy"),
        "mean_match_rank": compressed.get("mean_match_rank"),
        "mean_margin_vs_best_nonmatch": compressed.get("mean_margin_vs_best_nonmatch"),
    }


def _write_markdown_report(
    output_path: Path,
    *,
    model: str,
    sample: dict[str, Any],
    frame_selection: dict[str, Any],
    compression_metrics: dict[str, Any],
    retrieval_metrics: dict[str, Any],
    original_eval: dict[str, Any],
    reconstructed_eval: dict[str, Any],
    verdict: dict[str, str],
) -> None:
    answer_index = sample["answer_index"]
    options = sample["options"]
    answer_text = options[answer_index]
    content = textwrap.dedent(
        f"""
        # OpenAI Single-Video QA Comparison

        - Model: `{model}`
        - Sample UID: `{sample["q_uid"]}`
        - Question: {sample["question"]}
        - Official answer: [{answer_index}] {answer_text}
        - Compression PSNR: {compression_metrics.get("psnr_avg")}
        - Compression teacher-MSE: {compression_metrics.get("teacher_mse_avg")}
        - Compression bpp: {compression_metrics.get("bpp_avg")}
        - Compressed retrieval top-1: {retrieval_metrics.get("top1_accuracy")}

        ## OpenAI Predictions

        - Original contact sheet: {_format_choice(original_eval.get("predicted_index"), options)}
        - Original correct: {original_eval.get("correct")}
        - Reconstructed contact sheet: {_format_choice(reconstructed_eval.get("predicted_index"), options)}
        - Reconstructed correct: {reconstructed_eval.get("correct")}
        - Verdict: {verdict["status"]}

        ## Interpretation

        {verdict["summary"]}

        This comparison uses {len(frame_selection["selected_clip_positions"])} evenly spaced frames from the same
        32-frame clip for both the original video and the reconstructed outputs. It is a user-facing sanity
        check rather than a replacement for the existing retrieval metric.

        ## Rationales

        ### Original

        {original_eval["parsed"].get("rationale", original_eval["output_text"])}

        ### Reconstructed

        {reconstructed_eval["parsed"].get("rationale", reconstructed_eval["output_text"])}
        """
    ).strip()
    output_path.write_text(content + "\n", encoding="utf-8")


def _find_chunk_run_summary(
    *,
    chunk_name: str,
    runs: list[dict[str, Any]],
) -> dict[str, Any]:
    for run in runs:
        if run.get("chunk_name") == chunk_name:
            return run

    matches = [
        run
        for run in runs
        if Path(str(run.get("experiment_dir", ""))).name.endswith(chunk_name)
    ]
    if len(matches) == 1:
        return matches[0]
    raise FileNotFoundError(
        f"Could not match chunk_name={chunk_name} to a run summary in the chunked summary."
    )


def _resolve_chunk_decoded_dir(experiment_dir: Path, chunk_name: str) -> Path:
    candidates = [
        experiment_dir / "outputs" / "all" / "decoded" / chunk_name,
        experiment_dir / "outputs" / "0000" / "decoded" / "None" / chunk_name,
    ]
    for candidate in candidates:
        if candidate.is_dir():
            return candidate

    outputs_root = experiment_dir / "outputs"
    matches = [
        path
        for path in outputs_root.rglob(chunk_name)
        if path.is_dir() and "decoded" in path.parts
    ]
    if not matches:
        raise FileNotFoundError(
            f"Could not find decoded PNG outputs for chunk_name={chunk_name} under {experiment_dir}."
        )
    matches.sort(key=lambda path: (0 if "all" in path.parts else 1, len(path.parts), str(path)))
    return matches[0]


def _load_chunked_frame_records(
    chunked_summary_path: Path,
) -> tuple[dict[str, Any], Path, list[dict[str, Any]]]:
    chunked_summary = _load_json(chunked_summary_path)
    chunk_index_raw = chunked_summary.get("chunk_index_path")
    if not chunk_index_raw:
        raise KeyError("chunk_index_path is missing from the chunked summary JSON.")
    chunk_index_path = Path(chunk_index_raw).expanduser().resolve()
    chunk_index = _load_json(chunk_index_path)
    source_dir = Path(chunk_index["source_dir"]).expanduser().resolve()

    records: list[dict[str, Any]] = []
    runs = chunked_summary.get("runs", [])
    for chunk in chunk_index.get("chunks", []):
        chunk_name = chunk["chunk_name"]
        run_summary = _find_chunk_run_summary(chunk_name=chunk_name, runs=runs)
        manifest_path = Path(
            run_summary.get("chunk_manifest_path") or chunk["manifest_path"]
        ).expanduser().resolve()
        manifest = _load_json(manifest_path)
        decoded_dir = _resolve_chunk_decoded_dir(
            Path(run_summary["experiment_dir"]).expanduser().resolve(),
            chunk_name,
        )
        decoded_frames = {path.name: path for path in sorted(decoded_dir.glob("*.png"))}

        for frame in manifest.get("frames", []):
            original_index = int(frame["original_index"])
            source_name = frame.get("source_name") or frame["chunk_name"]
            chunk_frame_name = frame["chunk_name"]
            original_path = source_dir / source_name
            reconstructed_path = decoded_frames.get(chunk_frame_name)
            if not original_path.exists():
                raise FileNotFoundError(
                    f"Original frame {original_path} is missing for chunk_name={chunk_name}."
                )
            if reconstructed_path is None:
                raise FileNotFoundError(
                    f"Decoded frame {chunk_frame_name} is missing under {decoded_dir}."
                )
            records.append(
                {
                    "original_index": original_index,
                    "source_name": source_name,
                    "chunk_name": chunk_name,
                    "chunk_frame_name": chunk_frame_name,
                    "original_path": original_path,
                    "reconstructed_path": reconstructed_path,
                }
            )

    records.sort(key=lambda item: item["original_index"])
    return chunked_summary, chunk_index_path, records


def _write_chunked_markdown_report(
    output_path: Path,
    *,
    model: str,
    question: str,
    options: list[str],
    answer_index: int,
    frame_selection: dict[str, Any],
    compression_metrics: dict[str, Any],
    original_eval: dict[str, Any],
    reconstructed_eval: dict[str, Any],
    verdict: dict[str, str],
) -> None:
    answer_text = options[answer_index]
    content = textwrap.dedent(
        f"""
        # OpenAI Chunked-Video QA Comparison

        - Model: `{model}`
        - Question: {question}
        - Official answer: [{answer_index}] {answer_text}
        - Available chunked frames: {frame_selection["available_frame_count"]}
        - Sampled frames: {frame_selection["sampled_record_count"]}
        - Aggregate PSNR: {compression_metrics.get("psnr_avg")}
        - Aggregate teacher-MSE: {compression_metrics.get("teacher-mse_avg")}
        - Aggregate bpp: {compression_metrics.get("bpp_avg")}

        ## OpenAI Predictions

        - Original contact sheet: {_format_choice(original_eval.get("predicted_index"), options)}
        - Original correct: {original_eval.get("correct")}
        - Reconstructed contact sheet: {_format_choice(reconstructed_eval.get("predicted_index"), options)}
        - Reconstructed correct: {reconstructed_eval.get("correct")}
        - Verdict: {verdict["status"]}

        ## Interpretation

        {verdict["summary"]}

        This report samples evenly spaced frames across the currently available chunked-video
        coverage and compares the original extracted frames against decoded NVRC frames written
        by `run-chunked --eval-enable-log`.

        ## Sampled Absolute Indices

        {frame_selection["selected_absolute_source_indices"]}

        ## Rationales

        ### Original

        {original_eval["parsed"].get("rationale", original_eval["output_text"])}

        ### Reconstructed

        {reconstructed_eval["parsed"].get("rationale", reconstructed_eval["output_text"])}
        """
    ).strip()
    output_path.write_text(content + "\n", encoding="utf-8")


def generate_openai_video_qa_report(
    *,
    report_root: Path,
    repo_root: Path | None = None,
    model: str = "gpt-4.1-mini",
    sample_count: int = 8,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    repo_root = find_repo_root(str(repo_root)) if repo_root else find_repo_root()
    report_root = report_root.expanduser().resolve()

    report_payload = _load_json(report_root / "single_video_report.json")
    frame_selection_payload = _load_json(report_root / "metadata" / "frame_selection.json")
    sample = report_payload["sample"]
    q_uid = sample["q_uid"]

    clip_positions = _sample_positions(
        frame_selection_payload["frame_count"],
        sample_count,
    )
    output_dir = (
        output_dir.expanduser().resolve()
        if output_dir
        else report_root / "downstream_llm" / f"openai-{model.replace('.', '_')}"
    )
    originals_dir = output_dir / "frames" / "original"
    reconstructed_dir = output_dir / "frames" / "reconstructed"

    source_video_path = _resolve_source_video_path(report_root, q_uid)
    reconstructed_frame_paths = _resolve_reconstructed_frame_paths(report_root, q_uid)
    reconstructed_clip_positions = [index for index in clip_positions if index < len(reconstructed_frame_paths)]
    if not reconstructed_clip_positions:
        raise RuntimeError("No reconstructed frames were available for the requested sample_count.")

    selected_absolute_source_indices = [
        frame_selection_payload["chosen_start_frame"] + index
        for index in reconstructed_clip_positions
    ]
    extracted_original_frames = _extract_source_frames(
        source_video_path,
        selected_absolute_source_indices,
        originals_dir,
    )
    selected_reconstructed_frames = _copy_reconstructed_frames(
        reconstructed_frame_paths,
        reconstructed_clip_positions,
        reconstructed_dir,
    )

    original_sheet = _build_contact_sheet(
        extracted_original_frames,
        output_dir / "original_contact_sheet.png",
        title=f"Original view: {q_uid}",
    )
    reconstructed_sheet = _build_contact_sheet(
        selected_reconstructed_frames,
        output_dir / "reconstructed_contact_sheet.png",
        title=f"Reconstructed view: {q_uid}",
    )

    api_key = _resolve_openai_api_key(repo_root)
    original_eval = _evaluate_view(
        api_key=api_key,
        model=model,
        question=sample["question"],
        options=sample["options"],
        answer_index=sample["answer_index"],
        image_path=original_sheet,
        label="original",
    )
    reconstructed_eval = _evaluate_view(
        api_key=api_key,
        model=model,
        question=sample["question"],
        options=sample["options"],
        answer_index=sample["answer_index"],
        image_path=reconstructed_sheet,
        label="reconstructed",
    )

    verdict = _comparison_verdict(original_eval, reconstructed_eval)
    retrieval_metrics = _extract_retrieval_metrics(report_payload)
    comparison = {
        "provider": "openai",
        "model": model,
        "report_root": str(report_root),
        "sample": {
            "q_uid": sample["q_uid"],
            "question": sample["question"],
            "options": sample["options"],
            "answer_index": sample["answer_index"],
            "answer_text": sample["answer_text"],
        },
        "frame_selection": {
            "chosen_start_frame": frame_selection_payload["chosen_start_frame"],
            "frame_count": frame_selection_payload["frame_count"],
            "selected_clip_positions": reconstructed_clip_positions,
            "selected_absolute_source_indices": selected_absolute_source_indices,
        },
        "compression_metrics": report_payload["compression_metrics"]["logging_enabled_run"],
        "retrieval_metrics": retrieval_metrics,
        "views": {
            "original": {
                "image_path": str(original_sheet),
                "predicted_index": original_eval["predicted_index"],
                "predicted_text": original_eval["predicted_text"],
                "correct": original_eval["correct"],
                "rationale": original_eval["parsed"].get("rationale"),
                "confidence": original_eval["parsed"].get("confidence"),
                "output_text": original_eval["output_text"],
            },
            "reconstructed": {
                "image_path": str(reconstructed_sheet),
                "predicted_index": reconstructed_eval["predicted_index"],
                "predicted_text": reconstructed_eval["predicted_text"],
                "correct": reconstructed_eval["correct"],
                "rationale": reconstructed_eval["parsed"].get("rationale"),
                "confidence": reconstructed_eval["parsed"].get("confidence"),
                "output_text": reconstructed_eval["output_text"],
            },
        },
        "verdict": verdict,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "summary.json", comparison)
    write_json(output_dir / "original_response.json", original_eval["raw_response"])
    write_json(output_dir / "reconstructed_response.json", reconstructed_eval["raw_response"])
    _write_markdown_report(
        output_dir / "report.md",
        model=model,
        sample=sample,
        frame_selection=comparison["frame_selection"],
        compression_metrics=comparison["compression_metrics"],
        retrieval_metrics=retrieval_metrics,
        original_eval=original_eval,
        reconstructed_eval=reconstructed_eval,
        verdict=verdict,
    )
    return comparison


def generate_openai_chunked_video_qa_report(
    *,
    chunked_summary_path: Path,
    question: str,
    options: list[str],
    answer_index: int,
    repo_root: Path | None = None,
    model: str = "gpt-4.1-mini",
    sample_count: int = 8,
    output_dir: Path | None = None,
) -> dict[str, Any]:
    if len(options) < 2:
        raise ValueError("At least two answer options are required.")
    if answer_index < 0 or answer_index >= len(options):
        raise ValueError("answer_index must point to one of the provided options.")

    repo_root = find_repo_root(str(repo_root)) if repo_root else find_repo_root()
    chunked_summary_path = chunked_summary_path.expanduser().resolve()
    chunked_summary, chunk_index_path, frame_records = _load_chunked_frame_records(
        chunked_summary_path
    )
    if not frame_records:
        raise RuntimeError("The chunked summary does not expose any decoded frame records.")

    sample_positions = _sample_positions(len(frame_records), sample_count)
    selected_records = [frame_records[index] for index in sample_positions]

    output_dir = (
        output_dir.expanduser().resolve()
        if output_dir
        else chunked_summary_path.parent
        / "downstream_llm"
        / f"openai-{model.replace('.', '_')}"
    )
    originals_dir = output_dir / "frames" / "original"
    reconstructed_dir = output_dir / "frames" / "reconstructed"

    copied_original_frames = _copy_selected_frames(
        [record["original_path"] for record in selected_records],
        originals_dir,
    )
    copied_reconstructed_frames = _copy_selected_frames(
        [record["reconstructed_path"] for record in selected_records],
        reconstructed_dir,
    )

    original_sheet = _build_contact_sheet(
        copied_original_frames,
        output_dir / "original_contact_sheet.png",
        title="Original full-video view",
    )
    reconstructed_sheet = _build_contact_sheet(
        copied_reconstructed_frames,
        output_dir / "reconstructed_contact_sheet.png",
        title="Reconstructed full-video view",
    )

    api_key = _resolve_openai_api_key(repo_root)
    original_eval = _evaluate_view(
        api_key=api_key,
        model=model,
        question=question,
        options=options,
        answer_index=answer_index,
        image_path=original_sheet,
        label="original",
    )
    reconstructed_eval = _evaluate_view(
        api_key=api_key,
        model=model,
        question=question,
        options=options,
        answer_index=answer_index,
        image_path=reconstructed_sheet,
        label="reconstructed",
    )

    verdict = _comparison_verdict(original_eval, reconstructed_eval)
    compression_metrics = chunked_summary.get("aggregate_metrics_mean", {})
    comparison = {
        "provider": "openai",
        "model": model,
        "kind": "chunked_video_qa",
        "chunked_summary_path": str(chunked_summary_path),
        "chunk_index_path": str(chunk_index_path),
        "question": question,
        "options": options,
        "answer_index": answer_index,
        "answer_text": options[answer_index],
        "frame_selection": {
            "available_frame_count": len(frame_records),
            "sampled_record_count": len(selected_records),
            "selected_absolute_source_indices": [
                record["original_index"] for record in selected_records
            ],
            "selected_chunks": [record["chunk_name"] for record in selected_records],
            "selected_chunk_frame_names": [
                record["chunk_frame_name"] for record in selected_records
            ],
        },
        "compression_metrics": compression_metrics,
        "views": {
            "original": {
                "image_path": str(original_sheet),
                "predicted_index": original_eval["predicted_index"],
                "predicted_text": original_eval["predicted_text"],
                "correct": original_eval["correct"],
                "rationale": original_eval["parsed"].get("rationale"),
                "confidence": original_eval["parsed"].get("confidence"),
                "output_text": original_eval["output_text"],
            },
            "reconstructed": {
                "image_path": str(reconstructed_sheet),
                "predicted_index": reconstructed_eval["predicted_index"],
                "predicted_text": reconstructed_eval["predicted_text"],
                "correct": reconstructed_eval["correct"],
                "rationale": reconstructed_eval["parsed"].get("rationale"),
                "confidence": reconstructed_eval["parsed"].get("confidence"),
                "output_text": reconstructed_eval["output_text"],
            },
        },
        "verdict": verdict,
    }

    output_dir.mkdir(parents=True, exist_ok=True)
    write_json(output_dir / "summary.json", comparison)
    write_json(output_dir / "original_response.json", original_eval["raw_response"])
    write_json(
        output_dir / "reconstructed_response.json",
        reconstructed_eval["raw_response"],
    )
    _write_chunked_markdown_report(
        output_dir / "report.md",
        model=model,
        question=question,
        options=options,
        answer_index=answer_index,
        frame_selection=comparison["frame_selection"],
        compression_metrics=comparison["compression_metrics"],
        original_eval=original_eval,
        reconstructed_eval=reconstructed_eval,
        verdict=verdict,
    )
    return comparison
