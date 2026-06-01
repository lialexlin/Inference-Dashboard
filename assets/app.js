// Shared utilities + data loaders. Pure functions on window for reuse across pages.

window.DATA = window.DATA || {};

window.loadJson = async function (path) {
  const r = await fetch(path, { cache: "no-store" });
  if (!r.ok) throw new Error(`fetch ${path} failed: ${r.status}`);
  return r.json();
};

window.loadAll = async function () {
  const [layers, players, prices, fundamentals, signals, meta, multiplesHistory, manualEstimates, crossQuarter, bottleneck, demandSignals, exitTriggers, narrativeTracking] = await Promise.all([
    loadJson("data/layers.json"),
    loadJson("data/players.json"),
    loadJson("data/prices.json").catch(() => ({})),
    loadJson("data/fundamentals.json").catch(() => ({})),
    loadJson("data/signals.json").catch(() => []),
    loadJson("data/meta.json").catch(() => ({})),
    loadJson("data/multiples_history.json").catch(() => ({})),
    loadJson("data/manual_estimates.json").catch(() => ({})),
    loadJson("data/cross_quarter.json").catch(() => ({})),
    loadJson("data/bottleneck.json").catch(() => ({})),
    loadJson("data/demand_signals.json").catch(() => ({})),
    loadJson("data/exit_triggers.json").catch(() => ({})),
    loadJson("data/narrative_tracking.json").catch(() => ({ by_ticker: {} })),
  ]);
  Object.assign(window.DATA, {
    layers, players, prices, fundamentals, signals, meta,
    multiples_history: multiplesHistory,
    manual_estimates: manualEstimates,
    cross_quarter: crossQuarter,
    bottleneck,
    demand_signals: demandSignals,
    exit_triggers: exitTriggers,
    narrative_tracking: narrativeTracking,
  });
  return window.DATA;
};

// ---------- Formatting helpers ----------

window.fmtPct = function (v, withSign = true) {
  if (v == null || isNaN(v)) return "—";
  const s = (withSign && v > 0 ? "+" : "") + v.toFixed(1) + "%";
  return s;
};

window.fmtPrice = function (v, currency) {
  if (v == null || isNaN(v)) return "—";
  const c = currency || "USD";
  const sign = { USD: "$", EUR: "€", GBP: "£", JPY: "¥", KRW: "₩", TWD: "NT$", HKD: "HK$", CNY: "¥" }[c] || "";
  if (c === "JPY" || c === "KRW") return sign + Math.round(v).toLocaleString();
  return sign + v.toLocaleString(undefined, { maximumFractionDigits: 2 });
};

window.fmtMcap = function (v) {
  if (v == null || isNaN(v)) return "—";
  if (v >= 1e12) return "$" + (v / 1e12).toFixed(2) + "T";
  if (v >= 1e9) return "$" + (v / 1e9).toFixed(1) + "B";
  if (v >= 1e6) return "$" + (v / 1e6).toFixed(0) + "M";
  return "$" + v.toLocaleString();
};

window.fmtPE = function (v) {
  if (v == null || isNaN(v)) return "—";
  if (v < 0) return "—";
  return v.toFixed(1);
};

// Generic ratio (EV/EBITDA, P/S, P/B, etc.) — same shape as fmtPE but stays as a separate helper
// in case we want to differentiate styling later.
window.fmtMultiple = function (v) {
  if (v == null || isNaN(v)) return "—";
  if (v < 0) return "—";
  return v.toFixed(1);
};

window.fmtDate = function (iso) {
  if (!iso) return "—";
  try {
    const d = new Date(iso);
    return d.toISOString().slice(0, 10);
  } catch (e) {
    return iso;
  }
};

window.relDate = function (iso) {
  if (!iso) return "";
  const d = new Date(iso);
  const now = new Date();
  const days = Math.round((now - d) / 86400000);
  if (days < 0) return "in " + Math.abs(days) + "d";
  if (days === 0) return "today";
  if (days === 1) return "1d ago";
  if (days < 30) return days + "d ago";
  if (days < 365) return Math.floor(days / 30) + "mo ago";
  return Math.floor(days / 365) + "y ago";
};

window.changeClass = function (v) {
  if (v == null || isNaN(v)) return "flat";
  if (v > 0.05) return "up";
  if (v < -0.05) return "dn";
  return "flat";
};

// ---------- URL helpers ----------

window.qs = function (key) {
  return new URLSearchParams(location.search).get(key);
};

// ---------- Layer + player helpers ----------

window.playersForLayer = function (layerId) {
  return DATA.players.filter(
    (p) => p.layer_id === layerId || (p.secondary_layers || []).includes(layerId)
  );
};

window.layerById = function (id) {
  return DATA.layers.find((l) => l.id === id);
};

window.playerByTicker = function (ticker) {
  return (DATA.players || []).find((p) => p.ticker === ticker) || null;
};

// Median of a numeric array, ignoring null/NaN. Returns null if no values.
window.peerMedian = function (values) {
  const xs = (values || []).filter((v) => v != null && !isNaN(v)).slice().sort((a, b) => a - b);
  if (!xs.length) return null;
  const m = Math.floor(xs.length / 2);
  return xs.length % 2 ? xs[m] : (xs[m - 1] + xs[m]) / 2;
};

// Friendly labels + raw-value resolvers for each score component.
// Mirrors the component math in jobs/scoring.py (75-203). Returns null if the
// underlying raw value isn't present in fundamentals (rare for biz components,
// expected for val_*_fwd_pe when the ticker has no manual estimates).
window.COMPONENT_META = {
  biz_revenue_yoy_z: {
    axis: "business",
    label: "Revenue growth vs peers",
    desc: "Trailing 12-month revenue growth, z-scored within this ticker's primary layer.",
    fmt: (v) => fmtPct(v == null ? null : v * 100),
    raw: (t, f) => (f.ciq || {}).revenue_yoy,
    peer: (peers) => peerMedian(peers.map((p) => ((DATA.fundamentals[p.ticker] || {}).ciq || {}).revenue_yoy)),
    peerLabel: "peer median",
  },
  biz_accel_z: {
    axis: "business",
    label: "Growth acceleration",
    desc: "Latest YoY growth minus 3-year revenue CAGR. Positive = re-accelerating.",
    fmt: (v) => v == null ? "—" : (v >= 0 ? "+" : "") + (v * 100).toFixed(1) + " pp",
    raw: (t, f) => {
      const c = f.ciq || {};
      return c.revenue_yoy != null && c.revenue_cagr_3y != null ? c.revenue_yoy - c.revenue_cagr_3y : null;
    },
    peer: (peers) => peerMedian(peers.map((p) => {
      const c = (DATA.fundamentals[p.ticker] || {}).ciq || {};
      return c.revenue_yoy != null && c.revenue_cagr_3y != null ? c.revenue_yoy - c.revenue_cagr_3y : null;
    })),
    peerLabel: "peer median",
  },
  biz_margin_z: {
    axis: "business",
    label: "EBITDA margin vs peers",
    desc: "Latest fiscal-year EBITDA margin.",
    fmt: (v) => fmtPct(v == null ? null : v * 100, false),
    raw: (t, f) => (f.ciq || {}).ebitda_margin,
    peer: (peers) => peerMedian(peers.map((p) => ((DATA.fundamentals[p.ticker] || {}).ciq || {}).ebitda_margin)),
    peerLabel: "peer median",
  },
  biz_eps_revision_z: {
    axis: "business",
    label: "Forward-EPS revision",
    desc: "Change in forward-EPS estimate vs the most recent prior snapshot in manual_estimates.",
    fmt: (v) => v == null ? "—" : (v >= 0 ? "+" : "") + (v * 100).toFixed(1) + "%",
    raw: () => null, // not directly stored in fundamentals; the z value tells the story
    peer: () => null,
    peerLabel: "peer median",
  },
  biz_signal_density_z: {
    axis: "business",
    label: "Demand-tightness mentions (90d)",
    desc: "Count of signals in the last 90 days mentioning this ticker with capex / lead-time / shortage / backlog language.",
    fmt: (v) => v == null ? "—" : String(v),
    raw: (t, f) => (f.score && f.score.signal_density_90d != null) ? f.score.signal_density_90d : null,
    peer: (peers) => peerMedian(peers.map((p) => {
      const s = (DATA.fundamentals[p.ticker] || {}).score;
      return s && s.signal_density_90d != null ? s.signal_density_90d : null;
    })),
    peerLabel: "peer median",
  },
  val_vs_own_pe_z: {
    axis: "valuation",
    label: "P/E vs own history",
    desc: "Current trailing P/E vs this ticker's 8-year median. Positive z = cheaper than own history.",
    fmt: (v) => fmtPE(v),
    raw: (t, f) => (f.ciq || {}).pe_trailing,
    peer: (t) => {
      const mh = (DATA.multiples_history || {})[t];
      return mh ? peerMedian((mh.pe || []).map((x) => x.value)) : null;
    },
    peerLabel: "own median",
  },
  val_vs_own_fwd_pe_z: {
    axis: "valuation",
    label: "Forward P/E vs own history",
    desc: "Current forward P/E vs manual_estimates 5-year median. Positive z = cheaper than own history.",
    fmt: (v) => fmtPE(v),
    raw: (t, f) => f.pe_forward,
    peer: (t) => {
      const me = (DATA.manual_estimates || {})[t];
      return me ? me.fwd_pe_5y_median : null;
    },
    peerLabel: "own 5y median",
  },
  val_vs_peer_pe_z: {
    axis: "valuation",
    label: "P/E vs peers",
    desc: "Trailing P/E vs the median of this ticker's primary-layer peers. Positive z = cheaper.",
    fmt: (v) => fmtPE(v),
    raw: (t, f) => (f.ciq || {}).pe_trailing,
    peer: (peers) => peerMedian(peers.map((p) => ((DATA.fundamentals[p.ticker] || {}).ciq || {}).pe_trailing)),
    peerLabel: "peer median",
  },
  val_vs_peer_ev_z: {
    axis: "valuation",
    label: "EV/EBITDA vs peers",
    desc: "Trailing EV/EBITDA vs the median of layer peers. Positive z = cheaper.",
    fmt: (v) => fmtMultiple(v),
    raw: (t, f) => (f.ciq || {}).ev_ebitda,
    peer: (peers) => peerMedian(peers.map((p) => ((DATA.fundamentals[p.ticker] || {}).ciq || {}).ev_ebitda)),
    peerLabel: "peer median",
  },
  val_price_run_z: {
    axis: "valuation",
    label: "1-year price run vs peers",
    desc: "12-month total return vs peer median. Positive z = under-rallied (still has room).",
    fmt: (v) => fmtPct(v),
    raw: (t) => {
      const px = (DATA.prices || {})[t];
      return px && px.history && px.history.length > 20
        ? ((px.history[px.history.length - 1].close / px.history[0].close - 1) * 100)
        : null;
    },
    peer: (peers) => peerMedian(peers.map((p) => {
      const px = (DATA.prices || {})[p.ticker];
      return px && px.history && px.history.length > 20
        ? ((px.history[px.history.length - 1].close / px.history[0].close - 1) * 100)
        : null;
    })),
    peerLabel: "peer median",
  },
};

// ---------- Score / quadrant helpers ----------

window.scoreFor = function (ticker) {
  const f = (DATA.fundamentals || {})[ticker];
  return f && f.score ? f.score : null;
};

window.quadrantLabel = function (q) {
  return ({
    underappreciated: "Underappreciated",
    "priced-in": "Priced in",
    "value-trap": "Value trap",
    avoid: "Avoid",
    fair: "Fair",
    unscored: "—",
  })[q] || q;
};

// Plain-language definitions surfaced on hover and in inline legends.
// These mirror the thresholds in jobs/scoring.py (THRESH = 0.3 for quadrants;
// ROLL_UNDER_FRACTION = 0.30 and ROLL_PRICED_FRACTION = 0.50 for layer rollup).
window.quadrantDefinition = function (q) {
  return ({
    underappreciated: "Strong fundamentals AND cheap vs. peers — top idea zone.",
    "priced-in": "Strong fundamentals but already expensive — the trade is consensus.",
    "value-trap": "Cheap on paper but weak fundamentals — optical bargain, no growth.",
    avoid: "Weak fundamentals AND expensive — no edge either way.",
    fair: "Middle ground — fundamentals and price roughly in balance vs. peers.",
    unscored: "Not yet scored — usually missing fundamentals or price data.",
  })[q] || "";
};

window.statusDefinition = function (status) {
  return ({
    underappreciated: "≥30% of the layer's tickers are in the underappreciated quadrant — top-idea zone.",
    "priced-in": "≥50% of the layer's tickers are strong but already expensive — consensus trade.",
    "value-trap": "≥50% of the layer's tickers are cheap but weak — optical bargains, no growth.",
    avoid: "≥50% of the layer's tickers are weak AND expensive — no edge.",
    fair: "Default — no quadrant dominates; the layer is balanced overall.",
  })[status] || "";
};

// Score bar fill: maps a value in roughly [-2, +2] to a half-bar that grows
// out from the center, colored green (positive) or red (negative).
window.renderScoreBar = function (v) {
  if (v == null || isNaN(v)) {
    return `<span class="score-bar"></span><span class="score-bar__val">—</span>`;
  }
  const clamped = Math.max(-2, Math.min(2, v));
  const half = Math.abs(clamped) / 2 * 50; // up to 50% of bar
  const pos = clamped >= 0;
  const fillStyle = pos
    ? `left: 50%; width: ${half}%;`
    : `right: 50%; width: ${half}%;`;
  const cls = pos ? "score-bar__fill--pos" : "score-bar__fill--neg";
  return `<span class="score-bar"><span class="score-bar__fill ${cls}" style="${fillStyle}"></span></span><span class="score-bar__val">${v >= 0 ? "+" : ""}${v.toFixed(1)}</span>`;
};
