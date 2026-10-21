#!/usr/bin/env python3
"""B4 (D-017): train learned feature autoencoders on the 32 donors' pooled token caches.

  PYTHONPATH=src python tools/featcache_ae_train.py --pool 64 --latent 128 --lambdas 0.25 1 4 16 \
      --out-dir /mnt/nas/xinyizheng/vidtok_out/exp_featcache/ae

Donor pooled tokens are cached once per K at <out-dir>/donor_pooled_K<K>.pt (fp16 [D, T, K, 4096]).
The last VMME donor and the last Ego donor are held out for validation (reported, not trained on).
Loss = bits_per_token / dim + lambda * MSE(standardised); one model per lambda, each saved with its
estimated and ACTUAL (entropy-coded) val bits per token.
"""
import argparse, os, sys, time, math
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import torch
from machine_codec_pipeline.featcache.ae import AEConfig, TokenAE, save_ae, payload_bits
from machine_codec_pipeline.featcache.codec import pool_tokens

R = "/mnt/nas/xinyizheng/vidtok_out"


def donor_pooled(args, pool):
    cache = os.path.join(args.out_dir, f"donor_pooled_K{pool}.pt")
    if os.path.exists(cache):
        d = torch.load(cache, map_location="cpu"); print(f"[data] cached {cache} {tuple(d['x'].shape)}", flush=True)
        return d["x"], d["donors"]
    from machine_codec_pipeline.vlm.internvl_backend import load_internvl, DEFAULT_MODEL_PATH
    from machine_codec_pipeline.featcache.extract import video_tokens, frame_dir_of
    donors = [l.split() for l in open(args.donors_file) if l.strip() and not l.startswith("#")]
    model, _ = load_internvl(os.environ.get("INTERNVL_MODEL_PATH", DEFAULT_MODEL_PATH))
    xs = []
    for i, (ds, u) in enumerate(donors):
        root = f"{R}/u_egos" if ds == "egoschema" else f"{R}/u_vmme"
        tok = video_tokens(model, frame_dir_of(root, ds, u))
        xs.append(pool_tokens(tok, pool).to(torch.float16))
        print(f"[data] {i+1}/{len(donors)} {u} {tuple(xs[-1].shape)}", flush=True)
    x = torch.stack(xs); del model; torch.cuda.empty_cache()
    os.makedirs(args.out_dir, exist_ok=True); torch.save({"x": x, "donors": donors}, cache)
    return x, donors


def main():
    ap = argparse.ArgumentParser()
    ap.add_argument("--donors-file", default="outputs/featcache/donors.txt")
    ap.add_argument("--out-dir", default=f"{R}/exp_featcache/ae")
    ap.add_argument("--pool", type=int, default=64)
    ap.add_argument("--latent", type=int, default=128)
    ap.add_argument("--hidden", type=int, default=1024)
    ap.add_argument("--no-hyper", action="store_true")
    ap.add_argument("--lambdas", nargs="+", type=float, default=[0.25, 1.0, 4.0, 16.0])
    ap.add_argument("--steps", type=int, default=6000)
    ap.add_argument("--batch", type=int, default=2048)
    ap.add_argument("--lr", type=float, default=1e-3)
    ap.add_argument("--seed", type=int, default=0)
    args = ap.parse_args()
    dev = "cuda" if torch.cuda.is_available() else "cpu"
    torch.manual_seed(args.seed)

    x, donors = donor_pooled(args, args.pool)                      # [D, T, K, C] fp16
    is_val = torch.zeros(len(donors), dtype=torch.bool)
    for ds in ("vmme_long_motion", "egoschema"):                   # hold out the last donor of each dataset
        idx = [i for i, (d, _) in enumerate(donors) if d == ds]
        if idx: is_val[idx[-1]] = True
    c = x.shape[-1]
    train = x[~is_val].reshape(-1, c); val = x[is_val].reshape(-1, c)
    val_video = x[is_val][0].reshape(-1, c)                        # one held-out video for ACTUAL coding
    mean = train.float().mean(0); std = train.float().std(0)
    train_d = train.to(dev); val_d = val.to(dev)
    print(f"[data] train tokens {train.shape[0]} val tokens {val.shape[0]} dim {c}", flush=True)
    os.makedirs(args.out_dir, exist_ok=True)

    for lam in args.lambdas:
        cfg = AEConfig(dim=c, hidden=args.hidden, latent=args.latent, hyper=not args.no_hyper, pool=args.pool)
        model = TokenAE(cfg).to(dev); model.set_standardisation(mean.to(dev), std.to(dev))
        main_params = [p for n, p in model.named_parameters() if not n.endswith(".quantiles")]
        aux_params = [p for n, p in model.named_parameters() if n.endswith(".quantiles")]
        opt = torch.optim.AdamW(main_params, lr=args.lr, weight_decay=1e-5)
        aux_opt = torch.optim.Adam(aux_params, lr=1e-3)
        sched = torch.optim.lr_scheduler.CosineAnnealingLR(opt, args.steps)
        t0 = time.time(); g = torch.Generator(device=dev).manual_seed(args.seed)
        for step in range(1, args.steps + 1):
            idx = torch.randint(0, train_d.shape[0], (args.batch,), generator=g, device=dev)
            out = model(train_d[idx].float())
            loss = out["bits_per_token"] / c + lam * out["mse"]
            opt.zero_grad(set_to_none=True); loss.backward()
            torch.nn.utils.clip_grad_norm_(main_params, 1.0); opt.step(); sched.step()
            aux = model.aux_loss(); aux_opt.zero_grad(set_to_none=True); aux.backward(); aux_opt.step()
            if step % 500 == 0 or step == args.steps:
                print(f"[lam={lam}] step {step} bits/token {out['bits_per_token'].item():.1f} mse {out['mse'].item():.4f} "
                      f"aux {aux.item():.1f} {time.time()-t0:.0f}s", flush=True)
        model.eval(); model.update(force=True)
        with torch.no_grad():
            vo = model(val_d.float())
            pay = model.compress(val_video.float().to(dev))
            actual = payload_bits(pay) / val_video.shape[0]
            x_hat = model.decompress(pay).cpu()
            rel = ((x_hat - val_video.float()) ** 2).mean() / val_video.float().var()
        name = f"p{args.pool}_ae_z{args.latent}_l{lam:g}" + ("" if cfg.hyper else "_nohyper")
        meta = {"name": name, "lambda": lam, "val_bits_per_token_est": vo["bits_per_token"].item(),
                "val_mse_std": vo["mse"].item(), "val_bits_per_token_actual": actual, "val_rel_mse_actual": rel.item(),
                "steps": args.steps, "donors": donors, "bpp_at_128f": actual * args.pool / (256 * 256)}
        save_ae(model, os.path.join(args.out_dir, name + ".pt"), meta)
        print(f"[done] {name}: val est {vo['bits_per_token'].item():.1f} / actual {actual:.1f} bits/token "
              f"(= {meta['bpp_at_128f']:.4f} bpp), rel-mse {rel.item():.4f}, {time.time()-t0:.0f}s", flush=True)


if __name__ == "__main__":
    main()
