// Helpers shared by tw-movers.html and us-movers.html. Returns are in percent
// (12.3 = +12.3%), so they format with fmtPct from app.js.

const PERIOD_ORDER = ["ret_1d", "ret_1w", "ret_1m", "ret_3m", "ret_6m", "ret_1y"];

// Diverging color for a return, used in heat-map and table cells.
// Thresholds: ±5% mild, ±15% moderate, ±30% strong.
function retColor(v) {
  if (v == null || isNaN(v)) return "var(--text-faint)";
  if (v >= 30) return "#34d399";
  if (v >= 15) return "#6ee7b7";
  if (v >= 5)  return "#a7f3d0";
  if (v > -5)  return "var(--text-faint)";
  if (v > -15) return "#fda4af";
  return "var(--rose)";
}

function retClass(v) {
  if (v == null || isNaN(v)) return "ret-flat";
  if (v >= 30) return "ret-strong-up";
  if (v >= 5)  return "ret-up";
  if (v > -5)  return "ret-flat";
  if (v > -15) return "ret-dn";
  return "ret-strong-dn";
}

// Heat-map background on the same diverging scale.
function heatBg(v) {
  if (v == null || isNaN(v)) return "var(--bg-card)";
  const abs = Math.abs(v);
  const alpha = Math.min(abs / 40, 1) * 0.55 + 0.06;
  if (v >= 0) return `rgba(52,211,153,${alpha.toFixed(2)})`;
  return `rgba(251,113,133,${alpha.toFixed(2)})`;
}

// Missing values sort last in either direction.
function numCmp(a, b, dir) {
  const aNull = a == null || (typeof a === "number" && isNaN(a));
  const bNull = b == null || (typeof b === "number" && isNaN(b));
  if (aNull && bNull) return 0;
  if (aNull) return 1;
  if (bNull) return -1;
  return dir === "desc" ? b - a : a - b;
}

function strCmp(a, b, dir) {
  a = (a || "").toLowerCase();
  b = (b || "").toLowerCase();
  if (a < b) return dir === "desc" ? 1 : -1;
  if (a > b) return dir === "desc" ? -1 : 1;
  return 0;
}

function median(arr) {
  const a = arr.filter((v) => v != null && !isNaN(v)).sort((x, y) => x - y);
  if (!a.length) return null;
  const m = Math.floor(a.length / 2);
  return a.length % 2 ? a[m] : (a[m - 1] + a[m]) / 2;
}

// Per-industry median return for each period, over the stocks given.
function computeSectors(subset) {
  const by = new Map();
  subset.forEach((s) => {
    const key = s.industry_en || "Other";
    if (!by.has(key)) by.set(key, { industry_en: key, n: 0, vals: {} });
    const o = by.get(key);
    o.n += 1;
    PERIOD_ORDER.forEach((p) => { (o.vals[p] = o.vals[p] || []).push(s[p]); });
  });
  const out = [];
  by.forEach((o) => {
    const sec = { industry_en: o.industry_en, n: o.n };
    PERIOD_ORDER.forEach((p) => { sec["median_" + p.replace("ret_", "")] = median(o.vals[p]); });
    out.push(sec);
  });
  return out;
}
