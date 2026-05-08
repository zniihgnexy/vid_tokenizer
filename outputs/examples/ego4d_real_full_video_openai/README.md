# Example Bundle: Ego4D Full Video + OpenAI QA

This is the lightweight tracked example for one full-video machine-codec run.

Scenario:

- source type: one Ego4D raw video
- codec mode: chunked `shared_semchange_delta`
- downstream model: `gpt-4.1-mini`
- QA verdict: `parity_correct`

Headline numbers:

- available frames: `5400`
- chunk count: `18`
- sampled frames for QA: `12`
- aggregate `psnr_avg`: `15.1207`
- aggregate `teacher-mse_avg`: `0.5561`
- aggregate `bpp_avg`: `2.5289`
- original confidence: `0.9`
- reconstructed confidence: `0.7`

Tracked files kept here:

- `public_summary.json`
- `openai_chunked_qa_gpt41mini/report.md`
- `openai_chunked_qa_gpt41mini/original_contact_sheet.png`
- `openai_chunked_qa_gpt41mini/reconstructed_contact_sheet.png`
- `openai_chunked_qa_gpt41mini/original_response.json`
- `openai_chunked_qa_gpt41mini/reconstructed_response.json`

The full raw chunk-level codec artifacts are intentionally not tracked here.
They belong under the ignored `outputs/runs/` area so the repository stays
readable and GitHub-friendly.
