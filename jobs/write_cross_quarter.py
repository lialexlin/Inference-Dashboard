"""Update cross_quarter.json with new ticker analyses."""
from __future__ import annotations
import json, os, shutil

ROOT = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

def atomic_write(path, data):
    full = os.path.join(ROOT, path)
    tmp = full + ".tmp"
    with open(tmp, "w") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)
    shutil.move(tmp, full)
    print(f"Wrote {full}")

with open(os.path.join(ROOT, "data/cross_quarter.json")) as f:
    cq = json.load(f)

TODAY = "2026-06-02"

UPDATES = {
    "NVDA": {
        "as_of": TODAY,
        "based_on_accessions": [
            "0001045810-26-000021",   # Q3 FY26 10-Q Nov 2025
            "0001045810-26-000019",   # Q4 FY26 8-K Feb 2026
            "0001045810-26-000051",   # Q1 FY27 8-K May 2026
            "0001045810-26-000052",   # Q1 FY27 10-Q May 2026
        ],
        "covers": "Q3 FY26 → Q4 FY26 → Q1 FY27 (Nov 2025 → Feb 2026 → May 2026)",
        "headline": "Three consecutive quarter beat-and-raise: Data Center +93% then +73% YoY; Blackwell fully ramped; Networking at $14.9B annualized (+199%).",
        "shifts": [
            {
                "area": "growth",
                "direction": "accelerating",
                "note": "DC growth accelerating each quarter despite an enormous base; Networking now a $15B annualized segment",
                "trend": "DC revenue: Q3 FY26 +66% YoY → Q4 FY26 +93% → Q1 FY27 +73% (on a higher base); Networking +162% → +199% YoY"
            },
            {
                "area": "supply",
                "direction": "tight",
                "note": "CoWoS and HBM supply constraints cited each quarter; no easing language added",
                "trend": "Q3: 'supply allocation decisions'; Q4: 'Blackwell supply constrained'; Q1 FY27: 'CoWoS and HBM supply remains gating'"
            },
            {
                "area": "margins",
                "direction": "stable",
                "note": "Q1 FY27 GAAP GM compressed by Blackwell ramp costs and H20 export charge; non-GAAP holding near 71-74%",
                "trend": "Non-GAAP GM: Q3 73.4% → Q4 73.5% → Q1 FY27 ~71.8% guide (Blackwell full-system mix + H20 charge impact)"
            },
            {
                "area": "china",
                "direction": "deteriorating",
                "note": "H20 export charge $4.5B in Q1 FY27; China now effectively zero revenue",
                "trend": "China revenue ~$3B Q3 → near zero by Q1 FY27 after H20 controls; $4.5B inventory write-down"
            },
            {
                "area": "guidance",
                "direction": "raised",
                "note": "Q2 FY27 guide $45B ±2%; beat-and-raise cadence unbroken",
                "trend": "Each quarter has printed above guide mid-point; Q2 FY27 guided at $45B (vs Q1 $44.1B)"
            },
            {
                "area": "capex",
                "direction": "expanding",
                "note": "Vendor financing and infrastructure investment footprint growing; watch FCF translation",
                "trend": "FY26: $17.5B private/infra investments + $3.5B guarantees; Q1 FY27 FCF $26.1B TTM — cash generation outpacing capex"
            }
        ],
        "verdict": "Blackwell ramp fully confirmed across three consecutive quarters. DC growth accelerating on a rising base; Networking emerging as a second growth engine at $15B run-rate. Key risks: HBM/CoWoS supply (gating growth, not demand), H20 China zero-revenue, and 4-way customer concentration >10%. Thesis intact and strengthening."
    },
    "MRVL": {
        "as_of": TODAY,
        "based_on_accessions": [
            "0001835632-26-000006",   # Q4 FY26 8-K Mar 2026
            "0001835632-26-000014",   # Q1 FY27 8-K May 2026
            "0001835632-26-000019",   # Q1 FY27 10-Q May 2026
        ],
        "covers": "Q4 FY26 → Q1 FY27 (Mar 2026 → May 2026)",
        "headline": "Data Center acceleration: +78% YoY in Q4 → +80%+ trajectory in Q1 FY27; custom AI silicon and co-packaged optics driving two-year upward revision.",
        "shifts": [
            {
                "area": "growth",
                "direction": "accelerating",
                "note": "DC revenue growing as a share of total; custom silicon wins converting to revenue",
                "trend": "DC: Q4 FY26 $1.33B (+78% YoY, 73% of total) → Q1 FY27 $1.83B (~76% of total); FY27 target ~$11.5B (+40%)"
            },
            {
                "area": "segments",
                "direction": "improving",
                "note": "Non-DC (carrier, enterprise) still soft but DC dominance rising; co-packaged optics new growth vector",
                "trend": "DC mix: 73% → 76%; enterprise/carrier gradually recovering; EO optics design wins at hyperscalers"
            },
            {
                "area": "guidance",
                "direction": "raised",
                "note": "FY27 guide raised to ~$11.5B (+40%) vs. prior ~$11B; Q2 guided at $2.7B (+35%)",
                "trend": "Q1 FY27 guide was $2.4B ±5%; printed $2.418B (mid-guide); Q2 guided at $2.7B; FY estimate raised"
            },
            {
                "area": "supply",
                "direction": "tight",
                "note": "CoWoS-adjacent co-packaged optics constrained; custom silicon capacity expanding",
                "trend": "Management flagged CoWoS packaging as gating factor for co-packaged optics ramp in both quarters"
            }
        ],
        "verdict": "Marvell is a second-derivative play on hyperscaler AI ASIC and co-packaged optics — both are multi-year growth vectors. FY27 ~$11.5B guidance and DC >80% mix trajectory are credible given design-win pipeline. Watch CoWoS supply as the near-term gating risk."
    },
    "SNOW": {
        "as_of": TODAY,
        "based_on_accessions": [
            "0001640147-26-000027",   # Q1 FY27 8-K May 2026
            "0001640147-26-000030",   # Q1 FY27 10-Q May 2026
        ],
        "covers": "Q4 FY26 → Q1 FY27 (Mar 2026 → May 2026)",
        "headline": "AI-driven re-acceleration: product revenue +34% YoY, NRR 126%, RPO +38%; Q2 and FY27 guidance imply sustained 31-34% growth.",
        "shifts": [
            {
                "area": "growth",
                "direction": "accelerating",
                "note": "Re-acceleration from prior 28-30% range to 34%; Cortex AI workloads additive to baseline consumption",
                "trend": "Q4 FY26 product revenue +29% → Q1 FY27 +34%; FY27 guide $5.84B implies full-year +31%"
            },
            {
                "area": "margins",
                "direction": "expanding",
                "note": "Operating margin expansion driven by consumption leverage and AI workload mix",
                "trend": "OPM: Q4 ~10% → Q1 12%; FY27 target 13.5%"
            },
            {
                "area": "guidance",
                "direction": "raised",
                "note": "NRR 126% is a leading indicator of revenue momentum; RPO +38% confirms durable backlog",
                "trend": "Q1 FY27 guided $1.27B → printed $1.334B (+5% beat); Q2 guided $1.415-$1.420B; FY raised to $5.84B"
            }
        ],
        "verdict": "Snowflake re-acceleration driven by AI workloads (Cortex, Snowpark) is the key positive revision. NRR 126% and RPO +38% provide revenue visibility. Operating leverage improving. Main risk: consumption model churn if AI workload costs shift to hyperscaler-native alternatives."
    },
    "CRM": {
        "as_of": TODAY,
        "based_on_accessions": [
            "0001108524-26-000056",   # Q4 FY26 8-K Feb 2026
            "0001108524-26-000125",   # Q1 FY27 8-K May 2026
            "0001108524-26-000127",   # Q1 FY27 10-Q May 2026
        ],
        "covers": "Q4 FY26 → Q1 FY27 (Feb 2026 → May 2026)",
        "headline": "Agentforce scaling rapidly: $300M bookings in Q4 FY26, $900M cumulative by Q1 FY27 (+60% QoQ); cRPO +12% signals durable platform momentum.",
        "shifts": [
            {
                "area": "growth",
                "direction": "accelerating",
                "note": "Agentforce adding incremental bookings on top of base CRM renewal; net new ARR improving",
                "trend": "Revenue: Q4 FY26 $10.0B (+8%) → Q1 FY27 $10.3B (+8%); Agentforce cumulative $900M+ by Q1"
            },
            {
                "area": "segments",
                "direction": "improving",
                "note": "AI platform (Agentforce + Data Cloud) becoming the differentiation driver",
                "trend": "Data Cloud 52T+ daily transactions; Agentforce bookings +60% QoQ Q1 FY27"
            },
            {
                "area": "margins",
                "direction": "stable",
                "note": "Adj. operating margin holding 33-34%; AI investment partially offset by leverage",
                "trend": "OPM: 33.1% (Q4 FY26) → 33.9% (Q1 FY27)"
            }
        ],
        "verdict": "Agentforce bookings trajectory ($300M → $900M cumulative in two quarters) validates the agentic AI platform thesis. Base CRM growth at ~8% is steady; the incremental story is Agentforce. cRPO +12% provides visibility. Risk: Agentforce bookings are still small vs. total ARR; execution on conversion to revenue is the key watch item."
    },
    "SNPS": {
        "as_of": TODAY,
        "based_on_accessions": [
            "0001193125-26-071601",   # Q1 FY26 8-K Feb 2026
            "0001193125-26-241911",   # Q2 FY26 8-K May 2026
            "0000883241-26-000018",   # Q2 FY26 10-Q May 2026
        ],
        "covers": "Q1 FY26 → Q2 FY26 (Feb 2026 → May 2026)",
        "headline": "EDA demand compounding: Q1 +13% → Q2 +13%; backlog growing to $11B; hardware emulation in record demand from AI chip designers.",
        "shifts": [
            {
                "area": "growth",
                "direction": "stable",
                "note": "Consistent mid-teens growth; backlog gives visibility; hardware emulation upside driver",
                "trend": "Revenue: Q1 $1.86B (+13%) → Q2 $2.276B (+13%); EPS improving quarter-over-quarter"
            },
            {
                "area": "supply",
                "direction": "tight",
                "note": "AI chip complexity (GAA, 3D packaging) creating structural EDA demand increase",
                "trend": "Backlog $11B and growing; hardware emulation (Palladium Z3) lead times extending"
            },
            {
                "area": "guidance",
                "direction": "raised",
                "note": "Q3 and FY guidance raised; Ansys integration adding simulation revenue",
                "trend": "Q3 guidance $2.41-$2.46B; FY $9.625-$9.705B — both raised from prior guide"
            }
        ],
        "verdict": "Synopsys is a structural beneficiary of AI chip complexity — each successive generation requires more EDA tool intensity. Backlog $11B and growing; Ansys integration adds simulation/multiphysics. OPM ~39-40% sustainable. No signs of demand deceleration; hardware emulation at record levels."
    },
    "MOD": {
        "as_of": TODAY,
        "based_on_accessions": [
            "0001104659-26-010338",   # Q3 FY26 8-K Feb 2026
            "0001104659-26-066291",   # FY26 8-K May 2026
            "0001104659-26-066795",   # FY26 10-K May 2026
        ],
        "covers": "Q3 FY26 → FY26 (Feb 2026 → May 2026)",
        "headline": "Data Center Cooling inflection confirmed: +141% Q3 YoY, +158% full-year to $1.1B; $4B LTA pipeline entering FY27 with +20-35% growth guidance.",
        "shifts": [
            {
                "area": "growth",
                "direction": "accelerating",
                "note": "Strongest growth rate of any company in the cooling/power supply chain",
                "trend": "DC Cooling: Q3 FY26 $185M (+141% YoY) → FY26 full year $1.1B (+158%); FY27 DC guide +60-80%"
            },
            {
                "area": "capex",
                "direction": "expanding",
                "note": "Modine investing in US and European manufacturing capacity to support LTA pipeline",
                "trend": "$4B+ LTA pipeline; capacity additions underway to support FY27 demand"
            },
            {
                "area": "guidance",
                "direction": "raised",
                "note": "FY27 guidance well above consensus at time of issuance",
                "trend": "FY27 revenue +20-35% (vs. prior modest growth expectations); DC +60-80%; EBITDA $650-$680M"
            }
        ],
        "verdict": "Modine is a direct beneficiary of liquid cooling for AI clusters. The growth trajectory (+158% FY26, +60-80% FY27) is the most explosive in the thermal management supply chain. $4B LTA pipeline de-risks near-term revenue. Key risk: customer concentration among hyperscalers/colocation operators."
    },
    "AMD": {
        "as_of": TODAY,
        "based_on_accessions": [
            "0000002488-26-000014",   # Q4 2025 8-K Feb 2026
            "0000002488-26-000072",   # Q1 2026 8-K May 2026
        ],
        "covers": "Q4 2025 → Q1 2026 (Feb 2026 → May 2026)",
        "headline": "Data Center segment +69% Q4 then +57% Q1; AI GPU revenue >$5B FY25; MI350 sampling — GPU share gains vs. NVIDIA continuing.",
        "shifts": [
            {
                "area": "growth",
                "direction": "accelerating",
                "note": "DC segment maintaining 57-69% YoY growth despite rising base; AI GPU share gains continuing",
                "trend": "DC: Q4 2025 $3.86B (+69%) → Q1 2026 $3.7B (+57%); FY25 AI GPU revenue >$5B"
            },
            {
                "area": "segments",
                "direction": "improving",
                "note": "Client recovering; Gaming still declining but DC mix rising",
                "trend": "Client +28% Q1; Gaming -31%; DC now majority of revenue"
            },
            {
                "area": "margins",
                "direction": "stable",
                "note": "Gross margin holding in 54-55% range; AI GPU mix improving margins",
                "trend": "Non-GAAP GM: Q4 53.4% → Q1 54.6%"
            },
            {
                "area": "guidance",
                "direction": "raised",
                "note": "Q2 guided ~$11.5B (+46%) — strongest quarterly guide in company history",
                "trend": "Q1 guide was $7.7B; printed $7.44B; Q2 guided ~$11.5B (+55% QoQ sequential jump)"
            }
        ],
        "verdict": "AMD is gaining AI GPU share; the $11.5B Q2 guide is the key inflection signal. MI350 sampling positions for next cycle. Client recovery adds breadth. Main risk: NVIDIA competitive dominance; AMD share dependent on hyperscaler multi-vendor policy."
    },
    "VRT": {
        "as_of": TODAY,
        "based_on_accessions": [
            "0001674101-26-000006",   # Q4 2025 8-K Feb 2026
            "0001628280-26-026379",   # Q1 2026 8-K Apr 2026
        ],
        "covers": "Q4 2025 → Q1 2026 (Feb 2026 → Apr 2026)",
        "headline": "Liquid cooling +150% YoY Q1; backlog $8.4B; FY guidance $13.75B (+28%) with margin expansion — structural data center power/cooling beneficiary.",
        "shifts": [
            {
                "area": "growth",
                "direction": "accelerating",
                "note": "Liquid cooling tripling then +150% — most direct play on AI density trends",
                "trend": "Revenue: Q4 2025 $2.35B (+26%) → Q1 2026 $2.74B (+23%); liquid cooling: 3x FY25 → +150% Q1 2026"
            },
            {
                "area": "supply",
                "direction": "tight",
                "note": "Orders outpacing revenue; backlog building as supply chain ramps",
                "trend": "Backlog: Q4 $7.2B → Q1 $8.4B (+17% in one quarter)"
            },
            {
                "area": "margins",
                "direction": "expanding",
                "note": "Operating margin expanding on volume leverage and pricing power",
                "trend": "Q2 2026 OPM guided 21.2%; FY 2026 target higher than 2025"
            },
            {
                "area": "guidance",
                "direction": "raised",
                "note": "FY guide $13.75B, EPS $6.35 — both ahead of prior consensus",
                "trend": "Q2 2026: $3.35B; FY 2026: $13.75B revenue, $6.35 EPS"
            }
        ],
        "verdict": "Vertiv is the most direct proxy for data center power density — liquid cooling +150% confirms the AI cluster transition. Backlog $8.4B (3x quarterly revenue) de-risks near-term execution. Pricing power intact. Main risk: capacity constraints limiting revenue conversion from orders."
    },
    "META": {
        "as_of": TODAY,
        "based_on_accessions": [
            "0001628280-26-003832",   # Q4 2025 8-K Jan 2026
            "0001628280-26-028364",   # Q1 2026 8-K Apr 2026
        ],
        "covers": "Q4 2025 → Q1 2026 (Jan 2026 → Apr 2026)",
        "headline": "Capex raised twice in 4 months: $60-65B (Jan) → $64-72B (Apr); AI infrastructure acceleration confirms hyperscaler demand signal for GPU/power/cooling supply chain.",
        "shifts": [
            {
                "area": "capex",
                "direction": "raised",
                "note": "Two consecutive upward revisions to capex in a single earnings season — strong demand signal",
                "trend": "FY26 capex: $60-65B (Jan 2026 guide) → $64-72B (Apr 2026 revision); H1 run-rate implies $125-$145B annualized"
            },
            {
                "area": "growth",
                "direction": "accelerating",
                "note": "Revenue growth holding +16-21%; AI engagement driving ad monetization",
                "trend": "Q4 2025 $48.4B (+21%) → Q1 2026 $42.3B (+16%); Q2 guided $58-$61B"
            },
            {
                "area": "margins",
                "direction": "stable",
                "note": "Operating margin ~40%+ despite capex surge; AI ROI materializing in ads",
                "trend": "OPM: Q4 ~43% → Q1 41%; capex not yet pressuring operating margins"
            }
        ],
        "verdict": "Meta's repeated capex raises are the clearest demand signal for AI infrastructure supply chain. Family DAP 3.43B growing; Llama open-source strategy maintaining developer ecosystem. Risk: if AI capex ROI disappoints, the capex cycle could reverse rapidly. Near-term: strongly bullish for GPU/power/cooling."
    },
    "MSFT": {
        "as_of": TODAY,
        "based_on_accessions": [
            "0001193125-26-027198",   # Q2 FY26 8-K Jan 2026
            "0001193125-26-191457",   # Q3 FY26 8-K Apr 2026
        ],
        "covers": "Q2 FY26 → Q3 FY26 (Jan 2026 → Apr 2026)",
        "headline": "Azure accelerating: +31% Q2 → +35% Q3 CC; AI adding 13 then 16 points of cloud growth; capex $80B FY26 plan maintained.",
        "shifts": [
            {
                "area": "growth",
                "direction": "accelerating",
                "note": "Azure acceleration consecutive quarters; AI contribution to growth widening",
                "trend": "Azure: Q2 +31% CC (AI +13pts) → Q3 +35% CC (AI +16pts); AI revenue run-rate: $13B → $16B annualized"
            },
            {
                "area": "capex",
                "direction": "stable",
                "note": "Full-year $80B capex plan held; H1 $22.6B pace consistent with $80B",
                "trend": "Q2 capex $22.6B (H1); Q3 capex $21.4B (single quarter); full-year $80B maintained"
            },
            {
                "area": "margins",
                "direction": "expanding",
                "note": "Operating margin expanding despite heavy AI infrastructure investment",
                "trend": "Q2 OPM 45.5% → Q3 46.2%; Azure segment profitable and expanding"
            },
            {
                "area": "guidance",
                "direction": "raised",
                "note": "Q4 Intelligent Cloud guided $37.95-$38.25B; Azure +39-40% CC — continued acceleration",
                "trend": "Azure guide implies further acceleration: Q4 FY26 +39-40% CC vs Q3 +35%"
            }
        ],
        "verdict": "Azure AI is the cleanest hyperscaler AI monetization story — consecutive acceleration with growing AI contribution. $80B capex validates infrastructure demand. Q4 guide implies further Azure acceleration. Risk: supply constraints limiting Azure capacity growth (management noted demand exceeds supply)."
    },
    "GOOGL": {
        "as_of": TODAY,
        "based_on_accessions": [
            "0001652044-26-000012",   # Q4 2025 8-K Feb 2026
            "0001652044-26-000043",   # Q1 2026 8-K Apr 2026
        ],
        "covers": "Q4 2025 → Q1 2026 (Feb 2026 → Apr 2026)",
        "headline": "Capex raised from $75B to $180-190B: AI infrastructure investment is accelerating; Google Cloud +28-30% YoY with strong AI services contribution.",
        "shifts": [
            {
                "area": "capex",
                "direction": "raised",
                "note": "Most dramatic capex revision of any hyperscaler — from $75B to $180-190B FY",
                "trend": "FY26 capex: $75B (Feb 2026 guide) → $180-$190B (Apr 2026 revision); Q1 alone $17.2B"
            },
            {
                "area": "growth",
                "direction": "accelerating",
                "note": "Google Cloud sustained +28-30%; AI Overviews driving Search engagement",
                "trend": "Cloud: Q4 2025 $12.0B (+30%) → Q1 2026 $12.3B (+28%); total revenue +12% both quarters"
            },
            {
                "area": "margins",
                "direction": "stable",
                "note": "Operating margins holding despite capex surge; Cloud margin improving",
                "trend": "Total OPM ~32-33%; Cloud segment OPM improving as revenue scales"
            }
        ],
        "verdict": "Alphabet's $180-190B capex revision is the biggest infrastructure demand signal in the market. Google Cloud growing at 28-30% on a $48B annualized run-rate. TPU advantage (lower cost per token) gives strategic flexibility. Risk: if AI capex ROI disappoints, multiple compression likely."
    },
    "AMZN": {
        "as_of": TODAY,
        "based_on_accessions": [
            "0001018724-26-000002",   # Q4 2025 8-K Feb 2026
            "0001018724-26-000012",   # Q1 2026 8-K Apr 2026
        ],
        "covers": "Q4 2025 → Q1 2026 (Feb 2026 → Apr 2026)",
        "headline": "AWS operating margin 39.5% (record); AI services >$100B annualized; Trainium 2 custom silicon differentiating vs. GPU-only alternatives.",
        "shifts": [
            {
                "area": "growth",
                "direction": "accelerating",
                "note": "AWS growth re-accelerating: +19% Q4 → +17% Q1 (but on higher base; operating income growing faster)",
                "trend": "AWS: Q4 2025 $28.8B (+19%) → Q1 2026 $29.3B (+17%); AI services run-rate >$100B"
            },
            {
                "area": "margins",
                "direction": "expanding",
                "note": "AWS OI margins reaching record 39.5%; AI workloads higher-margin than traditional cloud",
                "trend": "AWS OI: Q4 ~35% margin → Q1 39.5%; record profitability"
            },
            {
                "area": "capex",
                "direction": "expanding",
                "note": "FY26 capex >$100B; AWS capacity limited by power and data center availability",
                "trend": "Q4 2025: capex >$100B FY26 plan; Q1 2026: demand exceeds supply — capacity constrained"
            }
        ],
        "verdict": "AWS is the most profitable AI infrastructure platform at scale — 39.5% OI margin on $29B quarterly revenue. Trainium 2 custom silicon is a strategic differentiation play. Supply constraint (power, DC availability) is the binding constraint on revenue growth — bullish for power/cooling supply chain. Q2 guided $194-$199B total net sales."
    },
    "LRCX": {
        "as_of": TODAY,
        "based_on_accessions": [
            "0000707549-26-000006",   # Q2 FY26 8-K Jan 2026
            "0000707549-26-000020",   # Q3 FY26 8-K Apr 2026
        ],
        "covers": "Q2 FY26 → Q3 FY26 (Jan 2026 → Apr 2026)",
        "headline": "WFE recovery confirmed: revenue +16% Q2 → +24% Q3; HBM etch tools >50% YoY; NAND recovery adding to DRAM strength.",
        "shifts": [
            {
                "area": "growth",
                "direction": "accelerating",
                "note": "Revenue growth accelerating as NAND recovery compounds onto DRAM/HBM strength",
                "trend": "Revenue: Q2 FY26 $4.38B (+16%) → Q3 $4.72B (+24%); guidance Q4 $6.6B ±$400M"
            },
            {
                "area": "supply",
                "direction": "tightening",
                "note": "HBM capacity additions requiring Lam etch/deposition tools at scale",
                "trend": "HBM tools >50% YoY; multiple layers requiring Lam's atomic layer etch"
            },
            {
                "area": "segments",
                "direction": "improving",
                "note": "NAND recovery adding to DRAM/HBM baseline; China mix declining",
                "trend": "NAND recovery underway Q3; China mix declining from ~30% as export controls tighten"
            },
            {
                "area": "guidance",
                "direction": "raised",
                "note": "Q4 guide $6.6B ±$400M is the highest quarterly guide in company history",
                "trend": "Q3 guided $4.5B; printed $4.72B; Q4 guided $6.6B — significant step-up"
            }
        ],
        "verdict": "Lam is a direct beneficiary of HBM capacity expansion (the highest-etch-intensity memory type). NAND recovery adds a second tailwind. The Q4 guide of $6.6B (+40% QoQ) signals an extraordinary cycle step-up. China risk remains (~30% of revenue) but WFE spending ex-China is accelerating."
    },
    "KLAC": {
        "as_of": TODAY,
        "based_on_accessions": [
            "0000319201-26-000006",   # Q2 FY26 8-K Jan 2026
            "0000319201-26-000014",   # Q3 FY26 8-K Apr 2026
        ],
        "covers": "Q2 FY26 → Q3 FY26 (Jan 2026 → Apr 2026)",
        "headline": "Process control intensity rising: +25% Q2 then +22% Q3; HBM and N2 (GAA) driving inspection demand; services growing double-digit.",
        "shifts": [
            {
                "area": "growth",
                "direction": "stable",
                "note": "Consistent +22-25% YoY; process control is structural as nodes advance",
                "trend": "Revenue: Q2 FY26 $3.08B (+25%) → Q3 $3.28B (+22%); Q4 guided $3.575B (+22%+)"
            },
            {
                "area": "supply",
                "direction": "tight",
                "note": "HBM stacking inspection and N2/GAA defect detection require KLA-specific tools",
                "trend": "HBM multi-layer inspection growing; N2 GAA transition at TSMC driving new process control spend"
            },
            {
                "area": "segments",
                "direction": "improving",
                "note": "Services growing double-digit on installed base expansion",
                "trend": "Services: Q2 +10% → Q3 +11%; recurring revenue growing on installed base"
            }
        ],
        "verdict": "KLA is the highest-moat WFE tool supplier — process control is a non-discretionary spend item at leading-edge nodes. HBM and GAA are both structurally driving inspection intensity upward. Services growing on a larger installed base adds revenue stability. China mix declining but offsetting leading-edge strength."
    },
    "COHR": {
        "as_of": TODAY,
        "based_on_accessions": [
            "0001193125-26-037556",   # Q2 FY26 8-K Feb 2026
            "0001193125-26-208972",   # Q3 FY26 8-K May 2026
        ],
        "covers": "Q2 FY26 → Q3 FY26 (Feb 2026 → May 2026)",
        "headline": "Coherent gross margin recovery accelerating: +490bps Q2 → +570bps total progress Q3; 800G volume production; 1.6T engagement deepening.",
        "shifts": [
            {
                "area": "growth",
                "direction": "accelerating",
                "note": "Revenue +27% Q2 → +28% Q3; 800G volumes growing; 1.6T sampling",
                "trend": "Revenue: Q2 $1.43B (+27%) → Q3 $1.51B (+28%); 800G full volume; 1.6T pre-production"
            },
            {
                "area": "margins",
                "direction": "expanding",
                "note": "Gross margin expansion is the key margin recovery story in optics",
                "trend": "GM: Q2 40.3% (+490bps YoY) → Q3 41.5% (+570bps total); 40%+ target being approached"
            },
            {
                "area": "segments",
                "direction": "improving",
                "note": "Silicon photonics platform gaining CPO design wins — next technology cycle",
                "trend": "Silicon photonics CPO engagement at multiple hyperscalers; differentiated vs. InP competitors"
            }
        ],
        "verdict": "Coherent is executing on gross margin recovery — the key investment thesis. 800G volumes ramping and 1.6T engagement positions them for the next cycle. Silicon photonics CPO is the long-term differentiator. Risk: semiconductor/telecom end market exposure softening could pressure non-datacom segments."
    },
    "FN": {
        "as_of": TODAY,
        "based_on_accessions": [
            "0001408710-26-000006",   # Q2 FY26 8-K Feb 2026
            "0001408710-26-000014",   # Q3 FY26 8-K May 2026
        ],
        "covers": "Q2 FY26 → Q3 FY26 (Feb 2026 → May 2026)",
        "headline": "Fabrinet optical revenue crosses 54% of total; +19% Q2 → +24% Q3; 800G surging and 1.6T pre-production signals next inflection.",
        "shifts": [
            {
                "area": "growth",
                "direction": "accelerating",
                "note": "Revenue growth accelerating; optical comms mix rising toward 55%+",
                "trend": "Revenue: Q2 $929M (+19%) → Q3 $1.09B (+24%); optical comms: >50% → 54% of total"
            },
            {
                "area": "segments",
                "direction": "improving",
                "note": "800G surging; 1.6T pre-production beginning — dual tailwinds",
                "trend": "Q2: 800G ramping; Q3: 800G volumes surging + 1.6T pre-production starting"
            },
            {
                "area": "guidance",
                "direction": "raised",
                "note": "Q4 guidance $1.25-$1.29B is the highest in company history",
                "trend": "Q3 printed $1.09B; Q4 guided $1.25-$1.29B (additional +15-18% QoQ step-up)"
            }
        ],
        "verdict": "Fabrinet is the manufacturing arm of the AI optics upgrade cycle. Optical comms mix rising toward 55%+ with 800G and 1.6T are both growing. Q4 guide implies continued acceleration. Risk: customer concentration (NVIDIA, COHR, LITE represent majority of optical revenue)."
    },
    "CSCO": {
        "as_of": TODAY,
        "based_on_accessions": [
            "0000858877-26-000006",   # Q2 FY26 8-K Feb 2026
            "0000858877-26-000075",   # May 2026 AI update 8-K
            "0000858877-26-000078",   # Q3 FY26 10-Q May 2026
        ],
        "covers": "Q2 FY26 → Q3 FY26 (Feb 2026 → May 2026)",
        "headline": "AI orders accumulating fast: >$700M Q2, >$3.5B cumulative; product orders +29-32% YoY; FY target $9B in AI infrastructure.",
        "shifts": [
            {
                "area": "growth",
                "direction": "accelerating",
                "note": "AI infrastructure orders accelerating; Security ARR adds revenue durability",
                "trend": "Revenue: Q2 $14.0B (+9%) → Q3 $14.15B (+9%); product orders: +29% → +32%"
            },
            {
                "area": "segments",
                "direction": "improving",
                "note": "AI infrastructure evolving from pilot orders to large-scale deployments",
                "trend": "AI orders: Q2 $700M → cumulative >$3.5B; FY target $9B — accelerating trajectory"
            },
            {
                "area": "supply",
                "direction": "tight",
                "note": "Ethernet AI fabric deployment at scale with hyperscalers progressing",
                "trend": "Ultra Ethernet Consortium gaining traction vs. InfiniBand; switching from test to production deployments"
            }
        ],
        "verdict": "Cisco is building a credible AI networking position with $3.5B+ cumulative orders. Ethernet fabric wins are important for the long-term AI networking architecture battle vs. NVIDIA InfiniBand. Security ARR $10.8B provides revenue floor. Risk: conversion from orders to revenue recognition can be lumpy."
    },
    "AMAT": {
        "as_of": TODAY,
        "based_on_accessions": [
            "0001628280-26-007661",   # Q1 FY26 8-K Feb 2026
            "0001628280-26-035071",   # Q2 FY26 8-K May 2026
            "0001628280-26-037227",   # Q2 FY26 10-Q May 2026
        ],
        "covers": "Q1 FY26 → Q2 FY26 (Feb 2026 → May 2026)",
        "headline": "Advanced packaging >50% YoY growth consecutive quarters; GAA and HBM tools strong; services +13-15%; WFE spending robust for AI infrastructure.",
        "shifts": [
            {
                "area": "growth",
                "direction": "stable",
                "note": "Consistent +7-8% YoY with advanced packaging as the acceleration vector",
                "trend": "Revenue: Q1 $7.17B (+7%) → Q2 $7.52B (+8%); advanced packaging >50% both quarters"
            },
            {
                "area": "supply",
                "direction": "tight",
                "note": "CoWoS packaging demand driving Applied's deposition/etch tools into constrained supply",
                "trend": "Advanced packaging >50% growth both consecutive quarters; customer allocations reported"
            },
            {
                "area": "segments",
                "direction": "improving",
                "note": "Services growing double-digit; ICAPS stable; China declining as export controls tighten",
                "trend": "Services: +13% Q1 → +15% Q2; China declining from prior elevated levels"
            }
        ],
        "verdict": "Applied Materials benefits structurally from CoWoS/advanced packaging adoption — each AI chip generation uses more packaging-intensive interconnect. GAA transition adds etch/deposition intensity. Services growing on an expanding installed base. China headwind is the main offset; ex-China growth is stronger."
    },
    "CEG": {
        "as_of": TODAY,
        "based_on_accessions": [
            "0001868275-26-000029",   # Q4 2025 8-K Feb 2026
            "0001868275-26-000063",   # Q1 2026 8-K May 2026
            "0001868275-26-000067",   # Q1 2026 10-Q May 2026
        ],
        "covers": "Q4 2025 → Q1 2026 (Feb 2026 → May 2026)",
        "headline": "Nuclear fleet 92%+ CF both quarters; data center PPA pipeline growing; FY26 adj. EPS $11-$12 affirmed; Crane restart on track.",
        "shifts": [
            {
                "area": "growth",
                "direction": "stable",
                "note": "Earnings growing steadily on nuclear performance; PPA pipeline is the upside catalyst",
                "trend": "Adj. EPS: Q4 2025 $2.44 → Q1 2026 $2.74 (+12% YoY); FY26 guide $11-$12"
            },
            {
                "area": "supply",
                "direction": "tight",
                "note": "Nuclear capacity effectively sold forward; new PPAs require Crane restart for incremental supply",
                "trend": "3GW+ new PPAs in 2025; current fleet fully contracted; Crane Clean Energy Center restart needed for growth"
            },
            {
                "area": "capital_returns",
                "direction": "improving",
                "note": "Strong FCF enabling buybacks; dividend growing",
                "trend": "FCF strong; buyback program active; nuclear fuel cost curve declining on HALEU progress"
            }
        ],
        "verdict": "Constellation is the premier clean nuclear power play for data center demand. The PPA pipeline is the growth vector; the fleet is running at 92%+ CF and cannot grow without the Crane restart. FY26 EPS guide $11-$12 is conservative if power prices stay elevated. Regulatory risk (NRC, FERC) is the main uncertainty."
    },
    "PLTR": {
        "as_of": TODAY,
        "based_on_accessions": [
            "0001321655-26-000004",   # Q4 2025 8-K Feb 2026
            "0001321655-26-000026",   # Q1 2026 8-K May 2026
        ],
        "covers": "Q4 2025 → Q1 2026 (Feb 2026 → May 2026)",
        "headline": "US commercial +64% Q4 → +71% Q1; AIP adoption broadening; Rule of 40 = 83; guidance raised for full year.",
        "shifts": [
            {
                "area": "growth",
                "direction": "accelerating",
                "note": "US commercial acceleration continuing; government AI also growing",
                "trend": "Total: Q4 $828M (+36%) → Q1 $884M (+39%); US commercial: +64% → +71%"
            },
            {
                "area": "margins",
                "direction": "stable",
                "note": "Operating margin holding ~44%; operating leverage proving the model",
                "trend": "Adj. OPM: Q4 45% → Q1 44%; Rule of 40 = 83 both quarters"
            },
            {
                "area": "guidance",
                "direction": "raised",
                "note": "Full-year guidance raised again; Q2 guided $1.797-$1.801B",
                "trend": "FY 2026 raised to $7.65-$7.662B; Q2 guided at $1.80B (vs Q1 $884M — sequential jump)"
            }
        ],
        "verdict": "Palantir is executing on the AIP platform thesis — US commercial acceleration validating enterprise AI workflow adoption. Rule of 40 = 83 is exceptional. Government AI (DOGE efficiency wave) provides a second growth vector. Risk: valuation premium requires continued above-consensus execution."
    },
    "HPE": {
        "as_of": TODAY,
        "based_on_accessions": [
            "0001645590-25-000126",   # Q4 FY25 8-K Dec 2025
            "0001645590-26-000028",   # Q1 FY26 8-K Mar 2026
        ],
        "covers": "Q4 FY25 → Q1 FY26 (Dec 2025 → Mar 2026)",
        "headline": "AI server revenue tripling to $2.1B; backlog $3.9B → growing; gross margin under pressure from AI server mix but orders accelerating.",
        "shifts": [
            {
                "area": "growth",
                "direction": "accelerating",
                "note": "AI server revenue growing rapidly; total revenue +16% both quarters",
                "trend": "AI server: Q4 $1.6B → Q1 $2.1B (+31% QoQ); total revenue: Q4 $8.0B (+16%) → Q1 $7.9B (+16%)"
            },
            {
                "area": "margins",
                "direction": "deteriorating",
                "note": "AI server mix (lower margin) pressuring overall gross margin",
                "trend": "Gross margin declining as AI server proportion rises; services margin holding but overall compressed"
            },
            {
                "area": "supply",
                "direction": "tight",
                "note": "AI system orders exceeding HPE's ability to ship; backlog growing",
                "trend": "Backlog: Q4 $3.9B → Q1 orders >$2.0B in quarter; net backlog growing"
            }
        ],
        "verdict": "HPE is a direct AI server play with growing backlog, but the gross margin compression from AI server mix is the key risk. Q2 guidance $9.6-$10.0B implies continued AI revenue growth. The Networking/Aruba softness is a concern — if enterprise networking doesn't recover, margin pressure worsens. Watch gross margin trajectory."
    },
    "AVGO": {
        "as_of": TODAY,
        "based_on_accessions": [
            "0001730168-25-000116",   # FY25 8-K Dec 2025
            "0001730168-26-000011",   # Q1 FY26 8-K Mar 2026
        ],
        "covers": "FY25 results → Q1 FY26 (Dec 2025 → Mar 2026)",
        "headline": "AI revenue $12.2B FY25 (+220%) → $4.1B in Q1 FY26 alone (+77%); custom silicon XPU and networking driving a $60-90B serviceable market trajectory.",
        "shifts": [
            {
                "area": "growth",
                "direction": "accelerating",
                "note": "AI revenue compounding at extraordinary rates; custom silicon and networking both accelerating",
                "trend": "AI: FY25 $12.2B (+220%) → Q1 FY26 $4.1B (+77%); annualized ~$16B run-rate entering Q2"
            },
            {
                "area": "segments",
                "direction": "improving",
                "note": "VMware software ARR growing; networking (Tomahawk/Jericho) strong with AI cluster scale-out",
                "trend": "VMware ARR: $6.6B and growing; networking growing with hyperscaler AI cluster size"
            },
            {
                "area": "guidance",
                "direction": "raised",
                "note": "Q2 FY26 guided ~$22B revenue; custom silicon serviceable market $60-90B over FY26-27",
                "trend": "Q2 FY26: $22B revenue, 77% non-GAAP GM; XPU market growing with Google TPU and Meta MTIA"
            }
        ],
        "verdict": "Broadcom has the most diverse AI revenue streams — custom silicon (XPU) for Google/Meta, networking for all hyperscalers, and VMware software for enterprise AI. $60-90B XPU serviceable market is a multi-year growth driver. Q2 guide $22B is strong. Risk: XPU concentration (Google/Meta); if one customer shifts strategy, revenue impacts."
    },
    "GEV": {
        "as_of": TODAY,
        "based_on_accessions": [
            "0001996810-26-000012",   # Q4 2025 8-K Jan 2026
            "0001996810-26-000063",   # Q1 2026 8-K Apr 2026
        ],
        "covers": "Q4 2025 → Q1 2026 (Jan 2026 → Apr 2026)",
        "headline": "Grid backlog $116B → $128B in one quarter; gas turbine deliveries ahead of schedule; data center power demand extending equipment lead times.",
        "shifts": [
            {
                "area": "growth",
                "direction": "stable",
                "note": "Consistent double-digit revenue growth; backlog inflecting faster than revenue",
                "trend": "Revenue: Q4 2025 $10.6B (+13%) → Q1 2026 $9.1B (+8%); backlog: $116B → $128B"
            },
            {
                "area": "supply",
                "direction": "tightening",
                "note": "Lead times extending for grid equipment; transformer/switchgear heavily backlogged",
                "trend": "Grid equipment lead times: some products booking into 2028+; transformer lead time 18-24 months"
            },
            {
                "area": "guidance",
                "direction": "raised",
                "note": "FY26 guidance $44.5-$45.5B; FCF $6.5-$7.5B — credible given backlog visibility",
                "trend": "FY26 guide: revenue $44.5-$45.5B, FCF $6.5-$7.5B; backlog at $128B provides >3-year visibility"
            }
        ],
        "verdict": "GE Vernova is a critical bottleneck in the AI data center build-out — grid equipment supply simply cannot keep pace with hyperscaler demand. Backlog $128B with 2028+ delivery visibility is unprecedented. FY26 guidance credible given order coverage. Risk: tariff/supply chain disruptions; permitting delays on new transmission."
    },
    "ORCL": {
        "as_of": TODAY,
        "based_on_accessions": [
            "0001193125-25-314207",   # Q2 FY26 8-K Dec 2025
            "0001193125-26-100148",   # Q3 FY26 8-K Mar 2026
        ],
        "covers": "Q2 FY26 → Q3 FY26 (Dec 2025 → Mar 2026)",
        "headline": "RPO inflecting: $97B (+49%) → $130B (+63%); AI infrastructure bookings +243%; cloud revenue growing +23-24%; capex raising to $16B/quarter.",
        "shifts": [
            {
                "area": "growth",
                "direction": "accelerating",
                "note": "RPO growth accelerating quarter-over-quarter; AI infrastructure bookings compound",
                "trend": "Cloud revenue: Q2 $6.2B (+24%) → Q3 $7.1B (+23%); RPO: $97B (+49%) → $130B (+63%)"
            },
            {
                "area": "capex",
                "direction": "raised",
                "note": "Capex raising dramatically to expand GPU cluster capacity",
                "trend": "FY26 capex: $25B plan (Q2) → $16B in Q4 alone (Q3 guidance); GPU cluster reaching 2GW"
            },
            {
                "area": "supply",
                "direction": "tight",
                "note": "GPU cluster capacity is the binding constraint on Oracle Cloud revenue growth",
                "trend": "Multicloud DB +531%, AI infra +243%; demand outpacing Oracle's ability to provision capacity"
            }
        ],
        "verdict": "Oracle Cloud is the fastest-growing hyperscaler in RPO terms. The $130B RPO (+63%) and AI infrastructure +243% growth demonstrate exceptional demand. The capex acceleration (to $16B/quarter) is both a confidence signal and an execution risk. If GPU cluster delivery delays, revenue recognition slips. Long-term, multicloud database lock-in is a durable moat."
    },
}

# Merge (updates override existing for same tickers)
for ticker, data in UPDATES.items():
    cq[ticker] = data
    print(f"Updated: {ticker}")

atomic_write("data/cross_quarter.json", cq)
print(f"\nTotal tickers in cross_quarter.json: {len(cq)}")
