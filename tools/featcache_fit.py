#!/usr/bin/env python3
"""E-04: fit the shared feature-cache book on the 32 universal-adapter donors.

  PYTHONPATH=src python tools/featcache_fit.py --donors-file outputs/featcache/donors.txt \
      --out /mnt/nas/xinyizheng/vidtok_out/exp_featcache/featcodec_internvl_v1.pt

donors.txt lines: "<dataset> <uuid>"; frames are read from <root>/_videos/<dataset>/<uuid>_256_uniform
where root is --ego-root for egoschema and --vmme-root otherwise.
"""
import argparse, os, sys, time
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import torch
from machine_codec_pipeline.vlm.internvl_backend import load_internvl, DEFAULT_MODEL_PATH
from machine_codec_pipeline.featcache.extract import video_tokens, frame_dir_of
from machine_codec_pipeline.featcache.fit import collect_pooled, fit_book, DEFAULT_POOLS, DEFAULT_PCAS, DEFAULT_PQ

R = "/mnt/nas/xinyizheng/vidtok_out"


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--donors-file", required=True)
    ap.add_argument("--ego-root", default=f"{R}/u_egos")
    ap.add_argument("--vmme-root", default=f"{R}/u_vmme")
    ap.add_argument("--model-path", default=os.environ.get("INTERNVL_MODEL_PATH", DEFAULT_MODEL_PATH))
    ap.add_argument("--pools", nargs="+", type=int, default=list(DEFAULT_POOLS))
    ap.add_argument("--pcas", nargs="+", default=[str(p) for p in DEFAULT_PCAS],
                    help="PCA dims; 'None' = raw")
    ap.add_argument("--out", required=True)
    ap.add_argument("--limit", type=int, default=0, help="debug: only the first N donors")
    args = ap.parse_args()

    donors = [l.split() for l in open(args.donors_file) if l.strip() and not l.startswith("#")]
    if args.limit:
        donors = donors[:args.limit]
    pcas = tuple(None if p == "None" else int(p) for p in args.pcas)
    model, _ = load_internvl(args.model_path)
    t0 = time.time()

    def gen():
        for i, (ds, u) in enumerate(donors):
            root = args.ego_root if ds == "egoschema" else args.vmme_root
            tok = video_tokens(model, frame_dir_of(root, ds, u))
            print(f"[tokens] {i+1}/{len(donors)} {ds} {u} {tuple(tok.shape)} {time.time()-t0:.0f}s", flush=True)
            yield tok

    pooled = collect_pooled(gen(), tuple(args.pools))
    del model; torch.cuda.empty_cache()
    for k, v in pooled.items():
        print(f"[pooled] K={k} {tuple(v.shape)}", flush=True)
    book = fit_book(pooled, pcas=pcas, pq=DEFAULT_PQ, device="cuda" if torch.cuda.is_available() else "cpu",
                    log=lambda *a: print(*a, flush=True))
    book["meta"]["donors"] = donors
    book["meta"]["model_path"] = args.model_path
    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    torch.save(book, args.out)
    print(f"[fit] saved {args.out} ({os.path.getsize(args.out)/1e6:.1f} MB) in {time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
