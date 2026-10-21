"""Local InternVL2.5-8B backend for Pathway B.

This module wraps the locally-stored InternVL2.5-8B checkpoint so the rest of
the pipeline can:

1. Extract InternViT patch tokens from frames (the VLM's *own* tokenizer).
2. Run video/image QA by injecting precomputed token embeddings directly,
   bypassing the pixel input path.

Capability (2) is what Pathway B needs: the codec will eventually emit token
embeddings of its own, and they get fed straight into the language model
without ever reconstructing pixels.

Phase 0 deliverable. The ``--smoke`` entry point verifies that the
embedding-injection path produces the same answer as the normal pixel path,
which is the hard gate for the whole Pathway B direction.
"""

from __future__ import annotations

import argparse
import os
from pathlib import Path

import torch
import torchvision.transforms as T
from PIL import Image
from torchvision.transforms.functional import InterpolationMode

# Model weights location: env INTERNVL_MODEL_PATH (set in scripts/control.sh)
# overrides the default, so deploying to another host needs no code edit.
DEFAULT_MODEL_PATH = os.environ.get(
    "INTERNVL_MODEL_PATH", "/mnt/nas/xinyizheng/InternVL2_5-8B"
)

# ImageNet normalisation, matching the checkpoint's preprocessor_config.json.
IMAGENET_MEAN = (0.485, 0.456, 0.406)
IMAGENET_STD = (0.229, 0.224, 0.225)

IMG_START_TOKEN = "<img>"
IMG_END_TOKEN = "</img>"
IMG_CONTEXT_TOKEN = "<IMG_CONTEXT>"


# --------------------------------------------------------------------------
# Image loading (standard InternVL2.5 dynamic-tiling preprocessing)
# --------------------------------------------------------------------------
def build_transform(input_size: int = 448) -> T.Compose:
    """Return the InternViT input transform: resize -> tensor -> normalise."""

    return T.Compose([
        T.Lambda(lambda img: img.convert("RGB") if img.mode != "RGB" else img),
        T.Resize((input_size, input_size), interpolation=InterpolationMode.BICUBIC),
        T.ToTensor(),
        T.Normalize(mean=IMAGENET_MEAN, std=IMAGENET_STD),
    ])


def _find_closest_aspect_ratio(aspect_ratio, target_ratios, width, height, image_size):
    best_diff = float("inf")
    best = (1, 1)
    area = width * height
    for ratio in target_ratios:
        target_ar = ratio[0] / ratio[1]
        diff = abs(aspect_ratio - target_ar)
        if diff < best_diff:
            best_diff = diff
            best = ratio
        elif diff == best_diff and area > 0.5 * image_size * image_size * ratio[0] * ratio[1]:
            best = ratio
    return best


def dynamic_preprocess(image, min_num=1, max_num=12, image_size=448, use_thumbnail=True):
    """Split an image into 1..max_num tiles of ``image_size`` following InternVL2.5."""

    width, height = image.size
    aspect_ratio = width / height

    target_ratios = sorted(
        {
            (i, j)
            for n in range(min_num, max_num + 1)
            for i in range(1, n + 1)
            for j in range(1, n + 1)
            if min_num <= i * j <= max_num
        },
        key=lambda x: x[0] * x[1],
    )

    ratio = _find_closest_aspect_ratio(aspect_ratio, target_ratios, width, height, image_size)
    target_width = image_size * ratio[0]
    target_height = image_size * ratio[1]
    blocks = ratio[0] * ratio[1]

    resized = image.resize((target_width, target_height))
    tiles = []
    cols = target_width // image_size
    for idx in range(blocks):
        box = (
            (idx % cols) * image_size,
            (idx // cols) * image_size,
            ((idx % cols) + 1) * image_size,
            ((idx // cols) + 1) * image_size,
        )
        tiles.append(resized.crop(box))

    if use_thumbnail and len(tiles) != 1:
        tiles.append(image.resize((image_size, image_size)))
    return tiles


def load_image(image_file, input_size: int = 448, max_num: int = 12) -> torch.Tensor:
    """Load one image file into a ``[num_tiles, 3, 448, 448]`` pixel tensor."""

    image = Image.open(image_file).convert("RGB")
    transform = build_transform(input_size=input_size)
    tiles = dynamic_preprocess(image, image_size=input_size, use_thumbnail=True, max_num=max_num)
    return torch.stack([transform(tile) for tile in tiles])


# --------------------------------------------------------------------------
# Model loading
# --------------------------------------------------------------------------
def load_internvl(
    model_path: str = DEFAULT_MODEL_PATH,
    device: str = "cuda",
    dtype: torch.dtype = torch.bfloat16,
):
    """Load the InternVL2.5 chat model and tokenizer from a local checkpoint.

    Returns ``(model, tokenizer)``. The model is in eval mode with all
    parameters frozen — this backend is a fixed teacher / evaluator.
    """

    from transformers import AutoModel, AutoTokenizer

    model = AutoModel.from_pretrained(
        model_path,
        torch_dtype=dtype,
        trust_remote_code=True,
        low_cpu_mem_usage=True,
    ).eval()
    model = model.to(device)
    for param in model.parameters():
        param.requires_grad = False

    tokenizer = AutoTokenizer.from_pretrained(
        model_path, trust_remote_code=True, use_fast=False
    )
    model.img_context_token_id = tokenizer.convert_tokens_to_ids(IMG_CONTEXT_TOKEN)

    _ensure_generation_mixin(model.language_model)
    return model, tokenizer


def _ensure_generation_mixin(language_model) -> None:
    """Re-attach ``GenerationMixin`` to the language model.

    transformers >= 4.50 stopped having ``PreTrainedModel`` inherit
    ``GenerationMixin``; this checkpoint's remote code predates that, so
    ``.generate()`` is otherwise missing. Reassigning ``__class__`` to a
    subclass that mixes it back in is layout-safe (mixin has no ``__slots__``).
    """

    from transformers import GenerationConfig, GenerationMixin

    if not isinstance(language_model, GenerationMixin):
        cls = language_model.__class__
        language_model.__class__ = type(cls.__name__, (cls, GenerationMixin), {})

    # The mixin was absent at __init__ time, so generation_config never got
    # populated; transformers' generate() dereferences it unconditionally.
    if getattr(language_model, "generation_config", None) is None:
        try:
            language_model.generation_config = GenerationConfig.from_model_config(
                language_model.config
            )
        except Exception:
            language_model.generation_config = GenerationConfig()


# --------------------------------------------------------------------------
# Token extraction (InternViT = the VLM's own tokenizer)
# --------------------------------------------------------------------------
@torch.no_grad()
def extract_internvit_tokens(model, pixel_values: torch.Tensor) -> torch.Tensor:
    """Run InternViT + pixel-shuffle + mlp1 on pixels.

    Returns ``[num_tiles, num_image_token, llm_hidden]`` token embeddings —
    exactly the tensor that gets substituted into the language model.
    """

    param = next(model.parameters())
    pixel_values = pixel_values.to(device=param.device, dtype=param.dtype)
    return model.extract_feature(pixel_values)


# --------------------------------------------------------------------------
# Prompt building (shared by both QA paths)
# --------------------------------------------------------------------------
def _build_query(model, tokenizer, question: str, num_patches_list: list[int]):
    """Replicate InternVLChatModel.chat()'s prompt construction.

    Returns ``(input_ids, attention_mask, eos_token_id)``.
    """

    # ``get_conv_template`` lives in the checkpoint's conversation.py, which the
    # modeling module imports. Pull it from the model's (trust_remote_code)
    # module namespace so no sys.path manipulation is needed.
    import importlib

    get_conv_template = importlib.import_module(model.__class__.__module__).get_conv_template

    if "<image>" not in question:
        question = "<image>\n" + question

    template = get_conv_template(model.template)
    template.system_message = model.system_message
    eos_token_id = tokenizer.convert_tokens_to_ids(template.sep.strip())

    template.append_message(template.roles[0], question)
    template.append_message(template.roles[1], None)
    query = template.get_prompt()

    for num_patches in num_patches_list:
        image_tokens = (
            IMG_START_TOKEN
            + IMG_CONTEXT_TOKEN * model.num_image_token * num_patches
            + IMG_END_TOKEN
        )
        query = query.replace("<image>", image_tokens, 1)

    model_inputs = tokenizer(query, return_tensors="pt")
    return model_inputs["input_ids"], model_inputs["attention_mask"], eos_token_id


@torch.no_grad()
def chat_pixels(model, tokenizer, pixel_values, question, max_new_tokens=64):
    """Normal QA path: pixels -> InternViT -> language model."""

    param = next(model.parameters())
    generation_config = {"max_new_tokens": max_new_tokens, "do_sample": False}
    return model.chat(
        tokenizer,
        pixel_values.to(device=param.device, dtype=param.dtype),
        question,
        generation_config,
    )


@torch.no_grad()
def chat_embeds(model, tokenizer, vit_embeds, num_patches_list, question, max_new_tokens=64):
    """Injection QA path: precomputed token embeddings -> language model.

    Pixels are replaced by a zero tensor; ``visual_features`` carries all the
    visual information. This is the Pathway B path — the language model never
    sees real pixels.
    """

    param = next(model.parameters())
    input_ids, attention_mask, eos_token_id = _build_query(
        model, tokenizer, question, num_patches_list
    )
    input_ids = input_ids.to(param.device)
    attention_mask = attention_mask.to(param.device)

    vit_embeds = vit_embeds.to(device=param.device, dtype=param.dtype)
    dummy_pixels = torch.zeros(
        sum(num_patches_list), 3, 448, 448, device=param.device, dtype=param.dtype
    )

    # Pass generation params as kwargs (not a bare GenerationConfig) so the
    # model's own generation_config — which carries bos_token_id — is used as
    # the base. inputs_embeds-only generation needs bos_token_id defined.
    output = model.generate(
        pixel_values=dummy_pixels,
        visual_features=vit_embeds,
        input_ids=input_ids,
        attention_mask=attention_mask,
        max_new_tokens=max_new_tokens,
        do_sample=False,
        eos_token_id=eos_token_id,
    )
    return tokenizer.batch_decode(output, skip_special_tokens=True)[0].strip()


# --------------------------------------------------------------------------
# Pathway B: QA directly on codec tokens (no pixel reconstruction)
# --------------------------------------------------------------------------
def _sample_frame_indices(idx, sample_count):
    """Uniformly sample frame ids from a codec-token ``idx`` tensor."""

    frames = sorted({int(v) for v in idx[:, 0].tolist()})
    if sample_count >= len(frames):
        return frames
    step = len(frames) / sample_count
    return [frames[int(i * step)] for i in range(sample_count)]


@torch.no_grad()
def qa_from_codec_tokens(
    model,
    tokenizer,
    tokens_path,
    question,
    options,
    sample_count=8,
    max_new_tokens=64,
):
    """Answer a multiple-choice question straight from saved codec tokens.

    Loads ``codec_tokens.pt`` (produced by the codec's token head), samples
    frames, injects their token sequences into InternVL, and returns the raw
    model answer. No pixel image is ever built — this is the Pathway B
    machine path end to end.
    """

    payload = torch.load(tokens_path, map_location="cpu")
    idx, tokens = payload["idx"], payload["tokens"]  # [M, 3], [M, 256, 4096]

    frame_ids = _sample_frame_indices(idx, sample_count)
    first_row_of_frame = {}
    for row in range(idx.shape[0]):
        frame = int(idx[row, 0])
        first_row_of_frame.setdefault(frame, row)
    rows = [first_row_of_frame[f] for f in frame_ids]
    vit_embeds = tokens[rows]  # [N, 256, 4096]

    option_lines = "\n".join(f"{chr(65 + i)}. {opt}" for i, opt in enumerate(options))
    image_tags = "".join("<image>\n" for _ in rows)
    prompt = (
        f"{image_tags}{question}\nOptions:\n{option_lines}\n"
        f"Answer with the option letter only."
    )
    return chat_embeds(
        model, tokenizer, vit_embeds, [1] * len(rows), prompt, max_new_tokens
    )


# --------------------------------------------------------------------------
# Raw-frames multiple-choice (oracle ceiling + pixel-codec baseline)
# --------------------------------------------------------------------------
def _parse_letter(answer: str):
    """First A-E letter in the model answer (matches the codec-token scorer)."""
    for ch in answer.upper():
        if ch in 'ABCDE':
            return ch
    return None


def _write_qa_json(output_json, payload):
    import json as _json
    from pathlib import Path as _P
    _P(output_json).parent.mkdir(parents=True, exist_ok=True)
    _P(output_json).write_text(_json.dumps(payload, indent=2, ensure_ascii=False))
    print(f"[qa] wrote {output_json}")


def _list_frames(frame_dir):
    from pathlib import Path as _P
    files = []
    for ext in ('*.png', '*.jpg', '*.jpeg'):
        files.extend(_P(frame_dir).glob(ext))
    return sorted(files)


@torch.no_grad()
def qa_from_raw_frames(model, tokenizer, frame_dir, question, options,
                       sample_count=8, max_new_tokens=64):
    """Multiple-choice QA on raw/decoded frames via the standard pixel path.

    Used for (a) the oracle ceiling (lossless frames) and (b) the pixel-codec
    baseline (HEVC/VVC-reconstructed frames). Uses the SAME MC prompt and
    letter parsing as ``qa_from_codec_tokens`` so the comparison is fair.
    """
    frames = _list_frames(frame_dir)
    if not frames:
        raise FileNotFoundError(f'no frame images (*.png/*.jpg) in {frame_dir}')
    if sample_count < len(frames):
        step = len(frames) / sample_count
        # QA_SAMPLE_OFFSET shifts the query grid phase (multi-phase averaging;
        # default 0 = the original grid). Set by the offset-mean harvest.
        _off = int(os.environ.get('QA_SAMPLE_OFFSET', '0'))
        frames = [frames[min(int(i * step) + _off, len(frames) - 1)]
                  for i in range(sample_count)]
    tiles = [load_image(str(p), max_num=1) for p in frames]
    pixel_values = torch.cat(tiles, dim=0)
    num_patches_list = [1] * len(frames)

    option_lines = "\n".join(f"{chr(65 + i)}. {opt}" for i, opt in enumerate(options))
    image_tags = ''.join('<image>\n' for _ in frames)
    prompt = (f"{image_tags}{question}\nOptions:\n{option_lines}\n"
              f"Answer with the option letter only.")
    param = next(model.parameters())
    generation_config = {'max_new_tokens': max_new_tokens, 'do_sample': False}
    return model.chat(
        tokenizer,
        pixel_values.to(device=param.device, dtype=param.dtype),
        prompt,
        generation_config,
        num_patches_list=num_patches_list,
    )


# --------------------------------------------------------------------------
# Pathway B-mid: free-form QA with raw-video oracle and self-judge
# --------------------------------------------------------------------------
def _free_form_qa_on_codec(model, tokenizer, vit_embeds, num_patches_list,
                           question, max_new_tokens=128):
    """Open-ended QA on already-loaded codec tokens (no options)."""
    image_tags = ''.join('<image>\n' for _ in num_patches_list)
    prompt = f'{image_tags}{question}'
    return chat_embeds(model, tokenizer, vit_embeds, num_patches_list, prompt,
                       max_new_tokens=max_new_tokens)


def _free_form_qa_on_pixels(model, tokenizer, pixel_values, num_patches_list,
                            question, max_new_tokens=128):
    """Open-ended QA on raw frames via the standard pixel path. Multi-frame:
    ``num_patches_list=[tiles_per_frame, ...]`` (typically [1,1,...,1]).
    """
    image_tags = ''.join('<image>\n' for _ in num_patches_list)
    prompt = f'{image_tags}{question}'
    param = next(model.parameters())
    generation_config = {'max_new_tokens': max_new_tokens, 'do_sample': False}
    return model.chat(
        tokenizer,
        pixel_values.to(device=param.device, dtype=param.dtype),
        prompt,
        generation_config,
        num_patches_list=list(num_patches_list),
    )


def _judge_two_answers(model, tokenizer, question, oracle_answer, codec_answer):
    """Use the same InternVL as a text judge. Returns (raw_text, agree_bool)."""
    prompt = (
        f'Two answers were given to the same question. Decide if they convey '
        f'substantially the same information.\n'
        f'Question: {question}\n'
        f'Answer A (oracle, from the real video): {oracle_answer.strip()}\n'
        f'Answer B (compressed-codec output): {codec_answer.strip()}\n'
        f'Reply with exactly "Yes" or "No".'
    )
    device = next(model.parameters()).device
    dtype = next(model.parameters()).dtype
    dummy = torch.zeros(1, 3, 448, 448, dtype=dtype, device=device)
    raw = chat_pixels(model, tokenizer, dummy, f'<image>\n{prompt}',
                      max_new_tokens=8)
    head = raw.strip().lower()
    return raw, head.startswith('yes')


@torch.no_grad()
def qa_self_judge_run(model, tokenizer, tokens_path, raw_chunk_dir, questions,
                     sample_count=4, max_new_tokens=128):
    """Compare codec-token VQA vs raw-pixel VQA on the same sampled frames.

    Returns a list of per-question records and the overall agreement rate.
    """
    import os
    from pathlib import Path
    payload = torch.load(tokens_path, map_location='cpu')
    idx, tokens = payload['idx'], payload['tokens']
    frame_ids = _sample_frame_indices(idx, sample_count)
    first_row_of_frame = {}
    for row in range(idx.shape[0]):
        frame = int(idx[row, 0])
        first_row_of_frame.setdefault(frame, row)
    rows = [first_row_of_frame[f] for f in frame_ids]
    codec_vit_embeds = tokens[rows]
    num_patches_list = [1] * len(rows)

    # Load matching raw frames via InternVL's standard preprocessing.
    raw_tiles = []
    for fid in frame_ids:
        png_path = Path(raw_chunk_dir) / f'{fid:04d}.png'
        if not png_path.exists():
            # fallback: zero-padded 6 digits
            png_path = Path(raw_chunk_dir) / f'{fid:06d}.png'
        if not png_path.exists():
            raise FileNotFoundError(f'No frame file for id {fid} in {raw_chunk_dir}')
        raw_tiles.append(load_image(str(png_path), max_num=1))
    raw_pixel_values = torch.cat(raw_tiles, dim=0)

    records = []
    agree_count = 0
    for q in questions:
        codec_ans = _free_form_qa_on_codec(
            model, tokenizer, codec_vit_embeds, num_patches_list, q,
            max_new_tokens=max_new_tokens,
        )
        oracle_ans = _free_form_qa_on_pixels(
            model, tokenizer, raw_pixel_values, num_patches_list, q,
            max_new_tokens=max_new_tokens,
        )
        judge_raw, agree = _judge_two_answers(model, tokenizer, q,
                                              oracle_ans, codec_ans)
        records.append({
            'question': q,
            'oracle_answer': oracle_ans,
            'codec_answer': codec_ans,
            'judge_raw': judge_raw,
            'agree': bool(agree),
        })
        if agree:
            agree_count += 1
        print(f'  Q: {q[:80]}')
        print(f'    oracle : {oracle_ans[:100]}')
        print(f'    codec  : {codec_ans[:100]}')
        print(f'    judge  : {judge_raw.strip()[:30]} -> agree={agree}')
    agreement_rate = (agree_count / len(questions)) if questions else None
    return {
        'sample_frame_ids': frame_ids,
        'agreement_rate': agreement_rate,
        'num_questions': len(questions),
        'num_agree': agree_count,
        'records': records,
    }


# --------------------------------------------------------------------------
# Phase 0 smoke test
# --------------------------------------------------------------------------
def smoke_test(model_path: str, image_path: str, device: str) -> bool:
    """Verify the injection path matches the pixel path. Returns True on pass."""

    print(f"[smoke] loading InternVL2.5-8B from {model_path} ...")
    model, tokenizer = load_internvl(model_path, device=device)
    print(f"[smoke] num_image_token per tile = {model.num_image_token}")

    pixel_values = load_image(image_path)
    num_patches_list = [pixel_values.shape[0]]
    print(f"[smoke] image '{image_path}' -> {pixel_values.shape[0]} tiles")

    question = "Describe this image in one sentence."

    answer_pixel = chat_pixels(model, tokenizer, pixel_values, question)
    print(f"[smoke] pixel-path answer    : {answer_pixel}")

    vit_embeds = extract_internvit_tokens(model, pixel_values)
    print(f"[smoke] InternViT tokens shape: {tuple(vit_embeds.shape)}")

    answer_inject = chat_embeds(model, tokenizer, vit_embeds, num_patches_list, question)
    print(f"[smoke] injection-path answer: {answer_inject}")

    passed = answer_pixel.strip() == answer_inject.strip()
    print(f"[smoke] GATE {'PASS' if passed else 'FAIL'} "
          f"(answers {'match' if passed else 'DIFFER'})")
    return passed


def main() -> None:
    parser = argparse.ArgumentParser(description="InternVL2.5 backend (Pathway B Phase 0).")
    parser.add_argument("--smoke", action="store_true", help="Run the injection-path gate test.")
    parser.add_argument("--qa-tokens", default=None,
                        help="Path to a codec_tokens.pt; runs Pathway B QA on it.")
    parser.add_argument("--qa-raw-frames", default=None,
                        help="Directory of raw/decoded frames; runs MC QA via the standard pixel "
                             "path (oracle ceiling or pixel-codec baseline).")
    parser.add_argument("--model-path", default=DEFAULT_MODEL_PATH)
    parser.add_argument(
        "--image",
        default=str(Path(DEFAULT_MODEL_PATH) / "examples" / "image1.jpg"),
    )
    parser.add_argument("--device", default="cuda")
    parser.add_argument("--question", default=None,
                        help="QA question to ask. Defaults to the gardening probe.")
    parser.add_argument("--option", action="append", default=None,
                        help="QA option line (repeat to add more). Default = 5 gardening options.")
    parser.add_argument("--expected-letter", default=None,
                        help="Correct option letter (A-E). If set, scoring is recorded in --output-json.")
    parser.add_argument("--output-json", default=None,
                        help="Where to write the QA result JSON (used by the demo renderer).")
    parser.add_argument("--qa-self-judge", action="store_true",
                        help="Free-form QA: oracle=raw-frames-through-VLM, codec=codec-tokens-through-VLM, "
                             "VLM judges agreement. Requires --raw-chunk-dir and --questions-file.")
    parser.add_argument("--raw-chunk-dir", default=None,
                        help="Directory of raw frame PNGs (NNNN.png) matching the codec_tokens.pt indices.")
    parser.add_argument("--questions-file", default=None,
                        help="Text file, one open-ended question per line.")
    parser.add_argument("--sample-count", type=int, default=4,
                        help="Number of frames to sample for both oracle and codec QA.")
    args = parser.parse_args()

    if args.smoke:
        ok = smoke_test(args.model_path, args.image, args.device)
        raise SystemExit(0 if ok else 1)
    if args.qa_self_judge:
        if not (args.qa_tokens and args.raw_chunk_dir and args.questions_file):
            raise SystemExit("--qa-self-judge requires --qa-tokens, --raw-chunk-dir, --questions-file")
        from pathlib import Path as _P
        import json as _json
        questions = [ln.strip() for ln in _P(args.questions_file).read_text().splitlines() if ln.strip()]
        model, tokenizer = load_internvl(args.model_path, device=args.device)
        result = qa_self_judge_run(model, tokenizer, args.qa_tokens,
                                   args.raw_chunk_dir, questions,
                                   sample_count=args.sample_count)
        if args.output_json:
            _P(args.output_json).parent.mkdir(parents=True, exist_ok=True)
            _P(args.output_json).write_text(_json.dumps(result, indent=2, ensure_ascii=False))
            print(f"[self-judge] wrote {args.output_json}")
        print(f"[self-judge] agreement_rate = {result['agreement_rate']:.3f} "
              f"({result['num_agree']}/{result['num_questions']})")
        raise SystemExit(0)
    if args.qa_raw_frames:
        model, tokenizer = load_internvl(args.model_path, device=args.device)
        question = args.question or "What is the camera wearer doing in the video?"
        options = list(args.option) if args.option else ["A", "B", "C", "D", "E"]
        answer = qa_from_raw_frames(model, tokenizer, args.qa_raw_frames,
                                    question, options, sample_count=args.sample_count)
        print(f"[qa-raw-frames] answer: {answer}")
        parsed_letter = _parse_letter(answer)
        correct = None
        if args.expected_letter:
            correct = (parsed_letter == args.expected_letter.upper())
        if args.output_json:
            _write_qa_json(args.output_json, {
                'mode': 'raw_frames',
                'frame_dir': args.qa_raw_frames,
                'question': question,
                'options': options,
                'expected_letter': args.expected_letter,
                'model_answer': answer,
                'parsed_letter': parsed_letter,
                'correct': correct,
            })
        raise SystemExit(0)
    if args.qa_tokens:
        model, tokenizer = load_internvl(args.model_path, device=args.device)
        question = args.question or (
            "What outdoor or agricultural task is the camera wearer performing?"
        )
        options = list(args.option) if args.option else [
            "Mowing a lawn.",
            "Constructing a building.",
            "Digging or tilling soil.",
            "Painting an outdoor surface.",
            "Cleaning an outdoor area.",
        ]
        answer = qa_from_codec_tokens(model, tokenizer, args.qa_tokens, question, options)
        print(f"[qa-tokens] codec-token QA answer: {answer}")
        parsed_letter = None
        for ch in answer.upper():
            if ch in 'ABCDE' and parsed_letter is None:
                parsed_letter = ch
        correct = None
        if args.expected_letter:
            correct = (parsed_letter == args.expected_letter.upper())
        if args.output_json:
            import json as _json
            from pathlib import Path as _P
            out = {
                'question': question,
                'options': options,
                'expected_letter': args.expected_letter,
                'model_answer': answer,
                'parsed_letter': parsed_letter,
                'correct': correct,
                'tokens_path': args.qa_tokens,
            }
            _P(args.output_json).parent.mkdir(parents=True, exist_ok=True)
            _P(args.output_json).write_text(_json.dumps(out, indent=2, ensure_ascii=False))
            print(f"[qa-tokens] wrote {args.output_json}")
        raise SystemExit(0)
    parser.print_help()


if __name__ == "__main__":
    main()
