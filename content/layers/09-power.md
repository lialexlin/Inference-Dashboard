## What it does
The grid-side and on-site power stack: utility transformers (GEV), switchgear (ETN, HUBB), backup gensets (CAT, CMI, GNRC), substation/transmission EPC (PWR), and integrated DC power systems (VRT, ETN, SU). The actual physical electrons that hit the GPU.

## Why it matters for inference scaling
This is increasingly the binding constraint, not silicon. Lead times have stretched from 24–30 months pre-2020 to up to 5 years now for transformers and gas turbines. >50% of US 2026 data centers are expected to be delayed or cancelled because the electrical gear physically isn't available.

## Current bottleneck (May 2026)
- **GE Vernova**: backlog $163B; 2026 DC orders $2.4B already exceed all 2025. Gas turbine slots sold out through 2028 (Mitsubishi quoting 2029–2030).
- **Eaton**: DC orders +30%+ for 4 consecutive quarters; electrical Americas backlog at record.
- **Generac**: only gas-genset slot in Stargate permitting docs because Cat/Cummins lead times are 70–107 weeks vs Generac's 50–60.
- **Cummins**: 18-month lead times even after $150M Fridley expansion.

## Priced-in vs underappreciated
**Mixed. GEV/ETN/VRT richly priced.** Underappreciated: **GNRC, HUBB, PWR.** Generac has the only gas-genset slot in Stargate permits because everyone else is sold out. PWR/HUBB get every grid-buildout dollar regardless of which hyperscaler wins. The further you go from "DC-pure-play" toward "structural grid build", the cheaper the multiple — and the demand is equally durable.
