"""What the campaign decodes, in which order, and where everything lives.

The plan is a flat list of jobs. A job is one model decoding one shard of one dataset under one
or more arms: decoding configurations that share a single pass of the audio encoder. Every job
carries a tier, and workers always take the lowest tier first. If the session ends early, every
cell of the design then has the same depth of coverage, instead of some cells being complete and
others empty.

Shards are consecutive slices of a dataset's fixed pseudo-random order (see prep_data.order_key),
so the first n utterances of any set are a random sample, and a model x set cell that reached
shard 2 holds exactly the same utterances for every model that reached it.
"""

from __future__ import annotations

import copy
import json
from pathlib import Path

# ---------------------------------------------------------------------------------------------
# datasets
# ---------------------------------------------------------------------------------------------

LS_REPO = "openslr/librispeech_asr"
ESB_REPO = "hf-audio/open-asr-leaderboard"

# kind: how prep_data builds it. n_max: cap after filtering (None = all).
SETS: dict[str, dict] = {
    # LibriSpeech. dev-* is only ever used to tune selection/ROVER parameters.
    "ls-dev-clean": dict(kind="hf_parquet", repo=LS_REPO, files=["all/validation.clean/0000.parquet"],
                         lang="en", role="dev", n_max=1000, domain="read audiobook"),
    "ls-dev-other": dict(kind="hf_parquet", repo=LS_REPO, files=["all/validation.other/0000.parquet"],
                         lang="en", role="dev", n_max=1000, domain="read audiobook, harder"),
    "ls-test-clean": dict(kind="hf_parquet", repo=LS_REPO, files=["all/test.clean/0000.parquet"],
                          lang="en", role="test", n_max=None, domain="read audiobook"),
    "ls-test-other": dict(kind="hf_parquet", repo=LS_REPO, files=["all/test.other/0000.parquet"],
                          lang="en", role="test", n_max=None, domain="read audiobook, harder"),
    # Open ASR Leaderboard test sets. Shards are spread over the file list because the files
    # may be sorted; `take` of `n_shards` are downloaded and sampled from.
    "ami": dict(kind="esb", config="ami", n_shards=15, take=4, lang="en", role="test",
                n_max=1600, domain="meetings, spontaneous"),
    "earnings22": dict(kind="esb", config="earnings22", n_shards=5, take=2, lang="en", role="test",
                       n_max=1600, domain="earnings calls, accented"),
    "voxpopuli": dict(kind="esb", config="voxpopuli", n_shards=4, take=2, lang="en", role="test",
                      n_max=1600, domain="parliament speeches"),
    "gigaspeech": dict(kind="esb", config="gigaspeech", n_shards=19, take=2, lang="en", role="test",
                       n_max=1600, domain="podcasts and YouTube"),
    "spgispeech": dict(kind="esb", config="spgispeech", n_shards=38, take=2, lang="en", role="test",
                       n_max=1600, domain="financial calls, formatted text"),
    "common_voice": dict(kind="esb", config="common_voice", n_shards=3, take=2, lang="en", role="test",
                         n_max=1600, domain="crowdsourced, many accents"),
    "fleurs-en": dict(kind="fleurs", code="en_us", lang="en", role="test", n_max=None,
                      domain="read Wikipedia sentences"),
    "slr83": dict(kind="slr83", subsets=["irish_english_male", "midlands_english_female",
                                         "northern_english_female", "scottish_english_female",
                                         "welsh_english_female"],
                  per_subset=320, lang="en", role="test", n_max=None, domain="UK and Irish accents"),
    # Controlled difficulty: the first n utterances of test-clean with added noise. The same
    # noise realisation is used at every SNR, so SNR is the only thing that changes.
    "ls-tc-babble10": dict(kind="noise", base="ls-test-clean", babble_from="ls-dev-other",
                           noise="babble", snr=10, n=600, lang="en", role="test", domain="babble 10 dB"),
    "ls-tc-babble5": dict(kind="noise", base="ls-test-clean", babble_from="ls-dev-other",
                          noise="babble", snr=5, n=600, lang="en", role="test", domain="babble 5 dB"),
    "ls-tc-babble0": dict(kind="noise", base="ls-test-clean", babble_from="ls-dev-other",
                          noise="babble", snr=0, n=600, lang="en", role="test", domain="babble 0 dB"),
    "ls-tc-white5": dict(kind="noise", base="ls-test-clean", babble_from="ls-dev-other",
                         noise="white", snr=5, n=600, lang="en", role="test", domain="white noise 5 dB"),
    # Multilingual, Drax only (Whisfusion and its tokenizer are English).
    "fleurs-de": dict(kind="fleurs", code="de_de", lang="de", role="test", n_max=800, domain="read, German"),
    "fleurs-fr": dict(kind="fleurs", code="fr_fr", lang="fr", role="test", n_max=800, domain="read, French"),
    "fleurs-es": dict(kind="fleurs", code="es_419", lang="es", role="test", n_max=800, domain="read, Spanish"),
    "fleurs-it": dict(kind="fleurs", code="it_it", lang="it", role="test", n_max=800, domain="read, Italian"),
    "fleurs-pt": dict(kind="fleurs", code="pt_br", lang="pt", role="test", n_max=800, domain="read, Portuguese"),
}

# order matters: prep_data builds them in this order, so early tiers can start sooner
PREP_ORDER = ["ls-dev-clean", "ls-dev-other", "ls-test-clean", "ls-test-other",
              "ls-tc-babble10", "ls-tc-babble5", "ls-tc-babble0", "ls-tc-white5",
              "fleurs-en", "ami", "earnings22", "voxpopuli", "common_voice", "gigaspeech",
              "spgispeech", "slr83", "fleurs-de", "fleurs-fr", "fleurs-es", "fleurs-it", "fleurs-pt"]

DEV_SETS = ["ls-dev-clean", "ls-dev-other"]
EN_EVAL = ["ls-test-clean", "ls-test-other", "ami", "earnings22", "voxpopuli", "gigaspeech",
           "spgispeech", "common_voice", "fleurs-en", "slr83",
           "ls-tc-babble10", "ls-tc-babble5", "ls-tc-babble0", "ls-tc-white5"]
MULTI_EVAL = ["fleurs-de", "fleurs-fr", "fleurs-es", "fleurs-it", "fleurs-pt"]
CONTROL_SETS = ["ls-dev-other", "ls-test-clean", "ls-test-other", "ami", "earnings22",
                "common_voice", "fleurs-en", "ls-tc-babble5"]

# utterances outside these bounds are dropped for every model, so all cells stay paired
MIN_DUR, MAX_DUR = 0.8, 28.0
MAX_REF_WORDS = 75          # Drax decodes into a fixed 128-token canvas

# ---------------------------------------------------------------------------------------------
# models
# ---------------------------------------------------------------------------------------------

MODELS: dict[str, dict] = {
    "whisfusion": dict(family="wf", paradigm="masked diffusion", langs=["en"],
                       encoder="whisper-small", params="170M decoder + 88M encoder"),
    "drax": dict(family="drax", hf="aiola/drax-v1", paradigm="discrete flow matching",
                 langs=["en", "de", "fr", "es", "it", "pt"], encoder="whisper-large-v3",
                 params="580M decoder + 635M encoder"),
    "whisper-small": dict(family="whisper", hf="openai/whisper-small", paradigm="autoregressive",
                          langs=["en"], encoder="whisper-small", params="244M"),
    "whisper-turbo": dict(family="whisper", hf="openai/whisper-large-v3-turbo",
                          paradigm="autoregressive", langs=["en"], encoder="whisper-large-v3",
                          params="809M"),
    "parakeet-ctc": dict(family="ctc", hf="nvidia/parakeet-ctc-1.1b", paradigm="CTC, one-step parallel",
                         langs=["en"], encoder="fastconformer", params="1.1B"),
}

DEFAULTS = {
    "mode": "full",
    "run_hours": 11.3,            # wall clock from start to the last output byte
    "tail_minutes": 30,           # reserved at the end for analysis and aggregation
    "shard_size": 200,
    "seed": 20260919,
    # Drax costs ~4x Whisfusion per candidate on a T4 (580M DiT, 16 steps, 51k vocab), so it gets
    # half the pool; the kscale jobs extend both ladders to 64 on one set
    "k_main": {"whisfusion": 32, "drax": 16},
    "k_scale": 64,
    "drax": {"T": 1.3, "steps": 16, "precision": "fp16", "ref_T": 0.1, "ref_K": 4},
    "drax_sweep_T": [0.1, 0.4, 0.7, 1.0, 1.3, 1.6, 2.0],
    "drax_sweep_K": 16,
    "drax_steps_sweep": [4, 8, 32],
    "whisper_sample": {"K": 16, "T": 0.6},
    "whisper_beams": 8,
    "ctc_sample": {"K": 32, "T": 1.0},
    "models": ["whisfusion", "drax", "whisper-small", "whisper-turbo", "parakeet-ctc"],
    "plan": "full",               # "round2" builds only what the first session missed
    "drax_low_T": 0.4,            # best realised temperature in the round-1 dev sweep
    "max_tier": 99,
    "analysis_workers": 2,
    # smoke-only knobs; ignored in full mode
    "smoke": {},
}


def load_config(path: str | None) -> dict:
    cfg = copy.deepcopy(DEFAULTS)
    if path:
        with open(path, encoding="utf-8") as f:
            user = json.load(f)
        for k, v in user.items():
            if isinstance(v, dict) and isinstance(cfg.get(k), dict):
                cfg[k].update(v)
            else:
                cfg[k] = v
    return cfg


def sets_for(cfg: dict) -> dict[str, dict]:
    """Dataset specs with any smoke-mode reductions applied."""
    sets = copy.deepcopy(SETS)
    sm = cfg.get("smoke") or {}
    if cfg["mode"] == "smoke":
        keep = sm.get("sets")
        if keep:
            sets = {k: v for k, v in sets.items() if k in keep or any(
                v2.get("base") == k or v2.get("babble_from") == k
                for k2, v2 in SETS.items() if k2 in keep)}
        n_cap = sm.get("n_max", 40)
        for name, s in sets.items():
            if s["kind"] == "esb":
                s["take"] = 1
            if s["kind"] == "slr83":
                s["subsets"] = s["subsets"][:1]
                s["per_subset"] = n_cap
            if s["kind"] == "noise":
                s["n"] = min(s["n"], n_cap)
            else:
                s["n_max"] = n_cap if s.get("n_max") is None else min(s["n_max"], n_cap)
    return sets


# ---------------------------------------------------------------------------------------------
# arms
# ---------------------------------------------------------------------------------------------

def arms_main(model: str, cfg: dict) -> list[dict]:
    fam = MODELS[model]["family"]
    if fam == "wf":
        return [dict(name="main", K=cfg["k_main"]["whisfusion"], steps=4,
                     schedule=[1.0, 0.9, 0.85, 0.8], seq_len=256)]
    if fam == "drax":
        d = cfg["drax"]
        return [dict(name="main", K=cfg["k_main"]["drax"], T=d["T"], steps=d["steps"]),
                dict(name="ref", K=d["ref_K"], T=d["ref_T"], steps=d["steps"])]
    if fam == "whisper":
        s = cfg["whisper_sample"]
        return [dict(name="greedy", mode="greedy"),
                dict(name="beam", mode="beam", beams=cfg["whisper_beams"]),
                dict(name="sample", mode="sample", K=s["K"], T=s["T"])]
    if fam == "ctc":
        s = cfg["ctc_sample"]
        return [dict(name="greedy", mode="greedy"), dict(name="sample", mode="sample", K=s["K"], T=s["T"])]
    raise ValueError(model)


def arms_drax_sweep(cfg: dict) -> list[dict]:
    d = cfg["drax"]
    return [dict(name=f"T{t:g}", K=cfg["drax_sweep_K"], T=t, steps=d["steps"])
            for t in cfg["drax_sweep_T"]]


def arms_drax_steps(cfg: dict) -> list[dict]:
    d = cfg["drax"]
    return [dict(name=f"steps{s}", K=cfg["drax_sweep_K"], T=d["T"], steps=s)
            for s in cfg["drax_steps_sweep"]] + [
            dict(name=f"steps{d['steps']}", K=cfg["drax_sweep_K"], T=d["T"], steps=d["steps"])]


def arms_kscale(model: str, cfg: dict) -> list[dict]:
    """One large pool, so the K ladder in the analysis extends to 64."""
    K = cfg.get("k_scale", 64)
    if MODELS[model]["family"] == "wf":
        return [dict(name=f"K{K}", K=K, steps=4, schedule=[1.0, 0.9, 0.85, 0.8], seq_len=256)]
    d = cfg["drax"]
    return [dict(name=f"K{K}", K=K, T=d["T"], steps=d["steps"])]


def arms_wf_ablation() -> list[dict]:
    base = dict(schedule=[1.0, 0.9, 0.85, 0.8], seq_len=256)
    return [dict(name="base16", K=16, steps=4, **base),
            dict(name="steps8", K=16, steps=8, **base),
            dict(name="fss_T1", K=16, steps=4, first_step_sampling=True, temperature=1.0, **base)]


# ---------------------------------------------------------------------------------------------
# plan
# ---------------------------------------------------------------------------------------------

def n_shards(set_name: str, n_utts: int, shard_size: int) -> int:
    return max(1, -(-n_utts // shard_size))


def expected_size(spec: dict) -> int:
    """Upper bound on a set's size before prep; the real count comes from its manifest."""
    if spec["kind"] == "noise":
        return spec["n"]
    if spec["kind"] == "slr83":
        return spec["per_subset"] * len(spec["subsets"])
    if spec.get("n_max"):
        return spec["n_max"]
    return {"ls-test-clean": 2620, "ls-test-other": 2939, "fleurs-en": 647}.get(spec.get("name", ""), 3000)


def build_plan(cfg: dict) -> list[dict]:
    """Every job, each with (tier, order). Lower is sooner."""
    sets = sets_for(cfg)
    for name, s in sets.items():
        s["name"] = name
    S = cfg["shard_size"]
    models = [m for m in cfg["models"] if m in MODELS]
    jobs: list[dict] = []

    def add(tier, model, set_name, shard, kind, arms, **extra):
        if set_name not in sets or model not in models:
            return
        lang = sets[set_name]["lang"]
        if lang not in MODELS[model]["langs"]:
            return
        jid = f"{model}__{set_name}__s{shard:02d}__{kind}"
        jobs.append(dict(id=jid, model=model, family=MODELS[model]["family"], set=set_name,
                         lang=lang, shard=shard, shard_size=S, kind=kind, arms=arms,
                         tier=tier, **extra))

    core = [m for m in ("drax", "whisfusion") if m in models]
    controls = [m for m in ("whisper-small", "whisper-turbo", "parakeet-ctc") if m in models]

    def max_shard(set_name):
        return n_shards(set_name, expected_size(sets[set_name]), S) if set_name in sets else 0

    # tier 0: dev, for tuning
    for sh in range(2):
        for s in DEV_SETS:
            for m in core:
                add(0, m, s, sh, "main", arms_main(m, cfg))
    # tiers 1, 2: the first two shards of every evaluation cell
    for tier, sh in [(1, 0), (2, 1)]:
        for s in EN_EVAL + MULTI_EVAL:
            for m in core:
                if sh < max_shard(s):
                    add(tier, m, s, sh, "main", arms_main(m, cfg))
    if "drax" in models:
        add(2, "drax", "ls-dev-other", 0, "sweepT", arms_drax_sweep(cfg))
    if "whisfusion" in models:
        add(2, "whisfusion", "ls-dev-other", 0, "ablation", arms_wf_ablation())
    # tier 3: controls on shard 0, K=64 scaling, and a third shard of every core cell
    for s in CONTROL_SETS:
        for m in controls:
            add(3, m, s, 0, "main", arms_main(m, cfg))
    for m in core:
        add(3, m, "ls-test-other", 0, "kscale", arms_kscale(m, cfg))
    for s in EN_EVAL + MULTI_EVAL:
        for m in core:
            if 2 < max_shard(s):
                add(3, m, s, 2, "main", arms_main(m, cfg))
    # tier 4: more ablations, controls shard 1, core shards 3-4
    if "drax" in models:
        add(4, "drax", "ami", 0, "sweepT", arms_drax_sweep(cfg))
        add(4, "drax", "ls-test-other", 0, "steps", arms_drax_steps(cfg))
    if "whisfusion" in models:
        add(4, "whisfusion", "ami", 0, "ablation", arms_wf_ablation())
    for s in CONTROL_SETS:
        for m in controls:
            if 1 < max_shard(s):
                add(4, m, s, 1, "main", arms_main(m, cfg))
    for sh in (3, 4):
        for s in EN_EVAL + MULTI_EVAL:
            for m in core:
                if sh < max_shard(s):
                    add(4, m, s, sh, "main", arms_main(m, cfg))
    # tier 5: everything else, round-robin over sets
    for sh in range(5, 20):
        for s in EN_EVAL + MULTI_EVAL:
            for m in core:
                if sh < max_shard(s):
                    add(5, m, s, sh, "main", arms_main(m, cfg))

    # smoke: one shard of everything, whatever the tier said
    if cfg["mode"] == "smoke":
        sm = cfg.get("smoke") or {}
        extra_sweep_shards = sm.get("drax_calibration_shards", 0)
        keep = []
        seen = set()
        for j in jobs:
            key = (j["model"], j["set"], j["kind"])
            if j["shard"] != 0 or key in seen:
                continue
            seen.add(key)
            keep.append(j)
        jobs = keep
        for sh in range(1, 1 + extra_sweep_shards):
            add(2, "drax", "ls-dev-other", sh, "sweepT", arms_drax_sweep(cfg))
        if sm.get("precision_check") and "drax" in models:
            add(1, "drax", "ls-dev-clean", 0, "prec-bf16", arms_main("drax", cfg), precision="bf16")

    jobs = [j for j in jobs if j["tier"] <= cfg["max_tier"]]
    # order: tier, then shard, then the listing order above (round-robin over sets and models)
    for i, j in enumerate(jobs):
        j["order"] = i
    jobs.sort(key=lambda j: (j["tier"], j["shard"], j["order"]))
    for i, j in enumerate(jobs):
        j["order"] = i
    return jobs


def build_plan_round2(cfg: dict) -> list[dict]:
    """Second session: what the first one could not reach.

    - the autoregressive and CTC controls, which never got a GPU turn in round 1;
    - Drax at the temperature its own dev sweep liked best (T=0.4), so composition can be
      reported at Drax's best operating point and not only at the diverse T=1.3;
    - the Whisfusion K=64 scaling job.

    Shards are the same utterances as round 1 (the ordering is a hash of the id), so everything
    stays paired with the data already collected.
    """
    sets = sets_for(cfg)
    for name, s in sets.items():
        s["name"] = name
    S = cfg["shard_size"]
    models = [m for m in cfg["models"] if m in MODELS]
    jobs: list[dict] = []

    def add(tier, model, set_name, shard, kind, arms):
        if set_name not in sets or model not in models:
            return
        if sets[set_name]["lang"] not in MODELS[model]["langs"]:
            return
        jobs.append(dict(id=f"{model}__{set_name}__s{shard:02d}__{kind}", model=model,
                         family=MODELS[model]["family"], set=set_name, lang=sets[set_name]["lang"],
                         shard=shard, shard_size=S, kind=kind, arms=arms, tier=tier))

    controls = [m for m in ("whisper-small", "whisper-turbo", "parakeet-ctc") if m in models]
    low = [dict(name="lowT", K=cfg["k_main"]["drax"], T=cfg.get("drax_low_T", 0.4),
                steps=cfg["drax"]["steps"])]

    for s in CONTROL_SETS:                                   # tier 0: the missing controls
        for m in controls:
            add(0, m, s, 0, "main", arms_main(m, cfg))
    for s in EN_EVAL + MULTI_EVAL:                           # tier 1: Drax at its best temperature
        add(1, "drax", s, 0, "lowT", low)
    add(1, "whisfusion", "ls-test-other", 0, "kscale", arms_kscale("whisfusion", cfg))
    for s in CONTROL_SETS:                                   # tier 2+: more of the same
        for m in controls:
            add(2, m, s, 1, "main", arms_main(m, cfg))
    for s in EN_EVAL + MULTI_EVAL:
        add(3, "drax", s, 1, "lowT", low)
    for sh in (2, 3):
        for s in CONTROL_SETS:
            for m in controls:
                add(4, m, s, sh, "main", arms_main(m, cfg))

    jobs = [j for j in jobs if j["tier"] <= cfg["max_tier"]]
    for i, j in enumerate(jobs):
        j["order"] = i
    jobs.sort(key=lambda j: (j["tier"], j["shard"], j["order"]))
    for i, j in enumerate(jobs):
        j["order"] = i
    return jobs


def model_key(job: dict) -> str:
    """Worker identity: one process per (model, precision)."""
    return job["model"] + (f"@{job['precision']}" if job.get("precision") else "")


def write_json(path: Path, obj) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    with open(tmp, "w", encoding="utf-8") as f:
        json.dump(obj, f, indent=2, ensure_ascii=False)
    tmp.replace(path)


def build_plan_sweep(cfg: dict) -> list[dict]:
    """Third session: the temperature ladder on more than one dataset.

    Round 1 swept Drax's temperature on ls-dev-other only; the same job on ami sat at tier 4 and
    no worker reached it. One dataset cannot carry a claim about how composition scales with
    candidate disagreement. This plan runs nothing but the ladder, and puts two extra points
    between T=1.0 and T=1.6, where the whole transition happens and round 1 has no measurement.
    """
    sets = sets_for(cfg)
    for name, s in sets.items():
        s["name"] = name
    jobs: list[dict] = []
    for i, name in enumerate(cfg.get("sweep_sets", ["ami"])):
        if name not in sets or sets[name]["lang"] not in MODELS["drax"]["langs"]:
            continue
        jobs.append(dict(id=f"drax__{name}__s00__sweepT", model="drax",
                         family=MODELS["drax"]["family"], set=name, lang=sets[name]["lang"],
                         shard=0, shard_size=cfg["shard_size"], kind="sweepT",
                         arms=arms_drax_sweep(cfg), tier=0, order=i))
    return jobs


# ---------------------------------------------------------------------------------------------
# tree arms
# ---------------------------------------------------------------------------------------------

def arms_tree(cfg: dict) -> list[dict]:
    """Where to branch, by feature, at a mask budget where the choice can matter.

    Round 1 settled the shape question: sharing the early steps is 1.7x cheaper for nothing
    (tree-early) and 3x cheaper for about half a point (tree-deep), and none of it moved
    availability or recoverability. It also killed pure uncertainty targeting, which starved
    the confident positions of revision and cost 30 WER points.

    So this round asks the remaining question -- does it help to choose WHICH positions get
    re-predicted -- and asks it properly. Every targeted arm keeps part of the budget uniform
    (mask_mix), so exploration never stops, and mix = 0 is flat by construction. flat-sched
    is the same lowered schedule with no targeting, so the schedule is never the explanation.
    """
    K = cfg["k_main"]["whisfusion"]
    q = max(K // 4, 1)
    low = cfg.get("tree_low_schedule", [1.0, 0.5, 0.35, 0.25])
    mix = cfg.get("tree_mask_mix", 0.5)
    tree = [1, q, K, K]
    arms = [
        dict(name="flat", K=K, steps=4),
        dict(name="tree-early", K=K, steps=4, branch_schedule=tree),
        dict(name="flat-sched", K=K, steps=4, schedule=low),
    ]
    for mode in ("uncertain", "entropy", "margin", "unstable", "disagree"):
        arms.append(dict(name=f"aim-{mode}", K=K, steps=4, schedule=low,
                         mask_mode=mode, mask_mix=mix, branch_schedule=tree))
    # the mixture sweep, on the one feature round 1 already has a reading for
    for m in (0.25, 1.0):
        arms.append(dict(name=f"aim-uncertain-mix{m:g}", K=K, steps=4, schedule=low,
                         mask_mode="uncertain", mask_mix=m, branch_schedule=tree))
    return arms


def build_plan_tree(cfg: dict) -> list[dict]:
    """Nothing but the tree ablation on Whisfusion, on the sets named in tree_sets."""
    sets = sets_for(cfg)
    for name, s in sets.items():
        s["name"] = name
    S = cfg["shard_size"]
    jobs, order = [], 0
    names = [n for n in cfg.get("tree_sets", ["ls-test-other"]) if n in sets]

    def max_shard(name):
        return n_shards(name, expected_size(sets[name]), S)
    # Shard-major, so if the budget runs out every set still has the same depth.
    for shard in range(cfg.get("tree_shards", 1)):
        for name in names:
            if shard >= max_shard(name):
                continue
            jobs.append(dict(id=f"whisfusion__{name}__s{shard:02d}__tree", model="whisfusion",
                             family=MODELS["whisfusion"]["family"], set=name,
                             lang=sets[name]["lang"], shard=shard, shard_size=cfg["shard_size"],
                             kind="tree", arms=arms_tree(cfg), tier=0, order=order))
            order += 1
    return jobs
