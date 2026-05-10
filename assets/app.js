// Shared utilities + data loaders. Pure functions on window for reuse across pages.

window.DATA = window.DATA || {};

window.loadJson = async function (path) {
  const r = await fetch(path, { cache: "no-store" });
  if (!r.ok) throw new Error(`fetch ${path} failed: ${r.status}`);
  return r.json();
};

window.loadAll = async function () {
  const [layers, players, prices, fundamentals, signals, meta] = await Promise.all([
    loadJson("data/layers.json"),
    loadJson("data/players.json"),
    loadJson("data/prices.json").catch(() => ({})),
    loadJson("data/fundamentals.json").catch(() => ({})),
    loadJson("data/signals.json").catch(() => []),
    loadJson("data/meta.json").catch(() => ({})),
  ]);
  Object.assign(window.DATA, { layers, players, prices, fundamentals, signals, meta });
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
