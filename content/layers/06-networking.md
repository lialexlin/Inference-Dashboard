## What it does
Switch ASICs (Broadcom Tomahawk/Jericho), DSPs (Marvell, MaxLinear), and specialty silicon that wires up the network fabric inside an AI cluster. Distinct from the boxes themselves (next layer).

## Why it matters for inference scaling
Modern training clusters run 100k+ accelerators; for them to act as one machine the network has to deliver near-line-rate at very low latency. Scale-out networking is now ~10–15% of total cluster spend and growing. Ethernet has decisively won the back-end network from InfiniBand (>⅔ of Q3 2025 AI cluster switch sales — Dell'Oro).

## Current bottleneck (May 2026)
- **Switch silicon**: Broadcom Tomahawk dominance; merchant share growing as hyperscalers standardize.
- **DSPs**: Marvell incumbent; competitive vs Broadcom's PAM4 stack.
- **The real squeeze**: optics, not switch silicon. See next layer.

## Priced-in vs underappreciated
**Mixed.** AVGO is priced in. MRVL DSPs is a continuation of the underappreciated GPU/ASIC story — same conviction.
