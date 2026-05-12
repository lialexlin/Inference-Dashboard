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
  return `
    <a href="layer.html?id=${layer.id}" class="layer-card block">
      <div class="layer-card__order">${String(layer.order).padStart(2, "0")}</div>
      <div class="flex items-start justify-between gap-4 pr-12">
        <div>
          <div class="text-xs uppercase tracking-widest text-[color:var(--text-faint)] mb-2">Layer ${layer.order}</div>
          <h3 class="font-display text-2xl text-white leading-tight mb-1">${layer.name}</h3>
          <p class="text-sm text-[color:var(--text-dim)] max-w-2xl">${layer.short_role}</p>
        </div>
        <div class="flex items-center gap-2 shrink-0">
          <span class="badge badge--${layer.status}" title="${escapeHtml(statusDefinition(layer.status))}">${statusLabel(layer.status)}</span>
          ${layer.status_override ? `<span class="badge-hint">manual</span>` : ""}
        </div>
      </div>
      <p class="mt-4 text-[13px] text-[color:var(--text-faint)] max-w-3xl italic">${layer.bottleneck_summary}</p>
      <div class="mt-4 flex flex-wrap gap-2">${chips}</div>
    </a>`;
};

window.renderSignalCard = function (sig, opts) {
  opts = opts || {};
  const tags = (sig.layer_ids || []).map((id) => {
    const l = layerById(id);
    return l ? `<a class="layer-pill" href="layer.html?id=${id}">${l.name}</a>` : "";
  }).join(" ");
  const tickers = (sig.tickers || []).slice(0, 6).map((t) => `<a href="stock.html?ticker=${encodeURIComponent(t)}" class="font-mono text-[11px] text-[color:var(--text-dim)] hover:text-[color:var(--sky)] hover:underline underline-offset-2">${t}</a>`).join("<span class='text-[color:var(--text-faint)]'>·</span>");

  // Filing summary block (10-K / 10-Q / paired earnings 8-K with summary from
  // data/filing_summaries.json). Falls back to bare card if no summary.
  let summaryBlock = "";
  if (sig.source_type === "filing" && sig.summary) {
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

  const quote = !summaryBlock && sig.quote ? `<div class="signal__quote">${escapeHtml(sig.quote)}</div>` : "";
  const sourceName = sig.url
    ? `<a href="${sig.url}" target="_blank" rel="noopener" class="text-sm text-[color:var(--text-dim)] hover:text-[color:var(--sky)] underline decoration-dotted underline-offset-2">${escapeHtml(sig.source)}</a>`
    : `<span class="text-sm text-[color:var(--text-dim)]">${escapeHtml(sig.source)}</span>`;
  let host = "";
  try { host = sig.url ? new URL(sig.url).hostname.replace(/^www\./, "") : ""; } catch (e) { host = ""; }
  const sourceFooter = sig.url
    ? `<div class="mt-3 text-[11px] text-[color:var(--text-faint)]">
         ${summaryBlock ? `<a href="${sig.url}" target="_blank" rel="noopener" class="hover:text-[color:var(--sky)]">Read full filing →</a>`
                        : `source: <a href="${sig.url}" target="_blank" rel="noopener" class="hover:text-[color:var(--sky)]">${escapeHtml(host || sig.url)} ↗</a>`}
       </div>`
    : "";
  return `
    <article class="signal" id="${sig.id}">
      <div class="flex items-center justify-between gap-3 flex-wrap">
        <div class="flex items-center gap-2 flex-wrap">
          <span class="tag tag--${sig.source_type}">${sig.source_type}</span>
          ${sourceName}
          <span class="text-[color:var(--text-faint)]">·</span>
          <span class="signal__date">${fmtDate(sig.date)} <span class="text-[color:var(--text-faint)]">(${relDate(sig.date)})</span></span>
        </div>
        <div class="flex items-center gap-2 flex-wrap">${tags}</div>
      </div>
      <h4 class="mt-2 text-[15px] text-white font-medium leading-snug">
        <a href="${sig.url}" target="_blank" rel="noopener" class="hover:text-[color:var(--sky)]">${escapeHtml(sig.headline)}</a>
      </h4>
      ${summaryBlock}
      ${quote}
      ${tickers ? `<div class="mt-3 flex items-center gap-2 flex-wrap">${tickers}</div>` : ""}
      ${sourceFooter}
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
    { id: "signals", label: "Signals feed", href: "signals.html" },
    { id: "about", label: "Sources", href: "about.html" },
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
