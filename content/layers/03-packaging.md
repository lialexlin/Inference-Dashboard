## What it does
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
