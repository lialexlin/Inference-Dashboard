# Memory

Inference-Dashboard store — memories specific to this repo, plus the universal working rules mirrored from the vault store.

## Repo-specific

- [user_personal_investor.md](user_personal_investor.md) — Personal investing focus: AI inference scaling, hunting under-priced layers of the stack
- [feedback_data_driven_layer_status.md](feedback_data_driven_layer_status.md) — Inference Dashboard: layer status and rollup labels derive from scoring data, never hardcoded
- [feedback_pull_before_data_analysis.md](feedback_pull_before_data_analysis.md) — Inference-Dashboard: git pull before any data-dependent analysis — a daily bot refreshes data/*.json
- [feedback_show_in_browser.md](feedback_show_in_browser.md) — Explain the dashboard by what renders in the browser, and open it — not by walking the code
- [project_inference_dashboard.md](project_inference_dashboard.md) — Static HTML + Python dashboard mapping the AI inference stack; now at projects/Inference-Dashboard
- [project_investment_framework.md](project_investment_framework.md) — Bottleneck-rotation investing framework (Druckenmiller/Mauboussin) behind the Inference Dashboard
- [project_tw_movers.md](project_tw_movers.md) — TW listed-universe momentum radar (tw-movers.html + tw_universe.py)
- [project_us_movers.md](project_us_movers.md) — US Movers — large-cap analogue of TW Movers; Nasdaq screener + yfinance, US$50B floor
- [reference_transcripts_source.md](reference_transcripts_source.md) — Earnings-call transcripts from earningscalls.dev (free, US + ADRs); 16 non-US tickers documented as gaps

## Mirrored from the vault store — edit there, then re-sync; never edit these copies

- [feedback_claude_subagents_over_third_party_apis.md](feedback_claude_subagents_over_third_party_apis.md) — Processing work defaults to Claude subagents, not third-party APIs (Gemini etc.) — cost routing; /pdf-to-md's Gemini conversion is the one established exception
- [feedback_content_before_polish.md](feedback_content_before_polish.md) — Iterate substance/structure first, build visual only after content is locked
- [feedback_deliverables_durable_paths.md](feedback_deliverables_durable_paths.md) — Scratchpad is wiped on session resume; deliverables + reusable code go to durable paths, scratchpad only for intermediates
- [feedback_digest_sources_fully.md](feedback_digest_sources_fully.md) — Read source material at full extent (probe dimensions first, never cap rows/cols/pages); negative claims require a full read
- [feedback_explain_logic_not_code.md](feedback_explain_logic_not_code.md) — Alex is non-technical: explain infra/tooling as logic and outcome (what happens, why), never walk through code
- [feedback_low_friction_launchers.md](feedback_low_friction_launchers.md) — Personal tools ship with a double-clickable launcher (.command), not just terminal instructions
- [feedback_mock_before_pipeline.md](feedback_mock_before_pipeline.md) — Front-end / "show me the result" asks: build a shape-matching output mock and confirm it FIRST, before wiring the pipeline
- [feedback_opus_executor_for_small_changes.md](feedback_opus_executor_for_small_changes.md) — already-specced small changes go to one Opus executor, never a Fable orchestrator with helpers; "touches production" is not a reason to orchestrate
- [feedback_self_contained_html.md](feedback_self_contained_html.md) — Internal visual artifacts = one self-contained HTML file (no server/CDN deps); generator code lives separately
- [feedback_visual_verification.md](feedback_visual_verification.md) — Verifying a render means scrutinizing against the chart's purpose, not narrating a flattering read of a defect
- [reference_readback_verification.md](reference_readback_verification.md) — Wrapped-CLI writes: verify by read-back, never trust exit code / success message
