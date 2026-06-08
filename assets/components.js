// Render helpers shared across pages.

window.statusLabel = function (status) {
  return status.replace("-", " ");
};

window.renderPlayerChip = function (player) {
  const px = DATA.prices[player.ticker];
  const chg = px && px.change_1m != null ? px.change_1m : null;
  const cls = changeClass(chg);
  const chgText = chg == null ? "" : `<span class="chip__chg ${cls}">${fmtPct(chg)}</span>`;
  const score = scoreFor(player.ticker);
  const q = (score && score.quadrant) || "unscored";
  const dot = `<span class="qdot qdot--${q}" title="${escapeHtml(quadrantLabel(q) + ' — ' + quadrantDefinition(q))}"></span>`;
  const scoreLine = score
    ? `\n${quadrantLabel(q)} — ${quadrantDefinition(q)}\nBiz ${score.business == null ? "—" : (score.business >= 0 ? "+" : "") + score.business.toFixed(1)} · Val ${score.valuation == null ? "—" : (score.valuation >= 0 ? "+" : "") + score.valuation.toFixed(1)}`
    : "";
  const title = `${player.name} — ${player.role}${scoreLine}`;
  return `
    <span class="chip" title="${escapeHtml(title)}">
      ${dot}<span class="chip__ticker">${player.ticker}</span>${chgText}
    </span>`;
};

// Single-line legend strips. Short defs inline, full def in the hover tooltip.
// Layer status and player quadrants now share the same 5 labels — the layer
// version means "≥X% of the layer's tickers fell into this quadrant".
const STATUS_SHORT = {
  underappreciated: "≥30% strong + cheap",
  "priced-in": "≥50% strong but expensive",
  "value-trap": "≥50% cheap but weak",
  avoid: "≥50% weak + expensive",
  fair: "no dominant quadrant",
};
const QUADRANT_SHORT = {
  underappreciated: "strong + cheap",
  "priced-in": "strong but expensive",
  "value-trap": "cheap but weak",
  avoid: "weak + expensive",
  fair: "middle ground",
};

window.renderStatusLegend = function () {
  const items = ["underappreciated", "priced-in", "value-trap", "avoid", "fair"];
  const parts = items.map((s) => `
    <span class="legend-row__item" title="${escapeHtml(statusDefinition(s))}">
      <span class="badge badge--${s}">${statusLabel(s)}</span>
      <span class="legend-row__def">${STATUS_SHORT[s]}</span>
    </span>`).join("");
  return `
    <div class="legend-row">
      <span class="legend-row__label">Layer status key</span>
      ${parts}
    </div>`;
};

window.renderQuadrantLegend = function () {
  const items = ["underappreciated", "priced-in", "value-trap", "avoid", "fair"];
  const parts = items.map((q) => `
    <span class="legend-row__item" title="${escapeHtml(quadrantDefinition(q))}">
      <span class="qpill qpill--${q}">${escapeHtml(quadrantLabel(q))}</span>
      <span class="legend-row__def">${QUADRANT_SHORT[q]}</span>
    </span>`).join("");
  return `
    <div class="legend-row">
      <span class="legend-row__label">Quadrant key</span>
      ${parts}
    </div>`;
};

window.renderLayerCard = function (layer) {
  const players = playersForLayer(layer.id).slice(0, 13);
  const chips = players.map(renderPlayerChip).join("");
  const bn = (DATA.bottleneck || {})[layer.id];
  const heat = bn ? renderHeatMeter(bn.tightness_score, bn.evidence, { count: bn.signal_count_90d }) : "";
  return `
    <a href="layer.html?id=${layer.id}" class="layer-card block">
      <div class="flex items-start justify-between gap-4">
        <div>
          <div class="text-xs uppercase tracking-widest text-[color:var(--text-faint)] mb-2">Layer ${layer.order}</div>
          <h3 class="font-display text-2xl text-white leading-tight mb-1">${layer.name}</h3>
          <p class="text-sm text-[color:var(--text-dim)] max-w-2xl">${layer.short_role}</p>
        </div>
        <div class="flex flex-col items-end gap-2 shrink-0">
          <div class="flex items-center gap-2">
            <span class="badge badge--${layer.status}" title="${escapeHtml(statusDefinition(layer.status))}">${statusLabel(layer.status)}</span>
            ${layer.status_override ? `<span class="badge-hint">manual</span>` : ""}
          </div>
          ${heat}
        </div>
      </div>
      <p class="mt-4 text-[13px] text-[color:var(--text-faint)] max-w-3xl italic">${layer.bottleneck_summary}</p>
      <div class="mt-4 flex flex-wrap gap-2">${chips}</div>
    </a>`;
};

// Renders a 0-100 tightness "heat meter". Rose at high tightness (binding
// bottleneck), amber at mid, faint at low. Tooltip carries up to 3 evidence
// quotes — the supply-language hits that pushed the score up.
window.renderHeatMeter = function (score, evidence, opts) {
  opts = opts || {};
  if (score == null || isNaN(score)) return "";
  const clamped = Math.max(0, Math.min(100, score));
  const tone = clamped >= 60 ? "hot" : clamped >= 30 ? "warm" : "cool";
  const ev = (evidence || []).slice(0, 3);
  const tipParts = [
    `Bottleneck tightness ${clamped}/100`,
    opts.count != null ? `${opts.count} signals in last 90d` : null,
    ev.length ? "\nEvidence:\n• " + ev.join("\n• ") : null,
  ].filter(Boolean);
  const tip = tipParts.join(" — ").replace(" — \n", "\n");
  return `
    <div class="heat-meter heat-meter--${tone}" title="${escapeHtml(tip)}">
      <span class="heat-meter__label">tightness</span>
      <span class="heat-meter__track"><span class="heat-meter__fill" style="width:${clamped}%"></span></span>
      <span class="heat-meter__val">${clamped}</span>
    </div>`;
};

// Full-width "Bottleneck status" callout for layer.html — same data as the
// homepage heat-meter but with evidence rendered inline.
window.renderBottleneckCallout = function (layerId) {
  const bn = (DATA.bottleneck || {})[layerId];
  if (!bn) return "";
  const score = bn.tightness_score;
  const tone = score >= 60 ? "hot" : score >= 30 ? "warm" : "cool";
  const ev = (bn.evidence || []).map((q) => `<li>${escapeHtml(q)}</li>`).join("");
  const evBlock = ev
    ? `<ul class="bottleneck-callout__evidence">${ev}</ul>`
    : `<div class="text-xs text-[color:var(--text-faint)] mt-2">No supply-tightness language in the last 90 days of signals for this layer.</div>`;
  return `
    <div class="bottleneck-callout bottleneck-callout--${tone}">
      <div class="bottleneck-callout__head">
        <div>
          <div class="text-[10px] uppercase tracking-widest text-[color:var(--text-faint)] mb-1">Bottleneck tightness (90d)</div>
          <div class="bottleneck-callout__score">${score}<span class="bottleneck-callout__score-suffix">/100</span></div>
        </div>
        <div class="bottleneck-callout__meta">
          <div>${bn.signal_count_90d} signals tagged · ${bn.tightness_language_hits_per_signal} tightness-terms/signal</div>
          ${bn.cross_quarter_supply_tight ? `<div class="text-[color:var(--rose)] mt-1">✓ cross-quarter supply-tight signal</div>` : ""}
        </div>
      </div>
      <div class="bottleneck-callout__track"><span class="bottleneck-callout__fill" style="width:${score}%"></span></div>
      ${evBlock}
    </div>`;
};

window.renderSignalCard = function (sig, opts) {
  opts = opts || {};
  const compact = !!opts.compact;
  const tags = (sig.layer_ids || []).map((id) => {
    const l = layerById(id);
    return l ? `<a class="layer-pill" href="layer.html?id=${id}">${l.name}</a>` : "";
  }).join(" ");
  const archTag = sig.arch_risk ? `<span class="layer-pill layer-pill--arch" title="Architectural-risk signal: mentions an algorithmic shift (Mamba, MoE, linear attention, KV-cache compression, etc.) that could change inference FLOPs/token economics.">arch risk</span>` : "";
  const tickers = (sig.tickers || []).slice(0, 6).map((t) => `<a href="stock.html?ticker=${encodeURIComponent(t)}" class="font-mono text-[11px] text-[color:var(--text-dim)] hover:text-[color:var(--sky)] hover:underline underline-offset-2">${t}</a>`).join("<span class='text-[color:var(--text-faint)]'>·</span>");

  // Filing summary block (10-K / 10-Q / paired earnings 8-K with summary from
  // data/filing_summaries.json). Falls back to bare card if no summary.
  // Compact mode (homepage arch-risk strip) hides this block entirely.
  let summaryBlock = "";
  if (!compact && sig.source_type === "filing" && sig.summary) {
    const s = sig.summary;
    const tldr = s.tldr ? `<div class="signal__tldr">${escapeHtml(s.tldr)}</div>` : "";
    let guidanceLine = "";
    if (s.guidance) {
      const g = s.guidance;
      const parts = [];
      if (g.period) parts.push(`<span class="signal__guidance-label">${escapeHtml(g.period)} guidance</span>`);
      if (g.revenue) parts.push(`Rev ${escapeHtml(g.revenue)}`);
      if (g.gross_margin) parts.push(`GM ${escapeHtml(g.gross_margin)}`);
      if (g.opex) parts.push(`Opex ${escapeHtml(g.opex)}`);
      if (parts.length) {
        guidanceLine = `<div class="signal__guidance">${parts.join(" <span class='text-[color:var(--text-faint)]'>·</span> ")}${g.notes ? `<div class="signal__guidance-notes">${escapeHtml(g.notes)}</div>` : ""}</div>`;
      }
    }
    const takeaways = (s.takeaways || []).length
      ? `<details class="signal__takeaways">
           <summary>
             <span>Key takeaways</span>
             <span class="signal__takeaways-hint signal__takeaways-hint-show">show ${s.takeaways.length}</span>
             <span class="signal__takeaways-hint signal__takeaways-hint-hide">hide</span>
           </summary>
           <ul>${s.takeaways.map((b) => `<li>${escapeHtml(b)}</li>`).join("")}</ul>
         </details>`
      : "";
    const pullQuote = s.quote
      ? `<blockquote class="signal__pullquote">
           "${escapeHtml(s.quote)}"
           ${s.quote_section ? `<cite>— ${escapeHtml(s.quote_section)}</cite>` : ""}
         </blockquote>`
      : "";
    summaryBlock = `${tldr}${guidanceLine}${takeaways}${pullQuote}`;
  }

  const quote = !compact && !summaryBlock && sig.quote ? `<div class="signal__quote">${escapeHtml(sig.quote)}</div>` : "";
  const sourceName = sig.url
    ? `<a href="${sig.url}" target="_blank" rel="noopener" class="text-sm text-[color:var(--text-dim)] hover:text-[color:var(--sky)] underline decoration-dotted underline-offset-2">${escapeHtml(sig.source)}</a>`
    : `<span class="text-sm text-[color:var(--text-dim)]">${escapeHtml(sig.source)}</span>`;
  let host = "";
  try { host = sig.url ? new URL(sig.url).hostname.replace(/^www\./, "") : ""; } catch (e) { host = ""; }
  const sourceFooter = !compact && sig.url
    ? `<div class="mt-3 text-[11px] text-[color:var(--text-faint)]">
         ${summaryBlock ? `<a href="${sig.url}" target="_blank" rel="noopener" class="hover:text-[color:var(--sky)]">Read full filing →</a>`
                        : `source: <a href="${sig.url}" target="_blank" rel="noopener" class="hover:text-[color:var(--sky)]">${escapeHtml(host || sig.url)} ↗</a>`}
       </div>`
    : "";
  const tickersBlock = !compact && tickers ? `<div class="mt-3 flex items-center gap-2 flex-wrap">${tickers}</div>` : "";
  return `
    <article class="signal${compact ? ' signal--compact' : ''}" id="${sig.id}">
      <div class="flex items-center justify-between gap-3 flex-wrap">
        <div class="flex items-center gap-2 flex-wrap">
          <span class="tag tag--${sig.source_type}">${sig.source_type}</span>
          ${sourceName}
          <span class="text-[color:var(--text-faint)]">·</span>
          <span class="signal__date">${fmtDate(sig.date)} <span class="text-[color:var(--text-faint)]">(${relDate(sig.date)})</span></span>
        </div>
        <div class="flex items-center gap-2 flex-wrap">${archTag}${tags}</div>
      </div>
      <h4 class="mt-2 text-[15px] text-white font-medium leading-snug">
        <a href="${sig.url}" target="_blank" rel="noopener" class="hover:text-[color:var(--sky)]">${escapeHtml(sig.headline)}</a>
      </h4>
      ${summaryBlock}
      ${quote}
      ${tickersBlock}
      ${sourceFooter}
    </article>`;
};

// Cross-quarter shifts — a single synthesized "what's changed over the last
// 2-4 filings" card per stock. Data lives in data/cross_quarter.json,
// populated by the Claude.ai daily routine (see docs/claude_routine_prompt.md).
// Schema: { headline, covers, as_of, based_on_accessions, shifts: [{area,
// direction, trend, note}], verdict }.
const CQ_DIR_UP = new Set(["accelerating", "improving", "raised", "easing", "expanding"]);
const CQ_DIR_DOWN = new Set(["decelerating", "deteriorating", "lowered", "tightening", "tight", "contracting"]);
const CQ_DIR_FLAT = new Set(["stable", "flat", "unchanged"]);

window.renderCrossQuarter = function (ticker, cq) {
  if (!cq || !cq.shifts || !cq.shifts.length) {
    return `<div class="text-sm text-[color:var(--text-faint)] py-2">No cross-quarter synthesis for ${escapeHtml(ticker)} yet — needs at least 2 prior filings, refreshed by the daily routine.</div>`;
  }
  const accCount = (cq.based_on_accessions || []).length;
  const accTip = (cq.based_on_accessions || []).join("\n");
  const meta = [
    cq.covers ? `<span class="cq-meta__covers">${escapeHtml(cq.covers)}</span>` : "",
    cq.as_of ? `<span class="cq-meta__date">${escapeHtml(cq.as_of)} <span class="text-[color:var(--text-faint)]">(${relDate(cq.as_of)})</span></span>` : "",
    accCount ? `<span class="cq-meta__pill" title="${escapeHtml(accTip)}">based on ${accCount} filing${accCount === 1 ? "" : "s"}</span>` : "",
  ].filter(Boolean).join("");

  const shiftsHtml = cq.shifts.map((s) => {
    const dir = (s.direction || "").toLowerCase();
    const tone = CQ_DIR_UP.has(dir) ? "up"
              : CQ_DIR_DOWN.has(dir) ? "down"
              : CQ_DIR_FLAT.has(dir) ? "flat"
              : "neutral";
    const arrow = tone === "up" ? "↑" : tone === "down" ? "↓" : tone === "flat" ? "→" : "·";
    return `
      <div class="cq-shift cq-shift--${tone}">
        <span class="cq-shift__area">${escapeHtml(s.area || "")}</span>
        <span class="cq-shift__dir">${arrow} ${escapeHtml(s.direction || "")}</span>
        <span class="cq-shift__trend">${escapeHtml(s.trend || "")}</span>
        ${s.note ? `<span class="cq-shift__note">${escapeHtml(s.note)}</span>` : ""}
      </div>`;
  }).join("");

  const verdict = cq.verdict ? `<div class="cq-verdict">${escapeHtml(cq.verdict)}</div>` : "";
  const headline = cq.headline ? `<div class="signal__tldr cq-headline">${escapeHtml(cq.headline)}</div>` : "";

  return `
    <article class="cq-card">
      <header class="cq-meta">${meta}</header>
      ${headline}
      <div class="cq-shifts">${shiftsHtml}</div>
      ${verdict}
    </article>`;
};

// Management narrative drift — per-theme tone score across earnings calls.
// Reads data/narrative_tracking.json. Positive tone = bottleneck thesis
// reinforced (tight supply / strong demand / raised capex / extending lead
// times / rising prices). Negative tone = thesis weakening.
const NARRATIVE_THEMES = [
  { id: "supply",     label: "Supply",     pos: "tight",     neg: "easing" },
  { id: "demand",     label: "Demand",     pos: "strong",    neg: "weak" },
  { id: "capex",      label: "Capex",      pos: "raised",    neg: "cut" },
  { id: "lead_times", label: "Lead times", pos: "extending", neg: "shortening" },
  { id: "pricing",    label: "Pricing",    pos: "rising",    neg: "pressure" },
];

window.renderNarrativeDrift = function (ticker) {
  const nt = DATA.narrative_tracking || {};
  const calls = (nt.by_ticker || {})[ticker] || [];
  if (!calls.length) {
    return `<div class="text-sm text-[color:var(--text-faint)] py-3">No transcript on file for ${escapeHtml(ticker)} — earningscalls.dev covers US listings + ADRs; local non-US tickers are documented gaps. Drift comparison becomes meaningful once 2–3 quarterly transcripts accumulate.</div>`;
  }

  // Helper: tone score [-1, +1] → centered fill on a score-bar.
  // Score 0 → no visible fill. Positive → green to the right; negative → rose to the left.
  const renderScoreBar = (score) => {
    const v = Math.max(-1, Math.min(1, score || 0));
    const widthPct = Math.abs(v) * 50; // half the bar = score of 1
    const fillClass = v >= 0 ? "score-bar__fill--pos" : "score-bar__fill--neg";
    const left = v >= 0 ? "50%" : `${50 - widthPct}%`;
    return `<span class="score-bar"><span class="score-bar__fill ${fillClass}" style="left: ${left}; width: ${widthPct}%;"></span></span>
            <span class="score-bar__val">${v >= 0 ? "+" : ""}${v.toFixed(2)}</span>`;
  };

  // Mini drift sparkline: one dot per call (newest on the right).
  // Color-coded by tone score. With one call it's just a single dot —
  // intentional; the user can see drift fill in as more quarters land.
  const renderSparkline = (themeId) => {
    const dots = [...calls].reverse().map((c) => {
      const s = (c.themes[themeId] || {}).tone_score || 0;
      const color = s > 0.2 ? "var(--green)" : s < -0.2 ? "var(--rose)" : "var(--text-faint)";
      const tip = `${c.date || "—"}: ${s >= 0 ? "+" : ""}${s.toFixed(2)}`;
      return `<span class="narrative-spark__dot" title="${escapeHtml(tip)}" style="background:${color};"></span>`;
    }).join("");
    return `<span class="narrative-spark">${dots}</span>`;
  };

  const latest = calls[0];
  const latestUrl = latest.url ? `<a class="narrative-call__src" href="${escapeHtml(latest.url)}" target="_blank" rel="noopener">source ↗</a>` : "";

  const rowsHtml = NARRATIVE_THEMES.map((th) => {
    const bucket = latest.themes[th.id] || { mentions: 0, tone_score: 0, counts: { positive: 0, negative: 0, neutral: 0 }, quotes: [] };
    const mentions = bucket.mentions;
    const counts = bucket.counts || { positive: 0, negative: 0, neutral: 0 };
    const quotesHtml = (bucket.quotes || []).slice(0, 4).map((q) => {
      const toneClass = q.tone === "positive" ? "tone-pos" : q.tone === "negative" ? "tone-neg" : "tone-neu";
      const toneLabel = q.tone === "positive" ? th.pos : q.tone === "negative" ? th.neg : "neutral";
      const who = q.speaker ? `${escapeHtml(q.speaker)}${q.role ? " · " + escapeHtml(q.role) : ""}` : "";
      return `<li class="narrative-quote">
                <span class="narrative-quote__tag ${toneClass}">${escapeHtml(toneLabel)}</span>
                <span class="narrative-quote__text">${escapeHtml(q.text)}</span>
                ${who ? `<span class="narrative-quote__who">— ${who}</span>` : ""}
              </li>`;
    }).join("");
    const evidence = quotesHtml
      ? `<details class="narrative-row__evidence"><summary>${counts.positive}+ / ${counts.negative}− / ${counts.neutral}∼ &nbsp;quotes</summary><ul class="narrative-quotes">${quotesHtml}</ul></details>`
      : `<span class="text-[color:var(--text-faint)] text-xs">no mentions</span>`;
    return `
      <div class="narrative-row">
        <div class="narrative-row__label">
          <div class="narrative-row__theme">${th.label}</div>
          <div class="narrative-row__legend">${th.pos} ↔ ${th.neg}</div>
        </div>
        <div class="narrative-row__bar">${mentions ? renderScoreBar(bucket.tone_score) : '<span class="text-[color:var(--text-faint)] text-xs">—</span>'}</div>
        <div class="narrative-row__count">${mentions}</div>
        <div class="narrative-row__spark">${renderSparkline(th.id)}</div>
        <div class="narrative-row__evidence-wrap">${evidence}</div>
      </div>`;
  }).join("");

  return `
    <article class="cq-card narrative-card">
      <header class="narrative-card__head">
        <div>
          <div class="narrative-card__title">${escapeHtml(latest.call_type || "Earnings call")}</div>
          <div class="narrative-card__sub">${escapeHtml(latest.date || "—")} · ${calls.length} call${calls.length === 1 ? "" : "s"} on file ${latestUrl}</div>
        </div>
        <div class="narrative-card__legend">
          <span>← thesis weakening</span>
          <span>thesis reinforced →</span>
        </div>
      </header>
      <div class="narrative-grid">
        <div class="narrative-row narrative-row--head">
          <div class="narrative-row__label">Theme</div>
          <div class="narrative-row__bar">Tone</div>
          <div class="narrative-row__count">N</div>
          <div class="narrative-row__spark">Drift</div>
          <div class="narrative-row__evidence-wrap">Top quotes</div>
        </div>
        ${rowsHtml}
      </div>
      ${calls.length === 1 ? `<div class="narrative-card__hint">Drift sparkline fills in as more quarterly transcripts accumulate — typically 2–3 cycles needed for a meaningful comparison.</div>` : ""}
    </article>`;
};

// Exit-trigger status panel — 4 tiles showing thesis-break trigger states.
// Lives at the top of index.html so the user sees thesis health at a glance,
// even during emotional drawdowns.
const EXIT_TRIGGER_META = {
  token_growth:      { label: "Token-growth",      desc: "Frontier inference token throughput (WoW)." },
  hyperscaler_capex: { label: "Hyperscaler capex", desc: "MSFT/GOOGL/META/AMZN capex-cut language in last 90d filings." },
  arch_risk:         { label: "Arch-risk",         desc: "Algorithmic shift collapsing FLOPs/token (Mamba/MoE/etc., last 30d)." },
  taiwan:            { label: "Taiwan",            desc: "Geopolitical break — manually flagged." },
};
const EXIT_STATE_TO_BADGE = { green: "underappreciated", amber: "priced-in", red: "avoid" };

window.renderExitTriggers = function () {
  const data = DATA.exit_triggers || null;
  if (!data || !data.triggers) return "";
  const tiles = ["token_growth", "hyperscaler_capex", "arch_risk", "taiwan"].map((key) => {
    const t = data.triggers[key];
    if (!t) return "";
    const badge = EXIT_STATE_TO_BADGE[t.state] || "fair";
    const meta = EXIT_TRIGGER_META[key];
    const evidence = (t.evidence || []).map((e) => `<li>${escapeHtml(e)}</li>`).join("");
    const rule = t.rule ? `<div class="exit-tile__rule">${escapeHtml(t.rule)}</div>` : "";
    const evHtml = evidence
      ? `<details class="exit-tile__details"><summary>evidence</summary><ul class="exit-tile__evidence">${evidence}</ul>${rule}</details>`
      : rule;
    return `
      <div class="exit-tile exit-tile--${t.state}" data-trigger="${key}">
        <div class="exit-tile__head">
          <span class="exit-tile__label">${escapeHtml(meta.label)}</span>
          <span class="badge badge--${badge} exit-tile__state">${t.state}</span>
        </div>
        <div class="exit-tile__desc">${escapeHtml(meta.desc)}</div>
        ${evHtml}
      </div>`;
  }).join("");
  const overallBadge = EXIT_STATE_TO_BADGE[data.overall] || "fair";
  return `
    <div class="exit-panel">
      <div class="exit-panel__head">
        <div>
          <div class="exit-panel__title">Exit triggers</div>
          <div class="exit-panel__sub">Codified thesis-break conditions. Overall = worst of all four.</div>
        </div>
        <div class="exit-panel__overall">
          <span class="text-xs text-[color:var(--text-faint)] uppercase tracking-widest mr-2">overall</span>
          <span class="badge badge--${overallBadge}">${escapeHtml(data.overall)}</span>
        </div>
      </div>
      <div class="exit-panel__tiles">${tiles}</div>
    </div>`;
};

// Demand telemetry strip — homepage. Shows latest OpenRouter snapshot of
// frontier inference token throughput, WoW change, and top model movers.
// This is the variant-perception signal that *leads* hyperscaler capex.
window.renderDemandStrip = function () {
  const demand = DATA.demand_signals || null;
  if (!demand || !demand.daily || !demand.daily.length) return "";
  const latest = demand.daily[demand.daily.length - 1];
  const summary = demand.summary || {};
  const fmtPctSigned = (v) => v == null ? "—" : (v >= 0 ? "+" : "") + (v * 100).toFixed(1) + "%";
  const wowCls = summary.wow_pct == null ? "" : (summary.wow_pct >= 0 ? "text-[color:var(--green)]" : "text-[color:var(--rose)]");
  const wowLabel = summary.wow_pct != null
    ? `<span class="${wowCls}">${fmtPctSigned(summary.wow_pct)}</span> WoW`
    : `<span class="text-[color:var(--text-faint)]">awaiting history</span>`;

  // Top 5 models for at-a-glance dominance view
  const topRows = (latest.top_models || []).slice(0, 5).map((m) => {
    const short = m.model.split("/").slice(-1)[0].replace(/-\d{8}$/, "");
    return `
      <div class="demand-strip__model">
        <span class="demand-strip__model-name font-mono">${escapeHtml(short)}</span>
        <span class="demand-strip__model-share">${(m.share * 100).toFixed(1)}%</span>
      </div>`;
  }).join("");

  // Movers (share-delta vs 7d prior, if we have history)
  let moversHtml = "";
  if (summary.top_movers_wow && summary.top_movers_wow.length) {
    const movers = summary.top_movers_wow.slice(0, 3).map((m) => {
      const short = m.model.split("/").slice(-1)[0].replace(/-\d{8}$/, "");
      const d = m.share_delta;
      const cls = d >= 0 ? "text-[color:var(--green)]" : "text-[color:var(--rose)]";
      return `<span><span class="font-mono">${escapeHtml(short)}</span> <span class="${cls}">${(d * 100 >= 0 ? "+" : "") + (d * 100).toFixed(1)}pp</span></span>`;
    }).join(' <span class="text-[color:var(--text-faint)]">·</span> ');
    moversHtml = `<div class="demand-strip__movers"><span class="demand-strip__movers-label">WoW movers:</span> ${movers}</div>`;
  }

  return `
    <div class="demand-strip">
      <div class="demand-strip__head">
        <div class="demand-strip__title">
          <span class="demand-strip__dot"></span>
          <span>Frontier inference demand</span>
          <span class="demand-strip__sub">OpenRouter token throughput · ${escapeHtml(latest.date)}</span>
        </div>
        <div class="demand-strip__totals">
          <div class="demand-strip__big">${latest.total_tokens_b.toFixed(0)}<span class="demand-strip__big-suffix">B tokens/week</span></div>
          <div class="demand-strip__wow">${wowLabel} · ${(latest.total_requests / 1e6).toFixed(0)}M requests</div>
        </div>
      </div>
      <div class="demand-strip__body">
        <div class="demand-strip__models">${topRows}</div>
        ${moversHtml}
      </div>
    </div>`;
};

// Reverse-DCF "What's priced in" card — surfaces the gap between the 5y EPS
// CAGR implied by the current multiple and the company's most-recent trailing
// revenue YoY. Negative delta = market expects deceleration = variant-perception
// zone if you believe recent growth is durable.
window.renderImpliedCAGRCard = function (ticker, fundamentals) {
  const score = fundamentals && fundamentals.score;
  const ciq = (fundamentals && fundamentals.ciq) || {};
  if (!score || score.implied_5y_cagr == null) {
    return `<div class="text-sm text-[color:var(--text-faint)] py-3">No reverse-DCF available for ${escapeHtml(ticker)} (needs a positive trailing P/E from S&P Capital IQ).</div>`;
  }
  const impl = score.implied_5y_cagr;          // decimal CAGR (e.g. 0.265 = 26.5%)
  const delta = score.implied_vs_recent_growth; // decimal delta
  const revYoy = ciq.revenue_yoy;
  const peT = ciq.pe_trailing;
  const a = score.rdcf_assumptions || {};
  const fmtP = (x) => x == null ? "—" : (x >= 0 ? "+" : "") + (x * 100).toFixed(1) + "%";

  // Verdict logic. Big-negative delta = variant-perception buy if you trust the demand thesis.
  // Big-positive delta = priced for growth that hasn't shown up yet.
  let verdict = "";
  let tone = "neutral";
  if (delta != null) {
    if (delta < -0.30) {
      tone = "variant";
      verdict = `Market is implying steep deceleration. At a trailing P/E of <strong>${peT == null ? "—" : peT.toFixed(1)}</strong>, the multiple only requires <strong>${fmtP(impl)}</strong> EPS CAGR over five years — yet revenue just grew <strong>${fmtP(revYoy)}</strong> in the last fiscal year. If you believe the recent demand pace is durable, this is the variant-perception zone.`;
    } else if (delta < -0.10) {
      tone = "variant-mild";
      verdict = `Market is modestly pricing in deceleration. The implied 5y EPS CAGR is <strong>${fmtP(impl)}</strong> vs trailing revenue YoY of <strong>${fmtP(revYoy)}</strong>.`;
    } else if (delta < 0.10) {
      tone = "neutral";
      verdict = `Implied CAGR (<strong>${fmtP(impl)}</strong>) roughly matches the most-recent revenue YoY (<strong>${fmtP(revYoy)}</strong>) — the market is largely extrapolating recent trends forward.`;
    } else if (delta < 0.30) {
      tone = "expensive-mild";
      verdict = `Market is pricing for an <em>acceleration</em>. The multiple requires <strong>${fmtP(impl)}</strong> EPS CAGR, but the company is currently growing revenue at <strong>${fmtP(revYoy)}</strong>. Needs a re-acceleration to justify the price.`;
    } else {
      tone = "expensive";
      verdict = `Market is pricing for steep <em>acceleration</em>. The multiple demands <strong>${fmtP(impl)}</strong> EPS CAGR while revenue just grew <strong>${fmtP(revYoy)}</strong>. Either growth re-accelerates dramatically or the multiple compresses.`;
    }
  } else {
    verdict = `Implied 5y EPS CAGR: <strong>${fmtP(impl)}</strong>. (No recent revenue YoY available to compare.)`;
  }

  return `
    <article class="rdcf-card rdcf-card--${tone}">
      <header class="rdcf-card__head">
        <div class="rdcf-card__numbers">
          <div class="rdcf-card__metric">
            <div class="rdcf-card__metric-label">Implied 5y EPS CAGR</div>
            <div class="rdcf-card__metric-val">${fmtP(impl)}</div>
          </div>
          <div class="rdcf-card__metric">
            <div class="rdcf-card__metric-label">Recent revenue YoY</div>
            <div class="rdcf-card__metric-val">${fmtP(revYoy)}</div>
          </div>
          <div class="rdcf-card__metric">
            <div class="rdcf-card__metric-label">Delta</div>
            <div class="rdcf-card__metric-val ${delta == null ? "" : (delta < 0 ? "text-[color:var(--rose)]" : "text-[color:var(--green)]")}">${fmtP(delta)}</div>
          </div>
        </div>
        <div class="rdcf-card__assumptions" title="Assumptions used in the reverse-DCF solve.">
          P/E<sub>trail</sub> ${peT == null ? "—" : peT.toFixed(1)} · r=${(a.discount_rate || 0.10) * 100}% · exit P/E=${a.terminal_pe || 18} · ${a.horizon_years || 5}y horizon
        </div>
      </header>
      <p class="rdcf-card__verdict">${verdict}</p>
    </article>`;
};

window.escapeHtml = function (s) {
  return String(s == null ? "" : s)
    .replace(/&/g, "&amp;")
    .replace(/</g, "&lt;")
    .replace(/>/g, "&gt;")
    .replace(/"/g, "&quot;")
    .replace(/'/g, "&#39;");
};

// Render a small horizontal bar showing where a z-score sits within roughly
// [-2, +2], plus the numeric value. Tinted green if positive (favours quadrant)
// or red if negative. Used on stock.html in the "Why this quadrant" breakdown.
window.renderZBar = function (z) {
  if (z == null || isNaN(z)) {
    return `<span class="zbar"></span><span class="zbar__val">—</span>`;
  }
  const clamped = Math.max(-2, Math.min(2, z));
  const half = Math.abs(clamped) / 2 * 50;
  const pos = clamped >= 0;
  const fillStyle = pos ? `left: 50%; width: ${half}%;` : `right: 50%; width: ${half}%;`;
  const cls = pos ? "zbar__fill--pos" : "zbar__fill--neg";
  return `<span class="zbar"><span class="zbar__fill ${cls}" style="${fillStyle}"></span></span><span class="zbar__val ${pos ? 'pos' : 'neg'}">${z >= 0 ? "+" : ""}${z.toFixed(2)}</span>`;
};

// "Why this quadrant" — turns the score.components dict into a table of rows
// (label, raw value, peer/own median, z-bar, one-line interpretation).
// Reads peer values client-side so we don't need to change scoring.py.
window.renderQuadrantBreakdown = function (player, fundamentals) {
  const score = fundamentals && fundamentals.score;
  if (!score || !score.components) {
    return `<div class="text-sm text-[color:var(--text-faint)]">No score components available for ${escapeHtml(player.ticker)}.</div>`;
  }
  const comps = score.components;
  const ticker = player.ticker;
  const peers = playersForLayer(player.layer_id).filter((p) => p.ticker !== ticker);

  const interpret = (z, axis) => {
    if (z == null) return "";
    const mag = Math.abs(z);
    const sign = z >= 0 ? "+" : "-";
    const direction = z >= 0
      ? (axis === "business" ? "strengthens business case" : "supports cheap valuation")
      : (axis === "business" ? "drags on business case" : "drags valuation toward expensive");
    if (mag >= 1.5) return `Strongly ${direction}.`;
    if (mag >= 0.7) return `${direction[0].toUpperCase()}${direction.slice(1)}.`;
    if (mag >= 0.3) return `Mildly ${direction}.`;
    return "Roughly in line with peers.";
  };

  const row = (key) => {
    const meta = COMPONENT_META[key];
    if (!meta) return "";
    const z = comps[key];
    if (z == null) return "";
    let raw = null, peer = null;
    try { raw = meta.raw(ticker, fundamentals); } catch (e) {}
    try {
      // val_vs_own_*: peer() is given the ticker (looks up own history).
      // Everything else: peer() is given the peer-player list.
      peer = (key === "val_vs_own_pe_z" || key === "val_vs_own_fwd_pe_z")
        ? meta.peer(ticker)
        : meta.peer(peers);
    } catch (e) {}
    return `
      <div class="component-row">
        <div class="component-row__label">
          <div class="component-row__name">${escapeHtml(meta.label)}</div>
          <div class="component-row__desc">${escapeHtml(meta.desc)}</div>
        </div>
        <div class="component-row__values">
          <div class="component-row__raw">
            <span class="component-row__raw-val">${meta.fmt(raw)}</span>
            <span class="component-row__peer">${peer == null ? "" : meta.peerLabel + " " + meta.fmt(peer)}</span>
          </div>
        </div>
        <div class="component-row__z">${renderZBar(z)}</div>
        <div class="component-row__interp">${escapeHtml(interpret(z, meta.axis))}</div>
      </div>`;
  };

  // Order: business components first (in scoring.py order), then valuation.
  const order = [
    "biz_revenue_yoy_z", "biz_accel_z", "biz_margin_z", "biz_eps_revision_z", "biz_signal_density_z",
    "val_vs_own_pe_z", "val_vs_own_fwd_pe_z", "val_vs_peer_pe_z", "val_vs_peer_ev_z", "val_price_run_z",
  ];
  const bizRows = order.filter((k) => COMPONENT_META[k] && COMPONENT_META[k].axis === "business").map(row).join("");
  const valRows = order.filter((k) => COMPONENT_META[k] && COMPONENT_META[k].axis === "valuation").map(row).join("");

  // One-line summary: pick the two highest-magnitude components per axis.
  const topByAxis = (axis) => {
    return Object.entries(comps)
      .filter(([k, v]) => COMPONENT_META[k] && COMPONENT_META[k].axis === axis && v != null)
      .sort((a, b) => Math.abs(b[1]) - Math.abs(a[1]))
      .slice(0, 2)
      .map(([k, v]) => `${COMPONENT_META[k].label.toLowerCase()} (${v >= 0 ? "+" : ""}${v.toFixed(1)})`)
      .join(" + ");
  };
  const q = score.quadrant;
  const fmtAxis = (v) => v == null ? "—" : (v >= 0 ? "+" : "") + v.toFixed(2);
  const summary = `<span class="qpill qpill--${q}">${escapeHtml(quadrantLabel(q))}</span> because business avg <strong>${fmtAxis(score.business)}</strong> (driven by ${topByAxis("business") || "—"}) and valuation avg <strong>${fmtAxis(score.valuation)}</strong> (${topByAxis("valuation") || "—"}).`;

  return `
    <div class="breakdown-summary">${summary}</div>
    <div class="breakdown-section">
      <div class="breakdown-section__title">Business components <span class="breakdown-section__avg">avg ${fmtAxis(score.business)}</span></div>
      <div class="breakdown-rows">${bizRows || '<div class="text-sm text-[color:var(--text-faint)]">No business components scored.</div>'}</div>
    </div>
    <div class="breakdown-section">
      <div class="breakdown-section__title">Valuation components <span class="breakdown-section__avg">avg ${fmtAxis(score.valuation)}</span></div>
      <div class="breakdown-rows">${valRows || '<div class="text-sm text-[color:var(--text-faint)]">No valuation components scored.</div>'}</div>
    </div>`;
};

window.shellHeader = function (active) {
  const items = [
    { id: "overview", label: "Stack overview", href: "index.html" },
    { id: "stocks", label: "Stocks", href: "stocks.html" },
    { id: "signals", label: "Signals feed", href: "signals.html" },
    { id: "about", label: "Sources", href: "about.html" },
    { id: "us-movers", label: "US Movers", href: "us-movers.html" },
    { id: "tw-movers", label: "TW Movers", href: "tw-movers.html" },
    { id: "architecture", label: "Architecture", href: "architecture.html" },
  ];
  const refreshTime = DATA.meta && DATA.meta.last_refresh_at
    ? new Date(DATA.meta.last_refresh_at).toISOString().replace("T", " ").slice(0, 16) + " UTC"
    : "—";
  return `
    <header class="border-b border-[color:var(--border-soft)] sticky top-0 z-20 bg-[color:var(--bg)]/95 backdrop-blur">
      <div class="max-w-7xl mx-auto px-6 py-4 flex items-center justify-between gap-6">
        <a href="index.html" class="flex items-center gap-3">
          <div class="w-7 h-7 rounded-md bg-gradient-to-br from-violet-500/40 to-emerald-400/40 border border-[color:var(--border)]"></div>
          <div>
            <div class="font-display text-[17px] leading-none text-white">Inference Stack</div>
            <div class="text-[11px] text-[color:var(--text-faint)] uppercase tracking-widest">Bottleneck-tracking dashboard</div>
          </div>
        </a>
        <nav class="flex items-center gap-1">
          ${items.map((it) => `
            <a href="${it.href}" class="btn-ghost ${active === it.id ? "active" : ""}">${it.label}</a>
          `).join("")}
        </nav>
        <div class="text-[11px] text-[color:var(--text-faint)] tabular-nums hidden md:block">
          last refresh<br><span class="font-mono text-[color:var(--text-dim)]">${refreshTime}</span>
        </div>
      </div>
    </header>`;
};
