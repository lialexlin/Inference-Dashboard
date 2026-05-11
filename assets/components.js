// Render helpers shared across pages.

window.statusLabel = function (status) {
  return status.replace("-", " ");
};

window.renderPlayerChip = function (player) {
  const px = DATA.prices[player.ticker];
  const chg = px && px.change_1m != null ? px.change_1m : null;
  const cls = changeClass(chg);
  const chgText = chg == null ? "" : `<span class="chip__chg ${cls}">${fmtPct(chg)}</span>`;
  return `
    <span class="chip" title="${escapeHtml(player.name)} — ${escapeHtml(player.role)}">
      <span class="chip__ticker">${player.ticker}</span>${chgText}
    </span>`;
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
        <span class="badge badge--${layer.status} shrink-0">${statusLabel(layer.status)}</span>
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
  const tickers = (sig.tickers || []).slice(0, 6).map((t) => `<span class="font-mono text-[11px] text-[color:var(--text-dim)]">${t}</span>`).join("<span class='text-[color:var(--text-faint)]'>·</span>");
  const quote = sig.quote ? `<div class="signal__quote">${escapeHtml(sig.quote)}</div>` : "";
  const sourceName = sig.url
    ? `<a href="${sig.url}" target="_blank" rel="noopener" class="text-sm text-[color:var(--text-dim)] hover:text-[color:var(--sky)] underline decoration-dotted underline-offset-2">${escapeHtml(sig.source)}</a>`
    : `<span class="text-sm text-[color:var(--text-dim)]">${escapeHtml(sig.source)}</span>`;
  let host = "";
  try { host = sig.url ? new URL(sig.url).hostname.replace(/^www\./, "") : ""; } catch (e) { host = ""; }
  const sourceFooter = sig.url
    ? `<div class="mt-3 text-[11px] text-[color:var(--text-faint)]">
         source: <a href="${sig.url}" target="_blank" rel="noopener" class="hover:text-[color:var(--sky)]">${escapeHtml(host || sig.url)} ↗</a>
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
