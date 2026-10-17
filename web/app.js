// Icon Atlas page: filters, results, detail drawer. Icons are fetched from
// the public Iconify API as they appear; nothing is redistributed here.

const API = "https://api.iconify.design";
const PAGE = 60;
const $ = (id) => document.getElementById(id);

const T = {
  ar: {
    brand: "أطلس الأيقونات", source: "المصدر على GitHub", lang: "English",
    title: "ابحث عن الأيقونة بمعناها وبشكلها",
    lede: (n, s) => `${n} أيقونة مفتوحة المصدر من ${s} مكتبة، مصنّفة بالمعنى وبسُمك الخط والزوايا. اكتب بالعربية أو بالإنجليزية.`,
    searchLabel: "ابحث عن أيقونة", placeholder: "محفظة، سلة تسوق، wallet…",
    style: "النمط", weight: "سُمك الخط", weightOn: "حدّد السُّمك", corners: "الزوايا", category: "التصنيف",
    license: "الرخصة", commercial: "تسمح بالاستخدام التجاري", more: "اعرض المزيد",
    any: "الكل", allCats: "كل التصنيفات",
    styles: { outline: "خطي", filled: "مصمت", duotone: "ثنائي اللون", multicolor: "ملوّن", mixed: "مختلط" },
    cornersL: { rounded: "دائرية", mixed: "مختلطة", sharp: "حادة" },
    loading: "يحمّل الفهرس…", loadErr: "تعذّر تحميل الفهرس. حدّث الصفحة بعد قليل.",
    count: (n) => `${n} نتيجة`, none: "لا نتائج. جرّب كلمة مرادفة أو خفّف الفلاتر.",
    browse: (n) => `${n} أيقونة تطابق الفلاتر`,
    color: "اللون", size: "الحجم", stroke: "السُّمك", mirror: "عكس للواجهات العربية",
    copySvg: "انسخ SVG", copyJsx: "انسخ كمكوّن React", download: "نزّل الملف",
    copied: "نُسخ", downloaded: "نُزّل الملف",
    report: "التصنيف غير دقيق؟ أخبرنا",
    fStyle: "النمط", fWeight: "سُمك الخط", fCorners: "الزوايا", fCat: "التصنيف", fGrid: "الشبكة",
    lic: (l) => `الرخصة: ${l}.`, credit: "يجب ذكر صاحبها عند الاستخدام.",
    noncom: "لا تسمح بالاستخدام التجاري.", share: "تفرض مشاركة التعديلات بنفس الرخصة.",
    by: (a) => `من ${a}`, terms: (t) => `يُعثر عليها أيضاً بـ: ${t}`,
  },
  en: {
    brand: "Icon Atlas", source: "Source on GitHub", lang: "العربية",
    title: "Find an icon by what it means and how it looks",
    lede: (n, s) => `${n} open-source icons from ${s} libraries, classified by meaning, stroke weight and corners. Search in English or Arabic.`,
    searchLabel: "Search icons", placeholder: "wallet, shopping cart, محفظة…",
    style: "Style", weight: "Stroke weight", weightOn: "Set a weight", corners: "Corners", category: "Category",
    license: "Licence", commercial: "Allows commercial use", more: "Show more",
    any: "Any", allCats: "All categories",
    styles: { outline: "Outline", filled: "Filled", duotone: "Duotone", multicolor: "Colour", mixed: "Mixed" },
    cornersL: { rounded: "Rounded", mixed: "Mixed", sharp: "Sharp" },
    loading: "Loading the index…", loadErr: "The index could not load. Refresh in a moment.",
    count: (n) => `${n} results`, none: "No results. Try a synonym or loosen the filters.",
    browse: (n) => `${n} icons match the filters`,
    color: "Colour", size: "Size", stroke: "Stroke", mirror: "Mirror for right-to-left",
    copySvg: "Copy SVG", copyJsx: "Copy as React", download: "Download",
    copied: "Copied", downloaded: "Downloaded",
    report: "Wrong label? Tell us",
    fStyle: "Style", fWeight: "Stroke weight", fCorners: "Corners", fCat: "Category", fGrid: "Grid",
    lic: (l) => `Licence: ${l}.`, credit: "Credit the author when you use it.",
    noncom: "Not for commercial use.", share: "Changes must be shared under the same licence.",
    by: (a) => `by ${a}`, terms: (t) => `Also found as: ${t}`,
  },
};

let lang = (() => { try { return localStorage.getItem("lang") || "ar"; } catch { return "ar"; } })();
let meta = null, terms = {}, seq = 0, limit = PAGE, current = null;
const state = { style: null, corners: null, cat: null, weight: null, commercial: true };
const cache = new Map();        // "prefix:name" -> icon data
const worker = new Worker("worker.js");
const t = () => T[lang];
const fmt = (n) => n.toLocaleString("en-US");

// ---------------------------------------------------------------- icons
async function fetchIcons(prefix, names) {
  const need = names.filter((n) => !cache.has(`${prefix}:${n}`));
  for (let i = 0; i < need.length; i += 40) {
    const chunk = need.slice(i, i + 40);
    try {
      const data = await fetch(`${API}/${prefix}.json?icons=${chunk.join(",")}`).then((r) => r.json());
      for (const n of chunk) {
        let ic = data.icons?.[n], tr = {};
        if (!ic && data.aliases?.[n]) { tr = data.aliases[n]; ic = data.icons?.[tr.parent]; }
        if (!ic) continue;
        const merged = { ...ic, ...tr };
        cache.set(`${prefix}:${n}`, {
          body: merged.body, left: merged.left ?? data.left ?? 0, top: merged.top ?? data.top ?? 0,
          width: merged.width ?? data.width ?? 16, height: merged.height ?? data.height ?? 16,
          hFlip: !!merged.hFlip, vFlip: !!merged.vFlip, rotate: merged.rotate || 0,
        });
      }
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
  const flipH = ic.hFlip !== mirror;
  if (flipH) tf.push(`translate(${2 * ic.left + ic.width} 0) scale(-1 1)`);
  if (ic.vFlip) tf.push(`translate(0 ${2 * ic.top + ic.height}) scale(1 -1)`);
  if (ic.rotate) tf.push(`rotate(${90 * ic.rotate} ${ic.left + ic.width / 2} ${ic.top + ic.height / 2})`);
  if (tf.length) body = `<g transform="${tf.join(" ")}">${body}</g>`;
  const dims = size ? ` width="${Math.round((size * ic.width) / ic.height * 1000) / 1000}" height="${size}"` : "";
  const style = color ? ` style="color:${color}"` : "";
  return `<svg xmlns="http://www.w3.org/2000/svg"${dims} viewBox="${ic.left} ${ic.top} ${ic.width} ${ic.height}"${style}>${body}</svg>`;
}

function toJsx(svg, name) {
  const comp = name.split(/[^a-zA-Z0-9]+/).filter(Boolean).map((s) => s[0].toUpperCase() + s.slice(1)).join("");
  const id = /^[A-Za-z]/.test(comp) ? comp + "Icon" : "Icon" + comp;
  let inner = svg.replace(/\s(width|height)="[^"]*"/g, "")
    .replace(/([a-z]+)-([a-z])([a-z-]*)=/g, (_, a, b, c) => a + b.toUpperCase() + c.replace(/-([a-z])/g, (m, x) => x.toUpperCase()) + "=")
    .replace(/style="color:([^"]*)"/, 'style={{ color: "$1" }}')
    .replace("<svg ", "<svg width={size} height={size} {...props} ");
  return `export default function ${id}({ size = 24, ...props }) {\n  return (\n    ${inner}\n  );\n}\n`;
}

// ---------------------------------------------------------------- results
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
  document.querySelectorAll(`.cell[data-p="${p}"][data-n="${CSS.escape(n)}"] .ic`).forEach((el) => {
    el.innerHTML = toSvg(ic);
  });
}

function render(res) {
  const grid = $("grid");
  grid.innerHTML = "";
  const L = t();
  const q = $("q").value.trim();
  $("status").textContent = res.total === 0 ? "" : (q ? L.count(fmt(res.total)) : L.browse(fmt(res.total)));
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
    b.className = "cell";
    b.type = "button";
    b.dataset.p = it.p;
    b.dataset.n = it.n;
    b.title = `${it.p}:${it.n}`;
    const ic = cache.get(`${it.p}:${it.n}`);
    b.innerHTML = `<span class="ic">${ic ? toSvg(ic) : '<span class="ph"></span>'}</span><span class="nm"></span>`;
    b.querySelector(".nm").textContent = it.n;
    b.addEventListener("click", () => openDrawer(it));
    li.append(b);
    grid.append(li);
    if (!ic) io.observe(b);
  }
  $("more").hidden = res.items.length >= res.total || res.items.length < limit;
}

function run() {
  if (!meta) return;
  worker.postMessage({ type: "search", seq: ++seq, query: $("q").value, filters: state, limit });
}

worker.onmessage = (e) => {
  const m = e.data;
  if (m.type === "ready") {
    meta = m.meta;
    terms = m.terms;
    setupFilters();
    applyLang();
    run();
  } else if (m.type === "results" && m.seq === seq) {
    render(m);
  } else if (m.type === "error") {
    $("status").textContent = t().loadErr;
  }
};

// ---------------------------------------------------------------- filters
function chips(el, values, labels, key) {
  el.innerHTML = "";
  const all = [[null, t().any], ...values.map((v, i) => [i, labels[v]]).filter(([, l]) => l)];
  for (const [val, label] of all) {
    const b = document.createElement("button");
    b.type = "button";
    b.className = "chip";
    b.textContent = label;
    b.setAttribute("aria-pressed", String(state[key] === val));
    b.addEventListener("click", () => {
      state[key] = val;
      el.querySelectorAll(".chip").forEach((c) => c.setAttribute("aria-pressed", "false"));
      b.setAttribute("aria-pressed", "true");
      limit = PAGE;
      run();
    });
    el.append(b);
  }
}

function setupFilters() {
  chips($("styleChips"), meta.styles, t().styles, "style");
  chips($("cornerChips"), meta.corners, t().cornersL, "corners");
  const sel = $("cat");
  sel.innerHTML = "";
  const opt = (v, l) => { const o = document.createElement("option"); o.value = v; o.textContent = l; sel.append(o); };
  opt("", t().allCats);
  meta.categories.forEach(([k, en, ar], i) => { if (k !== "other") opt(String(i), lang === "ar" ? ar : en); });
  sel.value = state.cat === null ? "" : String(state.cat);
}

function setWeightUI() {
  const on = $("weightOn").checked;
  const v = parseFloat($("weight").value);
  $("weight").disabled = !on;
  $("weightOut").textContent = on ? v.toFixed(2) : "";
  document.querySelector(".filter.weight").classList.toggle("off", !on);
  $("strokeSample").style.strokeWidth = v;
  // the headline is drawn at the chosen stroke weight
  document.documentElement.style.setProperty("--title-wght", on ? Math.round(160 + ((v - 0.5) / 2.5) * 540) : 400);
  state.weight = on ? v : null;
}

let debounce;
$("q").addEventListener("input", () => { clearTimeout(debounce); debounce = setTimeout(() => { limit = PAGE; run(); }, 120); });
$("weightOn").addEventListener("change", () => { setWeightUI(); limit = PAGE; run(); });
$("weight").addEventListener("input", () => { setWeightUI(); clearTimeout(debounce); debounce = setTimeout(() => { limit = PAGE; run(); }, 150); });
$("cat").addEventListener("change", (e) => { state.cat = e.target.value === "" ? null : +e.target.value; limit = PAGE; run(); });
$("commercial").addEventListener("change", (e) => { state.commercial = e.target.checked; limit = PAGE; run(); });
$("more").addEventListener("click", () => { limit += PAGE * 2; run(); });

// ---------------------------------------------------------------- drawer
let colorTouched = false, strokeTouched = false;
function drawerSvg() {
  const ic = cache.get(`${current.p}:${current.n}`);
  if (!ic) return "";
  // untouched controls keep the icon as drawn: themeable colour, original stroke
  const stroke = $("dStrokeWrap").hidden || !strokeTouched ? null : parseFloat($("dStroke").value);
  return toSvg(ic, { color: colorTouched ? $("dColor").value : null, stroke, mirror: $("dMirror").checked });
}

function refreshDrawer() {
  const svg = drawerSvg();
  $("dIcon").innerHTML = svg ? svg.replace("<svg ", '<svg width="100%" height="100%" ') : "";
}

async function openDrawer(it) {
  current = it;
  const L = t();
  const set = meta.setsInfo.find((s) => s.p === it.p);
  await fetchIcons(it.p, [it.n]);
  const ic = cache.get(`${it.p}:${it.n}`);
  $("dName").textContent = it.n;
  $("dSet").textContent = `${set.n}${lang === "ar" ? "، " : ", "}${L.by(set.a || "")}`;
  const facts = [
    [L.fStyle, L.styles[meta.styles[it.st]] || "—"],
    [L.fWeight, it.w >= 0 ? (it.w / 10).toFixed(1) : "—"],
    [L.fCorners, it.c >= 0 ? L.cornersL[meta.corners[it.c]] : "—"],
    [L.fCat, [it.k, it.k2].filter((k) => k >= 0).map((k) => (lang === "ar" ? meta.categories[k][2] : meta.categories[k][1])).join("، ")],
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
  $("dTerms").textContent = words.length ? L.terms([...new Set(words)].slice(0, 6).join("، ")) : "";
  const strokeIcon = ic && ic.body.includes("stroke-width");
  $("dStrokeWrap").hidden = !strokeIcon;
  if (strokeIcon) $("dStroke").value = it.w >= 0 ? (Math.round(it.w / 2.5) / 4).toFixed(2) : "2";
  $("dMirror").checked = false;
  colorTouched = strokeTouched = false;
  const ink = getComputedStyle(document.documentElement).getPropertyValue("--ink").trim();
  if (/^#[0-9a-f]{6}$/i.test(ink)) $("dColor").value = ink;
  const issue = new URLSearchParams({
    title: `Label: ${it.p}:${it.n}`,
    body: `Icon: ${it.p}:${it.n}\nCurrent: style=${meta.styles[it.st]}, corners=${it.c >= 0 ? meta.corners[it.c] : "-"}, category=${meta.categories[it.k][0]}\n\nWhat it should be:\n`,
  });
  $("report").href = `https://github.com/molamine08/icone-atlas/issues/new?${issue}`;
  refreshDrawer();
  $("drawer").setAttribute("aria-hidden", "false");
  document.querySelector(".drawer .close").focus();
}

function closeDrawer() { $("drawer").setAttribute("aria-hidden", "true"); current = null; }
document.querySelectorAll("[data-close]").forEach((el) => el.addEventListener("click", closeDrawer));
document.addEventListener("keydown", (e) => { if (e.key === "Escape") closeDrawer(); });
$("dColor").addEventListener("input", () => { colorTouched = true; refreshDrawer(); });
$("dStroke").addEventListener("input", () => { strokeTouched = true; refreshDrawer(); });
$("dMirror").addEventListener("input", refreshDrawer);

// 24-unit keyline grid behind the large preview
(() => {
  const g = document.querySelector(".kgrid");
  let html = "";
  for (let i = 1; i < 24; i++) html += `<line x1="${i}" y1="0" x2="${i}" y2="24"/><line x1="0" y1="${i}" x2="24" y2="${i}"/>`;
  g.innerHTML = html;
})();

function toast(msg) {
  const el = $("toast");
  el.textContent = msg;
  el.classList.add("show");
  setTimeout(() => el.classList.remove("show"), 1600);
}
async function copy(text) {
  try { await navigator.clipboard.writeText(text); toast(t().copied); }
  catch {
    const ta = document.createElement("textarea"); ta.value = text; document.body.append(ta); ta.select();
    document.execCommand("copy"); ta.remove(); toast(t().copied);
  }
}
const sizedSvg = () => drawerSvg().replace("<svg ", `<svg width="${$("dSize").value}" height="${$("dSize").value}" `);
$("copySvg").addEventListener("click", () => current && copy(sizedSvg()));
$("copyJsx").addEventListener("click", () => current && copy(toJsx(drawerSvg(), current.n)));
$("download").addEventListener("click", () => {
  if (!current) return;
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([sizedSvg()], { type: "image/svg+xml" }));
  a.download = `${current.p}-${current.n}.svg`;
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  toast(t().downloaded);
});

// ---------------------------------------------------------------- language
function applyLang() {
  const L = t();
  document.documentElement.lang = lang;
  document.documentElement.dir = lang === "ar" ? "rtl" : "ltr";
  document.querySelectorAll("[data-i18n]").forEach((el) => {
    const v = L[el.dataset.i18n];
    if (typeof v === "string") el.textContent = v;
  });
  $("lang").textContent = L.lang;
  $("q").placeholder = L.placeholder;
  $("lede").textContent = meta ? L.lede(fmt(meta.icons), fmt(meta.sets)) : L.loading;
  if (meta) { setupFilters(); run(); }
  if (current) openDrawer(current);
}
$("lang").addEventListener("click", () => {
  lang = lang === "ar" ? "en" : "ar";
  try { localStorage.setItem("lang", lang); } catch { /* private mode */ }
  applyLang();
});

applyLang();
setWeightUI();
$("status").textContent = t().loading;
worker.postMessage({ type: "load", base: new URL("data/", location.href).href });
