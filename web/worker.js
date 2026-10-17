// Search engine for the page. Runs in a Web Worker so typing stays smooth
// while 400k icon names are scanned. Mirrors scripts/atlas/query.py.

let meta, rows, vocab, vocabKeys, rev, styleTokens;

const AR = /[؀-ۿ]/;
function normAr(text) {
  let t = text.normalize("NFC").replace(/[ً-ْٰـ]/g, "")
    .replace(/[أإآٱ]/g, "ا").replace(/ة/g, "ه").replace(/ى/g, "ي").replace(/ؤ/g, "و").replace(/ئ/g, "ي")
    .toLowerCase();
  return t.split(/\s+/).filter(Boolean).map((w) => {
    for (const art of ["وال", "بال", "لل", "ال"]) {
      if (w.startsWith(art) && w.length - art.length >= 2) return w.slice(art.length);
    }
    return w;
  }).join(" ");
}

async function load(base) {
  const [m, icons, ar] = await Promise.all([
    fetch(base + "meta.json").then((r) => r.json()),
    fetch(base + "icons.json").then((r) => r.json()),
    fetch(base + "ar.json").then((r) => r.json()),
  ]);
  meta = m;
  rev = ar.rev;
  styleTokens = new Set(meta.styleTokens);
  const setIndex = new Map(meta.setsInfo.map((s, i) => [s.p, i]));
  rows = [];
  vocab = new Map();
  for (const block of icons) {
    const si = setIndex.get(block.p);
    for (const r of block.i) {
      const id = rows.length;
      const toks = r[0].toLowerCase().split(/[-_:]+/).filter(Boolean);
      const concept = toks.filter((t) => !styleTokens.has(t) && !/^\d+(px)?$/.test(t)).join("-") || r[0];
      rows.push({ s: si, n: r[0], st: r[1], w: r[2], c: r[3], k: r[4], k2: r[5], pr: r[6], concept });
      for (const t of new Set(toks)) {
        const base = t.replace(/\d+$/, "") || t;
        for (const key of base === t ? [t] : [t, base]) {
          let list = vocab.get(key);
          if (!list) vocab.set(key, (list = []));
          list.push(id);
        }
      }
    }
  }
  vocabKeys = [...vocab.keys()];
  postMessage({ type: "ready", meta: { ...meta, setsInfo: meta.setsInfo }, terms: ar.terms });
}

function rowsForTokens(tokens) {
  const out = new Set();
  for (const t of tokens) for (const id of vocab.get(t) || []) out.add(id);
  return out;
}

function parse(query) {
  const q = query.trim().toLowerCase();
  if (!q) return null;
  const words = q.split(/\s+/).filter(Boolean);
  const isAr = AR.test(q);
  const groups = [];          // one set of name-words per query word (AND across groups)
  let exact = new Set();      // concepts that exactly mean the whole query
  let enTarget = "";
  if (isAr) {
    const nq = normAr(q);
    exact = new Set(rev[nq] || []);
    for (const w of nq.split(" ")) {
      const toks = new Set(rev[w] || []);
      for (const [phrase, list] of Object.entries(rev)) {
        if (phrase.split(" ")[0] === w) list.forEach((t) => toks.add(t));
      }
      if (toks.size) groups.push(toks);
    }
    if (!groups.length && exact.size) groups.push(exact);
  } else {
    enTarget = words.join("-");
    for (const w of words) {
      const toks = new Set(vocabKeys.filter((k) => k.startsWith(w)));
      groups.push(toks);
    }
  }
  return { groups, exact, enTarget, isAr };
}

function search(opts) {
  const f = opts.filters;
  const p = parse(opts.query || "");
  let candidates;
  if (p) {
    if (!p.groups.length || p.groups.some((g) => !g.size)) return { total: 0, items: [] };
    const sets = p.groups.map(rowsForTokens).sort((a, b) => a.size - b.size);
    candidates = [...sets[0]].filter((id) => sets.every((s) => s.has(id)));
  } else {
    candidates = rows.map((_, i) => i);
  }
  const union = p && p.isAr ? new Set(p.groups.flatMap((g) => [...g])) : null;
  const scored = [];
  for (const id of candidates) {
    const r = rows[id];
    const set = meta.setsInfo[r.s];
    if (f.commercial && set.t > 1) continue;
    if (f.style !== null && r.st !== f.style) continue;
    if (f.corners !== null && r.c !== f.corners) continue;
    if (f.cat !== null && r.k !== f.cat && r.k2 !== f.cat) continue;
    if (f.weight !== null && (r.w < 0 || Math.abs(r.w / 10 - f.weight) > 0.3)) continue;
    let score = r.pr / 10;
    if (p) {
      const parts = r.concept.split("-");
      if (p.enTarget) {
        if (r.concept === p.enTarget) score += 8;
        else if (r.concept.startsWith(p.enTarget)) score += 2;
      } else if (p.isAr) {
        if (p.exact.has(r.concept)) score += 8;
        else if (parts.every((t) => union.has(t)) && p.groups.every((g) => parts.some((t) => g.has(t)))) score += 6;
      }
      score -= 0.15 * (parts.length - 1);
    }
    scored.push([score, id]);
  }
  scored.sort((a, b) => b[0] - a[0]);
  // variety: at most two icons per library in a row of results
  const items = [], perSet = new Map(), overflow = [];
  for (const [, id] of scored) {
    const s = rows[id].s;
    const n = perSet.get(s) || 0;
    if (n < 2) { perSet.set(s, n + 1); items.push(id); } else overflow.push(id);
    if (items.length >= opts.limit) break;
  }
  if (items.length < opts.limit) items.push(...overflow.slice(0, opts.limit - items.length));
  return {
    total: scored.length,
    items: items.map((id) => {
      const r = rows[id];
      return { p: meta.setsInfo[r.s].p, n: r.n, st: r.st, w: r.w, c: r.c, k: r.k, k2: r.k2, concept: r.concept };
    }),
  };
}

onmessage = async (e) => {
  const m = e.data;
  if (m.type === "load") {
    try { await load(m.base); } catch (err) { postMessage({ type: "error", message: String(err) }); }
  } else if (m.type === "search") {
    postMessage({ type: "results", seq: m.seq, ...search(m) });
  }
};
