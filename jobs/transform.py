"""Tag raw signals (from RSS/EDGAR) to layers + tickers via heuristic match.

Inputs: list[Signal]-shaped dicts where layer_ids/tickers are empty.
Output: same dicts with layer_ids and tickers populated.

Algorithm: lowercase headline+quote, match against per-layer keyword lists and
ticker tokens (with word boundaries). Layer tags ranked by keyword density;
keep up to 2 layers.
"""
from __future__ import annotations

import re
from collections import Counter
from typing import Any


# Per-layer keyword lists. Order matters only for tie-breaking by list position.
LAYER_KEYWORDS: dict[str, list[str]] = {
    "hbm": ["hbm", "hbm3e", "hbm4", "high-bandwidth memory", "high bandwidth memory", "ddr5", "dram"],
    "foundry": ["tsmc", "samsung foundry", "intel foundry", "n2 process", "n3 process", "2nm", "3nm", "1.4nm", "wafer fab"],
    "packaging": ["cowos", "cowop", "copos", "advanced packaging", "soic", "interposer", "fan-out", "fopl", "chiplet", "emib", "foveros"],
    "wfe": ["asml", "applied materials", "lam research", "kla", "tokyo electron", "euv", "high-na", "wfe", "wafer fab equipment", "lithography"],
    "gpu": ["blackwell", "rubin", "gb200", "gb300", "h100", "h200", "mi300", "mi350", "mi400", "tpu", "trainium", "maia", "mtia", "asic", "accelerator"],
    "networking": ["tomahawk", "jericho", "switch silicon", "connectx", "spectrum-x", "infiniband", "ultra ethernet", "dpu", "smartnic"],
    "optics": ["transceiver", "1.6t", "800g", "200g/lane", "eml", "indium phosphide", "inp laser", "optical module", "lumentum", "coherent", "fabrinet", "innolight", "eoptolink", "co-packaged optics", "cpo", "silicon photonics"],
    "switches": ["arista", "cisco", "juniper", "white-box", "white box", "celestica", "accton", "data center switch"],
    "power": ["transformer", "switchgear", "genset", "gas turbine", "substation", "grid capacity", "data center power", "stargate", "vernova", "eaton", "generac", "cummins", "nuclear", "smr", "small modular reactor", "uranium", "haleu", "advanced reactor", "three mile island", "constellation energy", "oklo", "centrus"],
    "cooling": ["liquid cooling", "direct-to-chip", "immersion cooling", "cdu", "cold plate", "rear-door heat exchanger", "vertiv", "modine", "nvent"],
    "hyperscalers": ["hyperscaler", "capex", "data center investment", "azure", "google cloud", "aws", "microsoft cloud"],
    "neoclouds": ["coreweave", "nebius", "neocloud", "lambda labs", "crusoe"],
    "software": ["vllm", "tensorrt", "sglang", "agentforce", "now assist", "cortex ai", "aip", "model serving", "inference engine"],
    "eda": ["cadence", "synopsys", "siemens eda", "eda software", "chip design tool"],
    "substrates": ["abf substrate", "fc-bga", "ic substrate", "ibiden", "unimicron", "shinko electric", "at&s"],
}

# Build a master keyword → layer_id map (longest first to prefer specific matches).
_KEYWORD_INDEX: list[tuple[str, str]] = sorted(
    [(kw, layer) for layer, kws in LAYER_KEYWORDS.items() for kw in kws],
    key=lambda x: -len(x[0]),
)


# Architectural-risk keywords — algorithmic shifts that could collapse FLOPs/token
# and break the inference-capex thesis. Three classes:
#   (1) non-attention architectures (SSMs, RWKV, RetNet, Hyena, diffusion LMs)
#   (2) attention-cost reduction (MoE, linear/grouped/multi-query, paged, sparsity)
#   (3) inference-shape changes (speculative decoding, prefill/decode disagg,
#       KV-cache offload, distillation, quantization, edge/on-device inference)
# Word-isolation rules: short tokens are space-padded; ambiguous tokens
# ("compressed"→margin compression, "agentic"→product marketing) are excluded.
ARCH_RISK_KEYWORDS: list[str] = [
    # (1) Non-attention / sub-quadratic frontier architectures
    "mamba",
    "state space model",
    "state-space model",
    "rwkv",
    "retnet",
    "hyena",
    "jamba",
    "samba",
    "byte latent",
    "byte-latent",
    "diffusion language model",
    "diffusion llm",
    "dllm",
    "sub-quadratic",
    "subquadratic",
    "linear-time transformer",
    "recurrent gemma",
    "griffin",
    "mixture of recursions",
    "mixture-of-recursions",
    # (2) Attention-cost reduction
    "linear attention",
    "flash attention",
    "flashattention",
    "mixture of experts",
    "mixture-of-experts",
    " moe ",
    "moe routing",
    "fine-grained sparsity",
    "sparsity",
    "pruning",
    "tree attention",
    "ring attention",
    "grouped query attention",
    "grouped-query attention",
    " gqa ",
    "multi-query attention",
    "multi-query-attention",
    " mqa ",
    "paged attention",
    "pagedattention",
    # (3) Inference-shape changes
    "speculative decoding",
    "speculative streaming",
    "self-speculative",
    "draft model",
    "medusa",
    "lookahead decoding",
    "kv cache",
    "kv-cache",
    "kvcache",
    "kv cache offload",
    "kvcache offload",
    "disaggregated prefill",
    "prefill-decode",
    "prefill/decode",
    "distillation",
    "distilled model",
    "quantization",
    "bitnet",
    "1-bit llm",
    "1-bit model",
    "ternary llm",
    "test-time compute",
    "test-time scaling",
    "inference-time scaling",
    "reasoning effort",
    "small language model",
    " slm ",
    " slms ",
    "on-device inference",
    "edge inference",
]


def _norm(text: str) -> str:
    return re.sub(r"\s+", " ", (text or "").lower())


def _ticker_set(players: list[dict]) -> dict[str, dict]:
    """Build {alias_lower: player_dict}.

    Aliases are limited to ticker symbols (with and without exchange suffix)
    and distinctive multi-word company names. Single-word brand aliases are
    excluded to avoid false positives (e.g. "samsung 9100 SSD" mistagging HBM).
    """
    by_alias: dict[str, dict] = {}
    for p in players:
        by_alias[p["ticker"].lower()] = p
        sym = p["ticker"].split(".")[0].lower()
        by_alias.setdefault(sym, p)
        # Distinctive multi-word names only
        name = re.sub(
            r"\b(corporation|corp|inc|ltd|technologies|technology|company|co|group|holdings)\b\.?",
            "",
            p["name"].lower(),
        ).strip()
        # Require the cleaned name to have at least 2 tokens so we don't
        # tag generic brand mentions ("samsung", "intel", "amazon")
        if name and len(name.split()) >= 2:
            by_alias.setdefault(name, p)
    return by_alias


def _has_arch_risk(text: str) -> bool:
    """True if any architectural-risk keyword hits in the normalized text.

    Pads with spaces so short tokens like ' moe ' and ' gqa ' match word-isolated.
    """
    padded = f" {text} "
    return any(kw in padded for kw in ARCH_RISK_KEYWORDS)


def tag(signals: list[dict], players: list[dict]) -> list[dict]:
    """Mutate-and-return: fill layer_ids, tickers, and arch_risk on each signal."""
    aliases = _ticker_set(players)

    for sig in signals:
        text_for_arch = _norm(f"{sig.get('headline', '')} {sig.get('quote', '')}")
        sig["arch_risk"] = _has_arch_risk(text_for_arch)

        if sig.get("layer_ids") and sig.get("tickers"):
            continue  # already curated (arch_risk still set above)

        text = text_for_arch

        # Tickers: word-boundary match on each alias
        found_tickers: list[str] = []
        seen_tickers: set[str] = set()
        for alias, player in aliases.items():
            pat = r"\b" + re.escape(alias) + r"\b"
            if re.search(pat, text):
                t = player["ticker"]
                if t not in seen_tickers:
                    found_tickers.append(t)
                    seen_tickers.add(t)
        if not sig.get("tickers"):
            sig["tickers"] = found_tickers

        # Keyword score
        keyword_hits = 0
        layer_score: Counter[str] = Counter()
        for kw, layer in _KEYWORD_INDEX:
            if kw in text:
                layer_score[layer] += 3
                keyword_hits += 1

        # Filings and earnings transcripts are tagged purely by ticker — the
        # speaker is known, so the player's primary/secondary layers apply
        # regardless of whether the quoted text happens to mention a keyword.
        # RSS/news must clear a keyword OR full-company-name bar to stay
        # relevant (single-word brand mentions are too noisy).
        ticker_authoritative = (
            sig.get("source_type") in ("filing", "earnings") and sig.get("tickers")
        )
        has_strong_match = keyword_hits > 0 or any(
            len(a.split()) >= 2 for a in aliases if a in text
        )

        if not ticker_authoritative and not has_strong_match:
            sig["layer_ids"] = []
            continue

        # Layer credit from ticker primary/secondary layers
        for t in sig["tickers"]:
            p = next((pp for pp in players if pp["ticker"] == t), None)
            if p:
                layer_score[p["layer_id"]] += 2
                for sec in p.get("secondary_layers", []) or []:
                    layer_score[sec] += 1

        if not sig.get("layer_ids"):
            sig["layer_ids"] = [layer for layer, _ in layer_score.most_common(2) if layer_score[layer] > 0]

    return signals


def merge(curated: list[dict], discovered: list[dict]) -> list[dict]:
    """Merge curated (priority) with discovered (RSS/EDGAR) by id; sorted desc."""
    by_id: dict[str, dict] = {}
    for sig in discovered + curated:  # curated wins because written second
        by_id[sig["id"]] = sig
    merged = list(by_id.values())
    # `date` may be missing/None (e.g. a transcript whose date didn't parse) —
    # coerce to "" so the sort never raises TypeError comparing None to str.
    merged.sort(key=lambda s: s.get("date") or "", reverse=True)
    return merged
