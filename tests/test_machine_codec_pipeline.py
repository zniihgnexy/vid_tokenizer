from __future__ import annotations

import json
import tempfile
import unittest
from pathlib import Path

from machine_codec_pipeline.commands import build_nvrc_command
from machine_codec_pipeline.demo import run_demo
from machine_codec_pipeline.profiles import PROFILES, ensure_profile
from machine_codec_pipeline.results import compare_results, parse_results_file


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
            eval_only = False
            nvrc_arg: list[str] = []

        command = build_nvrc_command(Args, ensure_profile("shared_semchange_delta"))
        self.assertIn("main_nvrc.py", command)
        self.assertIn(
            "scripts/configs/tasks/overfit/l1_teacher-resnet18-shared-semchange-delta.yaml",
            command,
        )
        self.assertEqual(command[command.index("--train-dataset") + 1], "tiny_video")


if __name__ == "__main__":
    unittest.main()
