#!/usr/bin/env python3
"""P0-0 harvest: re-eval EXISTING trained codecs (+ oracle + HEVC recon) against ALL
questions per video, stratified by task_type bucket. Model loaded once. No training.
Squeezes every per-video codec for ~3x data + a detail/temporal/gist breakdown.

Output CSV rows: out_root_tag,interface,rate,uuid,bucket,task_type,correct,bpp
Usage:
  CUDA_VISIBLE_DEVICES=4 PYTHONPATH=src python tools/harvest_stratified.py \
    --out-root outputs/gate1_vmme --rates cap_r1 cap_g_mlo cap_xs \
    --crfs 28 33 40 45 51 --out outputs/gate1_vmme/stratified.csv
"""
import argparse, csv, glob, json, os, sys
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", "src"))
import torch
from machine_codec_pipeline.vlm.internvl_backend import (
    load_internvl, chat_embeds, qa_from_raw_frames, _parse_letter, DEFAULT_MODEL_PATH, _list_frames, load_image, extract_internvit_tokens)
from machine_codec_pipeline.vlm.visionzip import visionzip_reduce
from machine_codec_pipeline.vlm.fastv import fastv_prune
from machine_codec_pipeline.vlm.tome import tome_merge

def sample_rows(idx, k):
    frames = sorted({int(v) for v in idx[:,0].tolist()})
    if k < len(frames):
        step=len(frames)/k
        _off=int(os.environ.get('QA_SAMPLE_OFFSET','0'))
        frames=[frames[min(int(i*step)+_off,len(frames)-1)] for i in range(k)]
    first={}
    for r in range(idx.shape[0]): first.setdefault(int(idx[r,0]), r)
    return [first[f] for f in frames]

def bpp_map(csv_path):
    m={}
    if os.path.exists(csv_path):
        for r in csv.DictReader(open(csv_path)):
            if r["bpp"] not in ("NA",""): m[(r["interface"],r["rate"],r["uuid"])]=r["bpp"]
    return m

def main():
    ap=argparse.ArgumentParser()
    ap.add_argument("--out-root", default="outputs/gate1_vmme")
    ap.add_argument("--dataset", default="vmme_long_motion")
    ap.add_argument("--manifest-dir", default="outputs/datasets/vmme_long_motion")
    ap.add_argument("--manifest-file", default="questions.jsonl", help="manifest filename under --manifest-dir (egoschema uses manifest.jsonl)")
    ap.add_argument("--rates", nargs="+", default=["cap_r1","cap_g_mlo","cap_xs"])
    ap.add_argument("--interface", default="ours")
    ap.add_argument("--pool", type=int, default=256, help="tokens/frame after spatial avg-pool (256=off)")
    ap.add_argument("--crfs", nargs="+", default=["28","33","40","45","51"])
    ap.add_argument("--learned-qs", nargs="+", default=[])
    ap.add_argument("--vvc-qps", nargs="+", default=[])
    ap.add_argument("--dcvc-qps", nargs="+", default=[])
    ap.add_argument("--smcpp-crfs", nargs="+", default=[], help="SMC++ (TPAMI'25 VCM) recon crf list")
    ap.add_argument("--ugicm-qs", nargs="+", default=[], help="UG-ICM (AAAI'25 ICM) recon quality-ckpt list")
    ap.add_argument("--vcmrs-qps", nargs="+", default=[], help="MPEG VCM-RS v2.0 recon QP list")
    ap.add_argument("--shard", type=int, default=0)
    ap.add_argument("--nshard", type=int, default=1)
    ap.add_argument("--no-oracle", action="store_true", help="skip oracle re-eval (for codec-only top-up harvests)")
    ap.add_argument("--visionzip-k", nargs="+", type=int, default=[], help="QA-side VisionZip baseline: tokens/frame budgets (e.g. 64 16). Runs on the SAME oracle frames for a matched-pool comparison.")
    ap.add_argument("--fastv-k", nargs="+", type=int, default=[], help="QA-side FastV baseline: retained visual tokens/frame past the prune layer (e.g. 64 16). Same oracle frames, matched pool.")
    ap.add_argument("--tome-k", nargs="+", type=int, default=[], help="QA-side ToMe baseline: tokens/frame budgets after bipartite merging (e.g. 64 16). Same oracle frames, matched pool.")
    ap.add_argument("--sample-count", type=int, default=8)
    ap.add_argument("--model-path", default=os.environ.get("INTERNVL_MODEL_PATH", DEFAULT_MODEL_PATH))
    ap.add_argument("--out", default="outputs/gate1_vmme/stratified.csv")
    # CVPR-27 controls (2026-10-01). All run through the token-injection path so every
    # variant is scored by the same LLM call; pool=256 injection == the pixel chat path.
    ap.add_argument("--ctrl", choices=["none","shuffle","mismatch"], default="none",
                    help="shuffle: permute the 8 query frames' temporal order; mismatch: answer each "
                         "video's questions from the NEXT video's cache/frames (cyclic derangement). "
                         "Applies to ours and to the oracle; rows are labelled <iface>_<ctrl>.")
    ap.add_argument("--ctrl-seed", type=int, default=0)
    ap.add_argument("--pixel-cache-pool", nargs="+", type=int, default=[],
                    help="cached-pixel-path control: decode once -> vision tower once -> cache tokens -> "
                         "avg-pool to K tokens/frame -> LLM, for the oracle frames and every --crfs HEVC "
                         "recon. Rows: interface oraclecache/pixelcache, rate <src>_p<K>.")
    args=ap.parse_args()

    qmap={}  # uuid -> list of questions
    for l in open(os.path.join(args.manifest_dir,args.manifest_file)):
        d=json.loads(l); d.setdefault("bucket","all"); d.setdefault("task_type","all")
        qmap.setdefault(d["video_idx"],[]).append(d)
    bm=bpp_map(os.path.join(args.out_root,"results.csv"))
    model,tok=load_internvl(args.model_path); dev=next(model.parameters()).device
    base=model.num_image_token
    rows=[]
    ERRS=[0]  # swallowed eval exceptions — a large count invalidates the run (silent-failure guard)
    TSTAT=[0,0]  # running (true, total) over the new-baseline evals — tripwire input
    def ask_emb(emb,nf,q,pool=None):
        pool=args.pool if pool is None else pool
        ol="\n".join(f"{chr(65+i)}. {o}" for i,o in enumerate(q["options"]))
        prompt="".join("<image>\n" for _ in range(nf))+f"{q['question']}\nOptions:\n{ol}\nAnswer with the option letter only."
        if pool!=256:
            import torch.nn.functional as Fnn
            N,T,C=emb.shape; g=int(round(T**0.5)); o=int(round(pool**0.5))
            x=emb.view(N,g,g,C).permute(0,3,1,2)
            emb=Fnn.adaptive_avg_pool2d(x,(o,o)).permute(0,2,3,1).reshape(N,o*o,C)
        model.num_image_token=pool
        try: ans=chat_embeds(model,tok,emb.to(dev).to(next(model.parameters()).dtype),[1]*nf,prompt,16)
        finally: model.num_image_token=base
        return _parse_letter(ans)
    def frames_to_tokens(frame_dir):
        """Cached-pixel path: the SAME 8-frame grid as qa_from_raw_frames (incl. QA_SAMPLE_OFFSET),
        through the frozen vision tower + projector ONCE -> [N,256,4096] LLM tokens."""
        import random as _r
        frames=_list_frames(frame_dir)
        if args.sample_count<len(frames):
            step=len(frames)/args.sample_count; off=int(os.environ.get("QA_SAMPLE_OFFSET","0"))
            frames=[frames[min(int(i*step)+off,len(frames)-1)] for i in range(args.sample_count)]
        tiles=torch.cat([load_image(str(p),max_num=1) for p in frames],dim=0)
        with torch.no_grad(): return extract_internvit_tokens(model,tiles).float().cpu()
    def ctrl_rows(emb,uuid):
        """Apply --ctrl shuffle to an [N,T,C] frame-token stack (deterministic per video)."""
        if args.ctrl!="shuffle": return emb
        import random as _r
        perm=list(range(emb.shape[0])); _r.Random(f"{args.ctrl_seed}:{uuid}").shuffle(perm)
        return emb[perm]
    sfx="" if args.ctrl=="none" else f"_{args.ctrl}"
    ALL=sorted(qmap)
    def src_of(uuid):   # mismatch: cyclic derangement over the sorted pool
        if args.ctrl!="mismatch": return uuid
        return ALL[(ALL.index(uuid)+1)%len(ALL)]
    vids=sorted(qmap)[args.shard::args.nshard]
    for vi,uuid in enumerate(vids):
        qs=qmap[uuid]; vc=f"{args.out_root}/_videos/{args.dataset}/{uuid}_256_uniform"
        su=src_of(uuid); vc_src=f"{args.out_root}/_videos/{args.dataset}/{su}_256_uniform"
        # ---- ours codecs ----
        for rate in args.rates:
            tp=glob.glob(f"{args.out_root}/{args.dataset}/internvl/mid/{args.interface}/{rate}/{su}/**/codec_tokens.pt",recursive=True)
            if not tp: continue
            pay=torch.load(tp[0],map_location="cpu"); idx,tk=pay["idx"],pay["tokens"]
            rws=sample_rows(idx,args.sample_count); emb=ctrl_rows(tk[rws],uuid); nf=emb.shape[0]
            for q in qs:
                ok=ask_emb(emb,nf,q)==q["expected_letter"]
                rows.append([args.out_root,args.interface+sfx,rate,uuid,q["bucket"],q["task_type"],ok,bm.get((args.interface,rate,su),"NA")])
        # ---- oracle (raw frames) ----
        if os.path.isdir(vc) and not args.no_oracle and args.ctrl=="none":
            for q in qs:
                try: ok=_parse_letter(qa_from_raw_frames(model,tok,vc,q["question"],q["options"],args.sample_count))==q["expected_letter"]
                except Exception as e:
                    ok=False; ERRS[0]+=1
                    if ERRS[0]<=5 or ERRS[0]%100==0: print(f"[EVAL-ERR #{ERRS[0]}] oracle {uuid}: {type(e).__name__}: {e}",flush=True)
                rows.append([args.out_root,"oracle","NA",uuid,q["bucket"],q["task_type"],ok,"NA"])
        # ---- oracle under a control (shuffle / mismatch): same frames, via the token path ----
        if os.path.isdir(vc_src) and not args.no_oracle and args.ctrl!="none":
            try:
                emb=ctrl_rows(frames_to_tokens(vc_src),uuid); nf=emb.shape[0]
                for q in qs:
                    rows.append([args.out_root,"oracle"+sfx,"NA",uuid,q["bucket"],q["task_type"],ask_emb(emb,nf,q,256)==q["expected_letter"],"NA"])
            except Exception as e:
                ERRS[0]+=1; print(f"[EVAL-ERR #{ERRS[0]}] oracle{sfx} {uuid}: {type(e).__name__}: {e}",flush=True)
        # ---- cached-pixel-path control: decode once, vision tower once, cache, pool, LLM ----
        if args.pixel_cache_pool and args.ctrl=="none":
            srcs=[("oraclecache","oracle",vc,"NA")]+[("pixelcache",f"crf{c}",f"{vc}/hevc_crf{c}_recon",bm.get(("pixel",f"crf{c}",uuid),"NA")) for c in args.crfs]
            for iface,lbl,fd,bpp in srcs:
                if not os.path.isdir(fd): continue
                try: emb=frames_to_tokens(fd); nf=emb.shape[0]
                except Exception as e:
                    ERRS[0]+=1; print(f"[EVAL-ERR #{ERRS[0]}] {iface} {lbl} {uuid}: {type(e).__name__}: {e}",flush=True); continue
                for K in args.pixel_cache_pool:
                    for q in qs:
                        rows.append([args.out_root,iface,f"{lbl}_p{K}",uuid,q["bucket"],q["task_type"],ask_emb(emb,nf,q,K)==q["expected_letter"],bpp])
        # ---- VisionZip (QA-side token reduction, CVPR'25) on the SAME oracle frames ----
        # Same videos/questions/sampling as oracle -> matched pool; only the token
        # budget K differs, so it is directly comparable to ours-pooled (tab:qa).
        if os.path.isdir(vc) and args.visionzip_k:
            for K in args.visionzip_k:
                with visionzip_reduce(model, k=K):
                    for q in qs:
                        try: ok=_parse_letter(qa_from_raw_frames(model,tok,vc,q["question"],q["options"],args.sample_count))==q["expected_letter"]
                        except Exception as e:
                            ok=False; ERRS[0]+=1
                            if ERRS[0]<=5: print(f"[EVAL-ERR #{ERRS[0]}] visionzip k{K} {uuid}: {type(e).__name__}: {e}",flush=True)
                        rows.append([args.out_root,"visionzip",f"k{K}",uuid,q["bucket"],q["task_type"],ok,"NA"])
        # ---- ToMe (QA-side token merging, ICLR'23) on the SAME oracle frames ----
        if os.path.isdir(vc) and args.tome_k:
            for K in args.tome_k:
                with tome_merge(model, k=K):
                    for q in qs:
                        try: ok=_parse_letter(qa_from_raw_frames(model,tok,vc,q["question"],q["options"],args.sample_count))==q["expected_letter"]
                        except Exception as e:
                            ok=False; ERRS[0]+=1
                            if ERRS[0]<=5: print(f"[EVAL-ERR #{ERRS[0]}] tome k{K} {uuid}: {type(e).__name__}: {e}",flush=True)
                        rows.append([args.out_root,"tome",f"k{K}",uuid,q["bucket"],q["task_type"],ok,"NA"])
        # ---- FastV (QA-side LLM-layer token pruning, ECCV'24) on the SAME oracle frames ----
        if os.path.isdir(vc) and args.fastv_k:
            for K in args.fastv_k:
                with fastv_prune(model, k=K):
                    for q in qs:
                        try: ok=_parse_letter(qa_from_raw_frames(model,tok,vc,q["question"],q["options"],args.sample_count))==q["expected_letter"]
                        except Exception as e:
                            ok=False; ERRS[0]+=1
                            if ERRS[0]<=5: print(f"[EVAL-ERR #{ERRS[0]}] fastv k{K} {uuid}: {type(e).__name__}: {e}",flush=True)
                        rows.append([args.out_root,"fastv",f"k{K}",uuid,q["bucket"],q["task_type"],ok,"NA"])
        # ---- VVC recon frames ----
        for qp in args.vvc_qps:
            rc=f"{vc}/vvc_qp{qp}_recon"
            if not os.path.isdir(rc): continue
            for qq in qs:
                try: ok=_parse_letter(qa_from_raw_frames(model,tok,rc,qq["question"],qq["options"],args.sample_count))==qq["expected_letter"]
                except Exception: ok=False
                rows.append([args.out_root,"vvc",f"qp{qp}",uuid,qq["bucket"],qq["task_type"],ok,bm.get(("vvc",f"vvc_qp{qp}",uuid),"NA")])
        # ---- DCVC-RT (learned video codec) recon frames ----
        for qp in args.dcvc_qps:
            rc=f"{vc}/dcvc_q{qp}_recon"
            if not os.path.isdir(rc): continue
            for qq in qs:
                try: ok=_parse_letter(qa_from_raw_frames(model,tok,rc,qq["question"],qq["options"],args.sample_count))==qq["expected_letter"]
                except Exception: ok=False
                rows.append([args.out_root,"dcvc",f"q{qp}",uuid,qq["bucket"],qq["task_type"],ok,bm.get(("dcvc",f"dcvc_q{qp}",uuid),"NA")])
        # ---- SMC++ / UG-ICM (new 2025-26 VCM baselines) recon frames ----
        # per-call answer log + fail-fast tripwire (post-mortem of the 2026-07-12 silent
        # all-False poisoning: exceptions were swallowed / answers unlogged)
        def _eval_new(iface, ratelbl, rc, bppkey):
            for qq in qs:
                letter=None
                try:
                    letter=_parse_letter(qa_from_raw_frames(model,tok,rc,qq["question"],qq["options"],args.sample_count))
                except Exception as e:
                    ERRS[0]+=1
                    if ERRS[0]<=5 or ERRS[0]%100==0: print(f"[EVAL-ERR #{ERRS[0]}] {iface} {uuid} {ratelbl}: {type(e).__name__}: {e}",flush=True)
                ok=(letter==qq["expected_letter"])
                TSTAT[0]+=int(ok); TSTAT[1]+=1
                print(f"[ans] {iface} {ratelbl} {uuid} {qq['bucket']}: {letter} vs {qq['expected_letter']}",flush=True)
                rows.append([args.out_root,iface,ratelbl,uuid,qq["bucket"],qq["task_type"],ok,bm.get((iface,bppkey,uuid),"NA")])
        for c in args.smcpp_crfs:
            rc=f"{vc}/smcpp_crf{c}_recon"
            if os.path.isdir(rc): _eval_new("smcpp",f"crf{c}",rc,f"smcpp_crf{c}")
        for q in args.ugicm_qs:
            rc=f"{vc}/ugicm_q{q}_recon"
            if os.path.isdir(rc): _eval_new("ugicm",f"q{q}",rc,f"ugicm_q{q}")
        for q in args.vcmrs_qps:
            rc=f"{vc}/vcmrs_qp{q}_recon"
            if os.path.isdir(rc): _eval_new("vcmrs",f"qp{q}",rc,f"vcmrs_qp{q}")
        if TSTAT[1]>150 and TSTAT[0]/TSTAT[1]<0.05:
            print(f"RUN SUSPECT: true-rate {TSTAT[0]}/{TSTAT[1]} below 5% — aborting to avoid wasting hours",flush=True)
            sys.exit(3)
        # ---- learned-codec recon frames ----
        for q in args.learned_qs:
            rc=f"{vc}/learned_q{q}_recon"
            if not os.path.isdir(rc): continue
            for qq in qs:
                try: ok=_parse_letter(qa_from_raw_frames(model,tok,rc,qq["question"],qq["options"],args.sample_count))==qq["expected_letter"]
                except Exception: ok=False
                rows.append([args.out_root,"learned",f"q{q}",uuid,qq["bucket"],qq["task_type"],ok,bm.get(("learned",f"learned_q{q}",uuid),"NA")])
        # ---- HEVC recon frames ----
        for crf in args.crfs:
            rc=f"{vc}/hevc_crf{crf}_recon"
            if not os.path.isdir(rc): continue
            for q in qs:
                try: ok=_parse_letter(qa_from_raw_frames(model,tok,rc,q["question"],q["options"],args.sample_count))==q["expected_letter"]
                except Exception as e:
                    ok=False; ERRS[0]+=1
                    if ERRS[0]<=5 or ERRS[0]%100==0: print(f"[EVAL-ERR #{ERRS[0]}] pixel crf{crf} {uuid}: {type(e).__name__}: {e}",flush=True)
                rows.append([args.out_root,"pixel",f"crf{crf}",uuid,q["bucket"],q["task_type"],ok,bm.get(("pixel",f"crf{crf}",uuid),"NA")])
        print(f"[{vi+1}/{len(vids)}] {uuid} done ({len(qs)}q)",flush=True)
    with open(args.out,"w",newline="") as f:
        w=csv.writer(f); w.writerow(["out_root","interface","rate","uuid","bucket","task_type","correct","bpp"]); w.writerows(rows)
    print(f"\n{len(rows)} rows -> {args.out}")
    print(f"swallowed eval exceptions: {ERRS[0]}"+(" ⚠️ RUN SUSPECT" if ERRS[0]>len(rows)*0.01 else ""))

if __name__=="__main__":
    main()
