#!/usr/bin/env python3
"""E-04 harvest: feature-cache compression baselines on the SAME videos/questions/frames as
harvest_stratified. For every video: frozen vision tower once on all cached frames -> token
cache [T,256,4096] -> for each spec: encode (bits counted) -> decode the 8 query frames ->
same LLM call as ours (token injection, num_image_token = K) -> all questions.

Output CSV rows (same schema as stratified.csv): out_root,interface,rate,uuid,bucket,task_type,correct,bpp
  interface = "featcache", rate = spec name, bpp = bits / (T*256*256) with bits = ideal-coder entropy.
Sidecar JSON: per (uuid, spec) {bits_entropy, bits_lzma, bits_raw, bpp}.
"""
import argparse, csv, json, os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import torch
from machine_codec_pipeline.vlm.internvl_backend import load_internvl, chat_embeds, _parse_letter, DEFAULT_MODEL_PATH
from machine_codec_pipeline.featcache import FeatCodec, parse_spec
from machine_codec_pipeline.featcache.extract import video_tokens, query_frame_rows, frame_dir_of

PARTIAL_EVERY = 10
MAX_NEW_TOKENS = 16


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--out-root", required=True)
    ap.add_argument("--dataset", required=True)
    ap.add_argument("--manifest-dir", required=True)
    ap.add_argument("--manifest-file", default="questions.jsonl")
    ap.add_argument("--uuids-file", default=None, help="restrict to these video ids (one per line)")
    ap.add_argument("--book", default=None)
    ap.add_argument("--specs", nargs="+", default=[])
    ap.add_argument("--ae-models", nargs="+", default=[], help="B4: trained TokenAE .pt files (rate label = model name)")
    ap.add_argument("--sample-count", type=int, default=8)
    ap.add_argument("--model-path", default=os.environ.get("INTERNVL_MODEL_PATH", DEFAULT_MODEL_PATH))
    ap.add_argument("--out", required=True)
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--nshard", type=int, default=1)
    ap.add_argument("--limit", type=int, default=0)
    args = ap.parse_args()

    qmap = {}
    for l in open(os.path.join(args.manifest_dir, args.manifest_file)):
        d = json.loads(l); d.setdefault("bucket", "all"); d.setdefault("task_type", "all")
        qmap.setdefault(d["video_idx"], []).append(d)
    vids = sorted(qmap)
    if args.uuids_file:
        keep = {l.strip() for l in open(args.uuids_file) if l.strip()}
        vids = [v for v in vids if v in keep]
    vids = vids[args.shard::args.nshard]
    if args.limit:
        vids = vids[:args.limit]

    if not args.specs and not args.ae_models:
        raise SystemExit("give --specs and/or --ae-models")
    book = torch.load(args.book, map_location="cpu") if args.specs else {}
    specs = [parse_spec(s) for s in args.specs]
    codecs = {s.name: FeatCodec(book, s) for s in specs}
    if args.ae_models:
        from machine_codec_pipeline.featcache.ae import AECodec
        for p in args.ae_models:
            c = AECodec(p); codecs[c.spec.name] = c
    model, tok = load_internvl(args.model_path)
    dev = next(model.parameters()).device; dtype = next(model.parameters()).dtype
    base = model.num_image_token

    def ask(emb, q):
        nf, k = emb.shape[0], emb.shape[1]
        ol = "\n".join(f"{chr(65+i)}. {o}" for i, o in enumerate(q["options"]))
        prompt = "".join("<image>\n" for _ in range(nf)) + f"{q['question']}\nOptions:\n{ol}\nAnswer with the option letter only."
        model.num_image_token = k
        try:
            ans = chat_embeds(model, tok, emb.to(dev).to(dtype), [1] * nf, prompt, MAX_NEW_TOKENS)
        finally:
            model.num_image_token = base
        return _parse_letter(ans)

    rows, side = [], {}
    errs = 0
    t0 = time.time()

    def flush():
        with open(args.out, "w", newline="") as f:
            w = csv.writer(f); w.writerow(["out_root", "interface", "rate", "uuid", "bucket", "task_type", "correct", "bpp"]); w.writerows(rows)
        with open(os.path.splitext(args.out)[0] + "_bits.json", "w") as f:
            json.dump(side, f)

    for vi, uuid in enumerate(vids):
        qs = qmap[uuid]
        fd = frame_dir_of(args.out_root, args.dataset, uuid)
        if not os.path.isdir(fd):
            print(f"[skip] no frames {fd}", flush=True); continue
        try:
            cache = video_tokens(model, fd)                         # [T,256,4096] fp16
        except Exception as e:
            errs += 1; print(f"[EVAL-ERR #{errs}] tokens {uuid}: {type(e).__name__}: {e}", flush=True); continue
        rws = query_frame_rows(cache.shape[0], args.sample_count)
        side[uuid] = {}
        for name, codec in codecs.items():
            try:
                pay = codec.encode(cache)
                emb = codec.decode(pay, rws)                             # [8,K,4096]
            except Exception as e:
                errs += 1; print(f"[EVAL-ERR #{errs}] {name} {uuid}: {type(e).__name__}: {e}", flush=True); continue
            side[uuid][name] = {"bits_entropy": pay.bits_entropy, "bits_lzma": pay.bits_lzma,
                                "bits_raw": pay.bits_raw, "bpp": pay.bpp, "frames": pay.frames}
            for q in qs:
                try:
                    ok = ask(emb, q) == q["expected_letter"]
                except Exception as e:
                    ok = False; errs += 1
                    if errs <= 5 or errs % 100 == 0:
                        print(f"[EVAL-ERR #{errs}] qa {name} {uuid}: {type(e).__name__}: {e}", flush=True)
                rows.append([args.out_root, "featcache", name, uuid, q["bucket"], q["task_type"], ok, f"{pay.bpp:.6f}"])
        print(f"[{vi+1}/{len(vids)}] {uuid} done ({len(qs)}q x {len(codecs)} specs) {time.time()-t0:.0f}s", flush=True)
        if (vi + 1) % PARTIAL_EVERY == 0:
            flush()
    flush()
    print(f"\n{len(rows)} rows -> {args.out}")
    print(f"swallowed eval exceptions: {errs}" + (" ⚠️ RUN SUSPECT" if errs > max(1, len(rows)) * 0.01 else ""))


if __name__ == "__main__":
    main()
