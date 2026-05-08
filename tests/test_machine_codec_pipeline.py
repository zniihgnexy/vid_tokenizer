from __future__ import annotations

import json
import tempfile
import unittest
from argparse import Namespace
from pathlib import Path
from unittest.mock import patch

from PIL import Image

from machine_codec_pipeline.commands import build_nvrc_command
from machine_codec_pipeline.commands import run_chunked_profile
from machine_codec_pipeline.demo import run_demo
from machine_codec_pipeline.profiles import PROFILES, ensure_profile
from machine_codec_pipeline.results import compare_results, parse_results_file
from machine_codec_pipeline.video_data import prepare_video_window, split_png_video_chunks
from machine_codec_pipeline.video_qa import (
    _read_key_from_dotenv,
    _sample_positions,
    generate_openai_chunked_video_qa_report,
    generate_openai_video_qa_report,
)


class MachineCodecPipelineTests(unittest.TestCase):
    def test_profile_registry_contains_incumbent(self) -> None:
        self.assertIn("shared_semchange_delta", PROFILES)
        profile = ensure_profile("shared_semchange_delta")
        self.assertEqual(
            profile.task_config,
            "l1_teacher-resnet18-shared-semchange-delta.yaml",
        )
        self.assertIn("--temporal-delta-semantic-gating", profile.smoke_args)

    def test_demo_writes_comparable_result_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            comparison = run_demo(tmp_path)
            self.assertEqual(comparison[0]["name"], "shared_semchange_delta_demo")
            self.assertLess(
                comparison[0]["teacher-mse_avg"],
                comparison[1]["teacher-mse_avg"],
            )

            summary_path = tmp_path / "shared_semchange_delta_demo" / "pipeline_summary.json"
            summary = json.loads(summary_path.read_text(encoding="utf-8"))
            self.assertTrue(summary["demo"])
            self.assertEqual(summary["profile"]["name"], "shared_semchange_delta")

    def test_compare_accepts_experiment_directories(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            run_demo(tmp_path)
            rows = compare_results(
                [
                    str(tmp_path / "bootstrap_demo"),
                    str(tmp_path / "shared_semchange_delta_demo"),
                ]
            )
            self.assertEqual(
                [row["name"] for row in rows],
                ["shared_semchange_delta_demo", "bootstrap_demo"],
            )

    def test_parse_results_file_keeps_metric_types(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            result_path = Path(tmp) / "all.txt"
            result_path.write_text(
                "bpp_avg,psnr_avg,teacher-mse_avg,ok\n1.5,12.0,0.25,true\n",
                encoding="utf-8",
            )
            metrics = parse_results_file(result_path)
            self.assertEqual(
                metrics,
                {
                    "bpp_avg": 1.5,
                    "psnr_avg": 12,
                    "teacher-mse_avg": 0.25,
                    "ok": True,
                },
            )

    def test_build_nvrc_command_preserves_profile_task_config(self) -> None:
        class Args:
            exp_config = "exp.yaml"
            train_data_config = "data.yaml"
            eval_data_config = None
            train_task_config = None
            eval_task_config = None
            compress_model_config = "compress.yaml"
            model_config = "model.yaml"
            output_root = "/tmp/runs"
            exp_name = "unit"
            dataset_dir = None
            dataset = "tiny_video"
            video_size = [4, 32, 32]
            patch_size = [1, 32, 32]
            epochs = 1
            warmup_epochs = 0
            eval_epochs = 1
            rate_steps = 1
            num_frames = None
            start_frame = None
            intra_period = None
            seed = 0
            workers = 0
            train_batch_size = None
            eval_batch_size = None
            teacher_type = "resnet18_imagenet"
            train_enable_log = None
            eval_enable_log = True
            eval_only = False
            nvrc_arg: list[str] = []

        command = build_nvrc_command(Args, ensure_profile("shared_semchange_delta"))
        self.assertIn("main_nvrc.py", command)
        self.assertIn(
            "scripts/configs/tasks/overfit/l1_teacher-resnet18-shared-semchange-delta.yaml",
            command,
        )
        self.assertEqual(command[command.index("--train-dataset") + 1], "tiny_video")
        self.assertEqual(command[command.index("--eval-enable-log") + 1], "true")

    def test_sample_positions_spans_clip_endpoints(self) -> None:
        self.assertEqual(_sample_positions(32, 8), [0, 4, 9, 13, 18, 22, 27, 31])

    def test_read_key_from_dotenv_supports_quoted_values(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            dotenv_path = Path(tmp) / ".env"
            dotenv_path.write_text(
                "IGNORED=1\nexport OPENAI_API_KEY = 'test-key'\n",
                encoding="utf-8",
            )
            self.assertEqual(_read_key_from_dotenv(dotenv_path, "OPENAI_API_KEY"), "test-key")

    def test_generate_openai_video_qa_report_writes_summary_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo_root = tmp_path / "repo"
            report_root = tmp_path / "report"
            repo_root.mkdir()
            (repo_root / ".env").write_text("OPENAI_API_KEY=test-key\n", encoding="utf-8")

            (report_root / "metadata").mkdir(parents=True)
            (report_root / "videos").mkdir(parents=True)
            (report_root / "runs" / "demo-log" / "outputs" / "0000" / "train" / "0" / "sample_mid32_32x32").mkdir(
                parents=True
            )
            (report_root / "videos" / "sample.mp4").write_bytes(b"fake")

            for index in range(4):
                Image.new("RGB", (32, 32), color=(index * 20, 40, 60)).save(
                    report_root
                    / "runs"
                    / "demo-log"
                    / "outputs"
                    / "0000"
                    / "train"
                    / "0"
                    / "sample_mid32_32x32"
                    / f"{index:04d}.png"
                )

            (report_root / "single_video_report.json").write_text(
                json.dumps(
                    {
                        "sample": {
                            "q_uid": "sample",
                            "question": "What is happening?",
                            "options": ["A", "B", "C", "D"],
                            "answer_index": 2,
                            "answer_text": "C",
                            "source_video": {"fps": 30},
                        },
                        "compression_metrics": {
                            "logging_enabled_run": {
                                "psnr_avg": 14.0,
                                "teacher_mse_avg": 0.8,
                                "bpp_avg": 13.0,
                            }
                        },
                        "downstream_retrieval": {
                            "compressed_feature_retrieval": {
                                "top1_accuracy": 0.03125,
                                "mean_match_rank": 16.1875,
                            }
                        },
                    }
                ),
                encoding="utf-8",
            )
            (report_root / "metadata" / "frame_selection.json").write_text(
                json.dumps(
                    {
                        "chosen_start_frame": 100,
                        "frame_count": 4,
                    }
                ),
                encoding="utf-8",
            )

            def fake_extract_source_frames(_video_path: Path, absolute_indices: list[int], output_dir: Path) -> list[Path]:
                output_dir.mkdir(parents=True, exist_ok=True)
                paths: list[Path] = []
                for absolute_index in absolute_indices:
                    path = output_dir / f"{absolute_index:06d}.png"
                    Image.new("RGB", (32, 32), color=(90, 120, 30)).save(path)
                    paths.append(path)
                return paths

            def fake_openai_call(*, image_path: Path, **_: object) -> dict[str, object]:
                if "original" in image_path.name:
                    text = json.dumps(
                        {
                            "choice_index": 2,
                            "choice_text": "C",
                            "confidence": 0.81,
                            "rationale": "The original frames support option C.",
                        }
                    )
                else:
                    text = json.dumps(
                        {
                            "choice_index": 1,
                            "choice_text": "B",
                            "confidence": 0.42,
                            "rationale": "The reconstructed frames are less clear.",
                        }
                    )
                return {"output_text": text}

            with patch(
                "machine_codec_pipeline.video_qa._extract_source_frames",
                side_effect=fake_extract_source_frames,
            ), patch(
                "machine_codec_pipeline.video_qa._call_openai_responses",
                side_effect=fake_openai_call,
            ):
                summary = generate_openai_video_qa_report(
                    repo_root=repo_root,
                    report_root=report_root,
                    model="gpt-4.1-mini",
                    sample_count=4,
                )

            self.assertEqual(summary["verdict"]["status"], "degraded_after_compression")
            self.assertTrue((report_root / "downstream_llm" / "openai-gpt-4_1-mini" / "summary.json").exists())
            self.assertTrue(
                (report_root / "downstream_llm" / "openai-gpt-4_1-mini" / "report.md").exists()
            )

    def test_generate_openai_chunked_video_qa_report_writes_summary_contract(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            repo_root = tmp_path / "repo"
            source_dir = tmp_path / "source_frames"
            chunk_root = tmp_path / "chunks"
            run_root = tmp_path / "runs"
            repo_root.mkdir()
            source_dir.mkdir()
            chunk_root.mkdir()
            run_root.mkdir()
            (repo_root / ".env").write_text("OPENAI_API_KEY=test-key\n", encoding="utf-8")

            for index in range(6):
                Image.new("RGB", (32, 32), color=(index * 30, 40, 90)).save(
                    source_dir / f"{index:04d}.png"
                )

            chunk_specs = [
                ("ego4d_small_chunk00", [0, 1, 2]),
                ("ego4d_small_chunk01", [3, 4, 5]),
            ]
            runs: list[dict[str, object]] = []
            chunks: list[dict[str, object]] = []
            for chunk_name, absolute_indices in chunk_specs:
                chunk_dir = chunk_root / chunk_name
                manifest_path = chunk_dir / "chunk_manifest.json"
                experiment_dir = run_root / f"demo_{chunk_name}"
                decoded_dir = (
                    experiment_dir
                    / "outputs"
                    / "0000"
                    / "decoded"
                    / "None"
                    / chunk_name
                )
                chunk_dir.mkdir(parents=True)
                decoded_dir.mkdir(parents=True)

                frames = []
                for local_index, absolute_index in enumerate(absolute_indices):
                    local_name = f"{local_index:04d}.png"
                    frames.append(
                        {
                            "chunk_name": local_name,
                            "original_index": absolute_index,
                            "source_name": f"{absolute_index:04d}.png",
                        }
                    )
                    Image.new("RGB", (32, 32), color=(10, 120, 30 + local_index * 10)).save(
                        decoded_dir / local_name
                    )

                manifest_path.write_text(
                    json.dumps(
                        {
                            "chunk_index": len(chunks),
                            "chunk_name": chunk_name,
                            "chunk_size": len(absolute_indices),
                            "frames": frames,
                        }
                    ),
                    encoding="utf-8",
                )
                chunks.append(
                    {
                        "chunk_name": chunk_name,
                        "chunk_dir": str(chunk_dir),
                        "manifest_path": str(manifest_path),
                        "frame_count": len(absolute_indices),
                    }
                )
                runs.append(
                    {
                        "experiment_dir": str(experiment_dir),
                        "results_path": str(experiment_dir / "results" / "all.txt"),
                        "chunk_name": chunk_name,
                        "chunk_manifest_path": str(manifest_path),
                    }
                )

            chunk_index_path = chunk_root / "ego4d_small_chunk_index.json"
            chunk_index_path.write_text(
                json.dumps(
                    {
                        "source_dir": str(source_dir),
                        "chunk_size": 3,
                        "chunk_count": 2,
                        "chunks": chunks,
                    }
                ),
                encoding="utf-8",
            )
            chunked_summary_path = run_root / "ego4d_small_chunked_summary.json"
            chunked_summary_path.write_text(
                json.dumps(
                    {
                        "chunk_index_path": str(chunk_index_path),
                        "chunk_count": 2,
                        "runs": runs,
                        "aggregate_metrics_mean": {
                            "psnr_avg": 14.2,
                            "teacher-mse_avg": 0.5,
                            "bpp_avg": 2.1,
                        },
                    }
                ),
                encoding="utf-8",
            )

            def fake_openai_call(*, image_path: Path, **_: object) -> dict[str, object]:
                if "original" in image_path.name:
                    text = json.dumps(
                        {
                            "choice_index": 1,
                            "choice_text": "B",
                            "confidence": 0.88,
                            "rationale": "The original contact sheet supports B.",
                        }
                    )
                else:
                    text = json.dumps(
                        {
                            "choice_index": 0,
                            "choice_text": "A",
                            "confidence": 0.41,
                            "rationale": "The reconstructed contact sheet is less reliable.",
                        }
                    )
                return {"output_text": text}

            with patch(
                "machine_codec_pipeline.video_qa._call_openai_responses",
                side_effect=fake_openai_call,
            ):
                summary = generate_openai_chunked_video_qa_report(
                    repo_root=repo_root,
                    chunked_summary_path=chunked_summary_path,
                    question="What is the best answer?",
                    options=["A", "B", "C", "D"],
                    answer_index=1,
                    model="gpt-4.1-mini",
                    sample_count=4,
                )

            self.assertEqual(summary["verdict"]["status"], "degraded_after_compression")
            self.assertEqual(summary["frame_selection"]["available_frame_count"], 6)
            self.assertEqual(summary["frame_selection"]["sampled_record_count"], 4)
            self.assertTrue(
                (run_root / "downstream_llm" / "openai-gpt-4_1-mini" / "summary.json").exists()
            )
            self.assertTrue(
                (run_root / "downstream_llm" / "openai-gpt-4_1-mini" / "report.md").exists()
            )

    def test_split_png_video_chunks_preserves_tail_chunk(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            source_dir = tmp_path / "ego4d_window"
            output_root = tmp_path / "chunks"
            source_dir.mkdir()

            for index in range(5):
                Image.new("RGB", (16, 16), color=(index * 20, 10, 5)).save(
                    source_dir / f"{index:04d}.png"
                )

            summary = split_png_video_chunks(
                source_dir=source_dir,
                output_root=output_root,
                chunk_size=2,
                prefix="ego4d_small_bridge",
            )

            self.assertEqual(summary["chunk_count"], 3)
            self.assertEqual(summary["chunks"][-1]["frame_count"], 1)
            self.assertTrue((output_root / "ego4d_small_bridge_chunk_index.json").exists())

    def test_prepare_video_window_can_extract_and_chunk(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            video_path = tmp_path / "sample.mp4"
            output_dir = tmp_path / "ego4d_window"
            video_path.write_bytes(b"fake")

            def fake_read_probe(_video_path: Path) -> dict[str, object]:
                return {"nb_read_frames": "8", "width": 320, "height": 240}

            def fake_extract_frames(**kwargs: object) -> list[Path]:
                target_dir = Path(kwargs["output_dir"])
                target_dir.mkdir(parents=True, exist_ok=True)
                paths: list[Path] = []
                for index in range(int(kwargs["num_frames"])):
                    path = target_dir / f"{index:04d}.png"
                    Image.new("RGB", (32, 32), color=(index * 15, 40, 70)).save(path)
                    paths.append(path)
                return paths

            with patch(
                "machine_codec_pipeline.video_data.read_probe",
                side_effect=fake_read_probe,
            ), patch(
                "machine_codec_pipeline.video_data._extract_frames",
                side_effect=fake_extract_frames,
            ):
                summary = prepare_video_window(
                    video_path=video_path,
                    output_dir=output_dir,
                    start_frame=0,
                    num_frames=8,
                    width=32,
                    height=32,
                    chunk_size=3,
                )

            self.assertEqual(summary["dataset"]["frame_count"], 8)
            self.assertEqual(summary["chunks"]["chunk_count"], 3)
            self.assertEqual(summary["chunks"]["source_frame_shape"], [32, 32])
            self.assertTrue((output_dir / "extraction_manifest.json").exists())
            self.assertTrue(
                (output_dir.parent / "ego4d_window_chunks" / "ego4d_window_chunk_index.json").exists()
            )

    def test_run_chunked_profile_aggregates_chunk_metrics(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            chunk_root = tmp_path / "chunks"
            chunk_root.mkdir()
            chunk_index_path = chunk_root / "ego4d_small_chunk_index.json"
            chunk_payload = {
                "source_dir": str(tmp_path / "dataset"),
                "chunk_size": 4,
                "chunk_count": 2,
                "chunks": [
                    {
                        "chunk_name": "ego4d_small_chunk00",
                        "chunk_dir": str(chunk_root / "ego4d_small_chunk00"),
                        "manifest_path": str(chunk_root / "ego4d_small_chunk00" / "chunk_manifest.json"),
                        "frame_count": 4,
                    },
                    {
                        "chunk_name": "ego4d_small_chunk01",
                        "chunk_dir": str(chunk_root / "ego4d_small_chunk01"),
                        "manifest_path": str(chunk_root / "ego4d_small_chunk01" / "chunk_manifest.json"),
                        "frame_count": 4,
                    },
                ],
            }
            chunk_index_path.write_text(json.dumps(chunk_payload), encoding="utf-8")

            args = Namespace(
                repo_root=None,
                chunk_index=str(chunk_index_path),
                exp_name_prefix="shared_semchange_delta_fullvideo",
                output_root=str(tmp_path / "runs"),
                limit_chunks=None,
                video_size=[4, 32, 32],
                patch_size=[1, 32, 32],
                num_frames=None,
                start_frame=None,
                intra_period=None,
                epochs=1,
                warmup_epochs=0,
                eval_epochs=1,
                rate_steps=1,
                seed=0,
                workers=0,
                train_batch_size=None,
                eval_batch_size=None,
                teacher_type=None,
                train_enable_log=None,
                eval_enable_log=None,
                eval_only=False,
                exp_config="exp.yaml",
                train_data_config="data.yaml",
                eval_data_config=None,
                train_task_config=None,
                eval_task_config=None,
                compress_model_config="compress.yaml",
                model_config="model.yaml",
                smoke_first=False,
                smoke_arg=[],
                nvrc_arg=[],
                dry_run=True,
            )

            def fake_run_profile(
                args: object,
                _profile: object,
                *,
                smoke_summary_override: dict[str, object] | None = None,
            ) -> dict[str, object]:
                exp_name = args.exp_name
                teacher_mse = 0.1 if exp_name.endswith("chunk00") else 0.3
                return {
                    "profile": {"name": "shared_semchange_delta"},
                    "smoke_summary": smoke_summary_override,
                    "experiment_dir": str(Path(args.output_root) / exp_name),
                    "results_path": str(Path(args.output_root) / exp_name / "results" / "all.txt"),
                    "metrics": {
                        "teacher-mse_avg": teacher_mse,
                        "psnr_avg": 12.0,
                        "bpp_avg": 1.0,
                    },
                    "nvrc_command": ["python", "main_nvrc.py"],
                    "dry_run": True,
                }

            with patch(
                "machine_codec_pipeline.commands.run_profile",
                side_effect=fake_run_profile,
            ):
                summary = run_chunked_profile(args, ensure_profile("shared_semchange_delta"))

            self.assertEqual(summary["chunk_count"], 2)
            self.assertAlmostEqual(summary["aggregate_metrics_mean"]["teacher-mse_avg"], 0.2)
            self.assertEqual(
                summary["runs"][0]["experiment_dir"].split("/")[-1],
                "shared_semchange_delta_fullvideo_ego4d_small_chunk00",
            )

    def test_run_chunked_profile_infers_video_and_patch_size_from_manifest(self) -> None:
        with tempfile.TemporaryDirectory() as tmp:
            tmp_path = Path(tmp)
            dataset_dir = tmp_path / "dataset"
            chunk_root = tmp_path / "chunks"
            chunk_dir = chunk_root / "ego4d_small_chunk00"
            dataset_dir.mkdir()
            chunk_root.mkdir()
            chunk_dir.mkdir()

            (dataset_dir / "extraction_manifest.json").write_text(
                json.dumps(
                    {
                        "video_path": "/tmp/source.mp4",
                        "width": 48,
                        "height": 32,
                    }
                ),
                encoding="utf-8",
            )
            (chunk_dir / "chunk_manifest.json").write_text("{}", encoding="utf-8")

            chunk_index_path = chunk_root / "ego4d_small_chunk_index.json"
            chunk_index_path.write_text(
                json.dumps(
                    {
                        "source_dir": str(dataset_dir),
                        "chunk_size": 6,
                        "chunk_count": 1,
                        "source_manifest_path": str(dataset_dir / "extraction_manifest.json"),
                        "chunks": [
                            {
                                "chunk_name": "ego4d_small_chunk00",
                                "chunk_dir": str(chunk_dir),
                                "manifest_path": str(chunk_dir / "chunk_manifest.json"),
                                "frame_count": 6,
                            }
                        ],
                    }
                ),
                encoding="utf-8",
            )

            args = Namespace(
                repo_root=None,
                chunk_index=str(chunk_index_path),
                exp_name_prefix="shared_semchange_delta_fullvideo",
                output_root=str(tmp_path / "runs"),
                limit_chunks=None,
                video_size=None,
                patch_size=None,
                num_frames=None,
                start_frame=None,
                intra_period=None,
                epochs=1,
                warmup_epochs=0,
                eval_epochs=1,
                rate_steps=1,
                seed=0,
                workers=0,
                train_batch_size=None,
                eval_batch_size=None,
                teacher_type=None,
                train_enable_log=None,
                eval_enable_log=None,
                eval_only=False,
                exp_config="exp.yaml",
                train_data_config="data.yaml",
                eval_data_config=None,
                train_task_config=None,
                eval_task_config=None,
                compress_model_config="compress.yaml",
                model_config="model.yaml",
                smoke_first=False,
                smoke_arg=[],
                nvrc_arg=[],
                dry_run=True,
            )

            def fake_run_profile(
                args: object,
                _profile: object,
                *,
                smoke_summary_override: dict[str, object] | None = None,
            ) -> dict[str, object]:
                self.assertEqual(args.video_size, [6, 32, 48])
                self.assertEqual(args.patch_size, [1, 32, 48])
                return {
                    "profile": {"name": "shared_semchange_delta"},
                    "smoke_summary": smoke_summary_override,
                    "experiment_dir": str(Path(args.output_root) / args.exp_name),
                    "results_path": str(Path(args.output_root) / args.exp_name / "results" / "all.txt"),
                    "metrics": {
                        "teacher-mse_avg": 0.2,
                        "psnr_avg": 12.0,
                        "bpp_avg": 1.0,
                    },
                    "nvrc_command": ["python", "main_nvrc.py"],
                    "dry_run": True,
                }

            with patch(
                "machine_codec_pipeline.commands.run_profile",
                side_effect=fake_run_profile,
            ):
                summary = run_chunked_profile(args, ensure_profile("shared_semchange_delta"))

            self.assertEqual(summary["chunk_count"], 1)
            self.assertEqual(summary["runs"][0]["metrics"]["teacher-mse_avg"], 0.2)


if __name__ == "__main__":
    unittest.main()
