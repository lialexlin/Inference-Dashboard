## What it does
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
