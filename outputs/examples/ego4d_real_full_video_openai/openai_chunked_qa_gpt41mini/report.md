# OpenAI Chunked-Video QA Comparison

- Model: `gpt-4.1-mini`
- Question: Taking into account all the actions performed by c, what can you deduce about the primary objective and focus within the video content?
- Official answer: [3] C is cleaning dishes.
- Available chunked frames: 5400
- Sampled frames: 12
- Aggregate PSNR: 15.120677777777779
- Aggregate teacher-MSE: 0.5561444444444443
- Aggregate bpp: 2.528911111111111

## OpenAI Predictions

- Original contact sheet: [3] C is cleaning dishes.
- Original correct: True
- Reconstructed contact sheet: [3] C is cleaning dishes.
- Reconstructed correct: True
- Verdict: parity_correct

## Interpretation

Both the original and reconstructed contact sheets answered the question correctly.

This report samples evenly spaced frames across the currently available chunked-video
coverage and compares the original extracted frames against decoded NVRC frames written
by `run-chunked --eval-enable-log`.

## Sampled Absolute Indices

[0, 491, 982, 1472, 1963, 2454, 2945, 3436, 3927, 4417, 4908, 5399]

## Rationales

### Original

The frames show C handling plates and using a sink repeatedly, which indicates washing dishes rather than cooking, doing laundry, or cleaning other areas.

### Reconstructed

The frames show actions with hands near sinks and objects that look like dishes or utensils, suggesting dish cleaning activity.
