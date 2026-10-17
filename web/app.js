// Agent Glyphs page. The hero shows what an agent does with the skill, using
// real search results from the index; below, people can browse the same index.
// Icons come from the public Iconify API (or, for libraries outside Iconify,
// from data/ext/) as they scroll into view; nothing else is downloaded.
import { ui } from "./ui-icons.js";

const API = "https://api.iconify.design";
const REPO = "molamine08/agent-glyphs";
const PAGE = 72;
const $ = (id) => document.getElementById(id);

const T = {
  ar: {
    lang: "English", navInstall: "التثبيت", navBrowse: "تصفّح الأيقونات",
    title: "أيقونات يفهمها وكيلك",
    lede: (n, s) => `<b>${n}</b> أيقونة مفتوحة المصدر من <b>${s}</b> مكتبة، كل واحدة مقيسة من رسمها ومصنّفة بالمعنى وسُمك الخط والزوايا والرخصة. يبحث وكيلك فيها بالعربية أو بالإنجليزية، ويختار ما يشبه أيقوناتك، ويضيفها لمشروعك.`,
    install: ["npx", "Claude Code", "تطبيق Claude"],
    installNote: [
      "يعمل مع Claude Code وCursor وCodex وغيرها من الوكلاء التي تدعم المهارات.",
      "ينسخ المهارة في مجلد المهارات، ويقرأ وكيلك ملف SKILL.md تلقائياً.",
      'نزّل <a href="https://github.com/molamine08/agent-glyphs/archive/refs/heads/main.zip">الملف المضغوط</a>، ثم ارفعه من الإعدادات ← القدرات ← المهارات.',
    ],
    copy: "انسخ", copied: "نُسخ", downloaded: "نُزّل الملف",
    sessionTitle: "Claude Code · متجري",
    sUser: "أضف أيقونة محفظة لزر الدفع. لازم تشبه أيقوناتي: خط 1.5 وزوايا دائرية.",
    sSearch: "أبحث في Agent Glyphs بالمعنى وبالشكل.",
    sFound: (n, s) => `${n} نتيجة من ${s} مكتبة بنفس السُّمك والزوايا. أختار الأولى.`,
    sGet: "أضيفها كمكوّن React وأسجّل رخصتها.",
    sDone: (f, l) => `أضفت ${f} · الرخصة ${l} مسجّلة في ATTRIBUTION.md`,
    browseTitle: "ابحث كما يبحث وكيلك",
    searchLabel: "ابحث عن أيقونة", placeholder: "محفظة، سلة تسوق، wallet…",
    weight: "سُمك الخط", commercial: "للاستخدام التجاري", more: "اعرض المزيد",
    any: "الكل", allCats: "كل التصنيفات",
    styles: { outline: "خطي", filled: "مصمت", duotone: "ثنائي", multicolor: "ملوّن" },
    cornersL: { rounded: "دائرية", mixed: "مختلطة", sharp: "حادة" },
    stylesFull: { outline: "خطي", filled: "مصمت", duotone: "ثنائي اللون", multicolor: "ملوّن", mixed: "مختلط", unknown: "غير محدد" },
    loading: "يحمّل الفهرس…", loadErr: "تعذّر تحميل الفهرس. حدّث الصفحة بعد قليل.",
    count: (n) => `${n} نتيجة`, none: "لا نتائج. جرّب كلمة مرادفة أو خفّف الفلاتر.",
    browse: (n) => `${n} أيقونة`,
    tabDesign: "للتصميم", tabAgent: "لوكيلك",
    color: "اللون", size: "الحجم", stroke: "السُّمك", mirror: "عكس للواجهات العربية",
    copySvg: "انسخ SVG", copyJsx: "React", download: "نزّل الملف",
    askAgent: "اطلبها من وكيلك", command: "الأمر الذي سينفّذه", metadata: "بيانات الأيقونة",
    prompt: (id, set, lic, opts) => `استخدم مهارة Agent Glyphs وأضف الأيقونة \u2066${id}\u2069 من \u2068${set}\u2069 (رخصة \u2066${lic}\u2069)${opts}.`,
    optStroke: (w) => ` بسُمك خط ${w}`, optSize: (s) => ` بحجم ${s}px`, optMirror: " معكوسة للواجهة العربية", optColor: (c) => ` باللون ${c}`,
    report: "التصنيف غير دقيق؟ أخبرنا", alts: "نفس الأيقونة في مكتبات أخرى",
    fStyle: "النمط", fWeight: "سُمك الخط", fCorners: "الزوايا", fCat: "التصنيف", fGrid: "الشبكة",
    lic: (l) => `الرخصة: ${l}.`, credit: "يجب ذكر صاحبها عند الاستخدام.",
    noncom: "لا تسمح بالاستخدام التجاري.", share: "تفرض مشاركة التعديلات بنفس الرخصة.",
    by: (a) => `من ${a}`, terms: (t) => `يُعثر عليها أيضاً بـ: ${t}`,
    foot: (v) => `الكود برخصة MIT. كل أيقونة تبقى برخصة مكتبتها، وتأتي من Iconify أو من مستودع مكتبتها. يتحدّث الفهرس يومياً (Iconify ${v}).`,
  },
  en: {
    lang: "العربية", navInstall: "Install", navBrowse: "Browse icons",
    title: "Icons your agent understands",
    lede: (n, s) => `<b>${n}</b> open-source icons from <b>${s}</b> libraries, each measured from its drawing and labelled by meaning, stroke weight, corners and licence. Your agent searches them in English or Arabic, picks the ones that match your icons, and adds them to your project.`,
    install: ["npx", "Claude Code", "Claude app"],
    installNote: [
      "Works with Claude Code, Cursor, Codex and other agents that support skills.",
      "Copies the skill into your skills folder; your agent reads SKILL.md on its own.",
      'Download the <a href="https://github.com/molamine08/agent-glyphs/archive/refs/heads/main.zip">zip</a>, then upload it in Settings → Capabilities → Skills.',
    ],
    copy: "Copy", copied: "Copied", downloaded: "Downloaded",
    sessionTitle: "Claude Code · my-shop",
    sUser: "Add a wallet icon to the checkout button. It has to match my other icons: 1.5 stroke, rounded corners.",
    sSearch: "Searching Agent Glyphs by meaning and by shape.",
    sFound: (n, s) => `${n} matches from ${s} libraries with the same weight and corners. Taking the first.`,
    sGet: "Adding it as a React component and recording its licence.",
    sDone: (f, l) => `Added ${f} · ${l} licence recorded in ATTRIBUTION.md`,
    browseTitle: "Search the way your agent does",
    searchLabel: "Search icons", placeholder: "wallet, shopping cart, محفظة…",
    weight: "Stroke weight", commercial: "Commercial use", more: "Show more",
    any: "Any", allCats: "All categories",
    styles: { outline: "Outline", filled: "Filled", duotone: "Duotone", multicolor: "Colour" },
    cornersL: { rounded: "Rounded", mixed: "Mixed", sharp: "Sharp" },
    stylesFull: { outline: "Outline", filled: "Filled", duotone: "Duotone", multicolor: "Colour", mixed: "Mixed", unknown: "Unknown" },
    loading: "Loading the index…", loadErr: "The index could not load. Refresh in a moment.",
    count: (n) => `${n} results`, none: "No results. Try a synonym or loosen the filters.",
    browse: (n) => `${n} icons`,
    tabDesign: "Design", tabAgent: "For your agent",
    color: "Colour", size: "Size", stroke: "Stroke", mirror: "Mirror for right-to-left",
    copySvg: "Copy SVG", copyJsx: "React", download: "Download",
    askAgent: "Ask your agent", command: "What it will run", metadata: "Icon metadata",
    prompt: (id, set, lic, opts) => `Use the Agent Glyphs skill to add the icon ${id} from ${set} (${lic} licence)${opts}.`,
    optStroke: (w) => `, stroke ${w}`, optSize: (s) => `, ${s}px`, optMirror: ", mirrored for right-to-left", optColor: (c) => `, colour ${c}`,
    report: "Wrong label? Tell us", alts: "The same icon in other libraries",
    fStyle: "Style", fWeight: "Stroke weight", fCorners: "Corners", fCat: "Category", fGrid: "Grid",
    lic: (l) => `Licence: ${l}.`, credit: "Credit the author when you use it.",
    noncom: "Not for commercial use.", share: "Changes must be shared under the same licence.",
    by: (a) => `by ${a}`, terms: (t) => `Also found as: ${t}`,
    foot: (v) => `Code under MIT. Every icon keeps its library's licence and comes from Iconify or the library's own repository. The index updates daily (Iconify ${v}).`,
  },
};
const INSTALL = [
  "npx skills add molamine08/agent-glyphs",
  "git clone https://github.com/molamine08/agent-glyphs ~/.claude/skills/agent-glyphs",
  "https://github.com/molamine08/agent-glyphs/archive/refs/heads/main.zip",
];
const SWATCHES = [null, "#0D70FF", "#16A34A", "#E11D48", "#F59E0B", "#7C3AED"];
const SIZES = [16, 20, 24, 32, 48];

let lang = (() => { try { return localStorage.getItem("lang") || "ar"; } catch { return "ar"; } })();
let meta = null, terms = {}, seq = 0, limit = PAGE, current = null, lastRes = null, installTab = 0, tab = "design";
const state = { style: null, corners: null, cat: null, weight: null, commercial: true };
const view = { color: null, size: 24, stroke: null, mirror: false };
const cache = new Map();          // "prefix:name" -> icon data
const extSets = new Map();        // prefix -> promise of set JSON (libraries outside Iconify)
const worker = new Worker("worker.js");
const t = () => T[lang];
const fmt = (n) => n.toLocaleString("en-US");
const setOf = (p) => meta.setsInfo.find((s) => s.p === p);
const desktop = () => matchMedia("(min-width: 1181px)").matches;
const pending = new Map();        // worker request seq -> resolve
let rseq = 1e6;
const ask = (msg) => new Promise((res) => { const s = ++rseq; pending.set(s, res); worker.postMessage({ ...msg, seq: s }); });

// ---------------------------------------------------------------- icons
function store(prefix, n, data) {
  let ic = data.icons?.[n], tr = {};
  if (!ic && data.aliases?.[n]) { tr = data.aliases[n]; ic = data.icons?.[tr.parent]; }
  if (!ic) return;
  const m = { ...ic, ...tr };
  cache.set(`${prefix}:${n}`, {
    body: m.body, left: m.left ?? data.left ?? 0, top: m.top ?? data.top ?? 0,
    width: m.width ?? data.width ?? 16, height: m.height ?? data.height ?? 16,
    hFlip: !!m.hFlip, vFlip: !!m.vFlip, rotate: m.rotate || 0,
  });
}

async function fetchIcons(prefix, names) {
  const need = names.filter((n) => !cache.has(`${prefix}:${n}`));
  if (!need.length) return;
  if (prefix.startsWith("x-")) {
    if (!extSets.has(prefix)) extSets.set(prefix, fetch(`data/ext/${prefix}.json`).then((r) => r.json()).catch(() => ({})));
    const data = await extSets.get(prefix);
    need.forEach((n) => store(prefix, n, data));
    return;
  }
  for (let i = 0; i < need.length; i += 40) {
    const chunk = need.slice(i, i + 40);
    try {
      const data = await fetch(`${API}/${prefix}.json?icons=${chunk.join(",")}`).then((r) => r.json());
      chunk.forEach((n) => store(prefix, n, data));
    } catch { /* offline or blocked: cells keep their placeholder */ }
  }
}

function toSvg(ic, { size = null, color = null, stroke = null, mirror = false } = {}) {
  let body = ic.body;
  if (stroke !== null && body.includes("stroke-width")) {
    const native = (stroke * ic.height) / 24;
    body = body.replace(/stroke-width="[0-9.]+"/g, `stroke-width="${+native.toFixed(3)}"`);
  }
  const tf = [];
  if (ic.hFlip !== mirror) tf.push(`translate(${2 * ic.left + ic.width} 0) scale(-1 1)`);
  if (ic.vFlip) tf.push(`translate(0 ${2 * ic.top + ic.height}) scale(1 -1)`);
  if (ic.rotate) tf.push(`rotate(${90 * ic.rotate} ${ic.left + ic.width / 2} ${ic.top + ic.height / 2})`);
  if (tf.length) body = `<g transform="${tf.join(" ")}">${body}</g>`;
  const dims = size ? ` width="${Math.round((size * ic.width) / ic.height * 1000) / 1000}" height="${size}"` : "";
  const style = color ? ` style="color:${color}"` : "";
  return `<svg xmlns="http://www.w3.org/2000/svg"${dims} viewBox="${ic.left} ${ic.top} ${ic.width} ${ic.height}"${style}>${body}</svg>`;
}

const compName = (name) => {
  const c = name.split(/[^a-zA-Z0-9]+/).filter(Boolean).map((s) => s[0].toUpperCase() + s.slice(1)).join("");
  return /^[A-Za-z]/.test(c) ? c + "Icon" : "Icon" + c;
};
function toJsx(svg, name) {
  const inner = svg.replace(/\s(width|height)="[^"]*"/g, "")
    .replace(/([a-z]+)-([a-z])([a-z-]*)=/g, (_, a, b, c) => a + b.toUpperCase() + c.replace(/-([a-z])/g, (m, x) => x.toUpperCase()) + "=")
    .replace(/style="color:([^"]*)"/, 'style={{ color: "$1" }}')
    .replace("<svg ", "<svg width={size} height={size} {...props} ");
  return `export default function ${compName(name)}({ size = 24, ...props }) {\n  return (\n    ${inner}\n  );\n}\n`;
}

const io = new IntersectionObserver((entries) => {
  const want = new Map();
  for (const e of entries) {
    if (!e.isIntersecting) continue;
    io.unobserve(e.target);
    const { p, n } = e.target.dataset;
    if (!want.has(p)) want.set(p, []);
    want.get(p).push(n);
  }
  for (const [p, names] of want) fetchIcons(p, names).then(() => names.forEach((n) => paint(p, n)));
}, { rootMargin: "300px" });

function paint(p, n) {
  const ic = cache.get(`${p}:${n}`);
  if (!ic) return;
  document.querySelectorAll(`[data-p="${p}"][data-n="${CSS.escape(n)}"] .ic`).forEach((el) => { el.innerHTML = toSvg(ic); });
}

// ---------------------------------------------------------------- hero: install + agent session
function renderInstall() {
  const L = t();
  const seg = $("installSeg");
  seg.innerHTML = "";
  L.install.forEach((label, i) => {
    const b = document.createElement("button");
    b.type = "button";
    b.setAttribute("role", "tab");
    b.setAttribute("aria-checked", String(i === installTab));
    b.textContent = label;
    b.addEventListener("click", () => { installTab = i; renderInstall(); });
    seg.append(b);
  });
  const cmd = INSTALL[installTab];
  $("installCmd").innerHTML = `<span class="prompt-sign">${installTab === 2 ? "↓" : "$"}</span>`;
  $("installCmd").append(document.createTextNode(cmd));
  $("installCopy").innerHTML = `${ui("copy")}<span>${L.copy}</span>`;
  $("installNote").innerHTML = L.installNote[installTab];
}
$("installCopy").addEventListener("click", () => copy(INSTALL[installTab]));

let sessionRun = 0;
async function playSession() {
  const run = ++sessionRun;
  const L = t();
  const ol = $("turns");
  ol.innerHTML = "";
  $("sessionTitle").textContent = L.sessionTitle;
  const reduce = matchMedia("(prefers-reduced-motion: reduce)").matches;
  const wait = (ms) => new Promise((r) => setTimeout(r, reduce ? 0 : ms));
  const add = (who, html) => {
    if (run !== sessionRun) return null;
    const li = document.createElement("li");
    li.className = `turn ${who}`;
    li.innerHTML = `<span class="who">${ui(who === "user" ? "user" : "sparkle")}</span><div class="body">${html}</div>`;
    ol.append(li);
    requestAnimationFrame(() => requestAnimationFrame(() => li.classList.add("in")));
    return li;
  };
  // the agent searches in the person's language; show one icon per library, best-known first
  const query = lang === "ar" ? "محفظة" : "wallet";
  const filters = { style: 0, corners: 0, weight: 1.5, cat: null, commercial: true };
  const res = await ask({ type: "search", query, filters, limit: 60 });
  const known = ["tabler", "lucide", "ph", "hugeicons", "iconoir", "solar", "mynaui", "mingcute", "ri"];
  const rank = (it) => (known.includes(it.p) ? known.indexOf(it.p) : 99);
  const seen = new Set();
  const items = res.items.filter((it) => !seen.has(it.p) && seen.add(it.p))
    .sort((a, b) => rank(a) - rank(b)).slice(0, 6);
  await Promise.all([...new Set(items.map((i) => i.p))].map((p) => fetchIcons(p, items.filter((i) => i.p === p).map((i) => i.n))));
  const first = items[0];
  const esc = (s) => s.replace(/&/g, "&amp;").replace(/</g, "&lt;");

  add("user", esc(L.sUser));
  await wait(900);
  add("agent", `${esc(L.sSearch)}<code class="tool"><span class="k">search.py</span> "${query}" --style outline --weight 1.5 --corners rounded</code>`);
  await wait(1100);
  if (!first) return;
  const picks = items.map((it, i) => {
    const ic = cache.get(`${it.p}:${it.n}`);
    return `<span class="pick${i === 0 ? " chosen" : ""}" title="${it.p}:${it.n}">${ic ? toSvg(ic) : ""}</span>`;
  }).join("");
  const set = setOf(first.p);
  add("agent", `${esc(L.sFound(fmt(res.total), fmt(res.sets)))}<div class="picks">${picks}</div>`
    + `<div class="pick-meta">${first.p}:${first.n} · outline · ${(first.w / 10).toFixed(1)} · rounded · ${esc(set.l || "")}</div>`);
  await wait(1300);
  const file = `src/icons/${compName(first.n)}.tsx`;
  add("agent", `${esc(L.sGet)}<code class="tool"><span class="k">get.py</span> ${first.p}:${first.n} --format tsx --out src/icons</code>`);
  await wait(900);
  add("agent", `<span class="done">${ui("check")}${esc(L.sDone(file, set.l || ""))}</span>`);
}

// ---------------------------------------------------------------- browse: filters
function seg(el, options, key, onPick) {
  el.innerHTML = "";
  for (const [val, label] of options) {
    const b = document.createElement("button");
    b.type = "button";
    b.setAttribute("role", "radio");
    b.textContent = label;
    b.setAttribute("aria-checked", String(state[key] === val));
    b.addEventListener("click", () => {
      state[key] = val;
      el.querySelectorAll("button").forEach((c) => c.setAttribute("aria-checked", "false"));
      b.setAttribute("aria-checked", "true");
      (onPick || newSearch)();
    });
    el.append(b);
  }
}

function setupFilters() {
  const L = t();
  seg($("styleSeg"), [[null, L.any], ...["outline", "filled", "duotone", "multicolor"].map((s) => [meta.styles.indexOf(s), L.styles[s]])], "style");
  seg($("cornerSeg"), [[null, L.any], ...["rounded", "mixed", "sharp"].map((c) => [meta.corners.indexOf(c), L.cornersL[c]])], "corners");
  renderCats();
}

function renderCats(counts = null, all = null) {
  const L = t();
  const ul = $("cats");
  ul.innerHTML = "";
  const rows = [[null, "all", L.allCats, all], ...meta.categories.map(([k, en, ar], i) => [i, k, lang === "ar" ? ar : en, counts ? counts[i] : null])];
  for (const [i, k, label, n] of rows) {
    if (counts && i !== null && !n && state.cat !== i) continue;
    const li = document.createElement("li");
    const b = document.createElement("button");
    b.type = "button";
    b.className = "cat";
    b.setAttribute("aria-pressed", String(state.cat === i));
    b.innerHTML = `${ui("c_" + k)}<span class="name"></span><span class="n">${n === null || n === undefined ? "" : fmt(n)}</span>`;
    b.querySelector(".name").textContent = label;
    b.addEventListener("click", () => { state.cat = i; newSearch(); });
    li.append(b);
    ul.append(li);
  }
}

function setWeightUI() {
  const on = $("weightOn").checked;
  const v = parseFloat($("weight").value);
  $("weight").disabled = !on;
  $("weightOut").textContent = on ? v.toFixed(2) : "";
  $("weightBox").classList.toggle("off", !on);
  // the headline is drawn at the chosen stroke weight
  document.documentElement.style.setProperty("--title-weight", on ? String(Math.round((400 + ((v - 0.5) / 2.5) * 500) / 100) * 100) : "");
  state.weight = on ? v : null;
}

// ---------------------------------------------------------------- browse: results
function newSearch() { limit = PAGE; run(); }
function run() {
  if (!meta) return;
  worker.postMessage({ type: "search", seq: ++seq, query: $("q").value, filters: state, limit });
}

function render(res) {
  lastRes = res;
  const grid = $("grid");
  grid.innerHTML = "";
  const L = t();
  const q = $("q").value.trim();
  $("status").textContent = res.total === 0 ? "" : (q ? L.count(fmt(res.total)) : L.browse(fmt(res.total)));
  renderCats(res.counts, res.all);
  if (!res.items.length) {
    const li = document.createElement("li");
    li.className = "empty";
    li.textContent = L.none;
    grid.append(li);
    $("more").hidden = true;
    return;
  }
  for (const it of res.items) {
    const li = document.createElement("li");
    const b = document.createElement("button");
    b.className = "tile";
    b.type = "button";
    b.dataset.p = it.p;
    b.dataset.n = it.n;
    b.title = `${it.p}:${it.n}`;
    if (current && current.p === it.p && current.n === it.n) b.setAttribute("aria-current", "true");
    const ic = cache.get(`${it.p}:${it.n}`);
    b.innerHTML = `<span class="ic">${ic ? toSvg(ic) : '<span class="ph"></span>'}</span><span class="nm"></span>`;
    b.querySelector(".nm").textContent = it.n;
    b.addEventListener("click", () => open(it, true));
    li.append(b);
    grid.append(li);
    if (!ic) io.observe(b);
  }
  $("more").hidden = res.items.length >= res.total || res.items.length < limit;
  if (desktop() && (!current || !res.items.some((i) => i.p === current.p && i.n === current.n)) && !current?.pinned) open(res.items[0], false);
}

worker.onmessage = (e) => {
  const m = e.data;
  if (m.type === "ready") {
    meta = m.meta;
    terms = m.terms;
    setupFilters();
    applyLang();
  } else if (m.type === "results" && pending.has(m.seq)) {
    pending.get(m.seq)(m); pending.delete(m.seq);
  } else if (m.type === "results" && m.seq === seq) {
    render(m);
  } else if (m.type === "alts" && pending.has(m.seq)) {
    pending.get(m.seq)(m); pending.delete(m.seq);
  } else if (m.type === "error") {
    $("status").textContent = t().loadErr;
  }
};

let debounce;
$("q").addEventListener("input", () => { clearTimeout(debounce); debounce = setTimeout(newSearch, 120); });
$("weightOn").addEventListener("change", () => { setWeightUI(); newSearch(); });
$("weight").addEventListener("input", () => { setWeightUI(); clearTimeout(debounce); debounce = setTimeout(newSearch, 150); });
$("commercial").addEventListener("change", (e) => { state.commercial = e.target.checked; newSearch(); });
$("more").addEventListener("click", () => { limit += PAGE * 2; run(); });
document.addEventListener("keydown", (e) => {
  if (e.key === "/" && document.activeElement !== $("q") && !/INPUT|TEXTAREA/.test(document.activeElement.tagName)) {
    e.preventDefault();
    $("q").focus();
    $("browse").scrollIntoView({ behavior: "smooth", block: "start" });
  }
  if (e.key === "Escape") close();
});

// ---------------------------------------------------------------- inspector
function viewSvg(sized = false) {
  const ic = current && cache.get(`${current.p}:${current.n}`);
  if (!ic) return "";
  const svg = toSvg(ic, { color: view.color, stroke: view.stroke, mirror: view.mirror });
  return sized ? svg.replace("<svg ", `<svg width="${view.size}" height="${view.size}" `) : svg;
}

function refreshPreview() {
  const svg = viewSvg();
  $("dIcon").innerHTML = svg ? svg.replace("<svg ", '<svg width="100%" height="100%" ') : "";
  $("dStrokeOut").textContent = view.stroke !== null ? view.stroke.toFixed(2) : (current && current.w >= 0 ? (current.w / 10).toFixed(1) : "");
  refreshAgent();
}

function refreshAgent() {
  if (!current) return;
  const L = t();
  const set = setOf(current.p);
  const id = `${current.p}:${current.n}`;
  const opts = (view.stroke !== null ? L.optStroke(view.stroke) : "") + (view.size !== 24 ? L.optSize(view.size) : "")
    + (view.color ? L.optColor(view.color) : "") + (view.mirror ? L.optMirror : "");
  $("agentPrompt").textContent = L.prompt(id, set.n, set.l || "?", opts);
  const flags = [`--format tsx`, `--out src/icons`];
  if (view.stroke !== null) flags.push(`--stroke ${view.stroke}`);
  if (view.size !== 24) flags.push(`--size ${view.size}`);
  if (view.color) flags.push(`--color "${view.color}"`);
  if (view.mirror) flags.push("--mirror");
  $("agentCmd").textContent = `python scripts/get.py ${id} \\\n  ${flags.join(" ")}`;
  const cat = (k) => (k >= 0 ? meta.categories[k][0] : null);
  $("agentJson").textContent = JSON.stringify({
    id, set: set.n, style: meta.styles[current.st], weight: current.w >= 0 ? current.w / 10 : null,
    corners: current.c >= 0 ? meta.corners[current.c] : null, category: [cat(current.k), cat(current.k2)].filter(Boolean),
    license: set.l, license_tier: meta.tiers[set.t], grid: set.g || null,
  }, null, 2);
}

function renderTabs() {
  const L = t();
  const el = $("tabSeg");
  el.innerHTML = "";
  for (const [key, label, icon] of [["design", L.tabDesign, "palette"], ["agent", L.tabAgent, "robot"]]) {
    const b = document.createElement("button");
    b.type = "button";
    b.setAttribute("role", "tab");
    b.setAttribute("aria-checked", String(tab === key));
    b.innerHTML = `${ui(icon)}<span></span>`;
    b.querySelector("span").textContent = label;
    b.addEventListener("click", () => { tab = key; renderTabs(); });
    el.append(b);
  }
  $("paneDesign").hidden = tab !== "design";
  $("paneAgent").hidden = tab !== "agent";
}

function renderControls() {
  const L = t();
  const sw = $("swatches");
  sw.innerHTML = "";
  for (const c of SWATCHES) {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "swatch";
    b.style.setProperty("--sw", c || "var(--ink)");
    b.setAttribute("aria-label", c || "currentColor");
    b.setAttribute("aria-pressed", String(view.color === c));
    b.addEventListener("click", () => { view.color = c; renderControls(); refreshPreview(); });
    sw.append(b);
  }
  const custom = document.createElement("label");
  custom.className = "swatch custom";
  custom.innerHTML = '+<input type="color" aria-label="Custom colour">';
  custom.querySelector("input").addEventListener("input", (e) => { view.color = e.target.value; refreshPreview(); });
  sw.append(custom);
  const ss = $("sizeSeg");
  ss.innerHTML = "";
  for (const s of SIZES) {
    const b = document.createElement("button");
    b.type = "button";
    b.textContent = s;
    b.setAttribute("aria-checked", String(view.size === s));
    b.addEventListener("click", () => { view.size = s; renderControls(); refreshAgent(); });
    ss.append(b);
  }
  $("copySvg").innerHTML = `${ui("copy")}<span>${L.copySvg}</span>`;
  $("copyJsx").innerHTML = `${ui("react")}<span>${L.copyJsx}</span>`;
  $("download").innerHTML = ui("download");
  $("download").setAttribute("aria-label", L.download);
  document.querySelectorAll("[data-copy]").forEach((b) => { b.innerHTML = `${ui("copy")}<span>${L.copy}</span>`; });
}

async function open(it, user) {
  current = { ...it, pinned: user };
  const L = t();
  const set = setOf(it.p);
  view.stroke = null; view.mirror = false;
  $("dMirror").checked = false;
  document.querySelectorAll(".tile[aria-current]").forEach((b) => b.removeAttribute("aria-current"));
  document.querySelector(`.tile[data-p="${it.p}"][data-n="${CSS.escape(it.n)}"]`)?.setAttribute("aria-current", "true");
  await fetchIcons(it.p, [it.n]);
  if (current.p !== it.p || current.n !== it.n) return;
  const ic = cache.get(`${it.p}:${it.n}`);
  $("dName").textContent = it.n;
  $("dSet").textContent = `${set.n}${lang === "ar" ? "، " : ", "}${L.by(set.a || "")}`;
  const facts = [
    [L.fStyle, L.stylesFull[meta.styles[it.st]] || "—"],
    [L.fWeight, it.w >= 0 ? (it.w / 10).toFixed(1) : "—"],
    [L.fCorners, it.c >= 0 ? L.cornersL[meta.corners[it.c]] : "—"],
    [L.fCat, [it.k, it.k2].filter((k) => k >= 0).map((k) => (lang === "ar" ? meta.categories[k][2] : meta.categories[k][1])).join(lang === "ar" ? "، " : ", ")],
    [L.fGrid, set.g ? `${set.g}px` : "—"],
  ];
  $("dFacts").innerHTML = "";
  for (const [k, v] of facts) {
    const dt = document.createElement("dt"); dt.textContent = k;
    const dd = document.createElement("dd"); dd.textContent = v;
    $("dFacts").append(dt, dd);
  }
  const tier = meta.tiers[set.t];
  const extra = tier === "attribution" ? L.credit : tier === "non-commercial" ? L.noncom : tier === "share-alike" ? L.share : "";
  $("dLicense").innerHTML = "";
  $("dLicense").append(document.createTextNode(L.lic(set.l || "?") + " "));
  if (extra) { const s = document.createElement("strong"); s.textContent = extra; $("dLicense").append(s); }
  const words = it.n.split(/[-_]/).flatMap((w) => terms[w] || []);
  $("dTerms").textContent = words.length ? L.terms([...new Set(words)].slice(0, 6).join(lang === "ar" ? "، " : ", ")) : "";
  const strokeIcon = !!ic && ic.body.includes("stroke-width");
  $("strokeWrap").hidden = !strokeIcon;
  if (strokeIcon) $("dStroke").value = it.w >= 0 ? (Math.round(it.w / 2.5) / 4).toFixed(2) : "2";
  const issue = new URLSearchParams({
    title: `Label: ${it.p}:${it.n}`,
    body: `Icon: ${it.p}:${it.n}\nCurrent: style=${meta.styles[it.st]}, corners=${it.c >= 0 ? meta.corners[it.c] : "-"}, category=${meta.categories[it.k][0]}\n\nWhat it should be:\n`,
  });
  $("report").href = `https://github.com/${REPO}/issues/new?${issue}`;
  renderControls();
  refreshPreview();
  loadAlts(it);
  if (desktop()) {
    $("inspector").setAttribute("aria-hidden", "false");
  } else if (user) {
    $("inspector").setAttribute("aria-hidden", "false");
    $("scrim").hidden = false;
    $("close").focus({ preventScroll: true });
  }
}

async function loadAlts(it) {
  const ul = $("alts");
  ul.innerHTML = "";
  const res = await ask({ type: "alts", p: it.p, concept: it.concept, commercial: state.commercial });
  if (!current || current.n !== it.n || current.p !== it.p) return;
  ul.parentElement.hidden = !res.items.length;
  for (const a of res.items) {
    const li = document.createElement("li");
    const b = document.createElement("button");
    b.type = "button";
    b.className = "alt";
    b.dataset.p = a.p;
    b.dataset.n = a.n;
    b.title = `${a.p}:${a.n}`;
    b.innerHTML = '<span class="ic"></span>';
    b.addEventListener("click", () => open(a, true));
    li.append(b);
    ul.append(li);
  }
  for (const p of new Set(res.items.map((a) => a.p))) {
    const names = res.items.filter((a) => a.p === p).map((a) => a.n);
    fetchIcons(p, names).then(() => names.forEach((n) => paint(p, n)));
  }
}

function close() {
  if (desktop()) return;
  $("inspector").setAttribute("aria-hidden", "true");
  $("scrim").hidden = true;
}
$("close").addEventListener("click", close);
$("scrim").addEventListener("click", close);
$("dStroke").addEventListener("input", (e) => { view.stroke = parseFloat(e.target.value); refreshPreview(); });
$("dMirror").addEventListener("change", (e) => { view.mirror = e.target.checked; refreshPreview(); });

function toast(msg) {
  const el = $("toast");
  el.textContent = msg;
  el.classList.add("show");
  clearTimeout(toast.t);
  toast.t = setTimeout(() => el.classList.remove("show"), 1600);
}
async function copy(text) {
  try { await navigator.clipboard.writeText(text); }
  catch {
    const ta = document.createElement("textarea"); ta.value = text; document.body.append(ta); ta.select();
    document.execCommand("copy"); ta.remove();
  }
  toast(t().copied);
}
$("copySvg").addEventListener("click", () => current && copy(viewSvg(true)));
$("copyJsx").addEventListener("click", () => current && copy(toJsx(viewSvg(), current.n)));
$("download").addEventListener("click", () => {
  if (!current) return;
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([viewSvg(true)], { type: "image/svg+xml" }));
  a.download = `${current.p}-${current.n}.svg`;
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  toast(t().downloaded);
});
document.querySelectorAll("[data-copy]").forEach((b) => b.addEventListener("click", () => copy($(b.dataset.copy).textContent)));

// ---------------------------------------------------------------- language
function applyLang() {
  const L = t();
  document.documentElement.lang = lang;
  document.documentElement.dir = lang === "ar" ? "rtl" : "ltr";
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const v = L[el.dataset.i18n];
    if (typeof v === "string") el.textContent = v;
  });
  $("lang").innerHTML = `${ui("lang")}<span>${L.lang}</span>`;
  $("q").placeholder = L.placeholder;
  $("lede").innerHTML = meta ? L.lede(fmt(meta.icons), fmt(meta.sets)) : L.loading;
  $("footText").textContent = meta ? L.foot(meta.version) : "";
  renderInstall();
  renderTabs();
  renderControls();
  if (meta) { setupFilters(); run(); playSession(); }
  if (current) open(current, current.pinned);
}
$("lang").addEventListener("click", () => {
  lang = lang === "ar" ? "en" : "ar";
  try { localStorage.setItem("lang", lang); } catch { /* private mode */ }
  applyLang();
});

$("searchIcon").innerHTML = ui("search");
$("gh").innerHTML = ui("github");
$("close").innerHTML = ui("close");
applyLang();
setWeightUI();
$("status").textContent = t().loading;
worker.postMessage({ type: "load", base: new URL("data/", location.href).href });
