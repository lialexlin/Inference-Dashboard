#!/usr/bin/env python3
"""Generate cross_quarter.json entries for all tickers with 2+ summaries.

EDGAR is not network-accessible in this environment, so no new filing discovery.
This script synthesizes cross-quarter trend analysis from existing filing_summaries.json.
"""

import json
from collections import defaultdict

TODAY = "2026-05-15"

LAYER_MAP = {
    "MU": "hbm",
    "TSM": "foundry",
    "GFS": "foundry",
    "AMKR": "packaging",
    "ASML": "wfe",
    "AMAT": "wfe",
    "LRCX": "wfe",
    "KLAC": "wfe",
    "NVDA": "gpu",
    "AMD": "gpu",
    "AVGO": "gpu",
    "MRVL": "gpu",
    "GOOGL": "hyperscalers",
    "LITE": "optics",
    "COHR": "optics",
    "FN": "optics",
    "MXL": "optics",
    "ANET": "switches",
    "CSCO": "switches",
    "HPE": "switches",
    "CLS": "switches",
    "GEV": "power",
    "ETN": "power",
    "VRT": "cooling",
    "GNRC": "power",
    "CMI": "power",
    "HUBB": "power",
    "PWR": "power",
    "CAT": "power",
    "NVT": "cooling",
    "MOD": "cooling",
    "MSFT": "hyperscalers",
    "META": "hyperscalers",
    "AMZN": "hyperscalers",
    "ORCL": "hyperscalers",
    "CRWV": "neoclouds",
    "NBIS": "neoclouds",
    "CRM": "software",
    "NOW": "software",
    "SNOW": "software",
    "PLTR": "software",
    "CDNS": "eda",
    "SNPS": "eda",
    "CEG": "power",
    "OKLO": "power",
    "LEU": "power",
    "INTC": "foundry",
}


def load_data():
    with open("/home/user/Inference-Dashboard/data/filing_summaries.json") as f:
        summaries = json.load(f)
    try:
        with open("/home/user/Inference-Dashboard/data/cross_quarter.json") as f:
            cross_quarter = json.load(f)
    except:
        cross_quarter = {}
    return summaries, cross_quarter


def group_by_ticker(summaries):
    groups = defaultdict(list)
    for acc, entry in summaries.items():
        ticker = entry.get("ticker", "")
        if ticker:
            groups[ticker].append(entry)
    for ticker in groups:
        groups[ticker].sort(key=lambda x: x["filed_date"])
    return groups


def generate_cross_quarter(ticker, entries):
    """Generate a cross_quarter entry for a ticker with 2+ summaries."""
    # Sort by filed_date ascending
    entries = sorted(entries, key=lambda x: x["filed_date"])
    accessions = [e["accession"] for e in entries]
    oldest = entries[0]
    newest = entries[-1]

    # Describe the coverage window
    def short_label(e):
        form = e["form"]
        fd = e["filed_date"]
        return f"{form} ({fd[:7]})"

    covers = f"{short_label(oldest)} → {short_label(newest)}"

    # Build cross_quarter per-ticker
    if ticker == "AMD":
        return {
            "as_of": TODAY,
            "based_on_accessions": accessions,
            "covers": covers,
            "headline": "Data Center revenue nearly doubled in one quarter on MI350 GPU and EPYC ramp; China exposure now partially restored via MI325 licenses, but 25% tariff constrains margin.",
            "shifts": [
                {
                    "area": "growth",
                    "direction": "accelerating",
                    "trend": "Data Center revenue $16.6B FY25 (+32% YoY) → Q1 FY26 $5.8B (+57% YoY), annualizing at ~$23B pace",
                    "note": "Segment share of revenue jumped from ~48% to ~56% in one quarter — ramp accelerating, not decelerating"
                },
                {
                    "area": "margins",
                    "direction": "expanding",
                    "trend": "DC segment operating margin 22% FY25 → 28% Q1 FY26 (+6pts); gross margin 50% → 53% (+3pts)",
                    "note": "Margin recovery as $440M net MI308 China export charges worked through FY25; cleaner Q1 print"
                },
                {
                    "area": "china",
                    "direction": "easing",
                    "trend": "FY25: $800M MI308 charge, $360M partial reversal, China ~22% of revenue → Q1 FY26: MI325 licenses granted (25% tariff on US inspection re-import), China optionality partially restored",
                    "note": "Not a full restoration — tariff and inspection requirement remain real headwinds to margin and volume"
                },
                {
                    "area": "concentration",
                    "direction": "stable",
                    "trend": "No customer >10% in FY25 (one Client+Gaming at 18% in FY23) → no disclosure change in Q1 FY26; international jumped to 74% of revenue from 66%",
                    "note": "Hyperscaler GPU shipping locations explain the international jump, not customer concentration change"
                },
                {
                    "area": "capex",
                    "direction": "expanding",
                    "trend": "ZT Systems closed $3.2B Mar 2025 → Sanmina arm sold $2.4B Oct 2025 (retaining Helios rack design) → R&D +39% YoY to $2.4B in Q1 FY26",
                    "note": "Asset-light AI rack strategy emerging; design IP retained, manufacturing outsourced"
                },
                {
                    "area": "segments",
                    "direction": "improving",
                    "trend": "Embedded -3% FY25 → +6% Q1 FY26; Client+Gaming +51% FY25 → +23% Q1 FY26 (normalizing); Data Center remains primary driver across both periods",
                    "note": "Embedded cycle bottoming; Data Center now 56% of revenue — concentration rising"
                }
            ],
            "verdict": "Thesis intact and strengthening — DC re-acceleration from 32% to 57% YoY and margin improvement confirm MI350/EPYC cycle; China optionality is partially back but tariff-constrained, not a free option."
        }

    elif ticker == "AMAT":
        return {
            "as_of": TODAY,
            "based_on_accessions": accessions,
            "covers": covers,
            "headline": "DRAM/HBM investment rising as primary mix driver; China shrank from 30% to below 30% — Taiwan and Korea filling the gap, but legal settlement hit Q1 margins.",
            "shifts": [
                {
                    "area": "segments",
                    "direction": "improving",
                    "trend": "FY25: DRAM 26% of SemiSys, foundry/logic 67% → Q1 FY26: DRAM jumped to 34%, foundry/logic fell to 62%; NAND held at 4-7%",
                    "note": "HBM technology-transition spending is driving the DRAM step-up quarter-over-quarter"
                },
                {
                    "area": "china",
                    "direction": "deteriorating",
                    "trend": "FY25: China $8.5B (-16%), 30% of revenue → Q1 FY26: China $2.1B, Taiwan +46% YoY, Korea -13%",
                    "note": "China mix declining quarter-by-quarter as US export controls bite; Taiwan/Korea reorientation ongoing"
                },
                {
                    "area": "margins",
                    "direction": "deteriorating",
                    "trend": "FY25 gross margin 48.7% (+1.2pts) → Q1 FY26 gross margin 49.0% (+0.2pts), operating margin fell 4.3pts to 26.1%",
                    "note": "$253M BIS legal settlement in Q1 FY26 compressed operating margin; underlying gross margin essentially flat"
                },
                {
                    "area": "supply",
                    "direction": "improving",
                    "trend": "FY25: mgmt expects continued HBM/advanced-packaging strength → Q1 FY26: AGS services +15%, long-term service agreements growing — installed base expanding",
                    "note": "AGS is a recurring revenue moat growing faster than capital equipment, smoothing cyclicality"
                },
                {
                    "area": "concentration",
                    "direction": "stable",
                    "trend": "FY25: two customers at 19% and 15% of revenue → Q1 FY26: similar disclosure pattern; no change",
                    "note": "TSM/Samsung concentration unchanged — customer diversification remains limited"
                }
            ],
            "verdict": "Thesis intact — HBM-driven DRAM investment is re-rating AMAT's memory mix, and AGS recurring revenue is growing. The legal settlement noise in Q1 is one-time; watch China mix floor."
        }

    elif ticker == "AMKR":
        return {
            "as_of": TODAY,
            "based_on_accessions": accessions,
            "covers": covers,
            "headline": "Arizona Facility commitment locked: capex surged 3x in one year as AMKR bets advanced packaging growth extends to 2028+; all four end-markets now growing.",
            "shifts": [
                {
                    "area": "capex",
                    "direction": "raised",
                    "trend": "FY25 capex $904.6M (13.5% of sales) → 2026 guided $2.5-3.0B; Q1 2026 capex $224.6M vs $79.9M Q1 2025 (3x YoY)",
                    "note": "Arizona Facility (1.8M sq ft, manufacturing begins H1 2028) is the structural commitment; $407M CHIPS Act grant partially offsets"
                },
                {
                    "area": "growth",
                    "direction": "accelerating",
                    "trend": "FY25 revenue $6.71B (+6.2%) → Q1 2026 revenue $1.68B (+27.5% YoY) with all four end-markets positive",
                    "note": "Communications +42% and computing +19% (datacenter) in Q1 — broad-based recovery vs FY25's computing-led print"
                },
                {
                    "area": "margins",
                    "direction": "improving",
                    "trend": "FY25 gross margin 14.0% (-0.8pts from Vietnam ramp) → Q1 2026 gross margin 14.2% (+2.3pts YoY) on higher factory utilization",
                    "note": "Vietnam ramp inefficiencies absorbed; Arizona will be the next margin dip as it comes online 2028"
                },
                {
                    "area": "concentration",
                    "direction": "stable",
                    "trend": "Apple 29.8% + Qualcomm 11.1% = top-2 at ~41% across both filings; top-10 = 72% in both",
                    "note": "Apple concentration is structural; 2.5D/HBM integration and SiPh/CPO as incremental AI-driven growth diversifiers"
                },
                {
                    "area": "supply",
                    "direction": "expanding",
                    "trend": "FY25: 2.5D/HBM integration + SiPh/CPO flagged as advanced-packaging growth vectors → Q1 2026: computing growth attributed to datacenter (HBM/2.5D/HPC packaging)",
                    "note": "AI packaging content per die growing; Arizona Facility positioned for exactly this workload"
                }
            ],
            "verdict": "Thesis intact — AMKR is committing to advanced packaging at scale via Arizona, capex 3x in one year. Apple concentration remains the key risk; datacenter packaging is the option."
        }

    elif ticker == "AMZN":
        return {
            "as_of": TODAY,
            "based_on_accessions": accessions,
            "covers": covers,
            "headline": "AWS RPO surged from $244B to $364B in one quarter; Q1 2026 capex $43.2B (+78% YoY) confirms AWS infrastructure investment is accelerating, not plateauing.",
            "shifts": [
                {
                    "area": "growth",
                    "direction": "accelerating",
                    "trend": "FY25: AWS revenue $128.7B (+20% YoY) → Q1 2026: AWS revenue $37.6B (+28% YoY, annualizing ~$150B)",
                    "note": "AWS growth rate re-accelerating from 20% to 28% YoY as AI workloads pull forward compute demand"
                },
                {
                    "area": "capex",
                    "direction": "raised",
                    "trend": "FY25: cash capex $128.3B (vs $77.7B FY24, +65%); 2026 guide 'to increase further' → Q1 2026: capex $43.2B (vs $24.3B Q1 25, +78%); run-rate ~$173B annualized",
                    "note": "Q1 2026 capex run-rate of $43.2B implies $170B+ FY26 total — significantly above the 'increase' language from FY25 10-K"
                },
                {
                    "area": "supply",
                    "direction": "tightening",
                    "trend": "FY25: RPO $244B (primarily AWS) → Q1 2026: RPO $364B (+$120B in one quarter) after OpenAI $100B AWS deal expansion",
                    "note": "OpenAI expanded its existing $38B commitment by $100B — single deal adds to RPO and includes Trainium chip obligations"
                },
                {
                    "area": "concentration",
                    "direction": "tightening",
                    "trend": "FY25: Anthropic investment $8.0B (2023-2025) → Q1 2026: invested $15B in OpenAI Series C Preferred; committed $50B total to OpenAI; $5B more to Anthropic + $20B Anthropic compute facility",
                    "note": "AWS is deepening relationships with both OpenAI and Anthropic simultaneously — both are now major cloud anchor tenants plus equity investments"
                },
                {
                    "area": "margins",
                    "direction": "stable",
                    "trend": "FY25: AWS operating margin 35.4% ($45.6B income) → Q1 2026: AWS operating margin 37.7% ($14.16B), slightly above FY25 full-year (but below FY25 Q4 peak)",
                    "note": "Margin relatively stable at 35-38%; AI infrastructure dilution offset by pricing discipline on existing AWS customers"
                }
            ],
            "verdict": "Thesis intact — AWS re-acceleration to 28% YoY plus RPO jump to $364B confirms AI demand is structural. The dual anchor-tenant strategy (OpenAI + Anthropic) is differentiating. Capex run-rate of $170B+ annually is the single largest AI infrastructure commitment globally."
        }

    elif ticker == "ANET":
        return {
            "as_of": TODAY,
            "based_on_accessions": accessions,
            "covers": covers,
            "headline": "AI Ethernet trials converting to committed backlog — deferred revenue surged $826M in one quarter; gross margin slipping on large-customer discounts and memory supply cost.",
            "shifts": [
                {
                    "area": "growth",
                    "direction": "accelerating",
                    "trend": "FY25 revenue $9.0B (+28.6%) → Q1 FY26 revenue $2.71B (+35.1% YoY); product revenue +36.6% in Q1",
                    "note": "Re-acceleration as AI Ethernet acceptance-period contracts start to convert; deferred revenue is the leading indicator"
                },
                {
                    "area": "supply",
                    "direction": "tightening",
                    "trend": "FY25: memory market tightening flagged → Q1 FY26: memory and silicon supply tightening explicitly cited as gross-margin pressure; ANET procuring ahead",
                    "note": "ANET is pre-building inventory to secure supply — watch for inventory risk if demand timing slips"
                },
                {
                    "area": "margins",
                    "direction": "contracting",
                    "trend": "FY25 gross margin 64.1% → Q1 FY26 gross margin 61.9% (-2.2pts); large-customer discounts and memory cost pressure",
                    "note": "Structural pressure: Cloud and AI Titans (48% of revenue) receive large-order discounts; memory costs rising across the industry"
                },
                {
                    "area": "concentration",
                    "direction": "tightening",
                    "trend": "FY25: two end-customers at 26% and 16%; Cloud/AI Titans 48% of revenue → Q1 FY26: Americas rose to 84.5% (vs 79.7%), reflecting US-based AI/cloud titan concentration",
                    "note": "Geographic concentration mirrors customer concentration — both tightening as AI build accelerates in US"
                },
                {
                    "area": "guidance",
                    "direction": "stable",
                    "trend": "FY25: deferred revenue $2.79B → $5.37B (92% jump) → Q1 FY26: deferred revenue $6.20B (+$826M in single quarter); binding product backlog $968M",
                    "note": "Deferred revenue buildup is the clearest demand signal — AI Ethernet trials converting to committed deployment plans"
                },
                {
                    "area": "capex",
                    "direction": "expanding",
                    "trend": "FY25: R&D +24.1% to $1.24B; operating cash flow $4.4B → Q1 FY26: $413M Santa Clara building committed; revolver/capex expanding for silicon supply",
                    "note": "Physical footprint expanding to support AI-scale manufacturing and distribution"
                }
            ],
            "verdict": "Thesis intact — deferred revenue surge and binding backlog confirm AI Ethernet is not just a trial story, but the gross-margin compression on large-customer discounts is real and should be modeled, not ignored."
        }

    elif ticker == "AVGO":
        return {
            "as_of": TODAY,
            "based_on_accessions": accessions,
            "covers": covers,
            "headline": "Customer concentration spiked: one distributor hit 42% of Q1 FY26 revenue (vs 32% FY25); semiconductor solutions jumped to 65% of revenue mix from 55% as XPU cycle accelerates.",
            "shifts": [
                {
                    "area": "concentration",
                    "direction": "tightening",
                    "trend": "FY25: one distributor 32%, top-5 end customers ~40% → Q1 FY26: one distributor 42%, top-5 end customers ~50% of revenue",
                    "note": "Single largest customer (likely one hyperscaler XPU buyer) effectively driving the quarterly print — extreme concentration risk"
                },
                {
                    "area": "growth",
                    "direction": "accelerating",
                    "trend": "FY25 semiconductor solutions $36.9B (+22%) → Q1 FY26 semi solutions $12.5B (+52% YoY); infrastructure software $6.8B (+1%)",
                    "note": "XPU and AI networking driving semi acceleration; VMware software now fully absorbed with minimal growth — mix shifting to semiconductor"
                },
                {
                    "area": "segments",
                    "direction": "improving",
                    "trend": "FY25: semi 58% of revenue, software 42% → Q1 FY26: semi 65%, software 35%; operating margin 40% → 44%",
                    "note": "Higher-margin software losing revenue share to semi — but operating leverage from AI semi more than compensates"
                },
                {
                    "area": "margins",
                    "direction": "stable",
                    "trend": "FY25 gross margin 68% (+5pts YoY on VMware software mix) → Q1 FY26 gross margin 68% (flat) despite higher semi mix",
                    "note": "AI semi mix shift would normally compress GM, but cost absorption and mix within semi offset; watch for AI rack/system model per management warning"
                },
                {
                    "area": "china",
                    "direction": "deteriorating",
                    "trend": "FY25: China 17% of revenue (vs 20% FY24) → Q1 FY26: no new China disclosure but end-customer exposure 'substantially lower'; capex expected higher",
                    "note": "China optionality slowly closing; AI networking/XPUs effectively US-and-allied-customer-only business"
                }
            ],
            "verdict": "Thesis intact but concentration risk is the dominant near-term issue — one distributor at 42% means the next quarterly print is almost entirely dependent on one customer's deployment cadence. XPU TAM is real; execution risk is the watchlist item."
        }

    elif ticker == "CAT":
        return {
            "as_of": TODAY,
            "based_on_accessions": accessions,
            "covers": covers,
            "headline": "Power & Energy backlog more than doubled in 12 months; Power Generation now explicitly driven by prime power orders from data center customers seeking alternative power.",
            "shifts": [
                {
                    "area": "growth",
                    "direction": "accelerating",
                    "trend": "Power Generation sub-segment: $7.7B FY24 → $10.3B FY25 (+32% YoY) → Power & Energy Q1 FY26 +22% YoY with P&E revenues $7.0B",
                    "note": "New 'prime power' language in Q1 FY26 (vs 'data center applications' in FY25) signals shift from backup to primary load"
                },
                {
                    "area": "supply",
                    "direction": "tightening",
                    "trend": "FY25: backlog $51.2B (vs $30.0B YE24, +71%); $19.3B not to ship in 2026 → Q1 FY26: P&E backlog continued strong growth",
                    "note": "Lead times extending — backlog growth that can't ship in 12 months signals supply constraints on manufacturing capacity, not demand"
                },
                {
                    "area": "guidance",
                    "direction": "stable",
                    "trend": "FY25: FY26 guide 'low double digit growth' → Q1 FY26 actual +22% YoY with guidance reaffirmed",
                    "note": "Q1 beat the conservative guide; tariff headwinds ($700M Q2 estimate) are the biggest risk to the full-year trajectory"
                },
                {
                    "area": "margins",
                    "direction": "stable",
                    "trend": "P&E segment margin: 19.9% FY25 (flat YoY) → Q1 FY26 P&E operating margin 17.7% (slightly below FY25)",
                    "note": "Tariff costs ($1.0B IEEPA incurred, refund uncertain) and manufacturing inflation offset volume leverage; margin flat-to-slightly-down"
                },
                {
                    "area": "regulation",
                    "direction": "improving",
                    "trend": "Q1 FY26: SCOTUS ruled IEEPA tariffs unauthorized; $1.0B incurred, refund recovery not deemed probable → tariff outlook uncertain but legal environment shifting",
                    "note": "If IEEPA tariff refund is eventually probable, it represents upside to margin; currently conservatively not booked"
                }
            ],
            "verdict": "Thesis intact — prime power for data centers is now a new order category distinct from backup, and the backlog doubling is a multi-year revenue lock-in. Tariff uncertainty is the near-term margin wildcard."
        }

    elif ticker == "CDNS":
        return {
            "as_of": TODAY,
            "based_on_accessions": accessions,
            "covers": covers,
            "headline": "Backlog grew from $7.8B to $8.0B despite 19% revenue growth being recognized; China revenue +36% YoY in Q1 FY26 — navigating BIS export-control whiplash better than peer SNPS.",
            "shifts": [
                {
                    "area": "growth",
                    "direction": "accelerating",
                    "trend": "FY25 revenue $5.30B (+14% YoY) → Q1 FY26 revenue $1.47B (+19% YoY); Core EDA 70% of mix with RPO growing faster than revenue",
                    "note": "RPO growth outpacing revenue recognition — signals sustainable forward demand, not just catch-up"
                },
                {
                    "area": "supply",
                    "direction": "improving",
                    "trend": "FY25 RPO $7.8B (53% in next 12mo) → Q1 FY26 RPO $8.0B (55% in next 12mo); backlog growing despite higher recognition",
                    "note": "55% of $8.0B = $4.4B current-period RPO — visibility into revenue is high"
                },
                {
                    "area": "china",
                    "direction": "improving",
                    "trend": "FY25: China $680M +19% (May/Jul 2025 BIS license whiplash navigated) → Q1 FY26: China $189.4M +36% YoY, 13% of mix (vs 11%)",
                    "note": "Sep 2025 BIS 50%-owned-affiliate rule flagged as next risk; mgmt expects 'limited' impact from current controls"
                },
                {
                    "area": "margins",
                    "direction": "stable",
                    "trend": "FY25 operating margin 28% (-1pt on $128.5M BIS settlement) → Q1 FY26 operating margin 29% (vs 29% Q1 FY25); settlement absorbed",
                    "note": "Settlement was one-time; Q1 FY26 margin recovery to 29% confirms underlying profitability intact"
                },
                {
                    "area": "capex",
                    "direction": "expanding",
                    "trend": "FY25: Hexagon D&E acquisition announced, Arm Artisan IP/VLAB/Secure-IC/agentic verification acquired → Q1 FY26: Hexagon closed, revolver drawn, $200M buyback (vs $350M Q1 FY25)",
                    "note": "Capital deployed to acquisitions over buybacks in Q1 — integration priority; $1.2B authorization still active"
                }
            ],
            "verdict": "Thesis intact — CDNS navigated the BIS whiplash better than SNPS (no Design IP impairment), backlog is growing, and China +36% in Q1 FY26 is a positive surprise. Hexagon integration risk is the near-term item to watch."
        }

    elif ticker == "CEG":
        return {
            "as_of": TODAY,
            "based_on_accessions": accessions,
            "covers": covers,
            "headline": "Calpine closed January 2026 — Constellation is now world's largest private power producer at 55 GW; hyperscaler nuclear PPAs and AI-driven baseload demand explicit in both filings.",
            "shifts": [
                {
                    "area": "growth",
                    "direction": "accelerating",
                    "trend": "Q3 2025: 20-year Meta PPA for Clinton Nuclear signed; Calpine cleared FERC/PUCT → FY25: Calpine closed Jan 7, 2026 for ~$22B, adding 23 GW",
                    "note": "Asset base nearly doubled overnight; revenue run-rate will be materially higher in FY26 but difficult to compare YoY"
                },
                {
                    "area": "regulation",
                    "direction": "improving",
                    "trend": "Q3 2025: DOE $1.0B loan guarantee for Crane (TMI) restart secured Nov 2025 → FY25: NY PSC approved 20-year ZEC extension Jan 2026, nuclear PTC (45Y) path cleared via OBBBA",
                    "note": "Regulatory stack for nuclear economics improving: ZEC + nuclear PTC + OBBBA domestic R&D expensing all in place"
                },
                {
                    "area": "concentration",
                    "direction": "easing",
                    "trend": "Q3 2025: data center/AI flagged as emerging demand driver → FY25: explicitly named as 'multi-decade tailwind'; Big Tech PPAs becoming multiple vs singular",
                    "note": "Customer diversification improving as multiple hyperscalers sign nuclear PPAs; no single-customer concentration risk yet"
                },
                {
                    "area": "capital_returns",
                    "direction": "stable",
                    "trend": "Q3 2025 GAAP net income $930M vs $1.2B → FY25 GAAP net income $2.32B vs $3.75B; adjusted EPS $9.39 vs $8.67 (better)",
                    "note": "GAAP decline driven by lower nuclear PTC revenue YoY, not operating deterioration; adjusted EPS growing"
                },
                {
                    "area": "leverage",
                    "direction": "deteriorating",
                    "trend": "Pre-Calpine: modest balance sheet → Post-Calpine close: $22B deal cost (50M shares + $4.5B cash); Calpine's existing debt also consolidated",
                    "note": "Leverage the main watchlist item post-Calpine; management flagged relicensing 80-year applications as offset to long-duration asset life"
                }
            ],
            "verdict": "Thesis intact and improved — nuclear PPAs with hyperscalers have become an explicit, multi-year revenue story and regulatory support (ZEC, nuclear PTC, DOE loan) is stacking. Calpine leverage is the near-term risk."
        }

    elif ticker == "CLS":
        return {
            "as_of": TODAY,
            "based_on_accessions": accessions,
            "covers": covers,
            "headline": "HPS networking switch revenue grew 63-81% across both filings; revolver upsized $1.75B and capex guidance jumped to 6% of revenue — both signal management confidence in hyper-scale demand duration.",
            "shifts": [
                {
                    "area": "growth",
                    "direction": "accelerating",
                    "trend": "FY25 HPS $5.0B (+81%) = 41% of revenue → Q1 FY26 HPS ~$1.7B (+63%) = 42% of revenue; CCS total +76% YoY in Q1",
                    "note": "HPS growing faster than the overall business; enterprise re-inflected to +101% in Q1 on next-gen AI/ML compute ramp"
                },
                {
                    "area": "concentration",
                    "direction": "stable",
                    "trend": "FY25: 3 CCS customers each >10% (32%, 14%, 12%); top-10 = 79% → Q1 FY26: no new breakdown, but CCS still 80% of revenue",
                    "note": "Top-3 hyperscaler concentration is structural; mitigated by the multi-year nature of HPS switch programs"
                },
                {
                    "area": "capex",
                    "direction": "raised",
                    "trend": "FY25 capex $904.6M (historical 1.5-2%) → FY26 guided ~$1.0B (~6% of revenue); revolver upsized $750M to $1.75B in Q1 FY26",
                    "note": "Capex tripling as % of revenue signals management commitment; revolver upsizing enables acquisitive capacity expansion"
                },
                {
                    "area": "margins",
                    "direction": "improving",
                    "trend": "CCS segment margin: 8.0% Q1 25 → 8.4% Q4 FY25 → 8.6% Q1 FY26; ATS 6.0%; adjusted EPS $2.16 beat $1.95-$2.15 guide",
                    "note": "Margin improving alongside volume — operating leverage is building on hyperscaler networking scale"
                },
                {
                    "area": "segments",
                    "direction": "improving",
                    "trend": "FY25: Enterprise -19% on technology transition → Q1 FY26: Enterprise +101% on next-gen AI/ML compute program ramp at same hyperscaler",
                    "note": "The technology-transition drag that hit FY25 enterprise revenue has fully reversed — timing, not permanent impairment"
                }
            ],
            "verdict": "Thesis intact and strongest in the switches/EMS basket — both HPS networking and AI/ML compute programs are accelerating simultaneously, and margin is expanding. The 6% capex commitment is management's highest-conviction signal."
        }

    elif ticker == "CMI":
        return {
            "as_of": TODAY,
            "based_on_accessions": accessions,
            "covers": covers,
            "headline": "Power Systems EBITDA margin surged to 29.5% in Q1 FY26 (from 23.6%) on data-center-driven demand; backlog extends 6-8 quarters — exceptional visibility for an industrial company.",
            "shifts": [
                {
                    "area": "growth",
                    "direction": "accelerating",
                    "trend": "FY25 Power Systems $7.46B (+16%), Power Generation $4.73B (+19%) → Q1 FY26 Power Systems $1.96B (+19%), Power Generation $1.28B (+28%)",
                    "note": "Power Generation re-accelerating QoQ — China and North America adding jointly in Q1"
                },
                {
                    "area": "margins",
                    "direction": "expanding",
                    "trend": "FY25 Power Systems EBITDA margin 22.7% (+4.3pts) → Q1 FY26 Power Systems EBITDA 29.5% (+5.9pts YoY) on volume + pricing leverage",
                    "note": "29.5% EBITDA margin in an industrial power segment is exceptional — data center mix is driving premium pricing and operating leverage"
                },
                {
                    "area": "supply",
                    "direction": "tight",
                    "trend": "FY25: 'strong demand extending 6-8 quarters out' → Q1 FY26: maintained 'strong demand' language for power generation; capacity ramp ongoing",
                    "note": "6-8 quarter backlog language consistent across both filings — supply is being managed carefully to protect pricing"
                },
                {
                    "area": "segments",
                    "direction": "deteriorating",
                    "trend": "FY25: Net income $2.8B vs $3.9B (absence of $1.3B Atmus gain + lower truck demand) → Q1 FY26: Engine segment EBITDA -$179M YoY on lower volumes",
                    "note": "Truck weakness dragging overall results — Power Systems offsetting but not fully compensating for Engine decline"
                },
                {
                    "area": "capex",
                    "direction": "stable",
                    "trend": "FY25: Exiting electrolyzer ($458M Accelera charges) → FY26: Accelera wind-down continues; Power Systems capacity ramp funded via operating cash flow",
                    "note": "Capital redeployed from failed hydrogen to power generation — cost reduction without growth sacrifice"
                }
            ],
            "verdict": "Thesis intact — the data center power generation demand is clearly durable (6-8Q backlog + margin expansion). Truck-cycle weakness is a near-term drag but doesn't touch the AI power thesis."
        }

    elif ticker == "COHR":
        return {
            "as_of": TODAY,
            "based_on_accessions": accessions,
            "covers": covers,
            "headline": "D&C segment growing at 34-41% YoY across two quarters with segment profit +44-49%; portfolio narrowing toward pure AI/datacom optics as industrial/aerospace divestitures complete.",
            "shifts": [
                {
                    "area": "growth",
                    "direction": "accelerating",
                    "trend": "FQ2 26: D&C revenue $1.21B (+34% YoY) → FQ3 26: D&C revenue $1.36B (+41% YoY); 9-month D&C revenue $3.66B (+34%)",
                    "note": "New 'scale across' interconnect demand in Q3 commentary — first explicit naming of inter-DC AI fabric as a growth driver alongside DCI"
                },
                {
                    "area": "margins",
                    "direction": "expanding",
                    "trend": "FQ2 26 gross margin 37% (+140bps) → FQ3 26 gross margin 38% (+243bps); segment profit +44% then +49%",
                    "note": "Margin expanding two quarters in a row on yield improvements and pricing optimization — D&C mix shift doing the heavy lifting"
                },
                {
                    "area": "segments",
                    "direction": "improving",
                    "trend": "FQ2 26: Industrial -10% (aerospace divested Sep 2025) → FQ3 26: Industrial -16% (Munich divested Jan 2026); D&C going from 71% to 75% of revenue",
                    "note": "Portfolio rationalization accelerating — becoming essentially a pure-play AI/datacom optics company"
                },
                {
                    "area": "capital_returns",
                    "direction": "improving",
                    "trend": "FQ2 26: $115M aerospace/defense divestiture gain → FQ3 26: Munich divested, $14M equity investment gain; interest expense falling -$39M YTD on term-loan paydown",
                    "note": "Divestitures funding debt repayment, reducing interest expense and improving FCF conversion"
                }
            ],
            "verdict": "Thesis intact and improving — two consecutive quarters of accelerating D&C growth with margin expansion, while Industrial drag is being sold off. The 'scale across' naming in Q3 extends the AI optics TAM beyond DCI."
        }

    elif ticker == "CRM":
        return {
            "as_of": TODAY,
            "based_on_accessions": accessions,
            "covers": covers,
            "headline": "Agentforce rebranding complete; RPO recovering to $72.4B from Q3's $59.5B as Informatica acquisition adds agentic data layer — operating cash flow $15B confirms durable FCF.",
            "shifts": [
                {
                    "area": "growth",
                    "direction": "accelerating",
                    "trend": "Q3 FY26: RPO $59.5B (down from $63.4B at Jan-25) → FY26 10-K: total RPO $72.4B (+14%), cRPO $35.1B (+16%)",
                    "note": "RPO troughed in Q3 and recovered strongly; cRPO outpacing total RPO signals near-term demand acceleration"
                },
                {
                    "area": "segments",
                    "direction": "improving",
                    "trend": "Q3 FY26: Agentforce 360 Platform/Slack +19% vs other segments +2-9% → FY26 10-K: Informatica ($9.6B deal) adds agentic data management to unified AI/CRM stack",
                    "note": "Agentforce is the only segment with double-digit growth; Informatica creates the data layer needed for agent autonomy"
                },
                {
                    "area": "margins",
                    "direction": "expanding",
                    "trend": "Q3 FY26: operating margin flat ~20% → FY26: operating margin 20% (vs 19%); diluted EPS $7.80 vs $6.36 (+23%); OCF $15.0B (+15%)",
                    "note": "Margin expansion and EPS growth while investing heavily in AI — the restructuring from prior years is paying off"
                },
                {
                    "area": "capital_returns",
                    "direction": "expanding",
                    "trend": "Q3 FY26: cash $11.3B (down from $14.0B) → FY26: $12.7B repurchases + $1.6B dividends from $15.0B OCF",
                    "note": "Capital allocation: aggressive buyback ($12.7B) funded primarily from OCF — no dilution despite Informatica deal"
                },
                {
                    "area": "guidance",
                    "direction": "raising",
                    "trend": "Q3: RPO dip + Agentforce 'relatively new and uncertain' language → FY26: cRPO +16%, Informatica $0.4B contribution, AI narrative firms",
                    "note": "Management risk language softened between Q3 and year-end — confidence in Agentforce monetization increasing"
                }
            ],
            "verdict": "Thesis intact — cRPO recovery to +16% plus $15B OCF confirms durable demand despite the consumption-model uncertainty language. Informatica adds the missing data layer for agentic CRM."
        }

    elif ticker == "CRWV":
        return {
            "as_of": TODAY,
            "based_on_accessions": accessions,
            "covers": covers,
            "headline": "RPO nearly doubled in one quarter to $98.8B as Meta joined Microsoft at scale; Microsoft concentration fell from 67% to 45% — customer diversification structurally improving.",
            "shifts": [
                {
                    "area": "growth",
                    "direction": "accelerating",
                    "trend": "FY25 revenue $5.1B (+168% YoY) → Q1 2026 revenue $2.08B (+112% YoY, annualizing ~$8.3B)",
                    "note": "Growth slightly decelerating (168% to 112%) but still extraordinary; Q1 is not seasonally strong — full-year trajectory likely stronger"
                },
                {
                    "area": "concentration",
                    "direction": "easing",
                    "trend": "FY25: Microsoft 67% of revenue → Q1 2026: Microsoft (Customer A) 45%, Meta (Customer B) 20%; RPO $60.7B → $98.8B",
                    "note": "Diversification is genuine — Meta committed $14.2B through 2031 and is now 20% of quarterly revenue; third customer cohort growing"
                },
                {
                    "area": "leverage",
                    "direction": "deteriorating",
                    "trend": "FY25: total debt $21.6B (vs $8.0B prior year) → Q1 2026 post-quarter: raised additional $7.8B (converts + senior notes + equity)",
                    "note": "Debt cost 9-15% effective rate; $107M interest sensitivity per 100bps; capital intensity is the dominant risk — CRWV is betting on rate environment staying manageable"
                },
                {
                    "area": "capex",
                    "direction": "expanding",
                    "trend": "FY25: capex $10.3B, 850 MW active (vs 360 MW prior year), 3.1 GW total contracted → Q1 2026: committed up to $1.2B for two new DC JV equity stakes",
                    "note": "Power footprint doubling is the operational goal; JV structures distribute some capex off-balance-sheet"
                },
                {
                    "area": "supply",
                    "direction": "tight",
                    "trend": "FY25: deploying NVIDIA GB200/GB300 NVL72 first-to-market → Q1 2026: RPO recognition schedule 36% in first 24 months, 39% in months 25-48",
                    "note": "Long-duration RPO tail (61-100% in years 3-7) means revenue unlock is slow relative to the debt servicing burden in near-term"
                }
            ],
            "verdict": "Thesis intact but high-risk — RPO and customer diversification are tracking well; the $21.6B+ debt load and 9-15% cost of capital are the thesis killers if a major customer delays or defaults."
        }

    elif ticker == "CSCO":
        return {
            "as_of": TODAY,
            "based_on_accessions": accessions,
            "covers": covers,
            "headline": "Networking grew 15-21% YoY across two quarters on AI Infrastructure and Silicon One hyperscaler commitments; Security declined on Splunk cloud shift — mixed portfolio.",
            "shifts": [
                {
                    "area": "growth",
                    "direction": "accelerating",
                    "trend": "Q1 FY26 Networking +15% (+$1.0B) → Q2 FY26 Networking +21% (+$1.4B); 1H FY26 product revenue +12%",
                    "note": "AI Infrastructure and Data Center Switching are the specific growth drivers named explicitly in both quarters"
                },
                {
                    "area": "segments",
                    "direction": "deteriorating",
                    "trend": "Q1 FY26: Security -4% on Splunk cloud shift → Q2 FY26: Security -4% continued; mgmt expects trend to continue 2H FY26",
                    "note": "Security drag from on-prem to cloud-subscription transition is structural, not cyclical — will persist throughout FY26"
                },
                {
                    "area": "supply",
                    "direction": "tightening",
                    "trend": "Q1 FY26: inventory +7%, purchase commitments +10% for Silicon One manufacturing → Q2 FY26: commitment buildup continues; mgmt warns on obsolescence risk",
                    "note": "CSCO is pre-committing to Silicon One capacity for hyperscalers — creates upside if orders land but downside if AI Ethernet vs InfiniBand tilts wrong"
                },
                {
                    "area": "margins",
                    "direction": "stable",
                    "trend": "Q1 FY26 product GM -0.6pts on mix/pricing → Q2 FY26 product GM +0.2pts on productivity; RPO $43.5B relatively stable",
                    "note": "Gross margin volatility is modest; the bigger risk is inventory obsolescence on Silicon One commitments if hyperscaler demand timing slips"
                }
            ],
            "verdict": "Thesis mixed — AI Infrastructure is a real growth driver, but Security decline and Silicon One inventory build-up create two distinct risks. Net thesis depends on AI Ethernet winning hyperscaler wallet share from InfiniBand."
        }

    elif ticker == "ETN":
        return {
            "as_of": TODAY,
            "based_on_accessions": accessions,
            "covers": covers,
            "headline": "Electrical Americas backlog surged to $14.5B (+44% YoY) by Q1 FY26; Boyd Thermal ($9.5B) extends Eaton from power to liquid cooling — 'chip to grid' strategy crystallizing.",
            "shifts": [
                {
                    "area": "supply",
                    "direction": "tightening",
                    "trend": "FY25: backlog $19.8B total, Electrical Americas $13.2B (+31% organic) → Q1 FY26: Electrical Americas backlog $14.5B (+44% YoY, +32% organic); orders +42% organic",
                    "note": "Book-to-bill 1.2x sustained across both quarters — demand exceeding delivery capacity"
                },
                {
                    "area": "growth",
                    "direction": "accelerating",
                    "trend": "FY25: Electrical Americas +16%, Electrical Global +9% → Q1 FY26: Americas +20%, Global +21% on data center across both segments",
                    "note": "Global segment now explicitly calling out data centers as primary growth driver — not just Americas"
                },
                {
                    "area": "capex",
                    "direction": "expanding",
                    "trend": "FY25: acquired Fibrebond + Resilient → Nov 2025: signed $9.5B Boyd Thermal deal (liquid cooling) → Q1 FY26: Boyd closing pending; more data-center M&A flagged",
                    "note": "M&A strategy shifting from pure power to power+cooling — TAM expansion to match HVDC architectures"
                },
                {
                    "area": "margins",
                    "direction": "deteriorating",
                    "trend": "FY25: Electrical Americas operating margin 29.9% (-30bps) → Q1 FY26: Electrical Americas 25.6% (-440bps) on commodity and tariff inflation",
                    "note": "Volume/mix tailwind not enough to offset commodity/tariff headwinds in Q1; 210bps of sales leverage vs 480bps commodity drag"
                }
            ],
            "verdict": "Thesis intact — backlog and order growth confirm multi-year data-center driven demand. Margin compression is the near-term watch item, but the Boyd Thermal deal positions Eaton as the full-stack DC power+cooling provider post-close."
        }

    elif ticker == "FN":
        return {
            "as_of": TODAY,
            "based_on_accessions": accessions,
            "covers": covers,
            "headline": "DCI revenue +90% and HPC +61% in FQ3 26 confirm Fabrinet is riding the 1.6T-cycle and AI scale-across fabric build; customer concentration widened from 2 to 4 customers >10%.",
            "shifts": [
                {
                    "area": "growth",
                    "direction": "accelerating",
                    "trend": "FQ2 26: revenue $1.13B +35.9% YoY → FQ3 26: revenue $1.21B +39.3% YoY; 9M revenue $3.33B +32.5%",
                    "note": "Growth accelerating quarter-over-quarter; DCI is the fastest-growing product line as inter-DC AI fabric ramps"
                },
                {
                    "area": "segments",
                    "direction": "improving",
                    "trend": "FQ2 26: DCI $142.2M, Telecom $412.2M, Datacom $278.1M → FQ3 26: DCI $196.9M (+90.4% YoY), Telecom $431.4M (+42.5%), Datacom $260.4M (flat)",
                    "note": "Datacom flat/declining as mix shifts to higher-speed DCI and Telecom — ASP improvement is happening through product mix"
                },
                {
                    "area": "growth",
                    "direction": "accelerating",
                    "trend": "Non-optical: FQ2 26 $300.3M +61% → FQ3 26 $325.6M +51.7%; HPC $85.6M → $106.7M; Auto $115.5M new disclosure",
                    "note": "HPC revenue (AI merchant silicon co-packaging?) is becoming a disclosed category — optical and non-optical both growing"
                },
                {
                    "area": "concentration",
                    "direction": "tightening",
                    "trend": "FQ2 26: 4 customers >10% (combined 59.1%) vs 2 customers (48.5%) prior year → FQ3 26: same 4-customer pattern",
                    "note": "Concentration normalizing at 4 major optics customers; consolidation risk (Nokia/Infinera + Lumentum acquisitions) flagged by mgmt as structural risk"
                },
                {
                    "area": "capex",
                    "direction": "expanding",
                    "trend": "FQ2 26: $133M Chonburi facility build → FQ3 26: capex up for Chonburi + customer-specific assets; operating cash flow declining on inventory build",
                    "note": "Capacity investment in Thailand to meet DCI demand; inventory build ahead of demand is watch item for FCF conversion"
                }
            ],
            "verdict": "Thesis intact — DCI +90% and Telecom +42% confirm 1.6T cycle is driving real volume, not just anticipation. The HPC line emerging as a new revenue category is incrementally bullish for AI co-packaging exposure."
        }

    elif ticker == "GEV":
        return {
            "as_of": TODAY,
            "based_on_accessions": accessions,
            "covers": covers,
            "headline": "Gas turbine orders: 68 units FY24 → 110 FY25 → 28 Q1 FY26 (run-rate ~112/yr); RPO surged to $163B (+32% YoY), dominated by Gas Power equipment and services.",
            "shifts": [
                {
                    "area": "growth",
                    "direction": "accelerating",
                    "trend": "FY25: Power RPO $94.4B (+29%), total RPO $150.2B (+26%) → Q1 FY26: Power RPO $99.7B (+30% YoY), total RPO $163.3B (+32% YoY)",
                    "note": "RPO acceleration continuing into 2026 — HA-Turbine and Heavy-Duty orders running above trend"
                },
                {
                    "area": "supply",
                    "direction": "tightening",
                    "trend": "FY25: 29.8 GW gas turbine orders, $94.4B Power RPO → Q1 FY26: 8.1 GW orders in one quarter = 32.4 GW annual run-rate; equipment RPO $75.9B vs $64.2B",
                    "note": "Lead times extending on heavy-duty turbines; Prolec GE (transformer JV) adds more supply-chain complexity in Electrification"
                },
                {
                    "area": "margins",
                    "direction": "improving",
                    "trend": "FY25: Power segment EBITDA margin 14.7% (vs 12.5%) → Q1 FY26: Power EBITDA margin 16.3% (vs 11.6% Q1 25)",
                    "note": "Pricing discipline + higher volume driving margin expansion; favorable pricing explicitly called out in Q1 management commentary"
                },
                {
                    "area": "segments",
                    "direction": "improving",
                    "trend": "FY25: First commercial SMR contract via Hitachi JV → Q1 FY26: Electrification RPO benefits from Prolec GE + AC substation/HVDC/synchronous condenser demand",
                    "note": "Electrification segment adding real revenue (Prolec GE) plus HVDC/grid-modernization orders — not just power generation"
                },
                {
                    "area": "capital_returns",
                    "direction": "improving",
                    "trend": "FY25: FCF $3.7B; Fitch BBB+ / S&P BBB upgrades → Q1 FY26: FCF $4.8B (single quarter); Prolec GE acquisition gain $4.7B included",
                    "note": "Prolec gain inflates Q1 FCF — strip it and underlying FCF still substantial on power delivery"
                }
            ],
            "verdict": "Thesis intact and one of the clearest beneficiaries — gas turbine order cadence tripling in 2 years, RPO at $163B growing at 32%, and margin expanding. The direct data center power thesis is explicit in management commentary."
        }

    elif ticker == "GNRC":
        return {
            "as_of": TODAY,
            "based_on_accessions": accessions,
            "covers": covers,
            "headline": "C&I data-center entry proven: Q1 FY26 C&I +28% on data center customers; FY25 was a re-set year for residential — large-megawatt diesel gensets are the new growth vector.",
            "shifts": [
                {
                    "area": "growth",
                    "direction": "accelerating",
                    "trend": "FY25: C&I +4.9% on data center/telecom; large-megawatt diesels launched → Q1 FY26: C&I +28% with core growth 'primarily driven by revenue from global data center customers'",
                    "note": "From a product launch in FY25 to explicit data-center revenue driver in Q1 FY26 — product ramping faster than expected"
                },
                {
                    "area": "segments",
                    "direction": "improving",
                    "trend": "FY25: total sales -2% (residential -6.8% quiet outage season) → Q1 FY26: total sales +12% (residential +1%, C&I +28%)",
                    "note": "Residential stabilized; C&I is now the growth driver — segment reorganization (Residential/C&I from Domestic/International) reflects this strategic shift"
                },
                {
                    "area": "margins",
                    "direction": "improving",
                    "trend": "FY25: adjusted EBITDA margin 17.0% (vs 18.4%) on mix → Q1 FY26: Residential margin 25.1% (+490bps), C&I margin 13.0% (+160bps) on operational efficiencies",
                    "note": "Both segments improving in Q1 — data center pricing and Allmand acquisition accretion lifting C&I; residential efficiency gains"
                },
                {
                    "area": "supply",
                    "direction": "tight",
                    "trend": "FY25: large-megawatt backup generator market 'significantly supply-constrained' → Q1 FY26: Enercon Engineering acquired for hyperscale/enterprise DC custom power",
                    "note": "Acquisition fills manufacturing gap; supply constraint for competitors is GNRC's opportunity to build market share"
                }
            ],
            "verdict": "Thesis intact and improving — the data center C&I pivot is working faster than FY25 suggested. If large-megawatt market stays supply-constrained, GNRC benefits from both volume and pricing as the market builds out."
        }

    elif ticker == "GOOGL":
        return {
            "as_of": TODAY,
            "based_on_accessions": accessions,
            "covers": covers,
            "headline": "Google Cloud re-accelerated to +63% YoY in Q1 2026 (from +36% FY25); RPO leaped from $242.8B to $467.6B in one quarter on multi-GW TPU hardware supply deals — unprecedented backlog build.",
            "shifts": [
                {
                    "area": "growth",
                    "direction": "accelerating",
                    "trend": "FY25: Google Cloud $58.7B (+36% YoY) → Q1 2026: Cloud $20.0B (+63% YoY, annualizing ~$80B)",
                    "note": "Re-acceleration from 36% to 63% is material — TPU hardware supply agreements and Wiz/Intersect integrations are adding to the top line"
                },
                {
                    "area": "margins",
                    "direction": "expanding",
                    "trend": "FY25: Cloud op income $13.9B (24% margin vs $6.1B prior) → Q1 2026: Cloud op income $6.6B (33% margin vs $2.2B prior-year Q1)",
                    "note": "33% Q1 margin vs 24% full-year FY25 — Cloud profitability is accelerating on scale and pricing discipline"
                },
                {
                    "area": "capex",
                    "direction": "raised",
                    "trend": "FY25: capex $91.4B vs $52.5B (FY24); 2026 guide 'significantly increase' → Q1 2026: capex $35.7B alone (run-rate $142B)",
                    "note": "Q1 alone exceeds FY24 capex; the 'significantly increase' language is being delivered — TPU hardware supply deals are the specific use"
                },
                {
                    "area": "supply",
                    "direction": "tightening",
                    "trend": "FY25: RPO $242.8B (primarily Cloud) → Q1 2026: RPO $467.6B (93% Cloud); multi-GW TPU supply agreements disclosed for first time",
                    "note": "TPU hardware supply deals (multi-GW to third-party DCs) are a new business model — GCP supplying compute to rivals' infrastructure"
                },
                {
                    "area": "concentration",
                    "direction": "stable",
                    "trend": "FY25: $32B Wiz + $4.8B Intersect announced → Q1 2026: Wiz closed $29.5B + Intersect $5.9B + $40B committed to private company (OpenAI-scale?)",
                    "note": "$40B commitment to unnamed private company is the most significant undisclosed exposure; if OpenAI analog, it's concentrated AI partner bet"
                }
            ],
            "verdict": "Thesis intact and strongest of the hyperscalers — Cloud re-acceleration to 63% at 33% margin plus the TPU supply deal model creates a new revenue stream beyond traditional PaaS. The $40B unnamed commitment is the undisclosed risk."
        }

    elif ticker == "GFS":
        return {
            "as_of": TODAY,
            "based_on_accessions": accessions,
            "covers": covers,
            "headline": "No summaries yet in filing_summaries.json for GFS — EDGAR not accessible in this environment. No cross_quarter entry generated.",
            "shifts": [],
            "verdict": "Insufficient data."
        }

    elif ticker == "HPE":
        return {
            "as_of": TODAY,
            "based_on_accessions": accessions,
            "covers": covers,
            "headline": "Juniper integration complete — Networking now 29% of revenue at +151.5% YoY in Q1 FY26; AI server growth is real but carries 'limited margins' offsetting the network mix lift.",
            "shifts": [
                {
                    "area": "growth",
                    "direction": "accelerating",
                    "trend": "FY25: Networking +51.1% ($2.3B from Juniper post-7/2/25) → Q1 FY26: Networking +151.5% ($1.6B) as full Juniper quarter included",
                    "note": "Apples-to-apples, Q1 FY26 Networking organic growth is still strong, but the 151% headline is vs only 4 months of Juniper in prior comparable"
                },
                {
                    "area": "margins",
                    "direction": "improving",
                    "trend": "FY25: non-GAAP operating margin 9.8% (-0.7pts, Juniper integration/restructuring) → Q1 FY26: gross margin 35.9% (+670bps); non-GAAP operating margin 12.7% (+280bps)",
                    "note": "Margin recovery faster than expected — Juniper's higher-margin networking software improving the mix significantly"
                },
                {
                    "area": "segments",
                    "direction": "improving",
                    "trend": "FY25: AI Systems 'significant AI backlog' but lumpy → Q1 FY26: Cloud & AI (Server + Storage) -2.7% overall; AI servers growing but GPU-heavy carries 'limited margins'",
                    "note": "AI server growth masked by AUP/volume declines in traditional server; GPU pass-through is margin-dilutive"
                },
                {
                    "area": "capex",
                    "direction": "stable",
                    "trend": "FY25: $13.4B Juniper acquisition + $275M Catalyst restructuring → Q1 FY26: $123M Juniper integration costs; ARR $3.15B (+63%)",
                    "note": "$600M synergy target by FY28 still intact; $800M investment required; integration quarter 2 of ~6-8 expected"
                },
                {
                    "area": "regulation",
                    "direction": "stable",
                    "trend": "FY25: DOJ Juniper divestiture (Instant On + Mist AIOps source-code) → Q1 FY26: IEEPA tariff uncertainty ($15.8B) but SCOTUS challenge active",
                    "note": "Tariff uncertainty is the near-term overhang; DOJ divestitures completed and don't constrain core networking"
                }
            ],
            "verdict": "Thesis intact — Juniper transformed the margin profile (+670bps gross margin in one quarter). AI server growth is real but margin-dilutive; the Networking segment is the thesis, not Server."
        }

    elif ticker == "HUBB":
        return {
            "as_of": TODAY,
            "based_on_accessions": accessions,
            "covers": covers,
            "headline": "Electrical Solutions growing 7-12% organically on datacenter strength in both filings; Utility Solutions adding T&D layer — firm backlog $2.16B entirely shipping in 2026.",
            "shifts": [
                {
                    "area": "growth",
                    "direction": "stable",
                    "trend": "FY25: Electrical Solutions $2.17B (+7.1%, organic +7.2%) on datacenter → Q1 FY26: Electrical Solutions $568M (+11.8%, organic +10.6%) on same driver",
                    "note": "Growth rate improving QoQ — datacenter vertical within Electrical Solutions is the consistent driver"
                },
                {
                    "area": "margins",
                    "direction": "stable",
                    "trend": "FY25: overall adjusted operating margin 22.5% (+80bps) → Q1 FY26: Electrical Solutions -30bps to 16.4%, Utility +190bps to 21.8%; overall +110bps",
                    "note": "Commodity/tariff inflation pressuring Electrical Solutions while Utility holds better — net margin expanding on mix"
                },
                {
                    "area": "supply",
                    "direction": "tight",
                    "trend": "FY25: backlog $2.16B (+14% YoY), 'substantially all to ship in 2026' → Q1 FY26: demand outpacing supply in datacenter vertical",
                    "note": "Short-cycle backlog (all shipping in 2026) is comforting but also means no multi-year visibility — more exposed to demand fluctuation"
                },
                {
                    "area": "capex",
                    "direction": "expanding",
                    "trend": "FY25: $958M deployed on acquisitions → Q1 FY26: further acquisitions not yet disclosed; acquisition program ongoing",
                    "note": "Acquisitive strategy expands product reach into 'high-growth markets' — datacenter is primary target vertical"
                }
            ],
            "verdict": "Thesis intact — datacenter-driven Electrical Solutions growth is consistent and improving QoQ. Short-cycle backlog (no multi-year lock-in) is the risk vs peers like ETN or GEV."
        }

    elif ticker == "INTC":
        return {
            "as_of": TODAY,
            "based_on_accessions": accessions,
            "covers": covers,
            "headline": "Intel Foundry lost $10.3B in FY25 and $2.4B in Q1 FY26 — improving but slowly; DCAI revenue +22% in Q1 on supply-constrained demand demonstrates Products resilience.",
            "shifts": [
                {
                    "area": "growth",
                    "direction": "accelerating",
                    "trend": "FY25: Intel Products $49.1B total, DCAI $14.3B (+$794M YoY) → Q1 2026: DCAI $5.1B (+22% YoY) on 27% higher server ASPs and demand-based pricing",
                    "note": "Supply constraints on Intel 7 creating a paradox: volume -5% but ASP +16-27% from premium mix and demand-based pricing"
                },
                {
                    "area": "supply",
                    "direction": "tightening",
                    "trend": "FY25: Intel 7 constraints hit CCG/DCAI in Q4 → Q1 2026: market demand exceeded available supply; 'most severe' constraints expected H1 2026; substrates and memory shortages added",
                    "note": "Supply constraints are layering — Intel 7 wafers plus now component shortages (substrates, memory); expect pricing to benefit"
                },
                {
                    "area": "segments",
                    "direction": "improving",
                    "trend": "FY25: Intel Foundry $10.3B operating loss; external revenue only $307M → Q1 2026: Foundry revenue $5.4B (+16%) on 18A/Intel 3/Intel 4 wafer volume; external $174M",
                    "note": "Foundry revenue growing from internal mix, not external customers — 18A ramp is accelerating volume but the P&L is still deeply negative"
                },
                {
                    "area": "leverage",
                    "direction": "improving",
                    "trend": "FY25: SoftBank $2.0B + NVIDIA $5.0B equity investments; 159M shares issued to USG at $20 → Q1 2026: Apollo Ireland SCIP buyout completing Q2 2026",
                    "note": "Strategic partners adding balance-sheet support while Foundry losses persist; pause on 14A if no external customer could be value-destructive"
                },
                {
                    "area": "guidance",
                    "direction": "deteriorating",
                    "trend": "FY25: may pause/discontinue Intel 14A if no significant external foundry customer → Q1 2026: same language; no 14A external customer announced",
                    "note": "No progress on 14A external customer in either filing — if pause announced, Intel 18A becomes the last leading-edge node for the foundry"
                }
            ],
            "verdict": "Thesis uncertain — Products segment is benefiting from supply-induced price discipline (a positive), but Foundry is burning $2-3B/quarter with no clear external revenue path. The 14A pause risk is an existential strategic question for foundry credibility."
        }

    elif ticker == "KLAC":
        return {
            "as_of": TODAY,
            "based_on_accessions": accessions,
            "covers": covers,
            "headline": "Revenue grew from $3.30B to $3.42B with memory/HBM the primary driver; China fell from 30% to 24% of revenue while Korea jumped 80% — geographic reorientation accelerating.",
            "shifts": [
                {
                    "area": "growth",
                    "direction": "accelerating",
                    "trend": "Q2 FY26: revenue $3.30B (+7% YoY) → Q3 FY26: revenue $3.42B (+11% YoY) — record quarter; Korea +80%, North America +40%",
                    "note": "Growth rate improving from 7% to 11% as HBM/DRAM investment intensifies; services +18% in Q2, +16% in Q3 — recurring revenue growing faster"
                },
                {
                    "area": "china",
                    "direction": "deteriorating",
                    "trend": "Q2 FY26: China $995M (30.2% of total, -9% YoY) → Q3 FY26: China $830M (24% of revenue, +5% YoY); nine-month China flat at $3.09B",
                    "note": "China share declining quarter-by-quarter from 30% to 24%; US export controls are the structural driver"
                },
                {
                    "area": "segments",
                    "direction": "improving",
                    "trend": "Q2 FY26: memory/DRAM-led-by-HBM + advanced packaging → Q3 FY26: same drivers with 'steady foundry/logic' added; Korea +80% on memory intensity",
                    "note": "Foundry/logic was weaker in Q2 but stabilized in Q3 — less dependent on China advanced foundry now"
                },
                {
                    "area": "margins",
                    "direction": "stable",
                    "trend": "Q2 FY26: gross margin 61.4% (+1.1pts) → Q3 FY26: gross margin 61.1% (-0.5pts QoQ) on escalating DRAM chip costs in image computers (transitory per mgmt)",
                    "note": "Two consecutive periods of DRAM cost pressure on image computers — mgmt flags as transitory; watch Q4"
                },
                {
                    "area": "capital_returns",
                    "direction": "raising",
                    "trend": "Q2 FY26: $548M repurchases + $250M dividends; 16th consecutive annual dividend increase → Q3 FY26: $626M repurchases + $249M dividends + $7B new authorization; 17th consecutive annual dividend increase",
                    "note": "Capital return cadence accelerating even as revenue grows — management confidence in cycle durability is high"
                }
            ],
            "verdict": "Thesis intact — memory/HBM investment cycle is driving both revenue growth and geographic reorientation away from China. DRAM cost headwind is transitory; capital returns accelerating signals durable cash generation."
        }

    elif ticker == "LEU":
        return {
            "as_of": TODAY,
            "based_on_accessions": accessions,
            "covers": covers,
            "headline": "Backlog grew from $3.8B to $3.9B (LEU $3.1B incl $2.4B contingent); JV with Oklo on HALEU deconversion signals nuclear fuel supply chain integration deepening.",
            "shifts": [
                {
                    "area": "growth",
                    "direction": "accelerating",
                    "trend": "FY25: $900M HALEU task order won Jan 2026 → Q1 FY26: Technical Solutions $32.1M (+47% YoY); Piketon EPC contract signed Feb 2026",
                    "note": "HALEU revenues growing faster than LEU — the nascent growth engine is Technical Solutions (government-funded HALEU)"
                },
                {
                    "area": "supply",
                    "direction": "tightening",
                    "trend": "FY25: SWU spot price $200 (vs $34 2018 historic low, +488%) → Q1 FY26: price held at $200; Oak Ridge centrifuge manufacturing began Dec 2025",
                    "note": "Supply tightness is structural (Russian enrichment ban, global undersupply) — Centrus is the only NRC-licensed HALEU producer"
                },
                {
                    "area": "concentration",
                    "direction": "easing",
                    "trend": "FY25: backlog extends to 2040 with mostly utility customers → Q1 FY26: Oklo JV for HALEU deconversion + Piketon co-location with Meta-backed nuclear campus",
                    "note": "From utility-only customers to nuclear renaissance ecosystem participant (Oklo, Meta indirectly via Oklo Meta deal)"
                },
                {
                    "area": "leverage",
                    "direction": "improving",
                    "trend": "FY25: new Oak Ridge centrifuge manufacturing ($560M+ multi-year) → Q1 FY26: Aug 2025 issued $805M 0% convertibles; redeemed $74.3M high-cost notes",
                    "note": "Debt refinanced from 8.25% to 0% convert — meaningful improvement in cost of capital for the expansion program"
                },
                {
                    "area": "capex",
                    "direction": "expanding",
                    "trend": "FY25: $62.4M IRS §48C credit allocated → Q1 FY26: Fluor Federal Services EPC contract (T&M) for Piketon; advanced technology costs +530% YoY to $18.9M",
                    "note": "Expansion spending accelerating sharply — Piketon and Oak Ridge simultaneously ramping up"
                }
            ],
            "verdict": "Thesis intact — Centrus is positioned at the intersection of the nuclear renaissance (SMR HALEU fuel) and data-center power (Meta-backed Oklo as downstream customer). $3.9B backlog and $200 SWU price confirm structural supply tightness."
        }

    elif ticker == "LITE":
        return {
            "as_of": TODAY,
            "based_on_accessions": accessions,
            "covers": covers,
            "headline": "Revenue nearly doubled from FQ2 to FQ3 on a per-unit basis ($665M → $808M); gross margin expanded 1,540bps in FQ3 as supply allocation tightens language and 1.6T mix pays off.",
            "shifts": [
                {
                    "area": "growth",
                    "direction": "accelerating",
                    "trend": "FQ2 26: revenue $665.5M +65.5% YoY → FQ3 26: revenue $808.4M +90.1% YoY; 9M revenue $2.01B +72.4%",
                    "note": "Growth rate re-accelerating — Q3 marked the highest quarterly growth rate, driven by cloud transceiver volume and OCS initial ramp"
                },
                {
                    "area": "margins",
                    "direction": "expanding",
                    "trend": "FQ2 26: gross margin 36.1% (+1,130bps YoY) → FQ3 26: gross margin 44.2% (+1,540bps YoY); 9M 38.8% (+1,300bps)",
                    "note": "Margin expansion is compounding quarter over quarter — supply allocation at 200G-lane speeds is commanding premium ASPs"
                },
                {
                    "area": "supply",
                    "direction": "tightening",
                    "trend": "FQ2 26: 'demand outpacing supply — has led to decisions on supply allocation' → FQ3 26: 'demand outpacing supply — has required us to make decisions on supply allocation' (language hardened)",
                    "note": "Language sharpened from 'led to' to 'required' — allocation decisions are now unavoidable, not discretionary"
                },
                {
                    "area": "segments",
                    "direction": "improving",
                    "trend": "FQ2 26: Components +68.3%, Systems +60.1% → FQ3 26: Components +77.3%, Systems +121.1%; OCS contributing >$25M in Q3 vs >$10M in Q2",
                    "note": "Systems growing faster than Components for first time — cloud transceivers and OCS (optical circuit switches) compounding"
                },
                {
                    "area": "concentration",
                    "direction": "tightening",
                    "trend": "FQ2 26: 2 customers at 24% and 17% (combined 41%) → FQ3 26: 2 customers at 26% and 12% (top customer up from 24%)",
                    "note": "Top customer increasing share — reflects hyperscaler-direct relationship deepening as 1.6T/200G-lane supply tightens"
                }
            ],
            "verdict": "Thesis intact and improving sharply — LITE is the InP/EML supply choke point for 1.6T transceivers, and both supply allocation language hardening and margin expansion of 1,540bps confirm it. This is the best evidence of structural repricing in the optics stack."
        }

    elif ticker == "LRCX":
        return {
            "as_of": TODAY,
            "based_on_accessions": accessions,
            "covers": covers,
            "headline": "DRAM investment surge lifted memory to 39% of mix from 34% in one quarter; revenue grew from $5.34B to $5.84B as DRAM customer investments drove a 9% sequential increase.",
            "shifts": [
                {
                    "area": "growth",
                    "direction": "accelerating",
                    "trend": "Q2 FY26: revenue $5.34B (+25% YoY first-half) → Q3 FY26: revenue $5.84B (+9% QoQ); nine-month $16.51B vs $13.26B (+24%)",
                    "note": "Re-acceleration driven by DRAM customer investments in Q3; six-month base already up 25% — the compounding continues"
                },
                {
                    "area": "segments",
                    "direction": "improving",
                    "trend": "Q2 FY26: Memory 34% of mix, Foundry 59% → Q3 FY26: Memory 39% (+5pts), Foundry 54% (-5pts) on DRAM strengthening and lower mature node foundry",
                    "note": "DRAM/HBM mix rising as HBM technology transition investment intensifies; foundry mature node slipping"
                },
                {
                    "area": "china",
                    "direction": "stable",
                    "trend": "Q2 FY26: China 35% of revenue → Q3 FY26: China 34%; Korea jumped from 20% to 23%; Taiwan 23% in both",
                    "note": "China mix relatively stable at 34-35% vs KLAC/AMAT where China is declining — LRCX's China exposure less export-control-sensitive for now"
                },
                {
                    "area": "margins",
                    "direction": "stable",
                    "trend": "Q2 FY26: gross margin 49.6% (down from 50.4%) → Q3 FY26: gross margin 49.8% (+0.2pts) on better factory efficiencies",
                    "note": "Modest recovery; China mix slightly declining, Korea rising — geographic mix improved margin by 0.2pts"
                },
                {
                    "area": "capital_returns",
                    "direction": "raising",
                    "trend": "Q3 FY26: $1.16B repurchases + $326M dividends + $751M debt paydown; cash $4.77B from $6.20B",
                    "note": "Aggressive capital return + debt paydown simultaneously; cash declining but balance sheet remains strong"
                }
            ],
            "verdict": "Thesis intact — DRAM/HBM investment cycle is pulling LRCX's mix toward memory and generating above-trend revenue. China exposure stable (not declining like peers). Capital return cadence strong."
        }

    elif ticker == "META":
        return {
            "as_of": TODAY,
            "based_on_accessions": accessions,
            "covers": covers,
            "headline": "FY26 capex guidance raised 9-12% from $115-135B to $125-145B just one quarter after initial guidance; Q1 ad revenue +33% justifies the investment pace.",
            "shifts": [
                {
                    "area": "capex",
                    "direction": "raised",
                    "trend": "FY25 capex $72.2B → FY26 initial guide $115-135B → FY26 raised to $125-145B (one quarter later); Q1 2026 capex $19.8B run-rate = $79B annual",
                    "note": "Guidance raised within one quarter of issuance — management underestimated AI infrastructure demand; actual Q1 run-rate implies $145B is the floor, not the midpoint"
                },
                {
                    "area": "growth",
                    "direction": "accelerating",
                    "trend": "FY25 revenue $201.0B (+22%), ad impressions +12%, price +9% → Q1 2026 revenue $56.3B (+33%), ad impressions +19%, price +12%",
                    "note": "Re-acceleration in both revenue and underlying ad metrics — AI-driven ad targeting is working; Llama/Advantage+ showing ROI"
                },
                {
                    "area": "leverage",
                    "direction": "stable",
                    "trend": "FY25: $29.9B senior notes issued Nov 2025 → Q1 2026: $237.7B non-cancelable commitments; $42.3B due 2026, $47.7B in 2027; $182.9B off-balance-sheet leases",
                    "note": "Commitment stack is enormous — Meta is the largest buyer of AI infrastructure among the hyperscalers by disclosed contractual obligation"
                },
                {
                    "area": "segments",
                    "direction": "deteriorating",
                    "trend": "FY25: RL operating loss $19.2B; 2026 expected 'similar' → Q1 2026: RL operating loss $4.03B (annualizing $16.1B, slightly below $19.2B)",
                    "note": "RL losses tracking slightly below FY25 annualization — still enormous; not a near-term catalyst to fix"
                },
                {
                    "area": "margins",
                    "direction": "stable",
                    "trend": "FY25: total operating margin ~41% → Q1 2026: FoA operating margin higher (RL $4B loss vs $4.8B Q1 25); overall operating income $22.9B (+30%)",
                    "note": "Core FoA business margin expanding while RL losses are below prior-year run-rate; net effect is margin improvement"
                }
            ],
            "verdict": "Thesis intact — Meta is the most aggressive AI infrastructure investor among hyperscalers and the ad revenue acceleration justifies it. The commitment stack and capex raise within one quarter suggest AI ROI is landing faster than expected."
        }

    elif ticker == "MOD":
        return {
            "as_of": TODAY,
            "based_on_accessions": accessions,
            "covers": covers,
            "headline": "Climate Solutions data center revenue grew $130M in Q3 FY26; Reverse Morris Trust spin announced Jan 2026 creates a pure-play DC cooling company — the portfolio rationalization is complete.",
            "shifts": [
                {
                    "area": "growth",
                    "direction": "accelerating",
                    "trend": "Q2 FY26: Climate Solutions data center +$67.4M YoY, segment +24% → Q3 FY26: data center +$130.0M, Climate Solutions +51%; 9M data center +$221.7M",
                    "note": "Data center growth doubling quarter-over-quarter — hyperscale and colocation demand in NA and Europe driving the acceleration"
                },
                {
                    "area": "segments",
                    "direction": "improving",
                    "trend": "Q2 FY26: Performance Technologies -4% drag → Q3 FY26: RMT announced (Jan 2026), Gentherm merger; Modine retains Climate Solutions",
                    "note": "Portfolio rationalization complete — Modine becomes pure-play DC cooling + commercial HVAC after close in CY26"
                },
                {
                    "area": "margins",
                    "direction": "deteriorating",
                    "trend": "Q2 FY26: Climate Solutions margin 13.7% (vs 17.6%) on rapid US capacity ramp → Q3 FY26: Climate Solutions margin 15.3% (vs 17.3%) still pressured",
                    "note": "Margin drag from rapid capacity expansion persisting — at some point capacity investment becomes efficient; Q3 slightly better than Q2"
                },
                {
                    "area": "capex",
                    "direction": "expanding",
                    "trend": "Q2 FY26: $59.4M capex 1H FY26; announced incremental $100M over next 12mo for US DC capacity → Q3 FY26: new DC manufacturing lease signed",
                    "note": "$100M incremental commitment reflects management confidence that data center demand will sustain the capacity build"
                }
            ],
            "verdict": "Thesis intact — data center cooling demand is accelerating and the RMT creates a pure-play to capture the full valuation. Margin pressure during ramp is transitory; the strategic clarity is the main catalyst."
        }

    elif ticker == "MRVL":
        return {
            "as_of": TODAY,
            "based_on_accessions": accessions,
            "covers": covers,
            "headline": "Data center revenue grew from $1.52B (73% of mix, +38% YoY) in Q3 FY26 to $6.1B FY26 total (+46% YoY); Celestial AI and XConn acquired post-year-end for photonic fabric and CXL/PCIe.",
            "shifts": [
                {
                    "area": "growth",
                    "direction": "accelerating",
                    "trend": "Q3 FY26: DC $1.52B (+38% YoY, 73% of mix) → FY26: DC $6.1B (+46% YoY, 74% of mix); Communications recovering from -neg prior year",
                    "note": "Acceleration from 38% to 46% on an annual basis — custom AI ASIC ramps are compounding within the hyperscaler deployment cycle"
                },
                {
                    "area": "margins",
                    "direction": "improving",
                    "trend": "Q3 FY26: gross margin 51.6% (vs 23.0% prior-year, which had $356.8M restructuring impairment) → FY26: gross margin 51.0% vs 41.3% prior year (+9.7pts, stripping restructuring)",
                    "note": "Structural margin improvement of ~10pts — mix shift to custom AI ASICs driving premium gross margins on silicon photonics + compute"
                },
                {
                    "area": "concentration",
                    "direction": "tightening",
                    "trend": "Q3 FY26: one Distributor A = 38% of revenue → FY26: Distributor A = 37%, Direct Customer A = 14% of revenue; top-10 ~81%",
                    "note": "37-38% distributor concentration is effectively single-hyperscaler concentration — the distributor is acting as an intermediary for a hyperscaler XPU buyer"
                },
                {
                    "area": "capex",
                    "direction": "expanding",
                    "trend": "Q3 FY26: announced Celestial AI ($5.5B max) → FY26: closed Celestial (~$1.3B cash + 24.5M shares) + XConn ($280M + 2.1M shares) post-year-end",
                    "note": "Two acquisitions in one month — photonic fabric (scale-up) and CXL/PCIe switching (scale-out) complete the AI interconnect portfolio"
                },
                {
                    "area": "china",
                    "direction": "stable",
                    "trend": "Q3 FY26: shipment destination China 40% (non-China end-customers) → FY26: export restrictions on certain Chinese customers expected to continue",
                    "note": "China shipment destination high but end-customer exposure lower — hyperscaler ASICs shipped via Asian distribution, not direct China sales"
                }
            ],
            "verdict": "Thesis intact and portfolio strengthened — photonic fabric (Celestial) + CXL switching (XConn) means MRVL now covers the full custom AI interconnect stack. Distributor concentration at 37% is the critical risk to monitor."
        }

    elif ticker == "MSFT":
        return {
            "as_of": TODAY,
            "based_on_accessions": accessions,
            "covers": covers,
            "headline": "Azure accelerated from +39% to +40% YoY in Q3 FY26; commercial RPO held at $625-627B; 9M FY26 capex hit $80.1B vs $40.9B prior year — AI infrastructure spend running 2x.",
            "shifts": [
                {
                    "area": "growth",
                    "direction": "accelerating",
                    "trend": "Q2 FY26: Azure +39% → Q3 FY26: Azure +40%; Cloud revenue $51.5B (+26%) → $54.5B (+29%); 9M cloud revenue $155.1B (+27%)",
                    "note": "Re-acceleration in Q3 after Q2 set the baseline — OpenAI partnership extensions and multi-year cloud deals pulling forward"
                },
                {
                    "area": "capex",
                    "direction": "raised",
                    "trend": "Q2 FY26: capex $29.9B (+89% YoY); H1 total $49.3B → Q3 FY26: capex $30.9B; 9M total $80.1B vs $40.9B (+96%)",
                    "note": "Capex doubling YoY is structural — OpenAI partnership (extended Oct 2025) and multi-year Azure commitments are the demand signal"
                },
                {
                    "area": "margins",
                    "direction": "deteriorating",
                    "trend": "Q2 FY26: Microsoft Cloud gross margin 67% on AI infrastructure investments → Q3 FY26: no change in direction; $5.9B OpenAI recapitalization gain partially offsets",
                    "note": "Gross margin pressure from AI infrastructure is structural while capex ramp continues; the $5.9B OpenAI gain is non-recurring"
                },
                {
                    "area": "supply",
                    "direction": "tightening",
                    "trend": "Q2 FY26: commercial RPO $625B (+110% YoY) → Q3 FY26: commercial RPO $627B (+99% YoY); 25% to recognize next 12 months in both periods",
                    "note": "RPO growth rate moderating slightly (110% to 99%) but absolute level stable at $625-627B — huge locked demand"
                },
                {
                    "area": "concentration",
                    "direction": "stable",
                    "trend": "Q2 FY26: new OpenAI definitive agreement signed Oct 2025 → Q3 FY26: $5.9B 9M OpenAI recapitalization dilution gain (OpenAI becoming public benefit corp)",
                    "note": "OpenAI structural relationship becoming more complex — dilution gain on recapitalization suggests Microsoft retains equity as OpenAI restructures"
                }
            ],
            "verdict": "Thesis intact — Azure +40% re-acceleration with $80B 9M capex confirms Microsoft is the largest AI infrastructure spender. The commercial RPO at $627B provides multi-year revenue visibility; Cloud gross margin compression is the only risk item."
        }

    elif ticker == "MU":
        # Already exists in cross_quarter.json — preserve it (no new filings to trigger update)
        return None

    elif ticker == "MXL":
        return {
            "as_of": TODAY,
            "based_on_accessions": accessions,
            "covers": covers,
            "headline": "Revenue recovered from $467.6M FY25 to $137.2M in Q1 26 (+43% YoY); customer concentration broadened while infrastructure optical DSPs and broadband drive both periods.",
            "shifts": [
                {
                    "area": "growth",
                    "direction": "accelerating",
                    "trend": "FY25: revenue $467.6M +30% (recovery from prior-year trough); Broadband +59% → Q1 26: revenue $137.2M +43% YoY; Infrastructure +$36.3M",
                    "note": "Infrastructure growth in Q1 26 confirms optical DSP demand is real, not just a FY25 inventory restocking"
                },
                {
                    "area": "concentration",
                    "direction": "easing",
                    "trend": "FY25: top customer >20%, top-10 = 65%, 82% Asia shipments → Q1 26: top customer 13%, top-10 = 56%",
                    "note": "Remarkable diversification in one quarter — either customer mix genuinely broadening or FY25 top customer restocking completed"
                },
                {
                    "area": "segments",
                    "direction": "improving",
                    "trend": "FY25: Industrial/multi-market -$37.0M (cyclical retracement) → Q1 26: Industrial +$3.9M recovery; Broadband both periods growing",
                    "note": "Industrial cyclical trough behind us; Broadband (49% → steady) and Infrastructure (optical DSPs) as dual growth pillars"
                },
                {
                    "area": "supply",
                    "direction": "stable",
                    "trend": "FY25: describes 400G → 800G → 1.6T (1600Gbps) switch interconnect transition as optical DSP roadmap → Q1 26: volume-led growth confirms traction",
                    "note": "800G to 1.6T cycle is the structural demand driver — each speed generation refresh is a new MXL content opportunity"
                },
                {
                    "area": "margins",
                    "direction": "improving",
                    "trend": "FY25: gross margin 57% (+3pts) on mix and lower intangible amortization → Q1 26: volume-led growth implies continued margin support",
                    "note": "R&D -7% in FY25 (workforce reductions) — mgmt flagged need to re-expand for next-gen products; R&D investment may pick up in FY26"
                }
            ],
            "verdict": "Thesis intact — optical DSP and broadband recovery are confirmed across both periods. The concentration normalization in Q1 26 is a positive structural shift. 1.6T cycle timing is the key watchlist item."
        }

    elif ticker == "NOW":
        return {
            "as_of": TODAY,
            "based_on_accessions": accessions,
            "covers": covers,
            "headline": "RPO grew consistently at +25-27% YoY across FY25 and Q1 2026; Now Assist AI agent deployment is now embedded across 9+ product lines — consumption-based monetization ramping.",
            "shifts": [
                {
                    "area": "growth",
                    "direction": "accelerating",
                    "trend": "FY25: revenue $13.28B (+21% YoY), cRPO +25% → Q1 2026: revenue $3.77B (+22% YoY), cRPO +23% YoY",
                    "note": "Growth rate holding in 21-22% range across both periods — exceptional consistency for a $13B+ software company"
                },
                {
                    "area": "supply",
                    "direction": "stable",
                    "trend": "FY25: RPO $28.2B (+27%), cRPO 46% of RPO → Q1 2026: RPO $27.7B (+25%), cRPO 46%; weighted avg contract stable",
                    "note": "RPO slightly down QoQ from FY25 YE — normal Q1 timing as renewals concentrate at year-end; cRPO ratio unchanged"
                },
                {
                    "area": "segments",
                    "direction": "improving",
                    "trend": "FY25: Now Assist deployed across ITSM/ITOM/CSM/HRSD/FSM/SecOps/RM/SPM/Industry → Q1 2026: same breadth; $83M federal on-prem increase in FY25 as US government customers demand self-hosted",
                    "note": "Federal on-prem demand growing — government AI deployment is a new vector on top of commercial SaaS"
                },
                {
                    "area": "capital_returns",
                    "direction": "stable",
                    "trend": "FY25: no buyback detail given → Q1 2026: subscription gross margin slightly pressured by self-hosted mix; professional services +19%",
                    "note": "Self-hosted revenue ($157M Q1 25 → $138M Q1 26, slight decline) suggests one-time federal surge in FY25 is normalizing"
                }
            ],
            "verdict": "Thesis intact — consistent 21-22% growth with Now Assist embedded across 9+ product lines and federal on-prem as a new demand vector. Consumption monetization of AI agents is early-stage but the distribution is already in place."
        }

    elif ticker == "NVT":
        return {
            "as_of": TODAY,
            "based_on_accessions": accessions,
            "covers": covers,
            "headline": "Systems Protection segment +76% YoY in Q1 FY26 with 46pts of organic data-center-driven infrastructure growth; Avail EPG acquisition contributes $137M in first full quarter.",
            "shifts": [
                {
                    "area": "growth",
                    "direction": "accelerating",
                    "trend": "FY25: Systems Protection +42.2% (organic ~17%) on data centers → Q1 FY26: Systems Protection +76.1% (organic +50.1%); Electrical Connections +9.9% → +15.3%",
                    "note": "Organic growth accelerating from 17% to 50% in one quarter — data center demand is pulling harder, not just Avail EPG contribution"
                },
                {
                    "area": "capex",
                    "direction": "expanding",
                    "trend": "FY25: closed Avail EPG ($1.0B, May 2025), divested Thermal Management ($1.6B, Jan 2025) → Q1 FY26: EPG contributed $121M in Systems Protection; ongoing acquisition program",
                    "note": "Divesting non-core (Thermal) while adding enclosures/liquid-cooling (EPG) — portfolio focusing on AI infrastructure"
                },
                {
                    "area": "margins",
                    "direction": "deteriorating",
                    "trend": "FY25: Systems Protection margin 20.7% (-1.4pts on capacity investment) → Q1 FY26: Systems Protection margin 22.7% (+220bps) despite tariff/material headwinds; consolidated GM -290bps",
                    "note": "Segment margin improving (volume leverage > cost pressure) but consolidated gross margin declining on tariff and raw materials"
                },
                {
                    "area": "supply",
                    "direction": "stable",
                    "trend": "FY25: backlog $2.3B driven by Avail EPG + data center → Q1 FY26: data center megatrends expected to continue driving sales growth through 2026 and beyond",
                    "note": "No specific backlog update in Q1 but management continues megatrend language — suggests order intake remained solid"
                },
                {
                    "area": "capital_returns",
                    "direction": "raising",
                    "trend": "FY25: returned ~$383M (buybacks + dividends) → Q1 2026: dividend raised to $0.21/share (Feb 16 announcement); buyback ongoing",
                    "note": "Dividend increase signals management confidence in data-center demand durability"
                }
            ],
            "verdict": "Thesis intact — Systems Protection organic growth of 50% in one quarter is the strongest evidence yet that data-center enclosures and liquid cooling are genuinely supply-constrained. Avail EPG accretion adds to the organic tailwind."
        }

    elif ticker == "NVDA":
        # Already exists in cross_quarter.json — preserve it (no new filings to trigger update)
        return None

    elif ticker == "OKLO":
        return {
            "as_of": TODAY,
            "based_on_accessions": accessions,
            "covers": covers,
            "headline": "Meta prepayment agreement for 1.2 GW (Jan 2026) validates the business model; order book at 18,100 MWe — but FY25 opex $139M (vs $52.8M) and FY26 burn $80-100M signal significant pre-revenue spend.",
            "shifts": [
                {
                    "area": "growth",
                    "direction": "accelerating",
                    "trend": "Q3 FY25: order book ~18,100 MWe (+2,500% since 2023 SPAC) → FY25 10-K: Meta prepayment agreement Jan 2026 for 1.2 GW Pike County, Ohio power campus",
                    "note": "First hyperscaler prepayment for advanced fission — Meta's $$ gives Oklo cash to advance development, not just LOIs"
                },
                {
                    "area": "leverage",
                    "direction": "deteriorating",
                    "trend": "Q3 FY25: 9M net loss $64.2M; raised $968M in 9M financing → FY25: opex $139.3M (+164% YoY); FY26 guided $80-100M opex + $350-450M capex",
                    "note": "Burn is accelerating pre-revenue — the $350-450M FY26 capex (vs virtually zero FY25) reflects land + design investment"
                },
                {
                    "area": "supply",
                    "direction": "improving",
                    "trend": "Q3 FY25: NRC Phase I readiness assessment complete; PDC topical report accepted → FY25: DOE safety design agreement approved Feb 2026; NRC engagement continuing",
                    "note": "Regulatory milestones advancing on schedule — each NRC approval step is a de-risking event for first powerhouse timeline"
                },
                {
                    "area": "capex",
                    "direction": "expanding",
                    "trend": "Q3 FY25: $968M raised via offerings → FY25: Dec 2025 ATM $300M; Pike County Ohio land acquired; $350-450M FY26 capex guided",
                    "note": "Capital formation front-loading ahead of commercial deployment — equity dilution is the mechanism"
                }
            ],
            "verdict": "Thesis intact as an option play — Meta prepayment is a meaningful de-risking event, but this is still a pre-revenue company with a 2028+ commercial timeline. The JV with LEU on HALEU deconversion adds technical credibility."
        }

    elif ticker == "ORCL":
        return {
            "as_of": TODAY,
            "based_on_accessions": accessions,
            "covers": covers,
            "headline": "OCI cloud infrastructure grew from +68% to +84% YoY across two quarters; RPO surged from $523B to $552B to $625B — three sequential quarters of unprecedented cloud contract backlog build.",
            "shifts": [
                {
                    "area": "growth",
                    "direction": "accelerating",
                    "trend": "Q2 FY26: OCI $4.08B (+68% YoY) → Q3 FY26: OCI $4.89B (+84% YoY, +81% constant currency); total revenue +14% → +22%",
                    "note": "Cloud infrastructure re-accelerating each quarter — AI workload demand is driving OCI faster than Oracle's traditional apps business"
                },
                {
                    "area": "supply",
                    "direction": "tightening",
                    "trend": "Q2 FY26: RPO $523.3B (vs $97.3B prior year, 5.4x leap) → Q3 FY26: RPO $552.6B (vs $130.2B, 4.2x); H1 capex $20.5B vs $6.3B (3.2x)",
                    "note": "RPO growth decelerating in multiple (5.4x → 4.2x) as base grows, but absolute additions still $100B+ — backlog is compounding"
                },
                {
                    "area": "capex",
                    "direction": "raised",
                    "trend": "H1 FY26: capex $20.5B vs $6.3B → 9M FY26: capex $39.2B vs $12.1B (3.2x); issued $42.7B senior notes + $5B mandatory converts",
                    "note": "Oracle is debt-funding the capex build at scale — $42.7B debt issuance in FY26 is historically unprecedented for the company"
                },
                {
                    "area": "leverage",
                    "direction": "deteriorating",
                    "trend": "Q2 FY26: issued $17.9B senior notes Sep 2025, sold Ampere stake for $4.3B → Q3 FY26: issued further debt + $5B mandatory converts + ATM offering program",
                    "note": "Balance sheet increasingly levered to fund OCI build-out; 9M operating margin declining as infrastructure spend ramps"
                },
                {
                    "area": "margins",
                    "direction": "deteriorating",
                    "trend": "Q2 FY26: cloud/software segment expenses +49%; margin pressure beginning → Q3 FY26: 9M operating margin declining on infrastructure spending",
                    "note": "Scale diseconomies during the OCI ramp phase; management expects margin recovery at scale but near-term is compressed"
                }
            ],
            "verdict": "Thesis intact — OCI is the fastest-growing cloud platform in the large-cap hyperscaler basket and AI demand is pulling the +84% growth rate. Leverage is the main risk: $42.7B debt issuance with compressing margins is manageable only if OCI growth sustains."
        }

    elif ticker == "PLTR":
        return {
            "as_of": TODAY,
            "based_on_accessions": accessions,
            "covers": covers,
            "headline": "Revenue growth re-accelerated from +53% FY25 to +85% Q1 2026 YoY; commercial outpacing government with +95% vs +76% growth; operating margin expanded to 46% from 20%.",
            "shifts": [
                {
                    "area": "growth",
                    "direction": "accelerating",
                    "trend": "FY25: revenue $4.5B (+53% YoY); commercial +60%, government +53% → Q1 2026: revenue $1.63B (+85% YoY); commercial +95%, government +76%",
                    "note": "Re-acceleration massive — Q1 85% YoY vs FY25 53% suggests the AIP/Foundry enterprise deployment wave is accelerating, not decelerating"
                },
                {
                    "area": "margins",
                    "direction": "expanding",
                    "trend": "FY25: income from ops $1.41B (31% operating margin, 4.5x YoY) → Q1 2026: income from ops $754M (46% operating margin, +328% YoY)",
                    "note": "Operating leverage compressing dramatically — fixed cost base means incremental revenue drops at very high margins (87% gross margin)"
                },
                {
                    "area": "segments",
                    "direction": "improving",
                    "trend": "FY25: commercial $2.07B (46% of total) vs government $2.40B (54%) → Q1 2026: commercial $774M vs government $858M; commercial contribution margin 73% vs gov 73%",
                    "note": "Commercial narrowing the gap with government — both segments now at equal contribution margins after commercial was lower historically"
                },
                {
                    "area": "concentration",
                    "direction": "easing",
                    "trend": "FY25: no customer >10% of revenue → Q1 2026: no customer >10% of Q1 26 or Q1 25 revenue",
                    "note": "Consistent no-concentration-risk disclosure — revenue is genuinely diversified across 100s of enterprise/government customers"
                },
                {
                    "area": "growth",
                    "direction": "accelerating",
                    "trend": "FY25: US 74%, international 26% → Q1 2026: US 79% ($1.28B), UK $130M, RoW $220M; US accelerating faster than international",
                    "note": "US concentration increasing on government contract wins and domestic enterprise AIP bootcamp momentum"
                }
            ],
            "verdict": "Thesis intact and the strongest print in the software basket — 85% YoY re-acceleration with 46% operating margin is exceptional for any software company. The commercial/government parity in contribution margins eliminates the prior concern about commercial profitability."
        }

    elif ticker == "PWR":
        return {
            "as_of": TODAY,
            "based_on_accessions": accessions,
            "covers": covers,
            "headline": "Backlog reached $48.47B (+10% sequential) by Q1 FY26, up from $43.98B at YE25; RPO growing faster than backlog signals pull-forward of long-cycle data-center-driven contracts.",
            "shifts": [
                {
                    "area": "growth",
                    "direction": "accelerating",
                    "trend": "FY25: revenues $28.5B (+20.3%), backlog $43.98B (+27.3%) → Q1 FY26: revenues $7.87B (+26.3% YoY), backlog $48.47B (+10.2% QoQ)",
                    "note": "Revenue growth accelerating from 20% to 26% YoY as Electric segment continues to outpace prior year"
                },
                {
                    "area": "supply",
                    "direction": "tightening",
                    "trend": "FY25: RPO $23.76B (+41.8% YoY), backlog $43.98B (+27.3%) → Q1 FY26: RPO $26.24B (+10.4% QoQ), backlog $48.47B",
                    "note": "Both RPO and backlog growing QoQ — demand is outpacing current execution capacity; Electric segment is the constraint"
                },
                {
                    "area": "margins",
                    "direction": "improving",
                    "trend": "FY25: Electric op margin 10.3% (flat); Underground 7.3% (+1.6pts) → Q1 FY26: operating income +41.7%; gross margin 14.1% vs 13.4%",
                    "note": "Q1 FY26 margin improvement broad-based — volume leverage kicking in; DSI acquisition adding Underground high-margin revenue"
                },
                {
                    "area": "capex",
                    "direction": "expanding",
                    "trend": "FY25: $3.30B deployed on acquisitions incl. DSI → Q1 FY26: operating cash flow $339M operating income; SG&A +$127M from compensation and acquisitions",
                    "note": "Acquisition-led expansion (DSI mechanical/plumbing, CEI electrical) increasing exposure to hyperscaler turnkey infrastructure"
                }
            ],
            "verdict": "Thesis intact — Quanta is the utility-to-data-center infrastructure play with the deepest backlog visibility ($48B) and the widest service breadth (HV substation, low-voltage inside-DC, generation). Double-digit sequential RPO and backlog growth is the demand confirmation."
        }

    elif ticker == "SNOW":
        return {
            "as_of": TODAY,
            "based_on_accessions": accessions,
            "covers": covers,
            "headline": "FY26 revenue $4.7B vs $3.6B FY25; RPO grew from $7.9B to $9.8B while NRR held at 125% — consumption model is performing with $1M+ customer cohort expanding 27%.",
            "shifts": [
                {
                    "area": "growth",
                    "direction": "stable",
                    "trend": "Q3 FY26: product revenue $1.16B (+29% YoY) → FY26: revenue $4.7B (+31% vs $3.6B FY25); quarterly run-rate consistent",
                    "note": "Growth rate holding at 29-31% across two periods — consumption model producing consistent quarterly cadence"
                },
                {
                    "area": "supply",
                    "direction": "improving",
                    "trend": "Q3 FY26: RPO $7.9B (48% to recognize next 12mo) → FY26: RPO $9.8B (+24%) at Jan 31, 46% to recognize next 12mo",
                    "note": "RPO building faster than revenue recognition — backlog is growing, not shrinking; weighted-avg contract 2.7 years"
                },
                {
                    "area": "concentration",
                    "direction": "easing",
                    "trend": "Q3 FY26: NRR 125% (vs 126% Jan-25) → FY26: NRR 125% (stable); $1M+ customers 733 vs 576 (+27%), Forbes G2000 790 at ~43% of revenue",
                    "note": "Large-customer cohort growing faster than overall customers — concentration improving through natural expansion, not new wins only"
                },
                {
                    "area": "margins",
                    "direction": "improving",
                    "trend": "Q3 FY26: no margin detail beyond net loss → FY26: SBC declining (34% vs 41% of revenue); OCF $1.2B; net loss $1.3B (but improving)",
                    "note": "SBC as % of revenue declining — path to GAAP profitability is in sight; OCF positive at $1.2B"
                },
                {
                    "area": "segments",
                    "direction": "improving",
                    "trend": "Q3 FY26: began public sector self-hosted accounting → FY26: self-hosted (ASC 985-20) becoming a new revenue recognition category",
                    "note": "Public sector self-hosted is a new business model — upfront recognition vs subscription; government AI data platform demand"
                }
            ],
            "verdict": "Thesis intact — consistent 29-31% growth, NRR 125%, $1M+ customer cohort +27%, and RPO building to $9.8B. The self-hosted public sector vertical is an emerging growth option not yet reflected in consensus."
        }

    elif ticker == "SNPS":
        return {
            "as_of": TODAY,
            "based_on_accessions": accessions,
            "covers": covers,
            "headline": "Ansys contributed $885.6M in Q1 FY26 after closing July 2025; Design IP -6% is the persistent weak spot; $3.5B term loan paid off in Q1 FY26 — deleveraging prioritized before buybacks resume.",
            "shifts": [
                {
                    "area": "growth",
                    "direction": "accelerating",
                    "trend": "FY25: revenue $7.05B (+15%, Ansys contributed $756.6M post-7/17 close) → Q1 FY26: revenue $2.41B (+66% YoY, Ansys $885.6M)",
                    "note": "Headline growth inflated by Ansys contribution — organic growth is positive but Design IP weakness offsets"
                },
                {
                    "area": "segments",
                    "direction": "deteriorating",
                    "trend": "FY25: Design IP -22% China decline ex-Ansys; expected muted FY26 → Q1 FY26: Design IP $407M -6% YoY; Design Automation (Ansys) +96%",
                    "note": "Design IP weakness persisted into Q1 FY26 despite July 2025 BIS license rescission — internal roadmap missteps are the driver, not just China"
                },
                {
                    "area": "leverage",
                    "direction": "improving",
                    "trend": "FY25: $13.5B total debt (Ansys financing); buyback suspended → Q1 FY26: $3.5B term loan paid off; deleveraging ahead of buyback resumption",
                    "note": "Cash prioritized to debt paydown — shareholder capital return not until leverage is reduced"
                },
                {
                    "area": "supply",
                    "direction": "stable",
                    "trend": "FY25: backlog $11.4B (45% next 12mo) → Q1 FY26: backlog $11.3B (47% next 12mo, slightly higher near-term share)",
                    "note": "Backlog essentially flat at $11.3-11.4B — no build but also no erosion; revenue recognition running at expected pace"
                },
                {
                    "area": "capex",
                    "direction": "expanding",
                    "trend": "FY25: $300-350M restructuring ('2026 Plan') → Q1 FY26: $118.3M charged against the plan; Processor IP business sold to GlobalFoundries",
                    "note": "Processor IP divestiture simplifies the Design IP portfolio; GFS gets IP, SNPS gets cash to reduce Ansys-acquisition-related drag"
                }
            ],
            "verdict": "Thesis intact but Design IP is the persistent concern — two filings in a row with Design IP weakness, and the BIS rescission didn't fix it. Ansys integration is on track, leverage declining. The design IP roadmap misstep needs resolution."
        }

    elif ticker == "VRT":
        return {
            "as_of": TODAY,
            "based_on_accessions": accessions,
            "covers": covers,
            "headline": "Backlog more than doubled YoY to $15.0B by FY25 YE; Americas +41.9% FY25 → +53.1% Q1 FY26 as AI/HPC demand accelerates; gross margin expanded 400bps in Q1 on volume leverage.",
            "shifts": [
                {
                    "area": "growth",
                    "direction": "accelerating",
                    "trend": "FY25: Americas +41.9%, total +27.7% → Q1 FY26: Americas +53.1% ($1.81B), total +30.1% ($2.65B); 'very robust' AI/HPC demand",
                    "note": "Americas acceleration from 42% to 53% in one quarter — hyperscaler data center build in the US is the specific driver"
                },
                {
                    "area": "supply",
                    "direction": "tightening",
                    "trend": "FY25: combined order backlog $15.0B (doubled from $7.2B); majority firm + expected in next 12-18 months → Q1 FY26: backlog still 'robust'; no new disclosed number",
                    "note": "Doubling backlog in 12 months is extraordinary — supply chain and manufacturing capacity are the constraints, not demand"
                },
                {
                    "area": "margins",
                    "direction": "improving",
                    "trend": "FY25: gross margin 36.3% (-30bps on tariffs vs volume) → Q1 FY26: gross margin 37.7% (+400bps) on mix and operating leverage",
                    "note": "Q1 gross margin recovery of 400bps is strong — Americas mix (27% op margin) is pulling the blended margin up despite EMEA softness"
                },
                {
                    "area": "capex",
                    "direction": "raised",
                    "trend": "FY25: capex $226.4M → CY26 guided $425-525M (2x); Q1 FY26 capex $114M; reaffirmed at $425-525M",
                    "note": "Capex doubling is necessary to expand manufacturing capacity for the doubled backlog; Americas-specific expansion planned"
                },
                {
                    "area": "segments",
                    "direction": "improving",
                    "trend": "FY25: Asia Pacific +17.5%, EMEA flat → Q1 FY26: Asia Pacific +14.9%, EMEA -20.3%; Americas now 68% of revenue",
                    "note": "EMEA weakening is a risk — it was 18% of FY25 revenue; Americas dominance increases geographic concentration risk"
                }
            ],
            "verdict": "Thesis intact and one of the clearest data-center infrastructure beneficiaries — backlog doubled, margin expanding, capex doubling to meet demand. EMEA softness and Americas concentration are watchlist items."
        }

    else:
        return None


def main():
    summaries, cross_quarter = load_data()
    groups = group_by_ticker(summaries)

    print(f"Tickers with entries:")
    for t, entries in sorted(groups.items()):
        print(f"  {t}: {len(entries)} entries")

    # Generate entries for all tickers with 2+ entries
    new_or_updated = {}
    skipped_single = []
    preserved = []

    for ticker, entries in sorted(groups.items()):
        if len(entries) < 2:
            skipped_single.append(ticker)
            continue

        # MU and NVDA: preserve existing unless new filings (none in this run)
        if ticker in ("MU", "NVDA") and ticker in cross_quarter:
            preserved.append(ticker)
            new_or_updated[ticker] = cross_quarter[ticker]
            continue

        result = generate_cross_quarter(ticker, entries)
        if result is not None:
            new_or_updated[ticker] = result
            print(f"  Generated: {ticker}")
        else:
            print(f"  Skipped (None returned): {ticker}")

    print(f"\nSummary:")
    print(f"  Generated: {len(new_or_updated)}")
    print(f"  Preserved: {preserved}")
    print(f"  Skipped (1 entry): {skipped_single}")

    # Write output
    with open("/home/user/Inference-Dashboard/data/cross_quarter.json", "w") as f:
        json.dump(new_or_updated, f, indent=2, ensure_ascii=False)
        f.write("\n")
    print(f"\nWrote {len(new_or_updated)} entries to data/cross_quarter.json")


if __name__ == "__main__":
    main()
