"""Seed the dashboard's static content: layer definitions, player roster,
curated initial signals, and per-layer markdown copy.

Run once (or after you edit the curated data here):
    python -m jobs.seed

Add `--refresh-ciq-mapping` to (re)resolve `ticker → companyId` against
S&P Capital IQ — required when adding new players. Refresh.py merges live
data into the structures this file produces.
"""
from __future__ import annotations

import argparse
import json
import logging
import re
from datetime import datetime, timezone
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
DATA = ROOT / "data"
CONTENT = ROOT / "content" / "layers"

log = logging.getLogger(__name__)


# ---------------------------------------------------------------------------
# Layers — the 15 bottleneck-candidate layers of the inference stack.
# ---------------------------------------------------------------------------

LAYERS = [
    {
        "id": "hbm",
        "order": 1,
        "name": "HBM / DRAM Memory",
        "short_role": "On-package memory feeding GPUs and ASICs.",
        "status": "priced-in",
        "status_note": "Fully priced. Memory has run hardest of any layer; risk now skews to mix shift, China DRAM, capex over-build.",
        "bottleneck_summary": "HBM3E + HBM4 sold out across all three vendors through 2026; ~20% price hike for 2026; 3-year LTAs being signed.",
        "key_sources": [
            {"name": "TrendForce — SK Hynix 2026 outlook", "url": "https://www.trendforce.com/news/2026/01/05/news-sk-hynix-2026-outlook-hbm3e-remains-mainstream-hbm4-dual-strategy-amid-triple-market-headwinds/"},
            {"name": "Astute — HBM share", "url": "https://www.astutegroup.com/news/general/sk-hynix-holds-62-of-hbm-micron-overtakes-samsung-2026-battle-pivots-to-hbm4/"},
            {"name": "SK Hynix IR", "url": "https://www.skhynix.com/ir/eng/main.do"},
            {"name": "Micron IR", "url": "https://investors.micron.com/"},
        ],
    },
    {
        "id": "foundry",
        "order": 2,
        "name": "Leading-Edge Foundry",
        "short_role": "Where the GPU/ASIC die is etched at 3nm/2nm.",
        "status": "priced-in",
        "status_note": "TSMC priced for perfection. Intel is a binary turnaround bet, not a stack play.",
        "bottleneck_summary": "TSMC N2 sold out for 2026–2027; N3 fully booked for AI. Wafers tight but packaging is the binding constraint.",
        "key_sources": [
            {"name": "TSMC monthly revenue", "url": "https://investor.tsmc.com/english/monthly-revenue"},
            {"name": "TSMC Q1 2026 transcript (Investing.com)", "url": "https://www.investing.com/news/transcripts/earnings-call-transcript-tsmcs-q1-2026-shows-strong-growth-and-margin-gains-93CH-4617167"},
            {"name": "DigiTimes Asia", "url": "https://www.digitimes.com/"},
        ],
    },
    {
        "id": "packaging",
        "order": 3,
        "name": "Advanced Packaging (CoWoS / SoIC / CoPoS)",
        "short_role": "Stacks die + HBM on a silicon interposer. The single tightest node in the AI stack.",
        "status": "underappreciated",
        "status_note": "TSMC priced in, but ASE/Amkor get the spillover at much lower multiples — that's the de-bottlenecking trade.",
        "bottleneck_summary": "TSMC CoWoS oversubscribed through mid-2026; NVDA holds >60% of 2026 allocation, forcing Google to cut 2026 TPU build ~25%.",
        "key_sources": [
            {"name": "TrendForce — CoWoS fully booked", "url": "https://www.trendforce.com/news/2025/12/08/news-tsmcs-cowos-l-s-reportedly-fully-booked-osat-partners-step-up-with-ases-cowop-in-focus/"},
            {"name": "DigiTimes — CoWoS demand", "url": "https://www.digitimes.com/news/a20260410VL204/packaging-capacity-tsmc-nvidia-demand.html"},
            {"name": "TrendForce — CoPoS pilot 2026", "url": "https://www.trendforce.com/news/2026/04/13/news-tsmc-advances-panel-level-packaging-copos-pilot-line-reportedly-set-for-june-completion-2028-29-ramp-eyed/"},
            {"name": "Tom's Hardware — Intel EMIB", "url": "https://www.tomshardware.com/tech-industry/semiconductors/intel-gains-ground-in-ai-packaging-as-cowos-capacity-remains-stretched"},
        ],
    },
    {
        "id": "wfe",
        "order": 4,
        "name": "Wafer Fab Equipment / Lithography",
        "short_role": "The tools that build the chips. Multi-year backlog visibility.",
        "status": "mixed",
        "status_note": "ASML priced in. LRCX/AMAT under-modeled for HBM TSV ramp — that's the underappreciated leg.",
        "bottleneck_summary": "Not capacity-constrained — WFE delivers the bottleneck-relievers. ASML 2026 guide €36–40B; €38.8B backlog. High-NA at SK Hynix and Samsung 1.4nm.",
        "key_sources": [
            {"name": "ASML Q4 FY25 (Futurum)", "url": "https://futurumgroup.com/insights/asml-q4-fy-2025-earnings-record-orders-capacity-execution-in-focus/"},
            {"name": "ASML IR", "url": "https://www.asml.com/en/investors"},
            {"name": "SEMI WFE tracker", "url": "https://www.semi.org/en/products-services/market-data"},
        ],
    },
    {
        "id": "gpu",
        "order": 5,
        "name": "GPUs / AI Accelerators",
        "short_role": "The compute itself — merchant GPUs and custom hyperscaler ASICs.",
        "status": "priced-in",
        "status_note": "NVDA and AVGO largely priced in. MRVL is the cleanest under-modeled name on ASIC mix shift.",
        "bottleneck_summary": "TrendForce: custom ASIC sales +45% in 2026 vs +16% GPU shipments. Blackwell sold out through mid-2026; Rubin pull-in slipping to GB300.",
        "key_sources": [
            {"name": "Introl — Custom silicon inflection", "url": "https://introl.com/blog/custom-silicon-inflection-2026-hyperscaler-asics-nvidia-gpu"},
            {"name": "The Register — Rubin slip", "url": "https://www.theregister.com/2026/04/08/nvidia_supply_chain/"},
            {"name": "NVDA IR", "url": "https://investor.nvidia.com/"},
            {"name": "AVGO IR", "url": "https://investors.broadcom.com/"},
        ],
    },
    {
        "id": "networking",
        "order": 6,
        "name": "Networking Silicon",
        "short_role": "Switch ASICs and DSPs that make 100k-GPU clusters work as one machine.",
        "status": "mixed",
        "status_note": "AVGO priced in via Tomahawk dominance. MRVL DSPs underappreciated.",
        "bottleneck_summary": "Scale-out networking now ~10–15% of cluster spend. Ethernet won the back-end shift (Dell'Oro: ⅔ of Q3 2025 AI cluster switch sales).",
        "key_sources": [
            {"name": "Dell'Oro — Ethernet shift", "url": "https://www.delloro.com/news/ai-back-end-networks-continue-their-shift-to-ethernet-now-accounting-for-over-two-thirds-of-3q-2025-switch-sales-in-ai-clusters/"},
            {"name": "Cignal AI", "url": "https://cignal.ai/"},
        ],
    },
    {
        "id": "optics",
        "order": 7,
        "name": "Optical Components / EML Lasers",
        "short_role": "InP lasers, transceivers, DSPs — the 1.6T enabler for AI clusters.",
        "status": "underappreciated",
        "status_note": "Top idea cluster. The closest analog to where memory was in early 2024 — multi-year supply gap, NVDA bankrolling capacity, market hasn't fully repriced.",
        "bottleneck_summary": "EML lasers (InP) sold out through 2027; LITE capacity tripling only by mid-2027. McKinsey: 1.6T transceivers short 30–40% through 2029.",
        "key_sources": [
            {"name": "TrendForce — Nvidia EML lock-in", "url": "https://www.trendforce.com/presscenter/news/20251208-12823.html"},
            {"name": "Coherent Q2 FY26", "url": "https://futurumgroup.com/insights/coherent-q2-fy-2026-ai-datacenter-demand-lifts-revenue-and-margins/"},
            {"name": "Lumentum OFC 2026", "url": "https://investor.lumentum.com/financial-news-releases/news-details/2026/Lumentum-Demonstrates-Industry-Leading-Technologies-and-Products-for-Scale-Out-Scale-Up-and-Scale-Across-AI-Infrastructure-at-OFC-2026/default.aspx"},
            {"name": "InnoLight/Eoptolink share", "url": "https://ip-fiber.com/blogs/news/nvidia-orders-surge-innolight-and-eoptolink-dominate-60-of-800g-sfp-optical-modules-supply"},
        ],
    },
    {
        "id": "switches",
        "order": 8,
        "name": "Switches & Networking Systems",
        "short_role": "The boxes that wire up the cluster — branded systems and white-box ODMs.",
        "status": "mixed",
        "status_note": "ANET priced in. Celestica is the white-box sleeper — hyperscaler share gain not fully in the multiple.",
        "bottleneck_summary": "Arista guide ~+20% 2026; AI/campus growth ~60%. Cisco raised AI infra revenue to $3B. White-box ODMs (CLS, Accton) gaining share.",
        "key_sources": [
            {"name": "ANET IR", "url": "https://investors.arista.com/"},
            {"name": "CSCO IR", "url": "https://investor.cisco.com/"},
        ],
    },
    {
        "id": "power",
        "order": 9,
        "name": "Grid, Transformers, Gensets, Switchgear",
        "short_role": "The actual binding constraint for putting watts on the GPU.",
        "status": "underappreciated",
        "status_note": "GEV/ETN/VRT richly priced. Underappreciated: GNRC, HUBB, PWR — they get every grid-buildout dollar regardless of which hyperscaler wins.",
        "bottleneck_summary": ">50% of US 2026 data centers expected delayed/cancelled due to electrical gear. Gas turbine slots sold out through 2028; transformer lead times stretched to 5 years.",
        "key_sources": [
            {"name": "Energy News Beat — DC delays", "url": "https://energynewsbeat.co/ai/more-than-half-of-the-data-centers-may-be-delayed-due-to-lack-of-transformers-and-electrical-equipment-2/"},
            {"name": "Hunterbrook — Generac/Stargate", "url": "https://hntrbrk.com/generac-stargate/"},
            {"name": "GEV IR", "url": "https://www.gevernova.com/investors"},
        ],
    },
    {
        "id": "cooling",
        "order": 10,
        "name": "Liquid / Direct-to-Chip Cooling",
        "short_role": "Cold plates, CDUs, immersion — mandatory above ~700W TDP (Blackwell+).",
        "status": "underappreciated",
        "status_note": "VRT priced in. MOD and NVT still underappreciated for the DC mix-shift inside an industrials wrapper.",
        "bottleneck_summary": "Vertiv backlog ~$15B (+109% YoY), book-to-bill 2.9x. Modine DC sales +31% sequential, mgmt guides 50–70% growth.",
        "key_sources": [
            {"name": "Vertiv Q1 2026", "url": "https://investors.vertiv.com/news/news-details/2026/Vertiv-Reports-Strong-First-Quarter-with-Diluted-EPS-Growth-of-136-Adjusted-Diluted-EPS-Growth-of-83-Raises-Full-Year-Guidance/default.aspx"},
        ],
    },
    {
        "id": "hyperscalers",
        "order": 11,
        "name": "Hyperscaler Capex (Demand Side)",
        "short_role": "MSFT, GOOG, META, AMZN, ORCL — combined ~$725B 2026 capex (+77% YoY).",
        "status": "mixed",
        "status_note": "META and ORCL most stretched on capex/sales. GOOG arguably under-loved given full integrated stack (TPU + DeepMind + YouTube ad attach).",
        "bottleneck_summary": "Self-imposed FCF discipline. AMZN projected –$17B FCF 2026; META –90% FCF. Memory pricing cited as $25B of MSFT's 2026 increase.",
        "key_sources": [
            {"name": "Tom's Hardware — $725B capex", "url": "https://www.tomshardware.com/tech-industry/big-tech/big-techs-ai-spending-plans-reach-725-billion"},
            {"name": "Futurum — Q1 2026 capex breakdown", "url": "https://futurumgroup.com/insights/ai-capex-2026-the-690b-infrastructure-sprint/"},
            {"name": "Evertiq — $830B capex", "url": "https://evertiq.com/news/2026-05-06-ai-boom-pushes-hyperscaler-capex-towards-usd-830-billion-in-2026"},
        ],
    },
    {
        "id": "neoclouds",
        "order": 12,
        "name": "Neoclouds / GPU Clouds",
        "short_role": "Specialist AI compute providers — CoreWeave, Nebius, Lambda (private).",
        "status": "fairly-priced",
        "status_note": "High beta, not under-priced. Leveraged plays on NVDA shipment continuity. Skip if you already own NVDA.",
        "bottleneck_summary": "Bottleneck = GPU allocation + power siting. CRWV + NBIS combined Meta deals ~$48B.",
        "key_sources": [
            {"name": "Motley Fool — Meta $48B", "url": "https://www.fool.com/investing/2026/04/21/meta-is-spending-48-billion-with-coreweave-nebius/"},
        ],
    },
    {
        "id": "software",
        "order": 13,
        "name": "Inference Software / Platforms",
        "short_role": "Model labs (private), serving runtimes (vLLM, TRT-LLM), enterprise AI (CRM, NOW).",
        "status": "priced-in",
        "status_note": "Most crowded layer ex-NVDA. PLTR especially. Hard to find under-priced names here.",
        "bottleneck_summary": "Not a hardware bottleneck — software margins compress as inference becomes a commodity. Differentiation moves to data + workflow.",
        "key_sources": [
            {"name": "vLLM project", "url": "https://github.com/vllm-project/vllm"},
        ],
    },
    {
        "id": "eda",
        "order": 14,
        "name": "EDA",
        "short_role": "Chip design tools. Toll-booth model, no capacity bottleneck.",
        "status": "fairly-priced",
        "status_note": "Quality compounders, not where alpha lives in this cycle.",
        "bottleneck_summary": "AI-EDA segment growing ~24% CAGR. Cadence 2026 guide raised; Synopsys closing Ansys merger.",
        "key_sources": [
            {"name": "CDNS IR", "url": "https://www.cadence.com/en_US/home/company/investor-relations.html"},
            {"name": "SNPS IR", "url": "https://investor.synopsys.com/"},
        ],
    },
    {
        "id": "substrates",
        "order": 15,
        "name": "FC-BGA / ABF Substrates & PCBs",
        "short_role": "The high-density laminate that connects die to package and package to board.",
        "status": "underappreciated",
        "status_note": "Ibiden in particular is a multi-decade quality compounder still trading like a cyclical PCB stock. Unimicron similar. Western retail underweights both.",
        "bottleneck_summary": "ABF tight in 2023 (–9% supply gap), now expanding ~15% — re-tightens with each AI cycle. Intel/AMD/NVDA pre-funded ~50% of capex.",
        "key_sources": [
            {"name": "DigiTimes — ABF expansion", "url": "https://www.digitimes.com/news/a20251218PD207/abf-substrate-packaging-expansion-ai-gpu-capacity.html"},
        ],
    },
]


# ---------------------------------------------------------------------------
# Players — public tickers mapped to layers. Primary layer is the one most
# meaningful for thesis-tracking; secondary_layers captures cross-cutting names.
# ---------------------------------------------------------------------------

PLAYERS = [
    # HBM
    {"ticker": "000660.KS", "name": "SK Hynix", "exchange": "KRX", "country": "KR", "layer_id": "hbm", "secondary_layers": [], "role": "~62% HBM share Q2 2025; anchor supplier to NVDA/OpenAI; 2026 capacity pre-booked."},
    {"ticker": "005930.KS", "name": "Samsung Electronics", "exchange": "KRX", "country": "KR", "layer_id": "hbm", "secondary_layers": ["foundry"], "role": "NVDA-qualified on 12-Hi HBM3E; first to claim HBM4 mass production (Feb 2026)."},
    {"ticker": "MU", "name": "Micron Technology", "exchange": "NASDAQ", "country": "US", "layer_id": "hbm", "secondary_layers": [], "role": "15–20% HBM share; HBM sold out through CY26; power-per-watt leader."},

    # Foundry
    {"ticker": "TSM", "name": "Taiwan Semiconductor", "exchange": "NYSE", "country": "TW", "layer_id": "foundry", "secondary_layers": ["packaging"], "role": "Effective monopoly on N3/N2 for AI silicon; controls CoWoS-S/L packaging."},
    {"ticker": "INTC", "name": "Intel", "exchange": "NASDAQ", "country": "US", "layer_id": "foundry", "secondary_layers": ["packaging"], "role": "18A risk-on; foundry remains a show-me. EMIB/Foveros qualifying with hyperscalers."},
    {"ticker": "GFS", "name": "GlobalFoundries", "exchange": "NASDAQ", "country": "US", "layer_id": "foundry", "secondary_layers": [], "role": "Mature-node foundry; not on AI leading edge but structural beneficiary of trailing-node demand."},

    # Packaging (OSATs)
    {"ticker": "ASX", "name": "ASE Technology", "exchange": "NYSE", "country": "TW", "layer_id": "packaging", "secondary_layers": [], "role": "Top OSAT; ramping CoWoP and FOPLP for CoWoS spillover."},
    {"ticker": "AMKR", "name": "Amkor Technology", "exchange": "NASDAQ", "country": "US", "layer_id": "packaging", "secondary_layers": [], "role": "US packaging buildout (Arizona); secondary CoWoS-class capacity."},
    {"ticker": "2449.TW", "name": "King Yuan Electronics (KYEC)", "exchange": "TWSE", "country": "TW", "layer_id": "packaging", "secondary_layers": [], "role": "Testing bottleneck partner for AI packaging."},

    # WFE / Litho
    {"ticker": "ASML", "name": "ASML", "exchange": "NASDAQ", "country": "NL", "layer_id": "wfe", "secondary_layers": [], "role": "EUV monopoly; 2026 guide €36–40B; €38.8B backlog. High-NA at SKH and Samsung."},
    {"ticker": "AMAT", "name": "Applied Materials", "exchange": "NASDAQ", "country": "US", "layer_id": "wfe", "secondary_layers": [], "role": "Deposition/etch breadth; HBM TSV exposure."},
    {"ticker": "LRCX", "name": "Lam Research", "exchange": "NASDAQ", "country": "US", "layer_id": "wfe", "secondary_layers": [], "role": "Etch + memory tooling; direct HBM levered. Underappreciated for HBM TSV ramp."},
    {"ticker": "KLAC", "name": "KLA Corporation", "exchange": "NASDAQ", "country": "US", "layer_id": "wfe", "secondary_layers": [], "role": "Process control; irreplaceable at 2nm."},
    {"ticker": "8035.T", "name": "Tokyo Electron", "exchange": "TYO", "country": "JP", "layer_id": "wfe", "secondary_layers": [], "role": "Etch/coat; strong HBM exposure."},

    # GPUs / Accelerators
    {"ticker": "NVDA", "name": "NVIDIA", "exchange": "NASDAQ", "country": "US", "layer_id": "gpu", "secondary_layers": ["networking"], "role": "~85%+ of merchant AI training silicon. Blackwell sold out mid-2026."},
    {"ticker": "AMD", "name": "Advanced Micro Devices", "exchange": "NASDAQ", "country": "US", "layer_id": "gpu", "secondary_layers": [], "role": "MI300/MI350 ramping at OpenAI, Meta inference."},
    {"ticker": "AVGO", "name": "Broadcom", "exchange": "NASDAQ", "country": "US", "layer_id": "gpu", "secondary_layers": ["networking"], "role": "Custom-AI ASIC kingmaker (Google TPU, Meta MTIA); ~70% custom-AI share."},
    {"ticker": "MRVL", "name": "Marvell Technology", "exchange": "NASDAQ", "country": "US", "layer_id": "gpu", "secondary_layers": ["networking", "optics"], "role": "Trainium (AWS), Maia (MSFT), Meta DPU; underappreciated on ASIC mix shift."},
    {"ticker": "GOOGL", "name": "Alphabet (TPU)", "exchange": "NASDAQ", "country": "US", "layer_id": "hyperscalers", "secondary_layers": ["gpu"], "role": "TPU is the only fully integrated hyperscaler stack (TPU + DeepMind + YT ads)."},

    # Networking silicon (most cross from gpu) — keep ANET as switches primary

    # Optics / EML
    {"ticker": "LITE", "name": "Lumentum", "exchange": "NASDAQ", "country": "US", "layer_id": "optics", "secondary_layers": [], "role": "Only volume supplier of 200G/lane EMLs (the 1.6T enabler). Demand 25–30% above supply."},
    {"ticker": "COHR", "name": "Coherent", "exchange": "NYSE", "country": "US", "layer_id": "optics", "secondary_layers": [], "role": "InP lasers sold out through 2027; 4x book-to-bill in DC."},
    {"ticker": "FN", "name": "Fabrinet", "exchange": "NYSE", "country": "TH", "layer_id": "optics", "secondary_layers": [], "role": "Contract optical manufacturer; first $1B quarter; +36% YoY."},
    {"ticker": "300308.SZ", "name": "InnoLight Technology", "exchange": "SZSE", "country": "CN", "layer_id": "optics", "secondary_layers": [], "role": "~50%+ of NVDA's 800G transceiver modules."},
    {"ticker": "300502.SZ", "name": "Eoptolink", "exchange": "SZSE", "country": "CN", "layer_id": "optics", "secondary_layers": [], "role": "33% net margins, +179% revenue. High-quality optics business."},
    {"ticker": "MXL", "name": "MaxLinear", "exchange": "NASDAQ", "country": "US", "layer_id": "optics", "secondary_layers": [], "role": "Optical DSPs."},

    # Switches / Systems
    {"ticker": "ANET", "name": "Arista Networks", "exchange": "NYSE", "country": "US", "layer_id": "switches", "secondary_layers": ["networking"], "role": "Took DC switch crown from Cisco. 2026 guide ~+20%; AI/campus growth ~60%."},
    {"ticker": "CSCO", "name": "Cisco Systems", "exchange": "NASDAQ", "country": "US", "layer_id": "switches", "secondary_layers": ["networking"], "role": "Raised AI infra revenue to $3B; HPE/Juniper combined now competitive."},
    {"ticker": "HPE", "name": "Hewlett Packard Enterprise", "exchange": "NYSE", "country": "US", "layer_id": "switches", "secondary_layers": [], "role": "Post-Juniper, full networking suite."},
    {"ticker": "CLS", "name": "Celestica", "exchange": "NYSE", "country": "CA", "layer_id": "switches", "secondary_layers": [], "role": "White-box ODM gaining hyperscaler networking share. Sleeper."},
    {"ticker": "2345.TW", "name": "Accton Technology", "exchange": "TWSE", "country": "TW", "layer_id": "switches", "secondary_layers": [], "role": "Taiwan white-box ODM; hyperscaler switch supplier."},

    # Power
    {"ticker": "GEV", "name": "GE Vernova", "exchange": "NYSE", "country": "US", "layer_id": "power", "secondary_layers": [], "role": "Transformers + gas turbines; backlog $163B; 2026 DC orders $2.4B already exceed all 2025."},
    {"ticker": "ETN", "name": "Eaton", "exchange": "NYSE", "country": "US", "layer_id": "power", "secondary_layers": [], "role": "Switchgear, distribution, PDUs. DC orders +30%+ for 4 quarters."},
    {"ticker": "VRT", "name": "Vertiv", "exchange": "NYSE", "country": "US", "layer_id": "cooling", "secondary_layers": ["power"], "role": "Power + cooling integrated; $15B backlog (+109% YoY); NVDA partner."},
    {"ticker": "GNRC", "name": "Generac", "exchange": "NYSE", "country": "US", "layer_id": "power", "secondary_layers": [], "role": "Gensets, 50–60 wk lead time vs. 70–107 wk for Cat/Cummins. Stargate slot."},
    {"ticker": "CMI", "name": "Cummins", "exchange": "NYSE", "country": "US", "layer_id": "power", "secondary_layers": [], "role": "High-HP gensets; 18-mo lead times even after $150M Fridley expansion."},
    {"ticker": "HUBB", "name": "Hubbell", "exchange": "NYSE", "country": "US", "layer_id": "power", "secondary_layers": [], "role": "Utility T&D — every grid-buildout dollar."},
    {"ticker": "PWR", "name": "Quanta Services", "exchange": "NYSE", "country": "US", "layer_id": "power", "secondary_layers": [], "role": "Substation/transmission EPC."},
    {"ticker": "CAT", "name": "Caterpillar", "exchange": "NYSE", "country": "US", "layer_id": "power", "secondary_layers": [], "role": "Gensets, prime power."},
    {"ticker": "CEG", "name": "Constellation Energy", "exchange": "NASDAQ", "country": "US", "layer_id": "power", "secondary_layers": [], "role": "Largest US nuclear operator; MSFT PPA to restart Three Mile Island Unit 1 for AI baseload."},
    {"ticker": "OKLO", "name": "Oklo Inc.", "exchange": "NYSE", "country": "US", "layer_id": "power", "secondary_layers": [], "role": "SMR developer (Aurora powerhouse); Sam Altman-backed; pure-play on AI-driven SMR demand."},
    {"ticker": "LEU", "name": "Centrus Energy", "exchange": "NYSE-AM", "country": "US", "layer_id": "power", "secondary_layers": [], "role": "Sole US producer of HALEU; fuel bottleneck for advanced reactors and SMRs."},

    # Cooling (VRT primary in cooling)
    {"ticker": "NVT", "name": "nVent Electric", "exchange": "NYSE", "country": "US", "layer_id": "cooling", "secondary_layers": ["power"], "role": "~30% DC exposure, growing NVDA depth."},
    {"ticker": "MOD", "name": "Modine Manufacturing", "exchange": "NYSE", "country": "US", "layer_id": "cooling", "secondary_layers": [], "role": "DC sales +31% sequential Q3 FY26; mgmt guides 50–70% DC growth."},
    {"ticker": "SU.PA", "name": "Schneider Electric", "exchange": "EPA", "country": "FR", "layer_id": "cooling", "secondary_layers": ["power"], "role": "Broadest DC power+cooling portfolio."},
    {"ticker": "3017.TW", "name": "Asia Vital Components (AVC)", "exchange": "TWSE", "country": "TW", "layer_id": "cooling", "secondary_layers": [], "role": "Taiwan thermal leader; liquid cooling + vapor chambers for AI servers; key supplier into NVDA OEMs."},
    {"ticker": "3653.TW", "name": "Jentech Precision Industrial", "exchange": "TWSE", "country": "TW", "layer_id": "cooling", "secondary_layers": [], "role": "Heat-spreader / vapor-chamber specialist for AI-server thermal solutions."},
    {"ticker": "3324.TWO", "name": "Auras Technology", "exchange": "TPEx", "country": "TW", "layer_id": "cooling", "secondary_layers": [], "role": "Liquid cooling / cold-plate supplier on TPEx; pure-play AI thermal beneficiary."},

    # Hyperscalers
    {"ticker": "MSFT", "name": "Microsoft", "exchange": "NASDAQ", "country": "US", "layer_id": "hyperscalers", "secondary_layers": [], "role": "CY26 capex $190B; CFO attributed $25B of increase to memory/component costs."},
    {"ticker": "META", "name": "Meta Platforms", "exchange": "NASDAQ", "country": "US", "layer_id": "hyperscalers", "secondary_layers": [], "role": "FY26 raised $10B to >$145B; –90% FCF projected."},
    {"ticker": "AMZN", "name": "Amazon", "exchange": "NASDAQ", "country": "US", "layer_id": "hyperscalers", "secondary_layers": [], "role": "~$200B FY26 capex; –$17B projected FCF."},
    {"ticker": "ORCL", "name": "Oracle", "exchange": "NYSE", "country": "US", "layer_id": "hyperscalers", "secondary_layers": [], "role": "~$50B capex; capex/sales ~86% — most stretched."},

    # Neoclouds
    {"ticker": "CRWV", "name": "CoreWeave", "exchange": "NASDAQ", "country": "US", "layer_id": "neoclouds", "secondary_layers": [], "role": "~$59B mkt cap, 2026E rev ~$12.5B (+143%); 2027 ~$23.5B."},
    {"ticker": "NBIS", "name": "Nebius Group", "exchange": "NASDAQ", "country": "NL", "layer_id": "neoclouds", "secondary_layers": [], "role": "2026E +206% rev; EV ~½ of CRWV."},

    # Software
    {"ticker": "CRM", "name": "Salesforce", "exchange": "NYSE", "country": "US", "layer_id": "software", "secondary_layers": [], "role": "Agentforce — enterprise AI agents."},
    {"ticker": "NOW", "name": "ServiceNow", "exchange": "NYSE", "country": "US", "layer_id": "software", "secondary_layers": [], "role": "Now Assist; workflow AI."},
    {"ticker": "SNOW", "name": "Snowflake", "exchange": "NYSE", "country": "US", "layer_id": "software", "secondary_layers": [], "role": "Cortex AI on data warehouse."},
    {"ticker": "PLTR", "name": "Palantir", "exchange": "NASDAQ", "country": "US", "layer_id": "software", "secondary_layers": [], "role": "AIP; richly priced."},

    # EDA
    {"ticker": "CDNS", "name": "Cadence Design Systems", "exchange": "NASDAQ", "country": "US", "layer_id": "eda", "secondary_layers": [], "role": "2026 guide raised $6.13–6.23B; TSMC alliance."},
    {"ticker": "SNPS", "name": "Synopsys", "exchange": "NASDAQ", "country": "US", "layer_id": "eda", "secondary_layers": [], "role": "~31% global EDA share; merging closes Ansys."},
    {"ticker": "SIEGY", "name": "Siemens (EDA)", "exchange": "OTC", "country": "DE", "layer_id": "eda", "secondary_layers": [], "role": "13% EDA share."},

    # Substrates
    {"ticker": "4062.T", "name": "Ibiden", "exchange": "TYO", "country": "JP", "layer_id": "substrates", "secondary_layers": [], "role": "Premium FC-BGA; NVDA supplier. Quality compounder mispriced as cyclical."},
    {"ticker": "3037.TW", "name": "Unimicron Technology", "exchange": "TWSE", "country": "TW", "layer_id": "substrates", "secondary_layers": [], "role": "Top 5 FC-BGA; expanding."},
    {"ticker": "6967.T", "name": "Shinko Electric", "exchange": "TYO", "country": "JP", "layer_id": "substrates", "secondary_layers": [], "role": "Premium high-end (being taken private by JIC consortium)."},
    {"ticker": "ATS.VI", "name": "AT&S", "exchange": "WBO", "country": "AT", "layer_id": "substrates", "secondary_layers": [], "role": "Austrian; Intel-aligned."},
    {"ticker": "8046.TW", "name": "Nan Ya PCB", "exchange": "TWSE", "country": "TW", "layer_id": "substrates", "secondary_layers": [], "role": "Capacity expansion."},
]


# ---------------------------------------------------------------------------
# Curated initial signals — concrete recent (Q1–Q2 2026) bottleneck datapoints.
# refresh.py adds new RSS-discovered entries on top of these.
# ---------------------------------------------------------------------------

SIGNALS = [
    {
        "id": "skhynix-q1-2026",
        "date": "2026-04-23",
        "source": "SK Hynix",
        "source_type": "earnings",
        "headline": "SK Hynix Q1 2026: HBM4 demand exceeds capacity for next 3 years",
        "quote": "HBM4 demand exceeds capacity for the next three years; full 2026 sold out, 3-year DDR5 LTA signed with Microsoft. Op margin 72%, revenue +198% YoY.",
        "url": "https://news.skhynix.com/q1-2026-business-results/",
        "layer_ids": ["hbm"],
        "tickers": ["000660.KS"],
    },
    {
        "id": "micron-fq1-2026",
        "date": "2025-12-17",
        "source": "Micron",
        "source_type": "earnings",
        "headline": "Micron F-Q1'26: HBM4 ramps Q2 2026; FY26 capex raised to $20B",
        "quote": "Sanjay Mehrotra: HBM4 ramps calendar Q2 2026 at >11 Gbps; entire 2026 HBM supply (HBM3E + HBM4) priced and booked. We can meet only ~50–66% of demand from core customers.",
        "url": "https://investors.micron.com/static-files/088991c5-a249-4f66-a0a6-258d9b66f3f9",
        "layer_ids": ["hbm"],
        "tickers": ["MU"],
    },
    {
        "id": "skhynix-hbm4-shift",
        "date": "2026-04-10",
        "source": "TrendForce",
        "source_type": "industry",
        "headline": "SK Hynix shifting 20–30% of HBM4 capacity back to HBM3E",
        "quote": "SK Hynix is reallocating 20–30% of HBM4 capacity to HBM3E because Nvidia placed incremental HBM3E orders for Blackwell Ultra/GB300. Reads as Rubin pull-in slipping right.",
        "url": "https://www.trendforce.com/news/2026/01/05/news-sk-hynix-2026-outlook-hbm3e-remains-mainstream-hbm4-dual-strategy-amid-triple-market-headwinds/",
        "layer_ids": ["hbm", "gpu"],
        "tickers": ["000660.KS", "NVDA"],
    },
    {
        "id": "tsmc-q1-2026",
        "date": "2026-04-17",
        "source": "TSMC",
        "source_type": "earnings",
        "headline": "TSMC Q1 2026: capex guide $52–56B, 70–80% advanced nodes",
        "quote": "Capex guide $52–56B (vs ~$40B a year prior); 70–80% advanced nodes, 10–20% advanced packaging. N2 HVM confirmed H2 2026; Apple, Nvidia Rubin, AMD MI400 booked. N2 wafer pricing ~$30K vs ~$20K for N3.",
        "url": "https://www.investing.com/news/transcripts/earnings-call-transcript-tsmcs-q1-2026-shows-strong-growth-and-margin-gains-93CH-4617167",
        "layer_ids": ["foundry", "packaging"],
        "tickers": ["TSM"],
    },
    {
        "id": "cowos-fully-booked",
        "date": "2025-12-08",
        "source": "TrendForce",
        "source_type": "industry",
        "headline": "TSMC CoWoS-L/S fully booked through 2026; OSATs ramping",
        "quote": "CoWoS-L and CoWoS-S fully booked through 2026. Capacity scaling from ~35K wpm late-2024 to ~130K wpm by end-2026; NVIDIA holds >60% of slots. ASE's CoWoP and Amkor pulled in to absorb spillover.",
        "url": "https://www.trendforce.com/news/2025/12/08/news-tsmcs-cowos-l-s-reportedly-fully-booked-osat-partners-step-up-with-ases-cowop-in-focus/",
        "layer_ids": ["packaging"],
        "tickers": ["TSM", "ASX", "AMKR"],
    },
    {
        "id": "tsmc-copos-pilot",
        "date": "2026-04-13",
        "source": "TrendForce",
        "source_type": "industry",
        "headline": "TSMC advances panel-level packaging (CoPoS); pilot June 2026, ramp 2028–29",
        "quote": "TSMC pilot line for panel-level packaging (CoPoS) targets June 2026 completion, volume 2028–29. Long-dated capacity relief — does not solve the 2026 squeeze.",
        "url": "https://www.trendforce.com/news/2026/04/13/news-tsmc-advances-panel-level-packaging-copos-pilot-line-reportedly-set-for-june-completion-2028-29-ramp-eyed/",
        "layer_ids": ["packaging"],
        "tickers": ["TSM"],
    },
    {
        "id": "intel-emib-cowos",
        "date": "2026-02-15",
        "source": "Tom's Hardware",
        "source_type": "news",
        "headline": "Intel EMIB/Foveros qualifying with hyperscaler ASIC programs as CoWoS stays stretched",
        "quote": "Intel EMIB/Foveros qualifying with at least one hyperscaler ASIC program as CoWoS capacity remains the binding constraint.",
        "url": "https://www.tomshardware.com/tech-industry/semiconductors/intel-gains-ground-in-ai-packaging-as-cowos-capacity-remains-stretched",
        "layer_ids": ["packaging", "foundry"],
        "tickers": ["INTC"],
    },
    {
        "id": "nvda-eml-lockin",
        "date": "2026-03-15",
        "source": "TrendForce",
        "source_type": "industry",
        "headline": "NVIDIA invests $4B combined into Lumentum + Coherent to lock 200G EML supply",
        "quote": "Strategic investment ($2B into LITE at $695.31/sh, plus Coherent stake) to lock priority on 200G/lane EMLs for 1.6T transceivers. Confirms EML lasers as the textbook 2026 bottleneck.",
        "url": "https://www.trendforce.com/presscenter/news/20251208-12823.html",
        "layer_ids": ["optics"],
        "tickers": ["NVDA", "LITE", "COHR"],
    },
    {
        "id": "lumentum-q3-fy26",
        "date": "2026-02-04",
        "source": "Lumentum",
        "source_type": "earnings",
        "headline": "Lumentum Q3 FY26: revenue $808M (+90% YoY), record",
        "quote": "Record quarterly revenue $808M, +90% YoY. Sole-source on 200G EML lasers; capacity tripling only by mid-2027.",
        "url": "https://investor.lumentum.com/financial-news-releases/news-details/2026/Lumentum-Demonstrates-Industry-Leading-Technologies-and-Products-for-Scale-Out-Scale-Up-and-Scale-Across-AI-Infrastructure-at-OFC-2026/default.aspx",
        "layer_ids": ["optics"],
        "tickers": ["LITE"],
    },
    {
        "id": "coherent-q2-fy26",
        "date": "2026-02-05",
        "source": "Coherent",
        "source_type": "earnings",
        "headline": "Coherent Q2 FY26: record $1.81B revenue, 1.6T order book >$200M",
        "quote": "Record $1.81B; 1.6T order book >$200M; guides 1.6T GM above 800G. InP lasers sold out through 2027.",
        "url": "https://futurumgroup.com/insights/coherent-q2-fy-2026-ai-datacenter-demand-lifts-revenue-and-margins/",
        "layer_ids": ["optics"],
        "tickers": ["COHR"],
    },
    {
        "id": "mckinsey-1p6t-shortfall",
        "date": "2025-06-15",
        "source": "McKinsey",
        "source_type": "analyst",
        "headline": "McKinsey: 1.6T transceivers short 30–40% through 2029",
        "quote": "800G transceivers running 40–60% short of demand through 2027; 1.6T short 30–40% through 2029. Multi-year supply gap.",
        "url": "https://www.mckinsey.com/",
        "layer_ids": ["optics"],
        "tickers": ["LITE", "COHR", "FN"],
    },
    {
        "id": "rubin-slip",
        "date": "2026-04-08",
        "source": "The Register",
        "source_type": "news",
        "headline": "Rubin slipping right; GB300 picks up slack at +129% YoY",
        "quote": "TrendForce cut Rubin's 2026 share of Nvidia high-end shipments from 29% to 22% (HBM4 validation, ConnectX-9 NIC migration, higher TDP, L2A cooling). GB300 picks up slack at +129% YoY.",
        "url": "https://www.theregister.com/2026/04/08/nvidia_supply_chain/",
        "layer_ids": ["gpu"],
        "tickers": ["NVDA"],
    },
    {
        "id": "broadcom-q1-fy26",
        "date": "2026-03-06",
        "source": "Broadcom",
        "source_type": "earnings",
        "headline": "Broadcom Q1 FY26: AI revenue $5.1B (+77% YoY), 5 hyperscaler designs",
        "quote": "AI revenue $5.1B (+77% YoY), 3 hyperscaler customers shipping, 2 more in design. Custom-AI ASIC share trajectory toward ~60% by 2027.",
        "url": "https://investors.broadcom.com/",
        "layer_ids": ["gpu", "networking"],
        "tickers": ["AVGO"],
    },
    {
        "id": "vertiv-q1-2026",
        "date": "2026-04-30",
        "source": "Vertiv",
        "source_type": "earnings",
        "headline": "Vertiv Q1 2026: backlog $15B (+109% YoY), book-to-bill 2.9x",
        "quote": "Revenue $2.65B (+30% YoY), backlog ~$15B (+109% YoY), book-to-bill 2.9x, op margin 20.8%. Raised FY26 to $13.5–14B.",
        "url": "https://investors.vertiv.com/news/news-details/2026/Vertiv-Reports-Strong-First-Quarter-with-Diluted-EPS-Growth-of-136-Adjusted-Diluted-EPS-Growth-of-83-Raises-Full-Year-Guidance/default.aspx",
        "layer_ids": ["cooling", "power"],
        "tickers": ["VRT"],
    },
    {
        "id": "eaton-q1-2026",
        "date": "2026-05-01",
        "source": "Eaton",
        "source_type": "earnings",
        "headline": "Eaton Q1 2026: DC orders +30%+ for 4 consecutive quarters",
        "quote": "Data center orders +30%+ for 4 consecutive quarters; electrical Americas backlog at record.",
        "url": "https://www.eaton.com/us/en-us/company/investor-relations.html",
        "layer_ids": ["power"],
        "tickers": ["ETN"],
    },
    {
        "id": "gev-turbines-2028",
        "date": "2026-04-20",
        "source": "GE Vernova",
        "source_type": "earnings",
        "headline": "GE Vernova: gas turbine slots sold out through 2028",
        "quote": "Gas turbine slots sold out through 2028; transformers similar. Backlog $163B; 2026 DC orders $2.4B already exceed all of 2025.",
        "url": "https://www.gevernova.com/investors",
        "layer_ids": ["power"],
        "tickers": ["GEV"],
    },
    {
        "id": "msft-capex-memory",
        "date": "2026-04-29",
        "source": "Microsoft",
        "source_type": "earnings",
        "headline": "Microsoft CY26 capex $190B; $25B of increase from rising memory/component costs",
        "quote": "CFO Amy Hood attributed $25B of the capex increase to rising memory/component costs — direct read-through to HBM pricing.",
        "url": "https://www.microsoft.com/en-us/Investor",
        "layer_ids": ["hyperscalers", "hbm"],
        "tickers": ["MSFT", "MU", "000660.KS"],
    },
    {
        "id": "meta-capex-145b",
        "date": "2026-04-30",
        "source": "Meta",
        "source_type": "earnings",
        "headline": "Meta FY26 capex raised $10B to >$145B",
        "quote": "FY26 raised $10B to >$145B, citing memory pricing + power/land/labor. ~–90% FCF projected.",
        "url": "https://investor.fb.com/",
        "layer_ids": ["hyperscalers"],
        "tickers": ["META"],
    },
    {
        "id": "google-capex-q1",
        "date": "2026-04-24",
        "source": "Alphabet",
        "source_type": "earnings",
        "headline": "Alphabet Q1 capex $35.67B; FY26 $180–190B",
        "quote": "Q1 alone $35.67B; FY26 $180–190B; 2027 to significantly increase.",
        "url": "https://abc.xyz/investor/",
        "layer_ids": ["hyperscalers"],
        "tickers": ["GOOGL"],
    },
    {
        "id": "amazon-capex-200b",
        "date": "2026-05-01",
        "source": "Amazon",
        "source_type": "earnings",
        "headline": "Amazon ~$200B FY26 capex; –$17B FCF projected",
        "quote": "AWS-led capex ~$200B FY26. FCF projected at –$17B.",
        "url": "https://ir.aboutamazon.com/",
        "layer_ids": ["hyperscalers"],
        "tickers": ["AMZN"],
    },
    {
        "id": "dc-delays-electrical",
        "date": "2026-03-05",
        "source": "Energy News Beat",
        "source_type": "news",
        "headline": ">50% of US 2026 data centers expected delayed/cancelled — electrical gear shortage",
        "quote": "More than half of US 2026 data centers expected to be delayed or cancelled due to lack of transformers and electrical equipment. Lead times stretched from 24–30 months to 5 years.",
        "url": "https://energynewsbeat.co/ai/more-than-half-of-the-data-centers-may-be-delayed-due-to-lack-of-transformers-and-electrical-equipment-2/",
        "layer_ids": ["power"],
        "tickers": ["GEV", "ETN", "HUBB"],
    },
    {
        "id": "generac-stargate",
        "date": "2026-02-01",
        "source": "Hunterbrook",
        "source_type": "analyst",
        "headline": "Generac is the only gas-genset slot in the Stargate permitting docs",
        "quote": "Generac has the only gas-genset slot in Stargate permitting because Cat/Cummins lead times are 70–107 weeks vs Generac's 50–60.",
        "url": "https://hntrbrk.com/generac-stargate/",
        "layer_ids": ["power"],
        "tickers": ["GNRC"],
    },
    {
        "id": "asml-q4-fy25",
        "date": "2026-01-28",
        "source": "ASML",
        "source_type": "earnings",
        "headline": "ASML Q4 FY25: 2026 guide €36–40B, €38.8B backlog",
        "quote": "Record orders; 2026 guide €36–40B; €38.8B backlog. High-NA at SK Hynix and Samsung 1.4nm. TSMC delayed High-NA to 2029.",
        "url": "https://futurumgroup.com/insights/asml-q4-fy-2025-earnings-record-orders-capacity-execution-in-focus/",
        "layer_ids": ["wfe"],
        "tickers": ["ASML"],
    },
    {
        "id": "abf-substrate-expansion",
        "date": "2025-12-18",
        "source": "DigiTimes",
        "source_type": "industry",
        "headline": "ABF substrate expansion: ~15%, ~50% pre-funded by NVDA/AMD/Intel",
        "quote": "ABF substrate capacity expanding ~15% (vs –9% gap in 2023). Intel/AMD/NVDA pre-funded ~50% of expansion capex. Re-tightens with each AI cycle.",
        "url": "https://www.digitimes.com/news/a20251218PD207/abf-substrate-packaging-expansion-ai-gpu-capacity.html",
        "layer_ids": ["substrates"],
        "tickers": ["4062.T", "3037.TW"],
    },
    {
        "id": "innolight-eoptolink-share",
        "date": "2026-01-20",
        "source": "IP Fiber",
        "source_type": "industry",
        "headline": "InnoLight + Eoptolink dominate 60% of NVIDIA 800G SFP supply",
        "quote": "InnoLight ~50%+ of NVDA 800G transceivers; Eoptolink complementary share. Combined ~60% of NVDA 800G supply.",
        "url": "https://ip-fiber.com/blogs/news/nvidia-orders-surge-innolight-and-eoptolink-dominate-60-of-800g-sfp-optical-modules-supply",
        "layer_ids": ["optics"],
        "tickers": ["300308.SZ", "300502.SZ"],
    },
    {
        "id": "delloro-ethernet-shift",
        "date": "2025-12-10",
        "source": "Dell'Oro Group",
        "source_type": "industry",
        "headline": "Ethernet >⅔ of AI cluster switch sales in Q3 2025",
        "quote": "AI back-end networks continue shift to Ethernet — now accounting for >2/3 of Q3 2025 switch sales in AI clusters. InfiniBand share compressing.",
        "url": "https://www.delloro.com/news/ai-back-end-networks-continue-their-shift-to-ethernet-now-accounting-for-over-two-thirds-of-3q-2025-switch-sales-in-ai-clusters/",
        "layer_ids": ["networking", "switches"],
        "tickers": ["AVGO", "ANET"],
    },
]


# ---------------------------------------------------------------------------
# Long-form per-layer markdown.
# ---------------------------------------------------------------------------

LAYER_CONTENT = {
    "hbm": """## What it does
High-Bandwidth Memory (HBM) is the on-package DRAM that feeds GPUs and AI ASICs. Unlike commodity DDR, HBM stacks 8–16 DRAM dies vertically, connects them with through-silicon vias (TSVs), and sits on the same silicon interposer as the compute die. That proximity is what enables the multi-TB/s memory bandwidth modern accelerators need.

## Why it matters for inference scaling
Inference is memory-bound far more than training. Every token generated by an LLM requires reading the full KV cache plus activations from HBM — bandwidth, not flops, is the gating factor for tokens-per-second. Larger models, longer contexts, and multi-modal workloads all amplify HBM demand per accelerator. HBM3E to HBM4 doubles bandwidth per stack and is the single biggest architectural lever in the next two product cycles.

## Current bottleneck (May 2026)
- **Sold out**: HBM3E and HBM4 fully booked across SK Hynix, Samsung, and Micron through 2026.
- **Pricing**: ~20% blended price hike for 2026; 3-year LTAs being signed (Micron–MSFT, Hynix–multiple).
- **Supply gap**: Micron management says they can meet only 50–66% of core-customer demand.
- **HBM4 ramp**: Starts calendar Q2 2026 at >11 Gbps; Hynix briefly shifting capacity *back* to HBM3E in April 2026 because Nvidia placed incremental orders for Blackwell Ultra/GB300 — a clean signal that Rubin is slipping right.

## Priced-in vs underappreciated
**Priced-in.** Memory has run hardest of any layer; stocks reflect a full supercycle. Risk is now to the downside — mix shift to HBM4 (margin re-set), China DRAM (CXMT), capex over-build for 2027–28. The trade-off here is good: you need exposure for the AI thesis, but this is not where 2026 alpha lives.
""",
    "foundry": """## What it does
The foundry is where the GPU/ASIC silicon die is actually fabricated, at leading-edge nodes (3nm, 2nm, 1.4nm). One company — TSMC — has effective monopoly on AI silicon at these nodes; Samsung Foundry is chasing, Intel is rebuilding, but neither materially constrains TSMC pricing today.

## Why it matters for inference scaling
Each node shrink delivers ~30–40% perf-per-watt improvement, the entire premise of being able to deliver more inference per dollar of power and per square meter of data center. AI customers are pre-paying multi-billion-dollar capacity reservations to lock allocation 2–3 years out.

## Current bottleneck (May 2026)
- **N2 sold out** for 2026–2027. Apple, Nvidia (Rubin), AMD (MI400) all booked.
- **N3** fully booked for AI. N2 wafer pricing ~$30K vs ~$20K for N3.
- **Capex**: TSMC 2026 capex guide $52–56B (vs ~$40B prior year), 70–80% advanced nodes, 10–20% advanced packaging.
- **The real constraint**: it isn't wafers — it's packaging (CoWoS). See that layer.

## Priced-in vs underappreciated
**Priced-in.** TSMC priced for perfection; Intel is a binary turnaround bet, not a stack play. The cleaner exposure is via packaging (where TSMC is also dominant but multiple looks different) or via WFE.
""",
    "packaging": """## What it does
Advanced packaging stacks the GPU/ASIC die with multiple HBM stacks on a silicon interposer (CoWoS), or stacks die directly on die (SoIC, 3D-IC). It's what turns a leading-edge silicon die into a usable AI accelerator.

## Why it matters for inference scaling
This is the binding physical constraint for AI compute volume in 2026. TSMC controls CoWoS and is the bottleneck name itself: every Blackwell, Rubin, and Google TPU has to flow through CoWoS. Demand exceeds capacity; Nvidia takes >60% of 2026 slots, which is why Google reportedly cut its 2026 TPU build from ~4M to ~3M.

## Current bottleneck (May 2026)
- **CoWoS-L/S fully booked** through 2026.
- **Capacity**: Scaling from ~35K wafers/month (late 2024) to ~130K wafers/month by end of 2026 — an extraordinary ramp that still leaves the market short.
- **Spillover**: ASE (CoWoP), Amkor, Intel (EMIB/Foveros) are all qualifying with hyperscaler ASIC programs to absorb overflow.
- **CoPoS** (panel-level): TSMC pilot June 2026, volume 2028–29 — long-dated, doesn't relieve the 2026 squeeze.

## Priced-in vs underappreciated
**Underappreciated for OSATs.** TSMC priced in. ASE and Amkor get the spillover at much lower multiples than warranted by the de-bottlenecking trade. The structural call: if TSMC physically cannot expand fast enough — and CoPoS is years away — then OSATs are the cleanest second-source overflow play.
""",
    "wfe": """## What it does
Wafer fab equipment (WFE) is the tooling that builds chips: lithography (ASML), deposition (AMAT, LRCX), etch (LRCX, TEL), process control (KLA), and dozens of niche tools. ASML's EUV scanners are the irreplaceable gate at leading-edge nodes; the rest is a quality oligopoly.

## Why it matters for inference scaling
WFE *delivers* the bottleneck-relievers — every foundry capacity expansion and every HBM/CoWoS ramp drives WFE orders. Backlog visibility is multi-year (ASML €38.8B), so revenue lags but is exceptionally predictable.

## Current bottleneck (May 2026)
- **ASML 2026 guide €36–40B**; record €38.8B backlog. Capacity-execution focus.
- **High-NA EUV** ramping at SK Hynix and Samsung (1.4nm); TSMC delayed High-NA adoption to 2029, a small near-term ASML overhang.
- **HBM TSV demand** is a second leg for LRCX/AMAT that street models still under-weight.

## Priced-in vs underappreciated
**Mixed.** ASML largely priced in. **LRCX is arguably underappreciated** for the HBM TSV ramp — every additional HBM die multiplies etch tool demand, and that's a cleaner, faster-cycling beneficiary than the foundry build-out that drives ASML.
""",
    "gpu": """## What it does
The compute itself: merchant GPUs (Nvidia, AMD) and custom hyperscaler ASICs (Broadcom-designed Google TPU and Meta MTIA, Marvell-designed AWS Trainium and Microsoft Maia). Custom ASICs are fabbed at TSMC and use the same CoWoS+HBM pipeline as merchant GPUs.

## Why it matters for inference scaling
The headline name. NVDA still has ~85%+ of merchant AI training silicon; ASICs are taking share faster on the inference side because hyperscalers can amortize a single workload across millions of nodes.

## Current bottleneck (May 2026)
- **Blackwell**: 3.6M-unit backlog, sold out through mid-2026. Supply-constrained, not demand-constrained.
- **Rubin**: 2026 share cut from 29% to 22% (HBM4 validation, ConnectX-9 NIC migration, higher TDP, L2A cooling). GB300 picks up slack at +129% YoY.
- **Custom ASIC**: TrendForce forecasts +45% in 2026 vs +16% GPU shipments. Broadcom Q1 FY26 AI revenue $5.1B (+77% YoY); 3 hyperscaler customers shipping, 2 in design.

## Priced-in vs underappreciated
**NVDA priced in. AVGO largely priced in. MRVL still arguably underappreciated** vs its design-win pipeline (Trainium 3, Maia 2). Not a contrarian call but the cleanest way to play the ASIC mix-shift remaining.
""",
    "networking": """## What it does
Switch ASICs (Broadcom Tomahawk/Jericho), DSPs (Marvell, MaxLinear), and specialty silicon that wires up the network fabric inside an AI cluster. Distinct from the boxes themselves (next layer).

## Why it matters for inference scaling
Modern training clusters run 100k+ accelerators; for them to act as one machine the network has to deliver near-line-rate at very low latency. Scale-out networking is now ~10–15% of total cluster spend and growing. Ethernet has decisively won the back-end network from InfiniBand (>⅔ of Q3 2025 AI cluster switch sales — Dell'Oro).

## Current bottleneck (May 2026)
- **Switch silicon**: Broadcom Tomahawk dominance; merchant share growing as hyperscalers standardize.
- **DSPs**: Marvell incumbent; competitive vs Broadcom's PAM4 stack.
- **The real squeeze**: optics, not switch silicon. See next layer.

## Priced-in vs underappreciated
**Mixed.** AVGO is priced in. MRVL DSPs is a continuation of the underappreciated GPU/ASIC story — same conviction.
""",
    "optics": """## What it does
Optical components — InP semiconductor lasers (EMLs, the "engine" of every transceiver), optical modules (the rectangles plugged into switches), and DSPs that drive them. The bridge from silicon to fiber for every cluster-scale AI deployment.

## Why it matters for inference scaling
You cannot wire 100k GPUs together with copper — past a few meters it's optics. Each Blackwell GB200 NVL72 rack consumes hundreds of transceivers; 1.6T modules are mandatory above ~50k-GPU scale-out. Lumentum is sole-source on 200G/lane EMLs that 1.6T optical modules need; capacity is tripling — only by mid-2027.

## Current bottleneck (May 2026)
- **EML lasers (InP)**: textbook 2026 bottleneck. Sold out through 2027.
- **800G transceivers**: 40–60% short of demand through 2027 (McKinsey).
- **1.6T transceivers**: 30–40% short through 2029.
- **NVDA invested ~$4B combined into LITE+COHR in March 2026** ($2B into LITE at $695.31/sh) to lock supply — exactly the move Apple made with Cirrus and TSMC made with ASML. That's the supplier-of-record signal.
- **Lumentum Q3 FY26**: revenue $808M (+90% YoY), record. Coherent Q2 FY26: record $1.81B; 1.6T order book >$200M.
- **InnoLight + Eoptolink (China)**: combined ~60% of Nvidia's 800G transceiver supply.

## Priced-in vs underappreciated
**UNDERAPPRECIATED — top idea cluster in this map.** Optical components (LITE, COHR, FN) are the cleanest "second leg" of the inference trade — closest analog to where memory was in early 2024. Multi-year supply gap is documented, NVDA is bankrolling capacity, and the public market hasn't fully repriced. The Chinese names (InnoLight, Eoptolink) are higher-quality businesses than the multiple suggests, with geopolitical overhang as the catch.
""",
    "switches": """## What it does
The actual network systems: branded switches (Arista, Cisco, HPE) and white-box ODMs (Celestica, Accton) that hyperscalers buy directly.

## Why it matters for inference scaling
Switches are where the network silicon and optics get integrated. Hyperscalers increasingly bypass branded vendors and buy white-box from ODMs to control cost and supply.

## Current bottleneck (May 2026)
- **Arista**: 2026 guide ~+20%; AI/campus growth ~60%. Took the DC switch crown from Cisco.
- **Cisco**: raised AI infra revenue to $3B; HPE/Juniper combination newly competitive.
- **White-box capture**: Celestica and Accton (Taiwan) gaining share — that's where the volume actually goes for hyperscale.

## Priced-in vs underappreciated
**ANET priced in. Celestica is a sleeper** — white-box capture of hyperscaler networking is real and CLS multiple still doesn't reflect it fully. CSCO + HPE are mostly value/yield trades.
""",
    "power": """## What it does
The grid-side and on-site power stack: utility transformers (GEV), switchgear (ETN, HUBB), backup gensets (CAT, CMI, GNRC), substation/transmission EPC (PWR), and integrated DC power systems (VRT, ETN, SU). The actual physical electrons that hit the GPU.

## Why it matters for inference scaling
This is increasingly the binding constraint, not silicon. Lead times have stretched from 24–30 months pre-2020 to up to 5 years now for transformers and gas turbines. >50% of US 2026 data centers are expected to be delayed or cancelled because the electrical gear physically isn't available.

## Current bottleneck (May 2026)
- **GE Vernova**: backlog $163B; 2026 DC orders $2.4B already exceed all 2025. Gas turbine slots sold out through 2028 (Mitsubishi quoting 2029–2030).
- **Eaton**: DC orders +30%+ for 4 consecutive quarters; electrical Americas backlog at record.
- **Generac**: only gas-genset slot in Stargate permitting docs because Cat/Cummins lead times are 70–107 weeks vs Generac's 50–60.
- **Cummins**: 18-month lead times even after $150M Fridley expansion.

## Clean baseload (nuclear / SMR)
Hyperscalers are now buying nuclear capacity directly — MSFT–CEG to restart Three Mile Island Unit 1, AMZN–Talen at Susquehanna. Two distinct sub-bets sit underneath:

- **Existing nuclear fleet operators** monetizing PPAs at premium pricing — **CEG** is the largest US nuclear operator and the cleanest expression.
- **The SMR build-out**, which needs both reactor designers (**OKLO** — Sam Altman-backed Aurora powerhouse) and a fuel supply chain that today bottlenecks on HALEU enrichment (**LEU** is the sole US producer).

Lead times: 5–15 years for a new reactor vs. 50–70 weeks for a genset. Different asset class, same demand driver — and the AI-power thesis only fully closes when this leg is included.

## Priced-in vs underappreciated
**Mixed. GEV/ETN/VRT richly priced.** Underappreciated: **GNRC, HUBB, PWR.** Generac has the only gas-genset slot in Stargate permits because everyone else is sold out. PWR/HUBB get every grid-buildout dollar regardless of which hyperscaler wins. The further you go from "DC-pure-play" toward "structural grid build", the cheaper the multiple — and the demand is equally durable. **CEG** the cleanest large-cap nuclear expression; **OKLO/LEU** more speculative but capture the SMR/HALEU bottleneck not yet reflected in the gensets-and-transformers framing.
""",
    "cooling": """## What it does
The thermal stack: cold plates, coolant distribution units (CDUs), liquid-to-air heat exchangers, immersion cooling fluids and tanks. Mandatory above ~700W TDP, which Blackwell crossed and Rubin/MI400 vastly exceed.

## Why it matters for inference scaling
Air cooling tops out around 50 kW/rack; modern AI racks are 130 kW+ and trending past 250 kW. Direct-to-chip liquid is the only thermodynamically viable path. Every rack sold means ~$15–25K of cooling content sold alongside.

## Current bottleneck (May 2026)
- **Vertiv** Q1 2026: revenue $2.65B (+30% YoY), backlog ~$15B (+109% YoY), book-to-bill 2.9x. NVDA reference partner.
- **Modine**: DC sales +31% sequential Q3 FY26; mgmt guides 50–70% DC growth.
- **nVent**: ~30% DC exposure, growing NVDA depth.
- **Schneider Electric** (private cooling lines, listed via SU.PA): broadest portfolio, slower-cycle.

## Priced-in vs underappreciated
**VRT priced in. MOD and NVT arguably still underappreciated** for the DC mix-shift inside an industrials wrapper — both are still partly priced as legacy industrials despite >50% incremental DC growth.
""",
    "hyperscalers": """## What it does
The demand side. MSFT, GOOG/GOOGL, META, AMZN, ORCL collectively spend ~$725B in 2026 capex (+77% YoY), of which ~75% is AI-related (~$540B). They are the customers funding every other layer in this map.

## Why it matters for inference scaling
Tracking hyperscaler capex *commentary* is more useful than tracking the headline numbers — what they say about memory pricing, power siting, lead times, and unit economics gives you the cleanest read on which layers have pricing power.

## Current bottleneck (May 2026)
- **Combined 2026 capex**: ~$725B (MSFT + GOOGL + META + AMZN), +77% YoY.
- **MSFT**: CY26 capex $190B; CFO Amy Hood attributed **$25B of the increase to rising memory/component costs** — direct read-through to HBM pricing.
- **Meta**: FY26 raised $10B to >$145B; –90% FCF projected.
- **GOOG**: Q1 capex $35.67B; FY26 $180–190B; 2027 to "significantly increase".
- **AMZN**: ~$200B FY26; –$17B FCF projected.
- **ORCL**: ~$50B; capex/sales ~86% — most stretched.

## Priced-in vs underappreciated
**META and ORCL most stretched** on capex/sales. **GOOG arguably under-loved** — the only fully integrated hyperscaler stack (TPU + DeepMind + YouTube ad attach) at a more reasonable multiple than peers.
""",
    "neoclouds": """## What it does
Specialist GPU clouds — CoreWeave (CRWV) and Nebius (NBIS) public; Lambda, Crusoe, Voltage Park private. Buy GPUs in volume from Nvidia, rent them out to hyperscalers and AI labs.

## Why it matters for inference scaling
A leveraged play on Nvidia shipment continuity. Their growth is whatever Nvidia's allocation and the second-tier hyperscaler/lab capex can absorb.

## Current bottleneck (May 2026)
- **CRWV**: ~$59B mkt cap, 2026E rev ~$12.5B (+143%), 2027 ~$23.5B.
- **NBIS**: 2026E +206% rev; EV ~½ of CRWV.
- **Combined Meta deals**: ~$48B (CRWV + NBIS together).
- **Bottlenecks**: GPU allocation, power siting.

## Priced-in vs underappreciated
**High beta, not under-priced.** These are leveraged plays on Nvidia. Skip if you already own NVDA — the risk-adjusted return is similar with more company-specific risk.
""",
    "software": """## What it does
The full inference software stack: model labs (OpenAI, Anthropic, xAI, Mistral — mostly private), serving runtimes (vLLM, SGLang, TensorRT-LLM, plus paid Together/Fireworks/Baseten), and enterprise AI platforms (Salesforce Agentforce, ServiceNow, Snowflake Cortex, Palantir AIP).

## Why it matters for inference scaling
Software is where margins compress as inference becomes a commodity. Differentiation moves to data + workflow integration, not the model itself.

## Current bottleneck (May 2026)
Not a hardware bottleneck. Margins are the story — and they're going down as token prices fall ~4x/yr.

## Priced-in vs underappreciated
**Most crowded layer in the stack ex-NVDA.** PLTR especially. Hard to find under-priced names here. The private side (model labs) is where most of the upside lives but is inaccessible to retail.
""",
    "eda": """## What it does
Electronic Design Automation — the software chip designers use to lay out and verify silicon. Cadence (CDNS) and Synopsys (SNPS) are the duopoly; Siemens EDA (via SIEGY) third.

## Why it matters for inference scaling
Toll-booth model. Every new GPU/ASIC tape-out is EDA revenue. Not capacity-constrained.

## Current bottleneck (May 2026)
None. AI-EDA segment growing ~24% CAGR. Cadence 2026 guide raised to $6.13–6.23B; Synopsys closing Ansys merger.

## Priced-in vs underappreciated
**Fairly priced quality compounders.** Not where alpha lives in this cycle. Buy when oversold, otherwise hold.
""",
    "substrates": """## What it does
The high-density laminate (FC-BGA, ABF) that connects the silicon die to the package and the package to the motherboard. Far from sexy, very hard to make.

## Why it matters for inference scaling
Every CoWoS package needs an FC-BGA substrate, and every AI server needs FC-BGA on its CPU sockets. ABF is the high-end material and a recurring choke point.

## Current bottleneck (May 2026)
- **Capacity expansion**: ~15% (vs –9% gap in 2023). Intel/AMD/NVDA pre-funded ~50% of the capex.
- **Players**: Ibiden (4062.T) is the premium FC-BGA name and an NVDA supplier; Unimicron (3037.TW) is the volume #2; Shinko Electric being taken private by JIC consortium; AT&S (Austria) Intel-aligned.
- **Re-tightens with each AI cycle** — supply chain doesn't carry safety stock.

## Priced-in vs underappreciated
**UNDERAPPRECIATED.** Ibiden in particular is a multi-decade quality compounder still trading like a cyclical PCB stock. Western retail underweights it. Unimicron similar. Both are well-positioned for the AI build cycle and the 2027–28 packaging-capacity wave.
""",
}


# ---------------------------------------------------------------------------
# CIQ ticker → companyId resolution
# ---------------------------------------------------------------------------

# Manual overrides for tickers that don't resolve cleanly via name search.
# Set to None to explicitly skip a ticker (e.g. delisted, wrong-name overlap).
# Add an integer companyId to override the resolver. Look up via the skill at
# ../Exponential-Growth/.claude/skills/s&p/SKILL.md (find_company helper).
CIQ_OVERRIDES: dict[str, int | None] = {
    "6967.T": None,     # Shinko Electric — being taken private by JIC; CIQ data stale anyway
    "ATS.VI": 2444485,  # AT&S Austria Technologie & Systemtechnik AG (special char in name foils resolver)
}


def _bare_ticker(ticker: str) -> str:
    """Strip exchange suffix. '000660.KS' -> '000660'. 'NVDA' -> 'NVDA'."""
    return ticker.split(".")[0]


def _resolve_one(cur, ticker: str, name: str) -> tuple[int | None, str | None, str]:
    """Return (companyId, companyName, resolved_via). Tries ticker then name."""
    bare = _bare_ticker(ticker)

    # 1. Ticker-based: most-securities wins among primaryFlag=1 hits.
    cur.execute("""
        SELECT s.companyId, c.companyName, COUNT(DISTINCT s2.securityId) AS sec_count
        FROM CIQTRADINGITEM ti
        JOIN CIQSECURITY s ON ti.securityId = s.securityId
        JOIN CIQCOMPANY c ON s.companyId = c.companyId
        LEFT JOIN CIQSECURITY s2 ON s2.companyId = c.companyId
        WHERE ti.tickerSymbol = %s AND ti.primaryFlag = 1
        GROUP BY s.companyId, c.companyName
        ORDER BY sec_count DESC
        LIMIT 5
    """, (bare,))
    rows = cur.fetchall()

    # Cross-check: ticker hit must share a name keyword. Avoids "000660"
    # collision where SZSE Guangzhou Datong shares the bare ticker with
    # SK Hynix on KOSPI (different exchange, same number). No ticker-only
    # fallback — too prone to picking unrelated companies on numeric tickers.
    name_keywords = [w for w in re.split(r"\s+", name.lower()) if len(w) > 2][:2]
    for cid, cname, _ in rows:
        if any(kw in cname.lower() for kw in name_keywords):
            return int(cid), cname, "ticker+name-cross-check"

    # 2. Name-based: highest-sec-count match wins (proxy for listed parent).
    cur.execute("""
        SELECT c.companyId, c.companyName, COUNT(DISTINCT s.securityId) AS sec_count
        FROM CIQCOMPANY c LEFT JOIN CIQSECURITY s ON s.companyId = c.companyId
        WHERE LOWER(c.companyName) LIKE %s
        GROUP BY c.companyId, c.companyName
        ORDER BY sec_count DESC LIMIT 5
    """, (f"%{name.lower()}%",))
    rows = cur.fetchall()
    if rows and rows[0][2] >= 3:  # at least 3 securities = real listed parent
        return int(rows[0][0]), rows[0][1], "name"

    return None, None, "unresolved"


def resolve_ciq_mapping(verbose: bool = True) -> dict:
    """Resolve every PLAYERS ticker → companyId via Snowflake. Persists to
    data/ciq_mapping.json. Idempotent — overrides take precedence; everything
    else is re-resolved on each call."""
    from jobs.sources.capital_iq import get_connection

    if verbose:
        print(f"Resolving CIQ mapping for {len(PLAYERS)} tickers...")
    conn = get_connection()
    cur = conn.cursor()
    try:
        mapping = {}
        unresolved = []
        for p in PLAYERS:
            ticker, name = p["ticker"], p["name"]
            if ticker in CIQ_OVERRIDES:
                cid = CIQ_OVERRIDES[ticker]
                mapping[ticker] = {
                    "company_id": cid,
                    "company_name": None,
                    "resolved_via": "override",
                    "resolved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
                }
                if verbose:
                    print(f"  {ticker:<14} OVERRIDE → {cid}")
                if cid is None:
                    unresolved.append(ticker)
                continue
            cid, cname, via = _resolve_one(cur, ticker, name)
            mapping[ticker] = {
                "company_id": cid,
                "company_name": cname,
                "resolved_via": via,
                "resolved_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
            }
            if verbose:
                status = f"{cid:<12} ({via})" if cid else f"UNRESOLVED ({via})"
                print(f"  {ticker:<14} {p['name']:<32} → {status}")
            if cid is None:
                unresolved.append(ticker)
    finally:
        cur.close()
        conn.close()

    _write_json(DATA / "ciq_mapping.json", mapping)
    if verbose:
        ok = sum(1 for v in mapping.values() if v["company_id"] is not None)
        print(f"\nResolved {ok}/{len(PLAYERS)}. Unresolved: {unresolved}")
    return mapping


# ---------------------------------------------------------------------------
# Writers
# ---------------------------------------------------------------------------

def _write_json(path: Path, data) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    tmp = path.with_suffix(path.suffix + ".tmp")
    tmp.write_text(json.dumps(data, indent=2, ensure_ascii=False) + "\n")
    tmp.replace(path)


def main() -> None:
    parser = argparse.ArgumentParser(description="Seed dashboard static content.")
    parser.add_argument("--refresh-ciq-mapping", action="store_true",
                        help="Re-resolve PLAYERS tickers against S&P Capital IQ.")
    args = parser.parse_args()

    DATA.mkdir(parents=True, exist_ok=True)
    CONTENT.mkdir(parents=True, exist_ok=True)

    _write_json(DATA / "layers.json", LAYERS)
    _write_json(DATA / "players.json", PLAYERS)
    _write_json(DATA / "signals.json", sorted(SIGNALS, key=lambda s: s["date"], reverse=True))

    for layer in LAYERS:
        body = LAYER_CONTENT.get(layer["id"], "_(content pending)_\n")
        (CONTENT / f"{layer['order']:02d}-{layer['id']}.md").write_text(body)

    print(f"Wrote {len(LAYERS)} layers, {len(PLAYERS)} players, {len(SIGNALS)} signals")
    print(f"Layer markdown → {CONTENT}")

    if args.refresh_ciq_mapping or not (DATA / "ciq_mapping.json").exists():
        resolve_ciq_mapping()


if __name__ == "__main__":
    main()
