## What it does
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
