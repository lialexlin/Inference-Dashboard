"""
One-shot bootstrap: generate cross_quarter.json entries for all tickers
that have 2+ filings in filing_summaries.json.

Run: python jobs/gen_cross_quarter.py
"""
import json
from datetime import date

AS_OF = str(date.today())  # 2026-06-07

# fmt: off
ENTRIES = {

  "AMAT": {
    "as_of": AS_OF,
    "based_on_accessions": ["0001628280-25-056742", "0001628280-26-009694"],
    "covers": "FY25 10-K (Dec 2025) → Q1 FY26 10-Q (Feb 2026)",
    "headline": "China eroding (-16%→-7% YoY), DRAM/HBM mix rising as leading-edge logic weakens; legal settlement masked otherwise stable margins.",
    "shifts": [
      {
        "area": "china",
        "direction": "improving",
        "trend": "FY25 China $8.5B (-16% YoY) → Q1 FY26 $2.1B (-7% annualized run-rate ~$8.4B); rate of decline slowing but absolute share still falling",
        "note": "Taiwan replacing China as the leading-edge growth region (+71% FY25, +46% Q1)"
      },
      {
        "area": "segments",
        "direction": "shifting",
        "trend": "DRAM mix in SemiSystems 26% (FY25) → 34% (+8pts Q1); foundry/logic 67% → 62% on weak trailing-edge",
        "note": "HBM technology transition driving the DRAM capex even as logic slows"
      },
      {
        "area": "growth",
        "direction": "decelerating",
        "trend": "FY25 revenue $28.4B (+4% YoY) → Q1 FY26 $7.0B (-2% YoY); first negative quarter in the cycle",
        "note": "AGS services +15% in Q1 is the stabilizer; systems segment carrying the weakness"
      },
      {
        "area": "margins",
        "direction": "stable",
        "trend": "Gross margin FY25 48.7% → Q1 FY26 49.0% (+0.3pts); operating margin fell 4.3pts in Q1 from $253M legal settlement — underlying GM intact",
        "note": "Legal settlement is one-time; gross margin trend is constructive"
      }
    ],
    "verdict": "Thesis intact but in a soft patch — DRAM/HBM is the bright spot offsetting logic softness and China erosion. Recovery hinges on logic capex turning; service revenue growing."
  },

  "AMD": {
    "as_of": AS_OF,
    "based_on_accessions": ["0000002488-26-000018", "0000002488-26-000076"],
    "covers": "FY25 10-K (Feb 2026) → Q1 FY26 10-Q (May 2026)",
    "headline": "Data Center re-accelerated from +32% FY25 to +57% in Q1; gross margin expanding on DC mix; China still the key overhang with 25% re-import tariff on MI325.",
    "shifts": [
      {
        "area": "growth",
        "direction": "accelerating",
        "trend": "Data Center FY25 $16.6B (+32% YoY) → Q1 FY26 $5.8B (+57% YoY); quarterly run-rate implies $23B annualized vs $16.6B full-year",
        "note": "Re-acceleration after OpenAI 6GW deal (Oct 2025); MI350/5th-gen EPYC both ramping"
      },
      {
        "area": "margins",
        "direction": "expanding",
        "trend": "Gross margin FY25 50% → Q1 FY26 53% (+3pts) on richer Data Center mix; DC operating margin FY25 22% → Q1 28%",
        "note": "Operating leverage improving as DC displaces lower-margin Client/Gaming mix"
      },
      {
        "area": "china",
        "direction": "stable",
        "trend": "China 22% of FY25 revenue ($7.8B); MI308 $800M charge reversed $360M; MI325 licenses granted Feb 2026 with 25% US re-import tariff",
        "note": "Tariff is ongoing structural cost, not resolved; MI450 roadmap may face same restrictions"
      },
      {
        "area": "concentration",
        "direction": "tightening",
        "trend": "International revenue FY25 66% of total → Q1 FY26 74%; no single customer >10% but hyperscaler dependence growing",
        "note": "OpenAI 6GW deal is a positive concentration — large committed demand but single-customer risk"
      }
    ],
    "verdict": "Thesis improving — Data Center re-acceleration is real and margins expanding. China tariff is a managed headwind, not a thesis-breaker. The OpenAI deal de-risks demand visibility through 2030."
  },

  "AMKR": {
    "as_of": AS_OF,
    "based_on_accessions": ["0001047127-26-000014", "0001047127-26-000020"],
    "covers": "FY25 10-K (Feb 2026) → Q1 2026 10-Q (Apr 2026)",
    "headline": "Revenue re-accelerated from +6% to +28%; Arizona fab capex stepping from $0.9B to $2.5-3.0B; Apple concentration stable at 30%.",
    "shifts": [
      {
        "area": "growth",
        "direction": "accelerating",
        "trend": "FY25 $6.71B (+6% YoY) → Q1 2026 $1.68B (+27.5% YoY); computing end market +19%, communications +42%",
        "note": "Recovery broad-based across computing (datacenter/AI packaging) and communications (premium smartphone)"
      },
      {
        "area": "capex",
        "direction": "accelerating",
        "trend": "FY25 capex $0.9B (13.5% of sales) → Q1 capex $225M (+181% YoY); FY26 guided $2.5-3.0B (3.3x FY25)",
        "note": "Arizona 1.8M sq ft CHIPS-Act facility; manufacturing starts H1 2028; $407M CHIPS direct funding committed"
      },
      {
        "area": "margins",
        "direction": "expanding",
        "trend": "Gross margin FY25 14.0% → Q1 2026 14.2% (+2.3pts YoY) on higher factory utilization",
        "note": "Margin recovery before Arizona ramp-up costs fully load in FY28-29"
      },
      {
        "area": "concentration",
        "direction": "stable",
        "trend": "Apple ~30% of sales both FY25 and Q1 2026; Qualcomm ~11%; top-10 = 72% in both periods",
        "note": "Customer mix unchanged — no diversification yet, but AI packaging opportunity (FCBGA/2.5D) is new"
      }
    ],
    "verdict": "Story improving — revenue recovering and margins rising ahead of the Arizona capex ramp. The $2.5-3.0B FY26 capex build is a temporary margin drag but positions AMKR as the US OSAT anchor for CHIPS Act."
  },

  "AMZN": {
    "as_of": AS_OF,
    "based_on_accessions": ["0001018724-26-000004", "0001018724-26-000014"],
    "covers": "FY25 10-K (Feb 2026) → Q1 2026 10-Q (Apr 2026)",
    "headline": "AWS re-accelerated to +28% with margin expansion; RPO surged +49% in one quarter on $100B OpenAI add; capex at $173B annualized run-rate.",
    "shifts": [
      {
        "area": "growth",
        "direction": "accelerating",
        "trend": "AWS FY25 $128.7B (+20% YoY) → Q1 2026 $37.6B (+28% YoY); annualized Q1 run-rate $150B",
        "note": "Re-acceleration driven by AI workloads and multi-year cloud deal maturation"
      },
      {
        "area": "capex",
        "direction": "accelerating",
        "trend": "FY25 $128.3B → Q1 $43.2B ($173B annualized, +78% YoY); FY26 expected higher still",
        "note": "Majority for AWS technical infrastructure; Trainium/Inferentia chips reducing GPU dependency"
      },
      {
        "area": "supply",
        "direction": "tightening",
        "trend": "AWS RPO $244B (Dec 2025) → $364B (Mar 2026) — +$120B in one quarter; OpenAI added $100B over 8 years",
        "note": "$50B OpenAI commitment + $8B Anthropic total; multi-year visibility unprecedented"
      },
      {
        "area": "margins",
        "direction": "expanding",
        "trend": "AWS operating margin FY25 35.4% → Q1 2026 37.7% (+2.3pts) even as capex surges",
        "note": "Operating leverage on fixed infra base outrunning capex depreciation — bullish"
      }
    ],
    "verdict": "Thesis strongly intact — AWS re-acceleration + margin expansion + RPO surge is the best combination. Capex is a use of capital, not a risk; committed demand (RPO) far exceeds the build."
  },

  "ANET": {
    "as_of": AS_OF,
    "based_on_accessions": ["0001596532-26-000013", "0001596532-26-000078"],
    "covers": "FY25 10-K (Feb 2026) → Q1 FY26 10-Q (May 2026)",
    "headline": "Revenue growth accelerated from +28.6% to +35.1%; deferred revenue compounding ($5.4B→$6.2B); gross margin under pressure from large-customer pricing.",
    "shifts": [
      {
        "area": "growth",
        "direction": "accelerating",
        "trend": "FY25 $9.0B (+28.6%) → Q1 FY26 $2.71B (+35.1%); annualized Q1 run-rate $10.8B",
        "note": "AI Ethernet trials converting to acceptance-period contracts is the structural driver"
      },
      {
        "area": "supply",
        "direction": "tightening",
        "trend": "Deferred revenue $2.79B (FY24) → $5.37B (FY25) → $6.20B (Q1 FY26, +$830M in one quarter); RPO $7.7B",
        "note": "Memory and silicon tightening explicitly flagged as shipment-cadence gating in both filings"
      },
      {
        "area": "margins",
        "direction": "contracting",
        "trend": "Gross margin FY25 64.1% → Q1 FY26 61.9% (-2.2pts) from large-customer pricing discounts",
        "note": "Americas concentration 79.7% → 84.5% reflects hyperscaler mix; pricing pressure is structural not transitory"
      },
      {
        "area": "concentration",
        "direction": "tightening",
        "trend": "Two end-customers FY25 at 26% and 16%; Americas 80% → 85% of revenue in Q1",
        "note": "AI Titan concentration rising as non-AI enterprise grows more slowly"
      }
    ],
    "verdict": "Thesis intact but GM pressure is the watch item — deferred revenue buildup confirms demand is real; the margin compression from hyperscaler pricing is the only new risk surfaced."
  },

  "AVGO": {
    "as_of": AS_OF,
    "based_on_accessions": ["0001730168-25-000121", "0001730168-26-000016"],
    "covers": "FY25 10-K (Dec 2025) → Q1 FY26 10-Q (Mar 2026)",
    "headline": "Semiconductor solutions re-accelerated sharply from +22% to +52%; customer concentration tightened (top-5: 40%→50%); gross margin held at 68%.",
    "shifts": [
      {
        "area": "growth",
        "direction": "accelerating",
        "trend": "Semi solutions FY25 $36.9B (+22%) → Q1 FY26 $12.5B (+52%); custom AI accelerators (XPUs) + AI networking are the drivers",
        "note": "Software ($6.8B) flat in Q1 vs +26% FY25 — XPU is pulling total revenue mix"
      },
      {
        "area": "concentration",
        "direction": "tightening",
        "trend": "Top-5 end customers ~40% FY25 → ~50% Q1 FY26; one semi distributor 32% → 42% of total revenue",
        "note": "Distributor concentration implies one hyperscaler XPU customer is effectively driving the print"
      },
      {
        "area": "segments",
        "direction": "shifting",
        "trend": "Semi 55% of FY25 revenue → 65% in Q1 FY26; Infrastructure software declining as proportion despite 26% FY25 growth",
        "note": "XPU ramp is diluting the software mix that originally expanded post-VMware integration"
      },
      {
        "area": "margins",
        "direction": "stable",
        "trend": "Gross margin 68% in both FY25 and Q1 FY26; semi GM improving while software stable",
        "note": "Semi gross margin benefit offset by mix shift away from high-margin software — net flat"
      }
    ],
    "verdict": "Thesis intact — XPU re-acceleration is the growth engine. Customer concentration tightening is the emerging risk to monitor; any hyperscaler XPU design-away would be disproportionate to revenue."
  },

  "CAT": {
    "as_of": AS_OF,
    "based_on_accessions": ["0000018230-26-000008", "0000018230-26-000021"],
    "covers": "FY25 10-K (Feb 2026) → Q1 FY26 10-Q (May 2026)",
    "headline": "Power & Energy maintaining 20%+ growth as data-center backlog extends 6-8 quarters; backlog surged to $51B; tariff headwind is the new risk.",
    "shifts": [
      {
        "area": "growth",
        "direction": "accelerating",
        "trend": "Power & Energy FY25 +12% ($32.2B) → Q1 FY26 +22% ($7.0B); Power Generation sub-segment FY25 +32%, Q1 +28%",
        "note": "Data-center prime power / reciprocating engine demand explicitly cited as driver in both filings"
      },
      {
        "area": "supply",
        "direction": "tightening",
        "trend": "Backlog $30.0B (YE24) → $51.2B (YE25) → growing in Q1 FY26; $19.3B not expected in 2026 — 6-8 quarter visibility",
        "note": "Book-to-bill and order mix shifting toward Power & Energy in both periods"
      },
      {
        "area": "guidance",
        "direction": "stable",
        "trend": "FY26 low double-digit growth guided at 10-K; reaffirmed at Q1 10-Q without change",
        "note": "Tariff impact ($2.2-2.4B FY26) is embedded in guidance; management not revising despite IEEPA ruling"
      },
      {
        "area": "margins",
        "direction": "deteriorating",
        "trend": "P&E operating margin FY25 19.9% flat; Q1 FY26 17.7% (vs 18.1%) pressured by $700M Q2 tariff estimate",
        "note": "Manufacturing-cost headwind from tariffs partially offset by volume; not a structural margin issue"
      }
    ],
    "verdict": "Thesis intact — data-center-driven power demand is a multi-year structural tailwind. Tariff headwind is manageable given 6-8Q backlog lock-in. Prime power is the new unlock: data-center customers seeking owned generation."
  },

  "CDNS": {
    "as_of": AS_OF,
    "based_on_accessions": ["0000813672-26-000016", "0000813672-26-000047"],
    "covers": "FY25 10-K (Feb 2026) → Q1 FY26 10-Q (May 2026)",
    "headline": "Growth re-accelerated from +14% to +19%; China re-accelerated to +36% despite BIS overhang; backlog ticking up; margins stable post-settlement.",
    "shifts": [
      {
        "area": "growth",
        "direction": "accelerating",
        "trend": "FY25 $5.30B (+14% YoY) → Q1 FY26 $1.47B (+19% YoY); non-US Americas +87%, Japan +36% lead the regional mix",
        "note": "Broad-based acceleration across geographies except US (+6%); Hexagon D&E acquisition adds simulation tools"
      },
      {
        "area": "china",
        "direction": "accelerating",
        "trend": "FY25 China $680M (+19%) → Q1 FY26 $189M (+36%); 13% of mix in both periods",
        "note": "BIS May-Jul 2025 license whiplash absorbed; company expects 'limited' impact from current expanded controls"
      },
      {
        "area": "supply",
        "direction": "improving",
        "trend": "RPO backlog $7.8B (FY25) → $8.0B (Q1 FY26); 55% to recognize next 12mo vs 53% — slightly front-loading",
        "note": "Backlog growth modest but consistent; cRPO acceleration is positive"
      },
      {
        "area": "margins",
        "direction": "stable",
        "trend": "Operating margin FY25 28% (vs 29% prior year, hit by $128.5M settlement) → Q1 FY26 29%; recovery confirmed",
        "note": "Settlement charge was one-time; underlying margin trajectory is stable-to-improving"
      }
    ],
    "verdict": "Thesis intact — acceleration in both growth rate and China despite BIS overhang is a positive surprise. EDA demand driven by AI chip complexity remains secular."
  },

  "CEG": {
    "as_of": AS_OF,
    "based_on_accessions": ["0001868275-25-000092", "0001868275-26-000032"],
    "covers": "Q3 FY25 10-Q (Nov 2025) → FY25 10-K (Feb 2026)",
    "headline": "Calpine closed Jan 2026, tripling generation portfolio to 55 GW; TMI restart secured $1B DOE guarantee; AI/DC baseload demand explicitly framed as multi-decade tailwind.",
    "shifts": [
      {
        "area": "segments",
        "direction": "accelerating",
        "trend": "CEG standalone ~20 GW nuclear → 55 GW combined after $22B Calpine close Jan 7, 2026 (21 GW gas + 730 MW geothermal + 800 MW battery)",
        "note": "Now world's largest private power producer; 2.5M retail accounts including 75% of Fortune 100"
      },
      {
        "area": "regulation",
        "direction": "improving",
        "trend": "Calpine FERC/PUCT/NYPSC all approved (Q3 2025); NY ZEC extended Jan 2026 to 2049; Crane $1B DOE loan guarantee Nov 2025",
        "note": "Regulatory backlog cleared — Calpine now closed; Crane restart on track"
      },
      {
        "area": "capex",
        "direction": "accelerating",
        "trend": "Q3: Meta 20-yr PPA (Clinton), Calpine pending; FY25 10-K: Calpine $22B closed, Crane $1B DOE guarantee, Clinton 30MW uprate",
        "note": "Capital deployment escalating; Calpine funded with 50M shares + $4.5B cash"
      },
      {
        "area": "growth",
        "direction": "stable",
        "trend": "Adjusted EPS $9.39 FY25 (vs $8.67 FY24); GAAP down on lower nuclear PTC — operating performance stable",
        "note": "Nuclear PTC headwind is structural but manageable; Calpine adds gas/thermal earnings in FY26"
      }
    ],
    "verdict": "Thesis strengthened — Calpine close + Crane restart + NY ZEC extension gives CEG the largest, most diversified clean-baseload fleet in the US. AI/DC demand framing is explicit management language; multi-decade PPA backlog building."
  },

  "CLS": {
    "as_of": AS_OF,
    "based_on_accessions": ["0001030894-26-000011", "0001030894-26-000032"],
    "covers": "FY25 10-K (Feb 2026) → Q1 FY26 10-Q (Apr 2026)",
    "headline": "Revenue re-accelerated to +53%; HPS (hyperscale-switch programs) +63% to $1.7B/quarter; capex stepping up 3-4x to $1B for FY26.",
    "shifts": [
      {
        "area": "growth",
        "direction": "accelerating",
        "trend": "FY25 +strong (CCS +42%, HPS +81%) → Q1 FY26 +53% total revenue to $4.05B; CCS +76%",
        "note": "Enterprise segment recovered +101% in Q1 on AI/ML compute program ramp (was paused in FY25)"
      },
      {
        "area": "segments",
        "direction": "stable",
        "trend": "HPS $5.0B (41% of FY25) → ~$1.7B (42% of Q1); HPS share holding at ~42% of revenue",
        "note": "HPS is the hyperscale switching/server segment — the AI infrastructure concentration exposure"
      },
      {
        "area": "capex",
        "direction": "accelerating",
        "trend": "FY25 historical 1.5-2% of revenue capex → FY26 guided ~$1B (~6% of revenue, 3-4x historical)",
        "note": "Revolver upsized to $1.75B to fund growth; Term A extended to Apr 2031"
      },
      {
        "area": "margins",
        "direction": "expanding",
        "trend": "CCS segment margin Q1 FY25 8.0% → Q1 FY26 8.6% (+60bps); adjusted EPS $2.16 vs implied ~$1.45 prior year",
        "note": "Margin expansion driven by operating leverage on higher HPS volume"
      }
    ],
    "verdict": "Thesis intact and re-accelerating — CLS is the pure-play EMS beneficiary of hyperscaler switch program ramps. Capex step-up is demand-pull, not supply-push; customer concentration is the watch item."
  },

  "CMI": {
    "as_of": AS_OF,
    "based_on_accessions": ["0000026172-26-000009", "0000026172-26-000016"],
    "covers": "FY25 10-K (Feb 2026) → Q1 FY26 10-Q (May 2026)",
    "headline": "Power Systems EBITDA margin expanded from 22.7% to 29.5% in one quarter as data-center demand absorbed capacity; Power Generation accelerating to +28%.",
    "shifts": [
      {
        "area": "margins",
        "direction": "expanding",
        "trend": "Power Systems EBITDA margin FY25 22.7% → Q1 FY26 29.5% (+6.8pts); EBITDA FY25 $1.69B (+44%), Q1 $577M (+48%)",
        "note": "Operating leverage from data-center power generation demand compressing overhead against higher volumes"
      },
      {
        "area": "growth",
        "direction": "accelerating",
        "trend": "Power Gen product FY25 $4.73B (+19%) → Q1 FY26 $1.28B (+28%); North America and China power generation both strong",
        "note": "Data-center backlog extending 6-8 quarters out as of FY25; no moderation mentioned in Q1"
      },
      {
        "area": "supply",
        "direction": "tight",
        "trend": "FY25: backlog '6-8 quarters out'; Q1 FY26: 'continued strength' — no capacity catch-up language added",
        "note": "Capacity ramp ongoing but demand remains ahead; positive for pricing power"
      }
    ],
    "verdict": "Thesis intact — Power Systems margin expansion is the clearest proof of data-center-driven pricing power. 6-8Q backlog visibility makes near-term demand risk negligible."
  },

  "COHR": {
    "as_of": AS_OF,
    "based_on_accessions": ["0000820318-26-000006", "0000820318-26-000013"],
    "covers": "Q2 FY26 10-Q (Feb 2026) → Q3 FY26 10-Q (May 2026)",
    "headline": "D&C accelerated from +34% to +41% as 'scale across' optics joined DCI; gross margin expanding +243bps; portfolio now pure AI/DC optics after divestitures.",
    "shifts": [
      {
        "area": "growth",
        "direction": "accelerating",
        "trend": "D&C segment Q2 +34% ($1.21B) → Q3 +41% ($1.36B); 9-month D&C $3.66B (+34% YoY)",
        "note": "'Scale across' inter-datacenter interconnect named as new demand vector in Q3 — a third growth driver after DCI and traditional telecom"
      },
      {
        "area": "margins",
        "direction": "expanding",
        "trend": "Gross margin Q2 37% (+140bps YoY) → Q3 38% (+243bps YoY); D&C segment profit Q2 +44% → Q3 +49%",
        "note": "Yield improvements and pricing optimization on AI-datacenter transceivers driving the lift"
      },
      {
        "area": "segments",
        "direction": "shifting",
        "trend": "Aerospace/defense divested Sep 2025; Munich Germany divested Jan 2026; Industrial declining both quarters (-10%, -16%)",
        "note": "Portfolio narrowing deliberately toward AI optics — quality of earnings improving"
      },
      {
        "area": "leverage",
        "direction": "improving",
        "trend": "Interest expense -$13M Q3, -$39M YTD on term-loan paydown; net debt declining quarter-over-quarter",
        "note": "Debt reduction + divestiture proceeds freeing capital for optics investment"
      }
    ],
    "verdict": "Thesis strengthening — D&C acceleration with gross margin expansion is the ideal combination. Portfolio simplification toward AI optics removes noise. 'Scale across' naming is the most significant new signal."
  },

  "CRM": {
    "as_of": AS_OF,
    "based_on_accessions": ["0001108524-25-000238", "0001108524-26-000060"],
    "covers": "Q3 FY26 10-Q (Dec 2025) → FY26 10-K (Mar 2026)",
    "headline": "Full-year growth confirmed +10% with cRPO (+16%) outpacing total RPO (+14%), signaling acceleration ahead; Informatica adds agentic data layer.",
    "shifts": [
      {
        "area": "growth",
        "direction": "stable",
        "trend": "Q3 FY26 +9% ($10.26B) → FY26 full year +10% ($41.5B); Agentforce Platform/AI bucket Q3 +19% is the fastest segment",
        "note": "Consistent 9-10% growth; re-acceleration would require Agentforce/AI consumption to meaningfully expand"
      },
      {
        "area": "supply",
        "direction": "improving",
        "trend": "RPO Q3 $59.5B (down from $63.4B Jan-25) → FY26 $72.4B (+14%); cRPO $35.1B (+16%) — outpacing total RPO",
        "note": "cRPO acceleration vs total RPO is the strongest near-term demand signal in the filings"
      },
      {
        "area": "margins",
        "direction": "expanding",
        "trend": "Operating margin Q3 ~19% → FY26 20%; diluted EPS $7.80 (+23% YoY)",
        "note": "EPS expansion outpacing revenue growth through buybacks ($12.7B in FY26) and margin improvement"
      },
      {
        "area": "segments",
        "direction": "shifting",
        "trend": "Informatica $9.6B closed Nov 2025 adding $0.4B FY26 revenue; Agentforce branding unified across all product lines",
        "note": "AI agent consumption pricing remains 'relatively new and uncertain' — risk to estimates"
      }
    ],
    "verdict": "Thesis stable but not exciting — 10% growth is solid, and cRPO acceleration + Informatica are the incremental positives. Agentforce consumption-pricing ramp is the option value that could re-rate the stock."
  },

  "CRWV": {
    "as_of": AS_OF,
    "based_on_accessions": ["0001769628-26-000104", "0001769628-26-000222"],
    "covers": "FY25 10-K (Mar 2026) → Q1 2026 10-Q (May 2026)",
    "headline": "RPO nearly doubled in one quarter ($60.7B→$98.8B); Microsoft falling from 67% to 45% as Meta emerges at 20%; debt load accelerating toward $29B+.",
    "shifts": [
      {
        "area": "supply",
        "direction": "tightening",
        "trend": "RPO $60.7B (Dec 2025) → $98.8B (Mar 2026) — +63% in a single quarter; 39% extends to months 25-48",
        "note": "Take-or-pay contracted revenues; near-term revenue visibility exceptional but future execution risk grows"
      },
      {
        "area": "concentration",
        "direction": "improving",
        "trend": "Microsoft 67% of FY25 revenue → 45% of Q1 2026 revenue; Meta emerges at 20% in Q1",
        "note": "Diversification accelerating faster than expected; still heavily concentrated but improving trend"
      },
      {
        "area": "leverage",
        "direction": "tightening",
        "trend": "Total debt $21.6B (Dec 2025) + $4.0B converts + $2.8B senior notes + $1.0B equity post-Q1 = ~$28.4B in debt alone",
        "note": "Effective rates 9-15%; ~$107M sensitivity per 100bps; EBITDA coverage critical as capex scales"
      },
      {
        "area": "growth",
        "direction": "stable",
        "trend": "Revenue +168% FY25 → +112% Q1 2026 — deceleration on a higher base, but still triple-digit",
        "note": "Power constraints (850 MW active, 3.1 GW contracted) are the gating factor on revenue growth"
      }
    ],
    "verdict": "High-conviction story with high leverage risk — RPO surge and Microsoft de-concentration are positives; debt load at ~$29B+ on ~$8B annual revenue run-rate is the primary thesis risk if demand softens."
  },

  "CSCO": {
    "as_of": AS_OF,
    "based_on_accessions": ["0000858877-25-000171", "0000858877-26-000021"],
    "covers": "Q1 FY26 10-Q (Nov 2025) → Q2 FY26 10-Q (Feb 2026)",
    "headline": "Networking re-accelerated from +15% to +21% as AI Infrastructure pulled; Security declining; Silicon One purchase commitment buildup the key supply indicator.",
    "shifts": [
      {
        "area": "growth",
        "direction": "accelerating",
        "trend": "Networking Q1 +15% (+$1.0B) → Q2 +21% (+$1.4B); total revenue Q1 +8% → Q2 +10%",
        "note": "AI Infrastructure, Data Center Switching, Service Provider Routing all named as drivers in both quarters"
      },
      {
        "area": "segments",
        "direction": "shifting",
        "trend": "Networking +15/+21% vs Security -4% Q2; Security shift from on-prem to cloud subscriptions creating revenue headwind",
        "note": "Security decline expected to continue through H2 FY26; drag on overall growth rate"
      },
      {
        "area": "supply",
        "direction": "tightening",
        "trend": "Purchase commitments +9-10% and inventory +7% in both quarters, explicitly tied to Silicon One contract-manufacturing capacity",
        "note": "Securing Silicon One supply for hyperscaler AI infrastructure orders; obsolescence risk flagged"
      },
      {
        "area": "margins",
        "direction": "stable",
        "trend": "Product gross margin -0.6pts Q1 (mix/pricing) → +0.2pts Q2 (productivity); overall GM stable ~68%",
        "note": "Silicon One commitments are a margin-neutral volume play; pricing pressure from large hyperscaler deals managed"
      }
    ],
    "verdict": "Networking thesis intact — Silicon One for AI infrastructure is inflecting. Security drag and sluggish overall growth (8-10%) are the offsets. Stock story hinges on Networking becoming a bigger share of the mix."
  },

  "ETN": {
    "as_of": AS_OF,
    "based_on_accessions": ["0001551182-26-000007", "0001551182-26-000013"],
    "covers": "FY25 10-K (Feb 2026) → Q1 FY26 10-Q (May 2026)",
    "headline": "Electrical Americas backlog compounded to $14.5B (+44% YoY, +32% organic); orders +42% organic Q1; Boyd Thermal adds liquid cooling; commodity/tariff pressure on margins.",
    "shifts": [
      {
        "area": "supply",
        "direction": "tightening",
        "trend": "Electrical Americas backlog $13.2B (FY25, +31% YoY) → $14.5B (Q1 FY26, +44% YoY, +32% organic); book-to-bill 1.2x both periods",
        "note": "Data center is the primary driver in both periods; Electrical Global backlog +73% YoY Q1"
      },
      {
        "area": "growth",
        "direction": "accelerating",
        "trend": "Electrical Americas FY25 +16% ($13.3B) → Q1 organic orders +42%; Electrical Global FY25 +9% → Q1 organic orders +20%",
        "note": "Book-to-bill consistency signals order momentum continues to build; not a pull-forward"
      },
      {
        "area": "capex",
        "direction": "accelerating",
        "trend": "Boyd Thermal $9.5B acquisition (liquid cooling, chip-to-grid) announced Nov 2025; Fibrebond/Resilient/Ultra PCS completed in FY25",
        "note": "Boyd extends ETN from electrical distribution into liquid cooling — full DC power+cooling stack"
      },
      {
        "area": "margins",
        "direction": "deteriorating",
        "trend": "Americas operating margin FY25 29.9% → Q1 FY26 25.6% (-480bps); commodity and tariff inflation outpacing price",
        "note": "Margin pressure is cycle-induced, not structural; backlog lock-in provides pricing adjustment runway"
      }
    ],
    "verdict": "Thesis intact — backlog compounding and Boyd Thermal acquisition extend the addressable opportunity to full liquid-cooling stack. Margin compression is the near-term drag but backlog pricing will catch up."
  },

  "FN": {
    "as_of": AS_OF,
    "based_on_accessions": ["0001408710-26-000008", "0001408710-26-000016"],
    "covers": "Q2 FY26 10-Q (Feb 2026) → Q3 FY26 10-Q (May 2026)",
    "headline": "Revenue accelerated from +36% to +39%; DCI nearly doubled (+90% Q3) as inter-DC AI fabric demand surges; HPC (AI server) category at $107M/quarter.",
    "shifts": [
      {
        "area": "growth",
        "direction": "accelerating",
        "trend": "Revenue Q2 $1.13B (+35.9% YoY) → Q3 $1.21B (+39.3% YoY); 9-month $3.33B (+32.5%)",
        "note": "Consistent top-line acceleration driven by product mix shift toward higher-value DCI and telecom"
      },
      {
        "area": "segments",
        "direction": "shifting",
        "trend": "DCI Q2 strong → Q3 $197M (+90.4% YoY); Telecom Q3 $431M (+42.5%); Datacom flat/slightly down both quarters as mix shifts to DCI",
        "note": "'Scale across' AI interconnect is the emerging DCI driver — 1.6T-cycle hyperscaler inter-DC fabric"
      },
      {
        "area": "supply",
        "direction": "tightening",
        "trend": "HPC category Q2 $85.6M → Q3 $106.7M (+25% QoQ); 9-month HPC $208M — new AI-specific disclosure growing rapidly",
        "note": "Customer concentration Q2: 4 customers >10% (59%) vs prior-year 2 customers (49%) — AI buildout concentrating demand"
      },
      {
        "area": "margins",
        "direction": "stable",
        "trend": "Gross margin Q2 12.2% → Q3 11.9% (-30bps); operating income Q3 +52.1% on volume leverage despite slight GM dip",
        "note": "Inventory build (OCF down) and Chonburi expansion capex are temporary margin headwinds"
      }
    ],
    "verdict": "Thesis intact and accelerating — DCI +90% confirms FN is capturing the 1.6T AI scale-across wave. HPC disclosure growth is the incremental positive signal not yet in consensus models."
  },

  "GEV": {
    "as_of": AS_OF,
    "based_on_accessions": ["0001996810-26-000015", "0001996810-26-000064"],
    "covers": "FY25 10-K (Jan 2026) → Q1 2026 10-Q (Apr 2026)",
    "headline": "RPO compounding +9% QoQ to $163B; Power EBITDA margin expanding from 14.7% to 16.3%; HA-Turbine order pace now implies ~50 units/year.",
    "shifts": [
      {
        "area": "supply",
        "direction": "tightening",
        "trend": "Total RPO $150.2B (YE25) → $163.3B (Q1 2026, +9% QoQ, +32% YoY); equipment RPO $64.2B → $75.9B (+18% in one quarter)",
        "note": "HA-Turbine orders FY25 43 units, Q1 12 units ($48/year pace); heavy-duty GW orders FY25 29.8 GW, Q1 8.1 GW ($32/year pace)"
      },
      {
        "area": "margins",
        "direction": "expanding",
        "trend": "Power segment EBITDA margin FY25 14.7% → Q1 2026 16.3% (+1.6pts); Q1 EBITDA +$439M YoY",
        "note": "Favorable pricing + higher volume on HA-Turbine deliveries and aeroderivative mix"
      },
      {
        "area": "growth",
        "direction": "accelerating",
        "trend": "FY25 revenue +9% ($38.1B), adjusted EBITDA +$1.2B; Q1 2026 +16%, EBITDA +$439M in one quarter",
        "note": "Q1 includes Prolec GE acquisition gain; adjusted EBITDA trend is the clean signal"
      },
      {
        "area": "capex",
        "direction": "accelerating",
        "trend": "Prolec GE (50% stake, transformer manufacturing) closed Feb 2026; Electrification RPO growing from AC substation/HVDC/synchronous condenser demand",
        "note": "First commercial SMR contract in North America; transformers now in-house via Prolec"
      }
    ],
    "verdict": "Thesis strongly intact — RPO compounding, margin expanding, and multi-year turbine backlog are all pointing the same direction. Prolec Transformer acquisition adds a decade of grid-investment exposure."
  },

  "GNRC": {
    "as_of": AS_OF,
    "based_on_accessions": ["0001437749-26-004568", "0001437749-26-014882"],
    "covers": "FY25 10-K (Feb 2026) → Q1 FY26 10-Q (May 2026)",
    "headline": "C&I (data center) inflected from +5% FY25 to +28% in Q1; residential recovering; large-MW diesel gensets for data centers now commercial; margins recovering.",
    "shifts": [
      {
        "area": "growth",
        "direction": "accelerating",
        "trend": "C&I FY25 +4.9% → Q1 FY26 +28%; residential FY25 -6.8% → Q1 FY26 +1%",
        "note": "Data-center prime power is the driver of C&I acceleration; Enercon acquisition adds hyperscale custom power"
      },
      {
        "area": "margins",
        "direction": "expanding",
        "trend": "Adjusted EBITDA margin FY25 17.0% → Q1 FY26 Residential 25.1% (vs 20.3%), C&I 13.0% (vs 11.4%)",
        "note": "Both segments expanding margins simultaneously — operational improvements and price realization"
      },
      {
        "area": "supply",
        "direction": "tight",
        "trend": "'Large-megawatt backup generator market significantly supply-constrained' (FY25 10-K) — no easing language in Q1 FY26",
        "note": "Supply constraint is the thesis-support signal; new large-MW products launched FY25 for data center entry"
      },
      {
        "area": "segments",
        "direction": "shifting",
        "trend": "Reorganized Mar 2026 from Domestic/International to Residential/C&I to align with strategic focus on data-center C&I",
        "note": "Acquired Enercon Engineering in Q1 for hyperscale/enterprise custom power equipment"
      }
    ],
    "verdict": "Thesis improving — C&I data-center inflection is real and accelerating. Supply constraint language unchanged means pricing power intact. Residential recovery removes the drag."
  },

  "GOOGL": {
    "as_of": AS_OF,
    "based_on_accessions": ["0001652044-26-000018", "0001652044-26-000048"],
    "covers": "FY25 10-K (Feb 2026) → Q1 2026 10-Q (Apr 2026)",
    "headline": "Cloud re-accelerated dramatically from +36% to +63%; RPO nearly doubled in one quarter to $468B on multi-GW TPU deals; capex at $35.7B/quarter.",
    "shifts": [
      {
        "area": "growth",
        "direction": "accelerating",
        "trend": "Cloud FY25 $58.7B (+36% YoY) → Q1 2026 $20.0B (+63% YoY); Q1 op income $6.6B vs $2.2B prior year (3x YoY, 33% margin)",
        "note": "Re-acceleration rate is unprecedented — +27pts from FY25 to Q1 rate; margin expansion concurrent with revenue surge"
      },
      {
        "area": "supply",
        "direction": "tightening",
        "trend": "RPO $242.8B (Dec 2025) → $467.6B (Mar 2026) — +93% in one quarter; multi-GW TPU hardware supply agreements first-time disclosed",
        "note": "TPU supply agreements generate revenue starting late 2026, majority 2027 — demand locked in well ahead of delivery"
      },
      {
        "area": "capex",
        "direction": "accelerating",
        "trend": "FY25 $91.4B (+74% YoY) → Q1 $35.7B ($143B annualized); 'significantly increase' remains the FY26 guidance language",
        "note": "Wiz ($29.5B) and Intersect ($5.9B) acquired Q1 2026; Waymo received $16B in Feb 2026"
      },
      {
        "area": "margins",
        "direction": "expanding",
        "trend": "Cloud op margin FY25 ~24% → Q1 2026 33% (+9pts) even as capex surges",
        "note": "Operating leverage on large existing infra base — revenue growing faster than depreciation + opex"
      }
    ],
    "verdict": "Thesis strongly intact — Cloud re-acceleration + margin expansion + RPO near-doubling is the clearest bull case in the hyperscaler group. Multi-GW TPU disclosure is new and significant: GOOGL is now also a hardware-supply player."
  },

  "HPE": {
    "as_of": AS_OF,
    "based_on_accessions": ["0001645590-25-000130", "0001645590-26-000032"],
    "covers": "FY25 10-K (Dec 2025) → Q1 FY26 10-Q (Mar 2026)",
    "headline": "Juniper integration driving Networking +151%; Cloud & AI server segment growing but GPU margins 'limited'; ARR $3.15B +63% on Networking mix.",
    "shifts": [
      {
        "area": "growth",
        "direction": "accelerating",
        "trend": "FY25 revenue +13.8% (Juniper 4-month partial) → Q1 FY26 +18.4% (Juniper full quarter); Networking FY25 +51% → Q1 +151%",
        "note": "Juniper full-quarter inclusion inflates Q1 comparisons; organic momentum still positive on AI server demand"
      },
      {
        "area": "segments",
        "direction": "shifting",
        "trend": "New segment structure: Cloud & AI (server+storage) -2.7% vs Networking +151%; GPU-heavy AI servers growing but 'limited margins' disclosed",
        "note": "HPE explicitly calls GPU server margins limited — AI servers are a revenue story, not yet a margin story"
      },
      {
        "area": "margins",
        "direction": "expanding",
        "trend": "Non-GAAP op margin FY25 9.8% (-0.7pts on impairment) → Q1 FY26 12.7% (+2.8pts) on Juniper networking mix",
        "note": "Networking margin much higher than server; Juniper mix is the engine of non-GAAP margin expansion"
      },
      {
        "area": "supply",
        "direction": "tightening",
        "trend": "ARR $3.15B (+63% on Networking from Merger) vs $1.93B prior; memory component shortages flagged Q1 as new supply risk",
        "note": "Supply risk is on components, not HPE system-level — manageable but adds backlog execution risk"
      }
    ],
    "verdict": "Thesis improving on Juniper — Networking ARR + margin expansion is the story. GPU server margins are the drag; HPE needs Juniper AI networking to prove out at scale to justify the $13.4B paid."
  },

  "HUBB": {
    "as_of": AS_OF,
    "based_on_accessions": ["0001628280-26-007500", "0001628280-26-029110"],
    "covers": "FY25 10-K (Feb 2026) → Q1 FY26 10-Q (May 2026)",
    "headline": "Both segments accelerating — Electrical Solutions +7% to +12% on datacenter; Utility Solutions +2% to +10% on T&D; adjusted op margin expanding.",
    "shifts": [
      {
        "area": "growth",
        "direction": "accelerating",
        "trend": "Electrical Solutions FY25 +7.1% → Q1 FY26 +11.8%; Utility Solutions FY25 +2.0% → Q1 FY26 +10%",
        "note": "Data center driving Electrical; T&D investment driving Utility; both accelerating simultaneously is rare"
      },
      {
        "area": "margins",
        "direction": "expanding",
        "trend": "Adjusted op margin +80bps FY25 → +110bps Q1 FY26; Utility Solutions Q1 adjusted +190bps to 21.8%",
        "note": "Both segments expanding on pricing/productivity, partially offset by commodity/tariff inflation"
      },
      {
        "area": "supply",
        "direction": "stable",
        "trend": "Backlog $2.16B at YE25 (vs $1.90B YE24); Q1 FY26 backlog building further",
        "note": "Backlog 'substantially all ship in 2026' provides high near-term visibility"
      }
    ],
    "verdict": "Thesis intact — synchronized acceleration across both segments is a quality signal. HUBB benefits from both AI infrastructure (electrical solutions) and grid modernization (T&D) without depending on either alone."
  },

  "INTC": {
    "as_of": AS_OF,
    "based_on_accessions": ["0000050863-26-000011", "0000050863-26-000079"],
    "covers": "FY25 10-K (Jan 2026) → Q1 2026 10-Q (Apr 2026)",
    "headline": "Intel Foundry loss widened to $2.4B in Q1; DCAI re-accelerated +22% on 18A/premium-mix; NVIDIA $5B strategic investment signals confidence in 18A but turnaround timeline long.",
    "shifts": [
      {
        "area": "growth",
        "direction": "accelerating",
        "trend": "DCAI FY25 $14.3B (+$794M YoY) → Q1 2026 $5.1B (+22% YoY) on 27% higher ASPs from premium mix",
        "note": "Volume -5% due to internal supply constraints (substrates, memory); ASP doing the work"
      },
      {
        "area": "segments",
        "direction": "deteriorating",
        "trend": "Intel Foundry FY25 operating loss $10.3B (vs $13.3B FY24) → Q1 2026 loss $2.4B (vs $2.3B Q1 2025); external revenue $307M FY25 → $174M Q1",
        "note": "Foundry loss narrowing slowly; 18A is in high-volume production but external customer pipeline thin — Intel 14A paused"
      },
      {
        "area": "supply",
        "direction": "tight",
        "trend": "Intel 7 supply constraints hit Q4 FY25 and expected throughout 2026; substrates, memory, other components flagged Q1",
        "note": "Supply constraints are internal to Intel — both Foundry capacity and component sourcing"
      },
      {
        "area": "leverage",
        "direction": "improving",
        "trend": "SoftBank $2B equity Sep 2025; NVIDIA $5B strategic partnership equity; $3.2B CHIPS Secure Enclave disbursements pending (3M shares of 159M released to date)",
        "note": "Capital inflows from partners validate 18A technology but do not resolve the $10B+ annual Foundry operating loss rate"
      }
    ],
    "verdict": "Turnaround thesis intact but slow — DCAI re-acceleration and NVIDIA partnership are positives; Foundry losses and supply constraints are the overhang. No thesis-break, but also no inflection yet."
  },

  "KLAC": {
    "as_of": AS_OF,
    "based_on_accessions": ["0000319201-26-000008", "0000319201-26-000016"],
    "covers": "Q2 FY26 10-Q (Jan 2026) → Q3 FY26 10-Q (Apr 2026)",
    "headline": "Revenue re-accelerated to +11% (record quarter); Korea memory capex surging (+80%); China declining from 30% to 24%; gross margins stable at ~61%.",
    "shifts": [
      {
        "area": "growth",
        "direction": "accelerating",
        "trend": "Q2 $3.30B (+7% YoY) → Q3 $3.42B (+11% YoY); 9-month $9.89B vs $8.81B prior year (+12%)",
        "note": "Record quarter driven by DRAM/HBM memory investment plus steady foundry/logic"
      },
      {
        "area": "china",
        "direction": "deteriorating",
        "trend": "Q2 China $995M (30.2%) → Q3 $830M (24.3%); nine-month China flat at $3.09B — export controls capping",
        "note": "China falling as a share from 30% → 24%; Korea/Taiwan/US growing to fill the gap"
      },
      {
        "area": "segments",
        "direction": "shifting",
        "trend": "Korea Q2 +34% → Q3 +80% on memory DRAM/HBM investment; North America Q2 +38% → Q3 +40% steady",
        "note": "Korea surge confirms HBM capacity is actively being built; KLAC is the gating process-control tool"
      },
      {
        "area": "margins",
        "direction": "stable",
        "trend": "Gross margin Q2 61.4% → Q3 61.1% (-0.3pts); DRAM chip cost in image-computers flagged as transitory headwind",
        "note": "17th consecutive annual dividend increase to $2.30/share; $10.31B repurchase authorization remaining"
      }
    ],
    "verdict": "Thesis intact — KLAC is capturing the HBM capacity wave via Korea surge. China erosion is structural but manageable (already declining). Record quarterly revenue with stable margins is the quality signal."
  },

  "LEU": {
    "as_of": AS_OF,
    "based_on_accessions": ["0001628280-26-007117", "0001628280-26-030891"],
    "covers": "FY25 10-K (Feb 2026) → Q1 FY26 10-Q (May 2026)",
    "headline": "Piketon build accelerating with Fluor EPC and $900M DOE task order; backlog ticking up $3.8B→$3.9B; advanced technology costs surging +530% as capital deployment begins.",
    "shifts": [
      {
        "area": "supply",
        "direction": "improving",
        "trend": "FY25: $900M HALEU DOE task order (Jan 2026), Oak Ridge centrifuge manufacturing begun (Dec 2025); Q1: Fluor EPC signed (Feb 2026), Oklo JV exploration for HALEU deconversion",
        "note": "De-risking Piketon execution — EPC contract, DOE task order, and manufacturing facility all started in sequence"
      },
      {
        "area": "growth",
        "direction": "stable",
        "trend": "Backlog $3.8B (FY25) → $3.9B (Q1); $2.3B → $2.4B contingent LEU (all under definitive agreements pending capacity)",
        "note": "Backlog growing but slowly; revenue is SWU-volume-timing-sensitive — quarterly variation expected"
      },
      {
        "area": "capex",
        "direction": "accelerating",
        "trend": "FY25: multiple contracts + CHIPS credits; Q1: advanced tech costs $18.9M (vs $3.0M, +530%); FY26 capex guided $350-450M",
        "note": "Capital deployment phase beginning; cash burn accelerating; $805M convertible (Aug 2025) provides runway"
      },
      {
        "area": "regulation",
        "direction": "improving",
        "trend": "Only NRC-licensed commercial HALEU enricher; Aurora DOE safety design agreement approved Feb 2026; Oklo co-location JV announced",
        "note": "Regulatory moat solidifying; partnerships with Oklo and Fluor expand the industrial ecosystem"
      }
    ],
    "verdict": "Thesis intact — de-risking milestones are hitting on schedule; capital ramp is beginning. The thesis is predicated on HALEU becoming a commercial market; SWU spot price at $200 vs $34 historic low confirms nuclear fuel thesis."
  },

  "LITE": {
    "as_of": AS_OF,
    "based_on_accessions": ["0001628280-26-005129", "0001628280-26-030777"],
    "covers": "Q2 FY26 10-Q (Feb 2026) → Q3 FY26 10-Q (May 2026)",
    "headline": "Revenue acceleration from +65.5% to +90.1% on 200G-lane mix; gross margin structurally re-rated from 36% to 44%; allocation language hardened from 'has led to' to 'has required'.",
    "shifts": [
      {
        "area": "growth",
        "direction": "accelerating",
        "trend": "Revenue Q2 $665.5M (+65.5% YoY) → Q3 $808.4M (+90.1% YoY); 9-month $2.01B (+72.4%)",
        "note": "Optical circuit switches grew from >$10M Q2 to >$25M Q3; laser chip ramp continues to outpace supply"
      },
      {
        "area": "margins",
        "direction": "expanding",
        "trend": "Gross margin Q2 36.1% (+1,130bps YoY) → Q3 44.2% (+1,540bps YoY); 9-month 38.8% (+1,300bps)",
        "note": "200G-lane ASP mix shift is structurally re-rating margins — not a one-quarter effect"
      },
      {
        "area": "supply",
        "direction": "tight",
        "trend": "'Demand outpacing supply — has led to allocation decisions' (Q2) → 'has required us to make decisions on supply allocation' (Q3) — language hardened",
        "note": "Allocation discipline means LITE is prioritizing highest-value customers; no supply catch-up language added"
      },
      {
        "area": "concentration",
        "direction": "tightening",
        "trend": "Top-2 customers Q2: 24%+17% = 41% → Q3: 26%+12% = 38%; top customer rose from 24% to 26%",
        "note": "Top customer concentration tightening while second-customer share falling — hyperscaler mix consolidating"
      }
    ],
    "verdict": "Thesis at peak strength — 90% revenue growth with 44% gross margin and hardening supply-allocation language is the strongest combination in the stack. The 200G-lane cycle has legs into at least FY27."
  },

  "LRCX": {
    "as_of": AS_OF,
    "based_on_accessions": ["0000707549-26-000009", "0000707549-26-000022"],
    "covers": "Q2 FY26 10-Q (Jan 2026) → Q3 FY26 10-Q (Apr 2026)",
    "headline": "Revenue re-accelerated +9% QoQ on DRAM investment surge; memory mix rose from 34% to 39%; China steady at 34-35%; gross margin stable near 50%.",
    "shifts": [
      {
        "area": "growth",
        "direction": "accelerating",
        "trend": "Q2 FY26 $5.34B (flat QoQ) → Q3 FY26 $5.84B (+9% QoQ); 9-month $16.51B vs $13.26B prior year (+24%)",
        "note": "DRAM customer investments in HBM capacity are the Q3 surge driver"
      },
      {
        "area": "segments",
        "direction": "shifting",
        "trend": "Memory 34% (Q2) → 39% (Q3) of mix on DRAM/HBM; Foundry 59% → 54%; Korea 20% → 23% of revenue",
        "note": "HBM capacity build is shifting the customer mix toward memory; foundry/logic spend still resilient"
      },
      {
        "area": "china",
        "direction": "stable",
        "trend": "Q2 China 35% → Q3 China 34%; nine-month trend shows gradual stepdown as export controls constrain leading-edge tools",
        "note": "China at 34-35% is a manageable floor; tool type mix (legacy-node compatible) limits export-control exposure"
      },
      {
        "area": "margins",
        "direction": "stable",
        "trend": "Gross margin Q2 49.6% → Q3 49.8% (+0.2pts); customer-support revenue growing faster than systems (+6% QoQ vs +11%)",
        "note": "Service revenue growth outpacing systems is a margin-quality signal — installed base monetization improving"
      }
    ],
    "verdict": "Thesis intact — DRAM/HBM surge is pulling LRCX into a re-acceleration after a flat Q2. Memory capex is durable as long as AI inference demand drives HBM build; China not the constraint it once was."
  },

  "META": {
    "as_of": AS_OF,
    "based_on_accessions": ["0001628280-26-003942", "0001628280-26-028526"],
    "covers": "FY25 10-K (Jan 2026) → Q1 2026 10-Q (Apr 2026)",
    "headline": "Revenue re-accelerated from +22% to +33%; capex guidance raised again to $125-145B; $237B+ in non-cancelable commitments — a decade-long infrastructure lock-in.",
    "shifts": [
      {
        "area": "growth",
        "direction": "accelerating",
        "trend": "FY25 $201.0B (+22% YoY) → Q1 2026 $56.3B (+33% YoY); ad impressions +12% FY25 → +19% Q1; price per ad +9% → +12%",
        "note": "Both volume and pricing re-accelerating simultaneously — advertising flywheel intact"
      },
      {
        "area": "capex",
        "direction": "accelerating",
        "trend": "FY25 $72.2B → Q1 $19.8B ($79B annualized); FY26 guidance raised to $125-145B (from $115-135B at 10-K)",
        "note": "Three consecutive guidance raises over 12 months; AI infrastructure is the primary driver"
      },
      {
        "area": "supply",
        "direction": "tightening",
        "trend": "Non-cancelable commitments $237.7B (Mar 2026) + $182.9B operating leases not yet commenced = $420B+ total infrastructure lock-in",
        "note": "These commitments flow directly to supply-chain beneficiaries — GPUs, networking, power, cooling"
      },
      {
        "area": "margins",
        "direction": "stable",
        "trend": "Family of Apps operating margin FY25 ~51% → Q1 2026 ~41%; consolidated op margin Q1 ~41% — holding as capex grows",
        "note": "RL operating loss $4.03B Q1 ($16B annualized) is the margin drag; ad core margin remains high"
      }
    ],
    "verdict": "Thesis strongest in hyperscalers — capex raising while revenue is re-accelerating is rare combination. $420B+ infrastructure commitment is a decade-long demand signal for the entire AI stack."
  },

  "MOD": {
    "as_of": AS_OF,
    "based_on_accessions": ["0001104659-25-103646", "0001104659-26-010790"],
    "covers": "Q2 FY26 10-Q (Oct 2025) → Q3 FY26 10-Q (Feb 2026)",
    "headline": "Climate Solutions (DC cooling) accelerated from +24% to +51%; RMT spin-off announced to create pure-play; margin headwinds from ramp easing.",
    "shifts": [
      {
        "area": "growth",
        "direction": "accelerating",
        "trend": "Climate Solutions Q2 $454.4M (+24%) → Q3 $545.M (+51%); data center revenue +$67M Q2 → +$130M Q3 YoY",
        "note": "Hyperscale and colocation in North America and Europe cited as primary drivers in both filings"
      },
      {
        "area": "segments",
        "direction": "transforming",
        "trend": "Jan 2026: announced Performance Technologies RMT spin to merge with Gentherm (~$1B value); MOD retains Climate Solutions only",
        "note": "Pure-play DC/commercial HVAC: $210M cash to MOD at close, MOD shareholders get ~40% of combined Gentherm"
      },
      {
        "area": "margins",
        "direction": "improving",
        "trend": "Climate Solutions op margin Q2 13.7% (-440bps YoY from US ramp) → Q3 15.3% (-200bps YoY); headwinds easing",
        "note": "$100M incremental DC manufacturing capex announced Q2; Q3 new facility lease signed — ramp inefficiencies transitional"
      },
      {
        "area": "capex",
        "direction": "accelerating",
        "trend": "Q2: $100M incremental DC capex announced; Q3: incremental lease for new data-center manufacturing facility signed",
        "note": "Capex is demand-pull for DC cooling capacity; utilization ramp is the margin recovery catalyst"
      }
    ],
    "verdict": "Thesis improving — acceleration to +51% and margin recovery signal the ramp phase is transitioning to steady-state. RMT spin is a catalyst that crystallizes pure-play DC cooling valuation."
  },

  "MRVL": {
    "as_of": AS_OF,
    "based_on_accessions": ["0001835632-25-000197", "0001835632-26-000011"],
    "covers": "Q3 FY26 10-Q (Dec 2025) → FY26 10-K (Mar 2026)",
    "headline": "Data Center +46% FY26; Celestial AI and XConn acquisitions post-close add photonic fabric and CXL/PCIe; roadmap from 5nm to 1.4nm is the clearest in custom ASIC.",
    "shifts": [
      {
        "area": "growth",
        "direction": "stable",
        "trend": "Data Center Q3 $1.52B (+38% YoY) → FY26 $6.1B (+46% FY26 vs FY25); Communications recovering +31% FY26",
        "note": "Consistent mid-40s data center growth; custom AI ASIC and electro-optics both contributing"
      },
      {
        "area": "supply",
        "direction": "tightening",
        "trend": "Celestial AI closed Feb 2026 (~$1.3B cash + shares) for photonic fabric scale-up interconnect; XConn closed Feb 2026 ($280M) for PCIe/CXL switching",
        "note": "Two bolt-ons in one month extend the AI interconnect stack from electro-optics to photonics and CXL — filling white space"
      },
      {
        "area": "segments",
        "direction": "reshaping",
        "trend": "Auto ethernet sold to Infineon Aug 2025 ($2.5B gain); Comm/carrier/consumer/auto consolidated to one segment; Data Center sole disclosed segment from Q4 FY26",
        "note": "Portfolio simplification to DC-only reporting matches the revenue concentration; 74% DC in FY26"
      },
      {
        "area": "concentration",
        "direction": "easing",
        "trend": "Distributor A Q3 38% → FY26 37%; Direct Customer A 11% → 14% — slight shift from distributor to direct",
        "note": "Customer concentration still high (top-10 ~81%) but Distributor A share slowly normalizing"
      }
    ],
    "verdict": "Thesis intact and deepening — Celestial + XConn extend MRVL into full-stack AI interconnect (electro-optics + photonics + CXL). 74% DC revenue concentration is a strength, not a risk, given the secular demand."
  },

  "MSFT": {
    "as_of": AS_OF,
    "based_on_accessions": ["0001193125-26-027207", "0001193125-26-191507"],
    "covers": "Q2 FY26 10-Q (Jan 2026) → Q3 FY26 10-Q (Apr 2026)",
    "headline": "Azure held +39-40%; capex stable at $30B/quarter ($120B annualized); commercial RPO plateaued at $625-627B after doubling YoY; cloud gross margin pressure from AI infra.",
    "shifts": [
      {
        "area": "growth",
        "direction": "stable",
        "trend": "Azure Q2 +39% → Q3 +40%; MS Cloud Q2 $51.5B (+26%) → Q3 $54.5B (+29%)",
        "note": "Slight re-acceleration but both within range; consistent high-30s Azure growth is the baseline"
      },
      {
        "area": "capex",
        "direction": "stable",
        "trend": "Q2 $29.9B → Q3 $30.9B; 9-month $80.1B vs $40.9B prior year (+96%); at a quarterly plateau",
        "note": "Plateau at $30B/quarter signals infrastructure investment may be at or near peak run-rate"
      },
      {
        "area": "supply",
        "direction": "stable",
        "trend": "Commercial RPO Q2 $625B (+110% YoY) → Q3 $627B (+99% YoY) — growth rate decelerating as base inflates",
        "note": "RPO growth rate decelerating from 110% to 99% as OpenAI contract base effect fades"
      },
      {
        "area": "margins",
        "direction": "contracting",
        "trend": "Cloud gross margin 'dropped to 67%' Q2 on AI infrastructure investments; trend not reversed in Q3",
        "note": "AI infra depreciation is the primary pressure; expect gradual recovery as assets scale utilization"
      }
    ],
    "verdict": "Thesis intact — Azure consistent at 39-40% is the durable flywheel. Cloud gross margin pressure is the watch item; capex at a plateau suggests the P&L headwind may be near its trough."
  },

  "MU": {
    "as_of": AS_OF,
    "based_on_accessions": [
      "0000723125-25-000044",
      "0000723125-25-000046",
      "0000723125-26-000004",
      "0000723125-26-000006"
    ],
    "covers": "Q1 FY26 (Nov 2025) → Q2 FY26 (Mar 2026) — two 10-Qs and paired 8-Ks",
    "headline": "Beat-and-raise cadence widening — Q2 beat guide by 28%, EPS by 45%; Q3 guide implies +40% QoQ more; GM expanded 56%→75%→81% guided.",
    "shifts": [
      {
        "area": "growth",
        "direction": "accelerating",
        "trend": "Revenue $13.6B (Q1) → $23.9B (Q2, +75% QoQ) → $33.5B guide (Q3, +40% QoQ); YoY: +57% → +196% → guided +250%+",
        "note": "QoQ growth re-accelerated from +21% to +75% and is guided +40% again in Q3"
      },
      {
        "area": "margins",
        "direction": "expanding",
        "trend": "Non-GAAP GM 56.8% (Q1) → 74.9% (Q2) → ~81% guide (Q3) — +24pts of expansion in two quarters",
        "note": "DRAM ASPs +mid-60% QoQ in Q2; pricing power from AI-driven supply shortage compounding"
      },
      {
        "area": "guidance",
        "direction": "raised",
        "trend": "Q2 revenue guided $18.7B → printed $23.9B (+28% beat); Q3 now guided to $33.5B (+40% QoQ)",
        "note": "Beat magnitude widening — credibility on the raised Q3 guide is high"
      },
      {
        "area": "supply",
        "direction": "tight",
        "trend": "'Supply allocation decisions may impact certain customers' (Q1) → 'Industry supply allocation decisions continue' (Q2) — no easing language added",
        "note": "Same constraint language for two consecutive quarters; tightness is persistent, not transient"
      },
      {
        "area": "concentration",
        "direction": "tightening",
        "trend": "One customer reached 13% of six-month revenue (Q2 disclosure) — primarily CMBU (HBM/hyperscale DRAM)",
        "note": "HBM hyperscaler reliance increasing; single-customer dependency to monitor"
      },
      {
        "area": "capex",
        "direction": "stable",
        "trend": "FY26 capex ~$20B guided; Q1 $5.39B + Q2 ~$5.0B = $10.4B H1 run-rate — on track for $20B+",
        "note": "Singapore HBM advanced-packaging fab broke ground; Idaho second leading-edge fab targeted 2028"
      },
      {
        "area": "capital_returns",
        "direction": "raised",
        "trend": "Dividend $0.115/share (Q1) → $0.15/share (Q2, +30%); $7.49B of $10B buyback executed",
        "note": "First meaningful dividend hike in years; signals management confidence cycle durability"
      }
    ],
    "verdict": "Thesis intact and strengthening — beat-and-raise cadence is widening, GM expansion compounding, and guidance credibility high. Only emerging risk is HBM customer concentration (13% of six-month revenue). Supply tightness language unchanged — bullish for memory pricing through CY2026."
  },

  "MXL": {
    "as_of": AS_OF,
    "based_on_accessions": ["0001288469-26-000011", "0001288469-26-000029"],
    "covers": "FY25 10-K (Jan 2026) → Q1 2026 10-Q (Apr 2026)",
    "headline": "Revenue re-accelerated from +30% to +43%; customer concentration broadening (top customer 20%+ → 13%); optical DSP infrastructure is the leading growth vector.",
    "shifts": [
      {
        "area": "growth",
        "direction": "accelerating",
        "trend": "FY25 $467.6M (+30% YoY) → Q1 2026 $137.2M (+43% YoY); infrastructure +$36.3M Q1 confirms DSP optical traction",
        "note": "Recovery from inventory trough: broadband +59% FY25, infrastructure +$34.3M; Q1 infrastructure again the growth leader"
      },
      {
        "area": "concentration",
        "direction": "improving",
        "trend": "Top customer FY25 >20% of revenue → Q1 2026 13%; top-10 FY25 65% → Q1 56%",
        "note": "Customer base broadening as optical DSP design-wins diversify across hyperscalers and telcos"
      },
      {
        "area": "segments",
        "direction": "shifting",
        "trend": "Infrastructure growing fastest both FY25 (+$34.3M) and Q1 2026 (+$36.3M); 800G→1.6T DSP roadmap confirmed",
        "note": "Broadband and connectivity stable; optical DSP is the incremental TAM growth driver"
      },
      {
        "area": "margins",
        "direction": "stable",
        "trend": "Gross margin FY25 57% (+3pts) on mix and lower amortization; Q1 not explicitly broken out but volume-led growth positive",
        "note": "R&D will need to re-expand for next-gen 1.6T products; current R&D lean from FY25 workforce reductions"
      }
    ],
    "verdict": "Thesis intact — customer concentration broadening + infrastructure acceleration confirms optical DSP is gaining design-wins. 1.6T cycle is the next leg; R&D investment timing is the risk to watch."
  },

  "NOW": {
    "as_of": AS_OF,
    "based_on_accessions": ["0001373715-26-000007", "0001373715-26-000056"],
    "covers": "FY25 10-K (Jan 2026) → Q1 2026 10-Q (Apr 2026)",
    "headline": "Consistent 21-22% growth with cRPO outpacing total RPO; Now Assist AI agents embedded across all product lines; consumption pricing still 'relatively new and uncertain'.",
    "shifts": [
      {
        "area": "growth",
        "direction": "stable",
        "trend": "FY25 $13.28B (+21%) → Q1 2026 $3.77B (+22%); subscription revenue 97% of mix in both periods",
        "note": "Steady-state 21-22% growth; no visible inflection from Agentforce/AI consumption yet"
      },
      {
        "area": "supply",
        "direction": "stable",
        "trend": "RPO FY25 $28.2B (+27%) → Q1 2026 $27.7B (+25% YoY, slight QoQ dip); cRPO FY25 +25% → Q1 +23%",
        "note": "cRPO growth rate slight moderation; still outpacing total RPO suggesting near-term demand solid"
      },
      {
        "area": "segments",
        "direction": "stable",
        "trend": "US federal self-hosted +$83M in FY25; Q1 self-hosted $138M (slight decline from $157M Q1 FY25); enterprise AI rollout continuing",
        "note": "Agentforce AI consumption model is the option value — management cites uncertainty on timing/size"
      }
    ],
    "verdict": "Thesis stable — 21-22% growth at 97% subscription is best-in-class SaaS quality. Agentforce consumption-pricing is the re-rating catalyst that hasn't materialized yet. Safe hold, not yet a high-conviction long."
  },

  "NVDA": {
    "as_of": AS_OF,
    "based_on_accessions": ["0001045810-25-000230", "0001045810-26-000021"],
    "covers": "Q3 FY26 10-Q (Nov 2025) → FY26 10-K (Feb 2026)",
    "headline": "DC growth held at +66-68% YoY; 4-way customer concentration now formally disclosed (22/15/13/11%); China zero after $4.5B charge; Rubin announced on annual cadence.",
    "shifts": [
      {
        "area": "growth",
        "direction": "accelerating",
        "trend": "Data Center Q3 FY26 +66% YoY ($51.2B) → FY26 full-year +68% YoY; Networking +162% YoY Q3 on NVLink scale-up",
        "note": "Slight full-year re-acceleration above Q3 rate; Blackwell is now majority of DC revenue"
      },
      {
        "area": "concentration",
        "direction": "tightening",
        "trend": "4 direct customers each >10% in Q3: 22%/15%/13%/11%; FY26 10-K re-confirms same hyperscaler concentration",
        "note": "Concentration first explicitly disclosed in Q3; full-year 10-K did not increase further — stable"
      },
      {
        "area": "china",
        "direction": "deteriorating",
        "trend": "Q3 China $3.0B (vs $8.1B prior-year Q3); FY26: $4.5B H20 inventory charge in Q1 FY26; China revenue now effectively zero",
        "note": "H20 optionality fully impaired; Feb 2026 H200 license carries 25% US re-import tariff — structural, not temporary"
      },
      {
        "area": "supply",
        "direction": "tight",
        "trend": "'Data center, energy, and capital availability as constraints on customer deployments' (10-K) — same framing as Q3",
        "note": "$7.5B new data center lease obligations in FY26 Q4-FY30 signals NVDA is investing in supply-side to relieve constraints"
      },
      {
        "area": "guidance",
        "direction": "raised",
        "trend": "Q1 FY27 guided $43.0B ± 2% revenue, 73.5% non-GAAP GM — meaningful sequential raise",
        "note": "Rubin platform on annual cadence after Blackwell — roadmap visibility extended"
      }
    ],
    "verdict": "Thesis intact — DC growth holding at +66-68% with clear roadmap through Rubin. China is a write-off, not a future drag. Only new risk is customer concentration (4 customers = 61% of compute), which tightened but is now stable."
  },

  "NVT": {
    "as_of": AS_OF,
    "based_on_accessions": ["0001628280-26-008608", "0001628280-26-029370"],
    "covers": "FY25 10-K (Feb 2026) → Q1 FY26 10-Q (May 2026)",
    "headline": "Revenue re-accelerated from +30% to +53.5%; Systems Protection organic +50% on data center; gross margin under tariff pressure; capex doubling to $425-525M.",
    "shifts": [
      {
        "area": "growth",
        "direction": "accelerating",
        "trend": "FY25 $3.89B (+29.5%) → Q1 FY26 $1.24B (+53.5%); Systems Protection FY25 +42% → Q1 FY26 +76%; ~46pts organic from infrastructure Q1",
        "note": "Acceleration is genuine organic — Systems Protection organic was 17pts FY25, jumped to 50pts Q1"
      },
      {
        "area": "margins",
        "direction": "contracting",
        "trend": "Gross margin FY25 37.7% → Q1 FY26 35.9% (-290bps); tariffs, raw materials, and capacity investment are the drivers",
        "note": "Margin pressure from volume ramp and tariff costs; operating leverage partially offsets at the segment level (22.7% vs 20.7%)"
      },
      {
        "area": "capex",
        "direction": "accelerating",
        "trend": "FY25 capex $226.4M → FY26 guided $425-525M (1.9-2.3x); Q1 $114M on pace for guided range",
        "note": "Capacity expansion for Systems Protection (enclosures/liquid cooling) and Electrical Connections"
      },
      {
        "area": "segments",
        "direction": "accelerating",
        "trend": "Systems Protection segment income Q1 +95%; margin 22.7% (vs 20.7% FY25) — organic data-center growth driving operating leverage",
        "note": "EPG acquisition (Avail, $1.0B, May 2025) contributed $137.7M in Q1, amplifying organic strength"
      }
    ],
    "verdict": "Thesis intact and accelerating — Systems Protection organic acceleration to +50% is the strongest signal. Gross margin compression is a cost to watch but segment-level margins are expanding. $15B backlog (doubled FY25) provides multi-year visibility."
  },

  "OKLO": {
    "as_of": AS_OF,
    "based_on_accessions": ["0001628280-25-051349", "0001628280-26-018698"],
    "covers": "Q3 FY25 10-Q (Nov 2025) → FY25 10-K (Mar 2026)",
    "headline": "Meta 1.2GW prepayment agreement (Jan 2026) is the first hyperscaler hard-dollar commitment for advanced fission; cash burn accelerating as capital deployment begins.",
    "shifts": [
      {
        "area": "supply",
        "direction": "improving",
        "trend": "Order book ~18,100 MWe in Q3 2025 (non-binding LOIs); Jan 5, 2026 Meta 1.2GW prepayment agreement — first hyperscaler prepayment for advanced fission",
        "note": "Prepayment is qualitatively different from LOI — first dollar-committed deal; de-risks the Aurora commercial pathway"
      },
      {
        "area": "regulation",
        "direction": "improving",
        "trend": "NRC Phase I pre-application readiness (no gaps) Sep 2025; Aurora DOE safety design agreement approved Feb 2026; PDC topical report accepted",
        "note": "Regulatory milestones hitting on schedule; 2028 first commercial deployment target unchanged"
      },
      {
        "area": "capex",
        "direction": "accelerating",
        "trend": "9M FY25 cash burn $48.7M; FY25 opex $139.3M (+164% YoY); FY26 capex guided $350-450M; operating cash burn $80-100M",
        "note": "Capital deployment phase beginning — Tennessee AFCF ($1.68B) and Piketon (via LEU JV) are the two construction programs"
      },
      {
        "area": "leverage",
        "direction": "stable",
        "trend": "Cash $1.18B (Sep 2025); $805M convertible issued Aug 2025; FY26 burn $80-100M operating + $350-450M capex",
        "note": "Runway approximately 2-3 years at guided burn; capital markets accessible given hyperscaler support"
      }
    ],
    "verdict": "Thesis at inflection — Meta prepayment is the milestone that separates LOI optionality from commercial reality. Regulatory cadence and LEU JV exploration add execution confidence. Cash burn acceleration is the watch item."
  },

  "ORCL": {
    "as_of": AS_OF,
    "based_on_accessions": ["0001193125-25-315925", "0001193125-26-101045"],
    "covers": "Q2 FY26 10-Q (Dec 2025) → Q3 FY26 10-Q (Mar 2026)",
    "headline": "OCI infrastructure re-accelerated from +68% to +84%; capex tripled to $39B for 9 months; RPO plateauing at $552B after initial 5x surge.",
    "shifts": [
      {
        "area": "growth",
        "direction": "accelerating",
        "trend": "OCI cloud infrastructure Q2 $4.08B (+68% YoY) → Q3 $4.89B (+84% YoY); cloud applications Q2 +11% → Q3 +13%",
        "note": "OCI is the pure AI workload/training bucket; +84% is exceptional and accelerating from an already-high rate"
      },
      {
        "area": "capex",
        "direction": "accelerating",
        "trend": "H1 FY26 capex $20.5B (vs $6.3B H1 FY25) → 9M FY26 $39.2B (vs $12.1B 9M FY25, +3.2x); Q3 alone ~$18.7B",
        "note": "Capex tripling from prior year; upward trend expected to continue 'next few fiscal years'"
      },
      {
        "area": "supply",
        "direction": "stable",
        "trend": "RPO Q2 $523.3B (+5.4x YoY from contract signings) → Q3 $552.6B (+6% QoQ, +4.2x YoY); growth rate moderating after initial surge",
        "note": "RPO is enormous but sequential growth rate slowing as base inflates — not a negative signal"
      },
      {
        "area": "leverage",
        "direction": "tightening",
        "trend": "Issued $17.9B senior notes (Sep 2025) + $25B more (Feb 2026) + $5B mandatory convert; total issuance ~$48B; minimal share buybacks",
        "note": "All capital deployed to infrastructure build; debt servicing will constrain buybacks for multiple years"
      }
    ],
    "verdict": "Thesis intact — OCI +84% re-acceleration is the key signal. RPO plateau is normal after initial contract surge; the capex tripling confirms conviction in multi-year demand. Leverage is the structural risk but manageable given OCI growth trajectory."
  },

  "PLTR": {
    "as_of": AS_OF,
    "based_on_accessions": ["0001321655-26-000011", "0001321655-26-000028"],
    "covers": "FY25 10-K (Feb 2026) → Q1 2026 10-Q (May 2026)",
    "headline": "Revenue re-accelerated from +53% to +85% in Q1; operating margin expanded from 31% to 46%; commercial re-acceleration to +95% is the standout.",
    "shifts": [
      {
        "area": "growth",
        "direction": "accelerating",
        "trend": "Total revenue FY25 $4.5B (+53%) → Q1 2026 $1.63B (+85%); commercial FY25 $2.07B (+60%) → Q1 $774M (+95%)",
        "note": "Re-acceleration from an already-high base is exceptional; AIP bootcamp model is scaling commercial adoption"
      },
      {
        "area": "margins",
        "direction": "expanding",
        "trend": "Income from operations FY25 $1.41B (31% margin) → Q1 2026 $754M (46% margin); contribution margins 66% both periods",
        "note": "Operating margin expansion from 31% to 46% in one quarter is exceptional; scale effects kicking in"
      },
      {
        "area": "concentration",
        "direction": "improving",
        "trend": "No customer >10% of revenue in FY25 or Q1 2026; government contribution 66-73%, commercial 66-73% — diversification confirmed",
        "note": "US commercial growing fastest (74% → 79% of revenue); AIP bootcamp pipeline converting to revenue"
      },
      {
        "area": "segments",
        "direction": "shifting",
        "trend": "US commercial Q1 $428M (vs $127M prior year, +237%); US government $494M (+73%); international commercial $346M (+52%)",
        "note": "US commercial is now outgrowing all other segments; AIP enterprise adoption is the incremental driver"
      }
    ],
    "verdict": "Thesis strengthening significantly — +85% revenue re-acceleration with 46% operating margins is rare at scale. Commercial inflection to +95% is the signal the market has been waiting for. No thesis risks surfaced."
  },

  "PWR": {
    "as_of": AS_OF,
    "based_on_accessions": ["0001050915-26-000006", "0001050915-26-000016"],
    "covers": "FY25 10-K (Feb 2026) → Q1 FY26 10-Q (Apr 2026)",
    "headline": "Backlog compounding to $48.5B; RPO +10% in one quarter; revenue growth re-accelerated from +20% to +26%; data center as 'primary catalyst' in both periods.",
    "shifts": [
      {
        "area": "supply",
        "direction": "tightening",
        "trend": "Backlog FY25 $43.98B (+27.3% YoY) → Q1 $48.47B (+10.2% QoQ, ~$4.5B added in one quarter)",
        "note": "RPO $23.76B (+41.8% FY25) → $26.24B (+10.4% QoQ); backlog and RPO compounding simultaneously"
      },
      {
        "area": "growth",
        "direction": "accelerating",
        "trend": "FY25 revenues $28.5B (+20.3%) → Q1 FY26 $7.87B (+26.3%); operating income +41.7% Q1",
        "note": "Data center + DSI acquisition + DSI (dynamic systems/mechanical) driving both Electric and Underground"
      },
      {
        "area": "margins",
        "direction": "expanding",
        "trend": "FY25 Electric operating margin 10.3%; Q1 gross margin 14.1% (vs 13.4%); operating income +42% ahead of +26% revenue",
        "note": "Operating leverage materializing as backlog converts; large-project mix improving margin quality"
      },
      {
        "area": "segments",
        "direction": "stable",
        "trend": "Electric FY25 +21% ($23.0B) → Q1 +26% implied; Underground FY25 +17.5% → Q1 continuing with DSI contribution",
        "note": "Both segments cited as data-center-driven in Q1; DSI (Dec 2025) contributes hyperscaler process infrastructure"
      }
    ],
    "verdict": "Thesis intact — $48.5B backlog compounding is the strongest supply-side signal. Revenue and margin re-acceleration confirm execution. Data-center turnkey infrastructure is increasingly Quanta's core opportunity."
  },

  "SNOW": {
    "as_of": AS_OF,
    "based_on_accessions": ["0001640147-25-000211", "0001640147-26-000008"],
    "covers": "Q3 FY26 10-Q (Dec 2025) → FY26 10-K (Mar 2026)",
    "headline": "Consistent 29-31% growth; NRR flat at 125%; $1M+ customer cohort growing faster than base (+27% vs +21%); public-sector self-hosted beginning to contribute.",
    "shifts": [
      {
        "area": "growth",
        "direction": "stable",
        "trend": "Product revenue Q3 $1.16B (+29% YoY) → FY26 ~$4.5B (+31%); total revenue Q3 $1.21B → FY26 $4.7B",
        "note": "Consistent 29-31% growth across both periods; no inflection in either direction"
      },
      {
        "area": "supply",
        "direction": "improving",
        "trend": "RPO Q3 $7.9B (48% next 12mo) → FY26 $9.8B (46% next 12mo); +24% YoY growth in contract backlog",
        "note": "Weighted-avg contract life 2.7 years; RPO growth slightly above revenue growth — moderate positive"
      },
      {
        "area": "concentration",
        "direction": "easing",
        "trend": "Forbes G2000 ~43% of revenue; $1M+ customers 576 (FY25) → 733 (FY26, +27%); total customers 10,996 → 13,328 (+21%)",
        "note": "$1M+ cohort growing 27% vs 21% total base — mix shifting toward larger enterprise with higher ARR"
      },
      {
        "area": "margins",
        "direction": "improving",
        "trend": "Operating cash flow $1.2B FY26; SBC declining from 41% to 34% of revenue; net loss $1.3B stable",
        "note": "Path to profitability visible via SBC normalization; OCF generation already strong"
      }
    ],
    "verdict": "Thesis stable — 30% growth with NRR at 125% is solid but not inflecting. Re-rating requires Cortex AI consumption to add incremental growth on top of the existing base. $1M+ cohort expansion is the quality signal."
  },

  "SNPS": {
    "as_of": AS_OF,
    "based_on_accessions": ["0000883241-25-000028", "0000883241-26-000014"],
    "covers": "FY25 10-K (Dec 2025) → Q1 FY26 10-Q (Feb 2026)",
    "headline": "Ansys doubled reported revenue base; Design IP declining (-6% Q1); China -22% ex-Ansys from BIS; $3.5B term loan paid in Q1 — buyback resuming after debt paydown.",
    "shifts": [
      {
        "area": "growth",
        "direction": "transforming",
        "trend": "FY25 $7.05B (+15%, incl. $757M Ansys from Jul 2025) → Q1 FY26 $2.41B (+66%, incl. $886M Ansys); organic trend masked by Ansys contribution",
        "note": "Ansys $34.9B acquisition closed Jul 2025; Design Automation doubled; Design IP -6% — organic bifurcation"
      },
      {
        "area": "china",
        "direction": "deteriorating",
        "trend": "FY25 China -22% ex-Ansys on BIS 'is-informed' license (May 29, 2025, rescinded Jul 2); Q1 Design IP -6% likely China-mix headwind",
        "note": "China EDA restrictions are a structural overhang despite Jul 2025 rescission — customer hesitancy persists"
      },
      {
        "area": "leverage",
        "direction": "improving",
        "trend": "$13.5B total debt at FY25-end (incl. $10B senior notes + $4.3B term loan) → term loan $3.5B paid in Q1 FY26; buyback suspended pending paydown",
        "note": "Aggressive debt reduction; $194.3M buyback authorization remains; resumes as debt normalizes"
      },
      {
        "area": "segments",
        "direction": "shifting",
        "trend": "Design Automation Q1 +96% ($2.0B, Ansys-driven) vs Design IP Q1 -6% ($407M); split widening",
        "note": "Processor IP business sold to GFS in Q1; Design IP portfolio being pruned; Ansys simulation tools growing fastest"
      }
    ],
    "verdict": "Thesis intact but complex — Ansys acquisition doubles the TAM and simulation revenue is high-quality; Design IP weakness and China overhang are the drags. Debt paydown + buyback resumption is the near-term catalyst."
  },

  "VRT": {
    "as_of": AS_OF,
    "based_on_accessions": ["0001674101-26-000008", "0001628280-26-026556"],
    "covers": "FY25 10-K (Feb 2026) → Q1 FY26 10-Q (Apr 2026)",
    "headline": "Revenue growth re-accelerated from +28% to +30%; Americas +41% → +53%; gross margin expanded 400bps; FY26 capex doubling to $425-525M for capacity.",
    "shifts": [
      {
        "area": "growth",
        "direction": "accelerating",
        "trend": "FY25 $10.23B (+27.7%) → Q1 FY26 $2.65B (+30.1%); Americas FY25 +41.9% → Q1 +53.1%",
        "note": "Americas acceleration is the leading indicator — hyperscaler buildout in North America is the engine"
      },
      {
        "area": "margins",
        "direction": "expanding",
        "trend": "Gross margin FY25 36.3% → Q1 FY26 37.7% (+140bps); Americas op margin FY25 26.8% → Q1 27.0% stable",
        "note": "Mix and operating leverage outpacing tariff and material headwinds — GM expanding despite cost inflation"
      },
      {
        "area": "supply",
        "direction": "tightening",
        "trend": "Backlog FY25 $15.0B (more than doubled from $7.2B); Q1 FY26 order pace sustaining the build",
        "note": "'Very robust' AI/HPC demand cited in Q1; hybrid air-and-liquid + HVDC architectures emerging as customer requirements"
      },
      {
        "area": "capex",
        "direction": "accelerating",
        "trend": "FY25 $226.4M → FY26 guided $425-525M (1.9-2.3x); Q1 $114M on pace for guided range",
        "note": "Capacity expansion demand-driven; $2.48B liquidity ($2.15B cash + revolver) provides ample funding"
      }
    ],
    "verdict": "Thesis intact and strengthening — Americas re-acceleration + GM expansion while capex doubling is the ideal combination. $15B backlog (doubled) removes near-term demand risk; liquid cooling demand is the secular driver."
  },

}
# fmt: on


def main():
    with open("data/cross_quarter.json") as f:
        existing = json.load(f)

    merged = dict(existing)
    new_count = 0
    updated_count = 0

    for ticker, entry in ENTRIES.items():
        if ticker in merged:
            updated_count += 1
        else:
            new_count += 1
        merged[ticker] = entry

    # Sort by ticker
    merged = dict(sorted(merged.items()))

    with open("data/cross_quarter.json", "w") as f:
        json.dump(merged, f, indent=2, ensure_ascii=False)
        f.write("\n")

    total = len(merged)
    print(f"cross_quarter.json: {new_count} new, {updated_count} updated → {total} total tickers")


if __name__ == "__main__":
    main()
