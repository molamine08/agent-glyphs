// Agent Glyphs search engine for the page. Runs in a Web Worker so typing stays smooth
// while 400k icon names are scanned. Mirrors scripts/atlas/query.py.

let meta, rows, vocab, vocabKeys, styleTokens, C, termsAr, glyphs = [];

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

async function load(base, v = "") {
  const q = v ? `?v=${v}` : "";
  const [m, icons, ar, gl] = await Promise.all([
    fetch(base + "meta.json" + q).then((r) => r.json()),
    fetch(base + "icons.json" + q).then((r) => r.json()),
    fetch(base + "ar.json" + q).then((r) => r.json()),
    fetch(base + "glyphs.json" + q).then((r) => r.json()).catch(() => []),
  ]);
  meta = m;
  glyphs = gl.map((g) => ({ ...g, t: new Set(g.t), f: new Set(g.f) }));
  C = { g: ar.g, ax: ar.ax, as: ar.as, en: ar.en };
  termsAr = ar.terms;
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
      rows.push({ s: si, n: r[0], sh: r[1], co: r[2], w: r[3], c: r[4], k: r[5], k2: r[6], pr: r[7], d: r[8], concept });
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
  postMessage({ type: "ready", meta: { ...meta, setsInfo: meta.setsInfo }, terms: ar.terms, labels: ar.lab || {},
    glyphChars: gl.filter((g) => !g.e).map((g) => g.ch).join("") });
}

function rowsForTokens(tokens) {
  const out = new Set();
  for (const t of tokens) {
    if (t.includes("-")) {
      // a compound like "log-out": icons whose names use every part
      const sets = t.split("-").map((x) => vocab.get(x) || []).sort((a, b) => a.length - b.length);
      const rest = sets.slice(1).map((x) => new Set(x));
      for (const id of sets[0]) if (rest.every((r) => r.has(id))) out.add(id);
    } else for (const id of vocab.get(t) || []) out.add(id);
  }
  return out;
}

// ---- meaning-aware expansion, mirrors scripts/atlas/concepts.py
const AR_PREFIXES = ["و", "ف", "ب", "ك", "ل"];
const AR_SUFFIXES = ["يات", "ات", "ون", "ين", "ان", "يه", "ها", "هم", "كم", "نا", "ه", "ي"];
const EN_SUFFIXES = [["ies", "y"], ["es", ""], ["s", ""], ["ing", ""], ["ed", ""]];

function arForms(word) {
  const w = normAr(word);
  if (!w) return [];
  const out = [w], bases = [w];
  if (w.length >= 4 && AR_PREFIXES.includes(w[0])) {
    const b = normAr(w.slice(1));
    if (b.length >= 3) { bases.push(b); out.push(b); }
  }
  for (const b of bases) {
    for (const suf of AR_SUFFIXES) {
      if (b.endsWith(suf) && b.length - suf.length >= 3) { out.push(b.slice(0, -suf.length)); break; }
    }
  }
  return [...new Set(out)];
}
function enForms(word) {
  const w = word.toLowerCase(), out = [w];
  // "-ing"/"-ed" need a longer stem: "rating" is not "rat"
  for (const [suf, rep] of EN_SUFFIXES) if (w.endsWith(suf) && w.length - suf.length >= (suf === "ing" || suf === "ed" ? 4 : 3)) out.push(w.slice(0, -suf.length) + rep);
  return [...new Set(out)];
}
function lookupAr(phrase) {
  if (phrase.includes(" ")) return C.ax[normAr(phrase)] || [];
  const forms = arForms(phrase);
  for (const f of forms) if (C.ax[f]) return C.ax[f];
  for (const f of forms) if (C.as[f]) return C.as[f];
  return [];
}
function lookupEn(word) {
  for (const f of enForms(word)) if (C.en[f]) return C.en[f];
  return [];
}
function expand(text) {
  const words = text.toLowerCase().match(/[\p{L}\p{N}]+/gu) || [];
  const parts = [];
  for (let i = 0; i < words.length;) {
    let hit = null;
    for (const n of [5, 4, 3, 2]) {
      if (i + n <= words.length && words.slice(i, i + n).every((w) => AR.test(w))) {
        const g = lookupAr(words.slice(i, i + n).join(" "));
        if (g.length) { hit = [words.slice(i, i + n).join(" "), g, n]; break; }
      }
    }
    if (!hit) { const w = words[i]; hit = [w, AR.test(w) ? lookupAr(w) : lookupEn(w), 1]; }
    const [t, gids, n] = hit;
    const part = { text: t, ar: AR.test(t), strong: new Set(), related: new Set(), groups: gids };
    for (const gi of gids) { C.g[gi][0].forEach((x) => part.strong.add(x)); C.g[gi][1].forEach((x) => part.related.add(x)); }
    if (!part.ar) enForms(t).forEach((x) => part.strong.add(x));
    part.strong.forEach((x) => part.related.delete(x));
    parts.push(part);
    i += n;
  }
  return parts;
}
function level(ctoks, concept, part) {
  if (part.strong.has(concept)) return 3;
  for (const t of ctoks) if (part.strong.has(t)) return 2;
  if (part.related.has(concept)) return 1;
  for (const t of ctoks) if (part.related.has(t)) return 1;
  return 0;
}

// ---- glyphs (Unicode characters), mirrors scripts/atlas/glyphs.py
function glyphLevel(g, part) {
  if (part.ar && g.a.includes(normAr(part.text))) return 5;
  if (part.strong.has(g.n) || (!part.ar && g.t.has(part.text))) return 4;
  for (const x of part.strong) if (g.t.has(x)) return 3;
  if (part.ar) {
    const words = normAr(part.text).split(" ").filter(Boolean);
    if (words.length && words.every((w) => arForms(w).some((f) => g.f.has(f)))) return 2;
  } else if (part.text.length >= 3 && [...g.t].some((x) => x.startsWith(part.text))) return 2;
  for (const x of part.related) if (g.t.has(x)) return 1;
  return 0;
}
function searchGlyphs(query, p, limit) {
  let out = [];
  for (const g of glyphs) {
    let lv = 0;
    if (query && query.includes(g.ch)) lv = 6;
    else if (p) lv = Math.min(...p.parts.map((pt) => glyphLevel(g, pt)));
    if (!lv) continue;
    let overlap = 0;
    for (const pt of p ? p.parts : []) for (const x of pt.strong) if (g.t.has(x)) overlap++;
    out.push([lv, overlap, -g.n.length, g]);
  }
  out.sort((a, b) => b[0] - a[0] || b[1] - a[1] || b[2] - a[2]);
  if (out.length && out[0][0] >= 2) out = out.filter((x) => x[0] >= 2);  // related glyphs only when nothing closer
  return out.slice(0, limit).map(([lv, , , g]) => glyphItem(g, lv));
}
const glyphItem = (g, lv = 4) => ({ g: 1, p: "unicode", n: g.n, ch: g.ch, cp: g.cp, un: g.un, e: g.e || 0, w: g.w || 0, lv, t: [...g.t] });

function parse(query) {
  const q = query.trim().toLowerCase();
  if (!q) return null;
  const parts = expand(q);
  const isAr = AR.test(q);
  // rows each part can reach: the word itself (English: as a name prefix), its synonyms, related things
  const groups = parts.map((p) => {
    const toks = new Set([...p.strong, ...p.related]);
    if (!p.ar) vocabKeys.forEach((k) => { if (k.startsWith(p.text)) toks.add(k); });
    return toks;
  });
  const rel = [];
  for (const p of parts) for (const gi of p.groups) for (const r of C.g[gi][1]) if (!p.strong.has(r) && !rel.includes(r)) rel.push(r);
  return { parts, groups, enTarget: isAr ? "" : (q.match(/[a-z0-9]+/g) || []).join("-"), isAr, rel: rel.slice(0, 8) };
}

function search(opts) {
  const f = opts.filters;
  const p = parse(opts.query || "");
  // glyphs have no style, stroke or corners: any of those filters means icons only
  const culture = meta.categories.findIndex(([k]) => k === "culture");
  const glyphsOk = f.kind !== "icon" && f.shape === null && f.color === null && f.density === null && f.corners === null
    && f.weight === null && (f.cat === null || f.cat === culture);
  let gl = [];
  if (glyphsOk) gl = p ? searchGlyphs(opts.query.trim(), p, f.kind === "glyph" ? opts.limit : 6) : f.kind === "glyph" ? glyphs.map((g) => glyphItem(g)) : [];
  if (f.kind === "glyph") return { total: gl.length, sets: 0, glyphs: gl.length, counts: null, all: null, rel: p ? p.rel : [], items: gl.slice(0, opts.limit) };
  const res = searchIcons(opts, f, p);
  if (gl.length) {
    const first = gl.filter((g) => g.lv >= 4).slice(0, 3), later = gl.filter((g) => !first.includes(g));
    res.items = [...first, ...res.items.slice(0, 4), ...later, ...res.items.slice(4)].slice(0, opts.limit);
  }
  res.glyphs = gl.length;
  return res;
}

function searchIcons(opts, f, p) {
  let candidates;
  if (p) {
    if (!p.groups.length || p.groups.some((g) => !g.size)) return { total: 0, sets: 0, items: [], counts: null, all: 0, rel: p.rel };
    const sets = p.groups.map(rowsForTokens).sort((a, b) => a.size - b.size);
    candidates = [...sets[0]].filter((id) => sets.every((s) => s.has(id)));
  } else {
    candidates = rows.map((_, i) => i);
  }
  const scored = [];
  const counts = new Array(meta.categories.length).fill(0);  // per category, before the category filter
  let all = 0;
  for (const id of candidates) {
    const r = rows[id];
    const set = meta.setsInfo[r.s];
    if (f.commercial && set.t > 1) continue;
    // filters always win: an icon shows only when it matches every one of them
    if (f.shape !== null && r.sh !== f.shape) continue;
    if (f.color !== null && r.co !== f.color) continue;
    if (f.density !== null && r.d !== f.density) continue;
    if (f.corners !== null && r.c !== f.corners) continue;
    if (f.weight !== null && (r.w < 0 || Math.abs(r.w / 10 - f.weight) > 0.3)) continue;
    all++;
    counts[r.k]++;
    if (r.k2 >= 0) counts[r.k2]++;
    if (f.cat !== null && r.k !== f.cat && r.k2 !== f.cat) continue;
    let score = r.pr / 10;
    if (p) {
      const parts = r.concept.split("-");
      const ctoks = new Set(parts);
      if (p.enTarget && r.concept === p.enTarget) score += 8;
      else if (p.enTarget && r.concept.startsWith(p.enTarget)) score += 2;
      else {
        const lv = p.parts.map((pt) => level(ctoks, r.concept, pt));
        const lo = Math.min(...lv);
        const allStrong = parts.every((t) => p.parts.some((pt) => pt.strong.has(t)));
        const top = p.isAr ? 8 : 6;  // an English synonym ranks just below the word itself
        if (lo === 3 || (p.parts.length > 1 && lo >= 2 && allStrong)) score += top;
        else if (lo >= 2) score += top - 3;
        else if (lo >= 1) score += 1.5;
      }
      score -= 0.15 * (parts.length - 1);
    }
    scored.push([score, id]);
  }
  scored.sort((a, b) => b[0] - a[0]);
  const setCount = new Set(scored.map(([, id]) => rows[id].s)).size;
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
    total: scored.length, sets: setCount, counts, all, rel: p ? p.rel : [],
    items: items.map((id) => {
      const r = rows[id];
      return { p: meta.setsInfo[r.s].p, n: r.n, sh: r.sh, co: r.co, d: r.d, w: r.w, c: r.c, k: r.k, k2: r.k2, concept: r.concept };
    }),
  };
}

// the same concept drawn by other libraries, best-known libraries first
function alternatives(prefix, concept, commercial) {
  const seen = new Set([prefix]), out = [];
  const ids = (vocab.get(concept.split("-")[0]) || []).filter((id) => rows[id].concept === concept);
  ids.sort((a, b) => rows[b].pr - rows[a].pr);
  for (const id of ids) {
    const r = rows[id], set = meta.setsInfo[r.s];
    if (seen.has(set.p) || (commercial && set.t > 1)) continue;
    seen.add(set.p);
    out.push({ p: set.p, n: r.n, sh: r.sh, co: r.co, d: r.d, w: r.w, c: r.c, k: r.k, k2: r.k2, concept: r.concept });
    if (out.length >= 12) break;
  }
  return out;
}

onmessage = async (e) => {
  const m = e.data;
  if (m.type === "load") {
    try { await load(m.base, m.v); } catch (err) { postMessage({ type: "error", message: String(err) }); }
  } else if (m.type === "search") {
    postMessage({ type: "results", seq: m.seq, ...search(m) });
  } else if (m.type === "alts") {
    postMessage({ type: "alts", seq: m.seq, items: alternatives(m.p, m.concept, m.commercial) });
  }
};
