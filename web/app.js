// Agent Glyphs page. The hero walks through what an agent does with the skill,
// using real results from the index; below, people browse the same index with
// filters that read as the exact command an agent would run.
// Icons come from the public Iconify API (or, for libraries outside Iconify,
// from data/ext/) as they scroll into view; nothing else is downloaded.
import { ui } from "./ui-icons.js?v=__BUILD__";

// replaced with the commit and run number when the page is published, so browsers fetch
// the new search engine and data after every update instead of a cached copy
const BUILD = "__BUILD__";

const API = "https://api.iconify.design";
const REPO = "molamine08/agent-glyphs";
const PAGE = 72;
const STEP_MS = 5600;
const $ = (id) => document.getElementById(id);
const esc = (s) => String(s).replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;").replace(/"/g, "&quot;");

const INSTALL = [
  "npx skills add molamine08/agent-glyphs",
  "git clone https://github.com/molamine08/agent-glyphs ~/.claude/skills/agent-glyphs",
  "https://github.com/molamine08/agent-glyphs/archive/refs/heads/main.zip",
];

const T = {
  ar: {
    themeLight: "الوضع الفاتح", themeDark: "الوضع الداكن",
    lang: "English", skip: "انتقل إلى البحث", navBrowse: "تصفّح", navAgents: "للوكلاء",
    title: "أيقونات يفهمها وكيلك",
    tag: (n, s) => `${n} أيقونة، ${s} مكتبة`,
    lede: "<b>كل أيقونة مفتوحة المصدر، مصنّفة بمعناها ومقيسة بشكلها.</b> يجد وكيلك الأيقونة التي تشبه أيقوناتك، بالعربية أو بالإنجليزية، ويسجّل رخصتها.",
    installCopy: "انسخ أمر التثبيت", browseCta: "تصفّح الأيقونات",
    steps: ["ثبّت المهارة", "اطلب بكلماتك", "يبحث ويضيف"],
    installTabs: ["npx", "Claude Code", "تطبيق Claude"],
    installNote: [
      "يعمل مع Claude Code وCursor وCodex وكل وكيل يدعم المهارات.",
      "ينسخ المهارة إلى مجلد المهارات، ويقرأ وكيلك ملف SKILL.md وحده.",
      'نزّل <a href="https://github.com/molamine08/agent-glyphs/archive/refs/heads/main.zip">الملف المضغوط</a> ثم ارفعه من الإعدادات، القدرات، المهارات.',
    ],
    ask: "أضف أيقونة محفظة لزر الدفع، لازم تشبه أيقوناتي: خط 1.5 وزوايا دائرية.",
    query: "محفظة",
    done: (f, l) => `أُضيفت ${f}، ورخصة ${l} مسجّلة في ATTRIBUTION.md`,
    prompts: ["ready to execute", "waiting for your request", "done"],
    next: "الخطوة التالية",
    browseLabel: "تصفّح الأيقونات", searchLabel: "ابحث عن أيقونة", placeholder: "محفظة، wallet، سلة…", hint: "ابحث عن أيقونات",
    shape: "الشكل", colors_: "الألوان", density: "الكثافة", corners: "الزوايا", stroke: "السُّمك", category: "التصنيف", licence: "الرخصة",
    any: "الكل", anyWeight: "أي سُمك", within: "ضمن ±0.3",
    strokeTitle: "سُمك الخط على شبكة 24px",
    shapes: { outline: "خطية", filled: "مملوءة", mixed: "مختلطة" },
    colors: { mono: "لون واحد", duotone: "ثنائية اللون", multicolor: "ملوّنة" },
    densities: { airy: "خفيفة", balanced: "متوازنة", heavy: "كثيفة" },
    cornersL: { rounded: "دائرية", mixed: "مختلطة", sharp: "حادة" },
    lic: { commercial: "للاستخدام التجاري", any: "كل الرخص" },
    clear: "امسح الفلاتر", copyCmd: "انسخ الأمر", more: "اعرض المزيد",

    loading: "يحمّل الفهرس…", loadErr: "تعذّر تحميل الفهرس. حدّث الصفحة بعد قليل.",
    count: (n, s) => `${n} أيقونة من ${s} مكتبة`, none: "لا نتائج. جرّب كلمة قريبة في المعنى أو خفّف الفلاتر.",
    tabs: { same: "نفس المعنى", agent: "لوكيلك", details: "التفاصيل" },
    noAlts: "لا توجد نسخة لهذه الأيقونة في مكتبات أخرى.",
    color: "اللون", size: "الحجم", mirror: "عكس للواجهات العربية",
    copySvg: "انسخ SVG", copyJsx: "React", download: "نزّل الملف", close: "أغلق",
    askAgent: "اطلبها من وكيلك", command: "الأمر الذي سينفّذه", metadata: "بيانات الأيقونة",
    prompt: (id, set, lic, opts) => `استخدم مهارة Agent Glyphs وأضف الأيقونة ⁦${id}⁩ من ⁨${set}⁩ (رخصة ⁦${lic}⁩)${opts}.`,
    optStroke: (w) => ` بسُمك خط ${w}`, optSize: (s) => ` بحجم ${s}px`, optMirror: " معكوسة للواجهة العربية", optColor: (c) => ` باللون ${c}`,
    report: "التصنيف غير دقيق؟ أخبرنا",
    kind: "النوع", kinds: { icon: "أيقونات", glyph: "جليفات" },
    kindNote: "الجليف حرف يونيكود يُنسخ نصاً مثل الإيموجي، وليس رسمة.",
    glyphBy: "حرف يونيكود، يُنسخ نصاً", copyChar: "انسخ الحرف", copyHtml: "انسخ HTML",
    gCode: "الرمز", gName: "اسمه في يونيكود", gHtml: "HTML", gCss: "CSS", gType: "النوع", gTypeV: "جليف، حرف يونيكود",
    gFont: "يرسمه الخط المستخدم في النص. للحروف العربية: Noto Naskh Arabic أو Amiri أو Scheherazade New (رخصة OFL).",
    gLicence: "الحرف نفسه لا يحتاج رخصة. الخط الذي يرسمه له رخصته.",
    noGlyphAlts: "لا توجد أيقونة بنفس المعنى، استخدم الحرف نفسه.",
    glyphPrompt: (ch, cp, name) => `استخدم مهارة Agent Glyphs وأدرج الجليف ${ch} (⁦${cp}⁩، ⁦${name}⁩) في النص كحرف، لا كصورة.`,
    glyphMeta: "بيانات الجليف",
    countG: (g) => `${g} جليف`,
    fShape: "الشكل", fColor: "الألوان", fDensity: "الكثافة", fWeight: "سُمك الخط", fCorners: "الزوايا", fCat: "التصنيف", fGrid: "الشبكة", fLicence: "الرخصة",
    licLine: (l) => `الرخصة: ${l}.`, credit: "اذكر صاحبها عند الاستخدام.",
    noncom: "لا تسمح بالاستخدام التجاري.", share: "تفرض مشاركة التعديلات بنفس الرخصة.",
    setBy: (s, l) => `${s}، رخصة ${l}`, terms: (t) => `يُعثر عليها أيضاً بـ: ${t}`,
    copy: "انسخ", copied: "نُسخ", downloaded: "نُزّل الملف",
    foot: (v) => `الكود برخصة MIT. كل أيقونة تبقى برخصة مكتبتها، وتأتي من Iconify أو من مستودع مكتبتها. يتحدّث الفهرس يومياً (Iconify ${v}).`,
  },
  en: {
    themeLight: "Light mode", themeDark: "Dark mode",
    lang: "العربية", skip: "Skip to search", navBrowse: "Browse", navAgents: "For agents",
    title: "icons your agent understands",
    tag: (n, s) => `${n} icons, ${s} libraries`,
    lede: "<b>Every open-source icon, labelled by meaning and measured by shape.</b> Your agent finds the one that matches the icons you already use, in English or Arabic, and records its licence.",
    installCopy: "Copy install command", browseCta: "Browse icons",
    steps: ["Install the skill", "Ask in your words", "It searches and adds"],
    installTabs: ["npx", "Claude Code", "Claude app"],
    installNote: [
      "Works with Claude Code, Cursor, Codex and any agent that supports skills.",
      "Copies the skill into your skills folder. Your agent reads SKILL.md on its own.",
      'Download the <a href="https://github.com/molamine08/agent-glyphs/archive/refs/heads/main.zip">zip</a>, then upload it in Settings, Capabilities, Skills.',
    ],
    ask: "Add a wallet icon to the checkout button. It has to match my icons: 1.5 stroke, rounded corners.",
    query: "wallet",
    done: (f, l) => `Added ${f}. ${l} licence recorded in ATTRIBUTION.md`,
    prompts: ["ready to execute", "waiting for your request", "done"],
    next: "Next step",
    browseLabel: "Browse icons", searchLabel: "Search icons", placeholder: "wallet, cart, محفظة…", hint: "Search icons for",
    shape: "Shape", colors_: "Colours", density: "Density", corners: "Corners", stroke: "Stroke", category: "Category", licence: "Licence",
    any: "Any", anyWeight: "Any weight", within: "Within ±0.3",
    strokeTitle: "Stroke weight on a 24 px grid",
    shapes: { outline: "Outline", filled: "Filled", mixed: "Mixed" },
    colors: { mono: "One colour", duotone: "Duotone", multicolor: "Multicolour" },
    densities: { airy: "Light", balanced: "Balanced", heavy: "Dense" },
    cornersL: { rounded: "Rounded", mixed: "Mixed", sharp: "Sharp" },
    lic: { commercial: "Commercial use", any: "Any licence" },
    clear: "Clear filters", copyCmd: "Copy command", more: "Show more",

    loading: "Loading the index…", loadErr: "The index could not load. Refresh in a moment.",
    count: (n, s) => `${n} icons from ${s} libraries`, none: "No results. Try a word with a similar meaning or loosen the filters.",
    tabs: { same: "Same meaning", agent: "For your agent", details: "Details" },
    noAlts: "No other library draws this icon.",
    color: "Colour", size: "Size", mirror: "Mirror for right-to-left",
    copySvg: "Copy SVG", copyJsx: "React", download: "Download", close: "Close",
    askAgent: "Ask your agent", command: "What it will run", metadata: "Icon metadata",
    prompt: (id, set, lic, opts) => `Use the Agent Glyphs skill to add the icon ${id} from ${set} (${lic} licence)${opts}.`,
    optStroke: (w) => `, stroke ${w}`, optSize: (s) => `, ${s}px`, optMirror: ", mirrored for right-to-left", optColor: (c) => `, colour ${c}`,
    report: "Wrong label? Tell us",
    kind: "Type", kinds: { icon: "Icons", glyph: "Glyphs" },
    kindNote: "A glyph is a Unicode character you paste as text, like an emoji. It is not a drawing.",
    glyphBy: "Unicode character, pasted as text", copyChar: "Copy character", copyHtml: "Copy HTML",
    gCode: "Code point", gName: "Unicode name", gHtml: "HTML", gCss: "CSS", gType: "Type", gTypeV: "Glyph, a Unicode character",
    gFont: "The font of your text draws it. For Arabic characters: Noto Naskh Arabic, Amiri or Scheherazade New (OFL licence).",
    gLicence: "The character itself needs no licence. The font that draws it has its own.",
    noGlyphAlts: "No icon has this meaning: use the character itself.",
    glyphPrompt: (ch, cp, name) => `Use the Agent Glyphs skill to put the glyph ${ch} (${cp}, ${name}) in the text as a character, not an image.`,
    glyphMeta: "Glyph metadata",
    countG: (g) => `${g} glyphs`,
    fShape: "Shape", fColor: "Colour", fDensity: "Density", fWeight: "Stroke", fCorners: "Corners", fCat: "Category", fGrid: "Grid", fLicence: "Licence",
    licLine: (l) => `Licence: ${l}.`, credit: "Credit the author when you use it.",
    noncom: "Not for commercial use.", share: "Changes must be shared under the same licence.",
    setBy: (s, l) => `${s}, ${l} licence`, terms: (t) => `Also found as: ${t}`,
    copy: "Copy", copied: "Copied", downloaded: "Downloaded",
    foot: (v) => `Code under MIT. Every icon keeps its library's licence and comes from Iconify or the library's own repository. The index updates daily (Iconify ${v}).`,
  },
};
const SWATCHES = [null, "#0E0E10", "#2563EB", "#16A34A", "#DC2626", "#D97706"];
const SIZES = [16, 20, 24, 32, 48];
const WEIGHTS = [0.75, 1, 1.25, 1.5, 1.75, 2, 2.5, 3];

// ---------------------------------------------------------------- where the visitor is
// Read from the browser's time zone: no request leaves the page, nothing is stored.
const ZONE_COUNTRY = {
  "Asia/Riyadh": "sa", "Asia/Dubai": "ae", "Asia/Qatar": "qa", "Asia/Kuwait": "kw", "Asia/Bahrain": "bh",
  "Asia/Muscat": "om", "Asia/Aden": "ye", "Asia/Baghdad": "iq", "Asia/Amman": "jo", "Asia/Gaza": "ps",
  "Asia/Hebron": "ps", "Asia/Beirut": "lb", "Asia/Damascus": "sy", "Africa/Cairo": "eg", "Africa/Khartoum": "sd",
  "Africa/Tripoli": "ly", "Africa/Tunis": "tn", "Africa/Algiers": "dz", "Africa/Casablanca": "ma",
  "Africa/El_Aaiun": "ma", "Africa/Nouakchott": "mr", "Africa/Djibouti": "dj", "Indian/Comoro": "km",
};
// words people around the visitor care about; every one returns icons in the index
const LOCAL = {
  sa: [["مسجد", "دلة", "نخلة", "ريال", "جمل"], ["mosque", "palm", "riyal", "camel", "coffee"]],
  ae: [["برج", "صقر", "درهم", "نخلة", "دلة"], ["tower", "falcon", "dirham", "palm", "camel"]],
  qa: [["صقر", "دلة", "ريال", "مسجد", "قارب"], ["falcon", "riyal", "mosque", "boat", "camel"]],
  kw: [["برج", "شراع", "دينار", "دلة", "نخلة"], ["tower", "sailboat", "coins", "palm", "coffee"]],
  bh: [["لؤلؤ", "شراع", "دينار", "نخلة", "مسجد"], ["oyster", "sailboat", "coins", "palm", "mosque"]],
  om: [["قلعة", "خنجر", "ريال", "قارب", "دلة"], ["castle", "boat", "rial", "camel", "coffee"]],
  ye: [["قهوة", "قلعة", "ريال", "مسجد", "جمل"], ["coffee", "castle", "rial", "mosque", "camel"]],
  iq: [["نخلة", "تمر", "دينار", "مسجد", "كتاب"], ["palm", "coins", "mosque", "book", "tea"]],
  jo: [["قلعة", "زيتون", "دينار", "جمل", "قهوة"], ["castle", "olive", "coins", "camel", "coffee"]],
  ps: [["زيتون", "مفتاح", "مسجد", "شجرة", "بيت"], ["olive", "key", "mosque", "tree", "home"]],
  lb: [["شجرة", "قهوة", "ليرة", "بحر", "جبل"], ["tree", "coffee", "lira", "beach", "mountain"]],
  sy: [["صابون", "زهرة", "قلعة", "ليرة", "قهوة"], ["soap", "flower", "castle", "lira", "coffee"]],
  eg: [["هرم", "فول", "جنيه", "مسجد", "فانوس"], ["pyramid", "beans", "pound", "mosque", "lantern"]],
  sd: [["جمل", "هرم", "نهر", "شاي", "نخلة"], ["camel", "pyramid", "river", "tea", "palm"]],
  ly: [["نخلة", "دينار", "جمل", "زيتون", "بحر"], ["palm", "coins", "camel", "olive", "beach"]],
  tn: [["زيتون", "دينار", "بحر", "شاي", "نخلة"], ["olive", "coins", "beach", "tea", "palm"]],
  dz: [["مسجد", "زيتون", "دينار", "شاي", "نخلة"], ["mosque", "olive", "coins", "tea", "palm"]],
  ma: [["شاي", "زليج", "درهم", "مسجد", "خيمة"], ["tea", "tile", "dirham", "mosque", "tent"]],
  mr: [["جمل", "شاي", "خيمة", "نخلة", "مسجد"], ["camel", "tea", "tent", "palm", "mosque"]],
  arab: [["مسجد", "محفظة", "سلة", "قهوة", "هلال"], ["mosque", "wallet", "cart", "coffee", "crescent"]],
  Europe: [["دراجة", "قطار", "قهوة", "يورو", "مظلة"], ["bicycle", "train", "coffee", "euro", "umbrella"]],
  America: [["سيارة", "دولار", "قهوة", "برغر", "كاميرا"], ["car", "dollar", "coffee", "burger", "camera"]],
  Asia: [["شاي", "قطار", "ين", "سوشي", "جوال"], ["tea", "train", "yen", "sushi", "phone"]],
  any: [["محفظة", "سلة", "جرس", "بيت", "قهوة"], ["wallet", "cart", "bell", "home", "coffee"]],
};
const ZONE = (() => { try { return Intl.DateTimeFormat().resolvedOptions().timeZone || ""; } catch { return ""; } })();
const COUNTRY = ZONE_COUNTRY[ZONE] || null;
const speaksArabic = (navigator.languages || [navigator.language || ""]).some((l) => /^ar\b/i.test(l));
function localWords(l) {
  const key = COUNTRY || (speaksArabic ? "arab" : ["Europe", "America", "Asia"].find((r) => ZONE.startsWith(r + "/")) || "any");
  return LOCAL[key][l === "ar" ? 0 : 1];
}

let lang = (() => {
  try { const saved = localStorage.getItem("lang"); if (saved) return saved; } catch { /* private mode */ }
  return COUNTRY || speaksArabic ? "ar" : "en";
})();
let meta = null, terms = {}, labels = {}, seq = 0, limit = PAGE, current = null, lastRes = null, tab = "same";
const state = { kind: null, shape: null, color: null, corners: null, weight: null, density: null, cat: null, commercial: true };
const EMPTY = { ...state };
const glyphMode = () => state.kind === "glyph";
const filledOnly = () => meta && state.shape !== null && meta.shapes[state.shape] === "filled";
const view = { color: null, size: 24, stroke: null, mirror: false };
const cache = new Map();
const extSets = new Map();
const worker = new Worker(`worker.js?v=${BUILD}`);
const t = () => T[lang];
const fmt = (n) => Number(n).toLocaleString("en-US");
const setOf = (p) => meta.setsInfo.find((s) => s.p === p);
const desktop = () => matchMedia("(min-width: 1181px)").matches;
const reduced = () => matchMedia("(prefers-reduced-motion: reduce)").matches;
const pending = new Map();
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

// ---------------------------------------------------------------- hero: three stacked steps
let step = 0, installTab = 0, stepTimer = null, paused = false, demo = null;

async function loadDemo() {
  // what the agent finds for the request in the second step, one icon per well-known library
  const L = t();
  const filters = { ...EMPTY, shape: meta.shapes.indexOf("outline"), corners: meta.corners.indexOf("rounded"), weight: 1.5 };
  const res = await ask({ type: "search", query: L.query, filters, limit: 60 });
  const known = ["tabler", "lucide", "ph", "hugeicons", "iconoir", "solar", "mynaui", "mingcute", "ri", "fluent"];
  const rank = (it) => (known.includes(it.p) ? known.indexOf(it.p) : 99);
  const seen = new Set();
  const items = res.items.filter((it) => !seen.has(it.p) && seen.add(it.p)).sort((a, b) => rank(a) - rank(b)).slice(0, 6);
  await Promise.all([...new Set(items.map((i) => i.p))].map((p) => fetchIcons(p, items.filter((i) => i.p === p).map((i) => i.n))));
  demo = { items, query: L.query, lang };
  if (step === 2) renderStep(false);
}

function renderStep(animate = true) {
  const L = t();
  const card = $("stepCard");
  const draw = () => {
    $("stepN").textContent = `${step + 1} / 3`;
    $("stepTitle").textContent = L.steps[step];
    $("stepPrompt").textContent = L.prompts[step];
    const body = $("stepBody");
    if (step === 0) {
      const cmd = INSTALL[installTab];
      const shown = installTab === 0 ? "npx skills add<br>molamine08/agent-glyphs"
        : installTab === 1 ? "git clone …/agent-glyphs<br>~/.claude/skills/agent-glyphs" : "agent-glyphs-main.zip";
      body.innerHTML = `<p class="term" dir="ltr">${shown}</p>
        <div class="step-tabs" role="group">${L.installTabs.map((x, i) => `<button type="button" data-tab="${i}" aria-pressed="${i === installTab}">${esc(x)}</button>`).join("")}</div>
        <p class="step-note">${L.installNote[installTab]}</p>`;
      body.querySelectorAll("[data-tab]").forEach((b) => b.addEventListener("click", () => { installTab = +b.dataset.tab; pause(); renderStep(false); }));
      body.dataset.cmd = cmd;
    } else if (step === 1) {
      body.innerHTML = `<p class="ask-bubble">${esc(L.ask)}</p>`;
    } else {
      const items = demo && demo.lang === lang ? demo.items : [];
      const first = items[0];
      const picks = items.map((it, i) => {
        const ic = cache.get(`${it.p}:${it.n}`);
        return `<span class="${i === 0 ? "chosen" : ""}" title="${esc(it.p + ":" + it.n)}">${ic ? toSvg(ic) : ""}</span>`;
      }).join("");
      const set = first && setOf(first.p);
      body.innerHTML = `<p class="term small" dir="ltr">search.py "${esc(L.query)}" <span class="say">--weight</span> 1.5 <span class="say">--corners</span> rounded</p>
        <div class="picks">${picks}</div>
        ${first ? `<p class="done">${ui("check")}<span>${esc(L.done(`src/icons/${compName(first.n)}.tsx`, set?.l || ""))}</span></p>` : ""}`;
    }
  };
  if (animate && !reduced()) {
    card.classList.add("leaving");
    setTimeout(() => { draw(); card.classList.remove("leaving"); }, 260);
  } else draw();
  restartRing();
}

function restartRing() {
  const ring = $("ring");
  ring.classList.remove("run");
  clearTimeout(stepTimer);
  if (paused || reduced()) return;
  void ring.offsetWidth;
  ring.style.setProperty("--step-ms", `${STEP_MS}ms`);
  ring.classList.add("run");
  stepTimer = setTimeout(() => { step = (step + 1) % 3; renderStep(); }, STEP_MS);
}
function pause() { paused = true; clearTimeout(stepTimer); $("ring").classList.remove("run"); }
$("next").addEventListener("click", () => { step = (step + 1) % 3; renderStep(); });
$("stack").addEventListener("mouseenter", () => { paused = true; clearTimeout(stepTimer); $("ring").classList.remove("run"); });
$("stack").addEventListener("mouseleave", () => { paused = false; restartRing(); });
$("stack").addEventListener("focusin", pause);
$("installCopy").addEventListener("click", () => copy(INSTALL[0]));

// ---------------------------------------------------------------- browse: filters as chips
let openPop = null, lastCounts = null, lastAll = null;

function chipLabel(key) {
  const L = t();
  if (key === "shape") return state.shape === null ? L.any : L.shapes[meta.shapes[state.shape]];
  if (key === "color") return state.color === null ? L.any : L.colors[meta.colors[state.color]];
  if (key === "density") return state.density === null ? L.any : L.densities[meta.density[state.density]];
  if (key === "corners") return state.corners === null ? L.any : L.cornersL[meta.corners[state.corners]];
  if (key === "weight") return state.weight === null ? L.any : String(state.weight);
  if (key === "cat") return state.cat === null ? L.any : (lang === "ar" ? meta.categories[state.cat][2] : meta.categories[state.cat][1]).replace(/\s*\(.*\)$/, "");
  if (key === "kind") return state.kind === null ? L.any : L.kinds[state.kind];
  return state.commercial ? L.lic.commercial : L.lic.any;
}
const isSet = (key) => (key === "commercial" ? state.commercial : state[key] !== null);

function renderFilters() {
  const L = t();
  const el = $("filters");
  // glyphs are characters: no style, corners, stroke or licence to pick
  // filled icons have no stroke: the stroke filter goes away while "filled" is picked
  const keys = [["kind", L.kind], ...(glyphMode() ? [] : [["shape", L.shape], ["color", L.colors_], ["corners", L.corners],
    ...(filledOnly() ? [] : [["weight", L.stroke]]), ["density", L.density], ["cat", L.category], ["commercial", L.licence]])];
  el.innerHTML = keys.map(([k, label]) => `<div class="fwrap" data-key="${k}"><button class="chip${isSet(k) ? " set" : ""}" type="button" aria-haspopup="true" aria-expanded="${openPop === k}"><small>${esc(label)}</small>${isSet(k) ? `<span>${esc(chipLabel(k))}</span>` : ""}${ui("down")}</button></div>`).join("")
    + `<button class="clear" type="button" ${anyFilter() ? "" : "hidden"}>${esc(L.clear)}</button>`;
  el.querySelectorAll(".fwrap").forEach((w) => w.querySelector(".chip").addEventListener("click", (e) => {
    e.stopPropagation();
    openPop = openPop === w.dataset.key ? null : w.dataset.key;
    renderFilters();
  }));
  el.querySelector(".clear").addEventListener("click", () => {
    Object.assign(state, EMPTY);
    openPop = null; newSearch();
  });
  if (openPop) renderPop(el.querySelector(`.fwrap[data-key="${openPop}"]`));
  renderAgentLine();
}
const anyFilter = () => Object.keys(EMPTY).some((k) => state[k] !== EMPTY[k]);

function renderPop(wrap) {
  const L = t();
  const key = wrap.dataset.key;
  const pop = document.createElement("div");
  pop.className = "pop" + (key === "cat" ? " cats" : "");
  pop.setAttribute("role", "dialog");
  pop.addEventListener("click", (e) => e.stopPropagation());
  const opt = (val, label, checked, extra = "", lead = "") => `<button class="opt" type="button" role="menuitemradio" data-v="${val}" aria-checked="${checked}">${ui("check", "tick")}${lead}<span>${esc(label)}</span>${extra}</button>`;
  if (key === "weight") {
    pop.innerHTML = `<h3>${esc(L.strokeTitle)}</h3><div class="sws">${WEIGHTS.map((w) => `<button class="sw" type="button" data-v="${w}" aria-checked="${state.weight === w}"><svg viewBox="0 0 24 24" aria-hidden="true"><rect x="4" y="4" width="16" height="16" rx="4" fill="none" stroke="currentColor" stroke-width="${w}"/></svg><span>${w}</span></button>`).join("")}</div>
      <div class="foot-row"><button type="button" data-v="null">${esc(L.anyWeight)}</button><span>${esc(L.within)}</span></div>`;
  } else if (key === "shape" || key === "color" || key === "density") {
    const [list, names] = key === "shape" ? [meta.shapes, L.shapes] : key === "color" ? [meta.colors, L.colors] : [meta.density, L.densities];
    pop.innerHTML = opt("null", L.any, state[key] === null) + Object.keys(names).map((v) => opt(list.indexOf(v), names[v], state[key] === list.indexOf(v))).join("");
  } else if (key === "corners") {
    const glyph = (r) => `<svg class="ui" viewBox="0 0 24 24"><path d="M5 19V${5 + r}a${r} ${r} 0 0 1 ${r}-${r}H19" fill="none" stroke="currentColor" stroke-width="2"/></svg>`;
    pop.innerHTML = opt("null", L.any, state.corners === null) + [["rounded", 7], ["mixed", 3], ["sharp", 0.01]].map(([c, r]) => opt(meta.corners.indexOf(c), L.cornersL[c], state.corners === meta.corners.indexOf(c), "", glyph(r))).join("");
  } else if (key === "cat") {
    const rows = meta.categories.map(([k, en, ar], i) => [i, lang === "ar" ? ar : en, lastCounts ? lastCounts[i] : null])
      .filter(([i, , n]) => n === null || n > 0 || state.cat === i);
    pop.innerHTML = opt("null", L.any, state.cat === null, lastAll !== null ? `<span class="n">${fmt(lastAll)}</span>` : "")
      + rows.map(([i, label, n]) => opt(i, label, state.cat === i, n !== null ? `<span class="n">${fmt(n)}</span>` : "")).join("");
  } else if (key === "kind") {
    const g = meta.glyphs ? `<span class="n">${fmt(meta.glyphs)}</span>` : "";
    pop.innerHTML = opt("null", L.any, state.kind === null) + opt("icon", L.kinds.icon, state.kind === "icon", `<span class="n">${fmt(meta.icons)}</span>`)
      + opt("glyph", L.kinds.glyph, state.kind === "glyph", g, '<span class="glyph-mark" aria-hidden="true">ﷺ</span>') + `<p class="pop-note">${esc(L.kindNote)}</p>`;
  } else {
    pop.innerHTML = opt("true", L.lic.commercial, state.commercial) + opt("false", L.lic.any, !state.commercial);
  }
  pop.querySelectorAll("[data-v]").forEach((b) => b.addEventListener("click", () => {
    const v = b.dataset.v;
    if (key === "commercial") state.commercial = v === "true";
    else if (key === "kind") state.kind = v === "null" ? null : v;
    else state[key] = v === "null" ? null : Number(v);
    if (filledOnly()) state.weight = null;  // a filled icon has no stroke to measure
    openPop = null;
    newSearch();
  }));
  wrap.append(pop);
  // keep the menu on screen
  requestAnimationFrame(() => {
    const r = pop.getBoundingClientRect();
    if (desktop() || innerWidth > 760) {
      if (r.right > innerWidth - 12) pop.style.insetInlineStart = "auto", pop.style.insetInlineEnd = "0";
      if (r.left < 12) pop.style.insetInlineStart = "auto", pop.style.insetInlineEnd = "auto", pop.style.left = "0";
    }
  });
}
document.addEventListener("click", () => { if (openPop) { openPop = null; renderFilters(); } });

function agentCommand() {
  const q = $("q").value.trim();
  const parts = [["search.py", ""], [q ? `"${q}"` : "", ""]];
  if (state.kind !== null) parts.push(["--kind", state.kind]);
  if (state.shape !== null) parts.push(["--shape", meta.shapes[state.shape]]);
  if (state.color !== null) parts.push(["--color", meta.colors[state.color]]);
  if (state.weight !== null) parts.push(["--weight", String(state.weight)]);
  if (state.corners !== null) parts.push(["--corners", meta.corners[state.corners]]);
  if (state.density !== null) parts.push(["--density", meta.density[state.density]]);
  if (state.cat !== null) parts.push(["--cat", meta.categories[state.cat][0]]);
  if (!state.commercial && !glyphMode()) parts.push(["--license", "any"]);
  return parts.filter(([a]) => a);
}
function renderAgentLine() {
  if (!meta) return;
  const parts = agentCommand();
  $("agentLine").innerHTML = parts.map(([a, b]) => (b ? `<s>${esc(a)}</s> ${esc(b)}` : esc(a))).join(" ");
}
$("copyCmd").addEventListener("click", () => copy("python scripts/" + agentCommand().map(([a, b]) => (b ? `${a} ${b}` : a)).join(" ")));

// ---------------------------------------------------------------- browse: results
function newSearch() { limit = PAGE; renderFilters(); run(); }
function run() {
  if (!meta) return;
  worker.postMessage({ type: "search", seq: ++seq, query: $("q").value, filters: state, limit });
}

function render(res) {
  lastRes = res;
  lastCounts = res.counts; lastAll = res.all;
  const grid = $("grid");
  grid.innerHTML = "";
  const L = t();
  const counts = [res.total - (glyphMode() ? res.total : 0) > 0 ? L.count(fmt(res.total), fmt(res.sets)) : "", res.glyphs ? L.countG(fmt(res.glyphs)) : ""].filter(Boolean);
  $("status").textContent = counts.join(lang === "ar" ? " و" : " + ");
  if (openPop === "cat") renderFilters();
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
    if (it.g) {
      // a glyph is shown as the character itself, in text, never as a drawing
      b.className = "tile glyph" + (it.e ? " emoji" : "") + (it.w ? " wide" : "");
      b.type = "button";
      b.dataset.p = it.p;
      b.dataset.n = it.n;
      b.title = `${it.ch}  ${it.cp}  ${it.n}`;
      b.setAttribute("aria-label", `${it.n} (${it.cp})`);
      if (current && current.p === it.p && current.n === it.n) b.setAttribute("aria-current", "true");
      b.innerHTML = `<span class="ch" lang="ar" dir="rtl">${esc(it.ch)}</span><span class="cp" dir="ltr">${esc(it.cp)}</span>`;
      b.addEventListener("click", () => open(it, true));
      li.append(b);
      grid.append(li);
      continue;
    }
    b.className = "tile";
    b.type = "button";
    b.dataset.p = it.p;
    b.dataset.n = it.n;
    b.title = `${it.p}:${it.n}`;
    b.setAttribute("aria-label", `${it.n} (${it.p})`);
    if (current && current.p === it.p && current.n === it.n) b.setAttribute("aria-current", "true");
    const ic = cache.get(`${it.p}:${it.n}`);
    b.innerHTML = `<span class="ic">${ic ? toSvg(ic) : '<span class="ph"></span>'}</span>`;
    b.addEventListener("click", () => open(it, true));
    li.append(b);
    grid.append(li);
    if (!ic) io.observe(b);
  }
  $("more").hidden = res.items.length >= res.total + (res.glyphs || 0) || res.items.length < limit;
  if (desktop() && (!current || !res.items.some((i) => i.p === current.p && i.n === current.n)) && !current?.pinned) open(res.items[0], false);
}


worker.onmessage = (e) => {
  const m = e.data;
  if (m.type === "ready") {
    meta = m.meta;
    terms = m.terms;
    labels = m.labels || {};
    loadGlyphFont(m.glyphChars);
    applyLang();
  } else if ((m.type === "results" || m.type === "alts") && pending.has(m.seq)) {
    pending.get(m.seq)(m); pending.delete(m.seq);
  } else if (m.type === "results" && m.seq === seq) {
    render(m);
  } else if (m.type === "error") {
    $("status").textContent = t().loadErr;
  }
};

let debounce;
$("q").addEventListener("input", () => { renderAgentLine(); clearTimeout(debounce); debounce = setTimeout(newSearch, 120); });
$("more").addEventListener("click", () => { limit += PAGE * 2; run(); });
document.addEventListener("keydown", (e) => {
  if (e.key === "/" && document.activeElement !== $("q") && !/INPUT|TEXTAREA/.test(document.activeElement.tagName)) {
    e.preventDefault();
    $("q").focus();
    $("browse").scrollIntoView({ behavior: reduced() ? "auto" : "smooth", block: "start" });
  }
  if (e.key === "Escape") { if (openPop) { openPop = null; renderFilters(); } else close(); }
});

// Arabic glyphs are drawn with Noto Naskh Arabic (OFL), the one free font that has
// every one of them; only those characters are downloaded
function loadGlyphFont(chars) {
  if (!chars) return;
  const l = document.createElement("link");
  l.rel = "stylesheet";
  l.href = `https://fonts.googleapis.com/css2?family=Noto+Naskh+Arabic&display=swap&text=${encodeURIComponent(chars)}`;
  document.head.append(l);
}

// ---------------------------------------------------------------- inspector
function viewSvg(sized = false) {
  const ic = current && cache.get(`${current.p}:${current.n}`);
  if (!ic) return "";
  const svg = toSvg(ic, { color: view.color, stroke: view.stroke, mirror: view.mirror });
  return sized ? svg.replace("<svg ", `<svg width="${view.size}" height="${view.size}" `) : svg;
}

function refreshPreview() {
  if (current?.g) { refreshAgent(); return; }
  const svg = viewSvg();
  $("dIcon").innerHTML = svg;
  $("dStrokeOut").textContent = view.stroke !== null ? view.stroke.toFixed(2) : (current && current.w >= 0 ? (current.w / 10).toFixed(1) : "");
  refreshAgent();
}

function refreshAgent() {
  if (!current) return;
  const L = t();
  if (current.g) {
    const id = `unicode:${current.n}`;
    $("agentPrompt").textContent = L.glyphPrompt(current.ch, current.cp, current.n);
    $("agentCmd").textContent = `python scripts/get.py ${id}`;
    $("agentJson").textContent = JSON.stringify({
      id, kind: "glyph", char: current.ch, codepoint: current.cp, unicode_name: current.un,
      html: htmlEntity(current.ch), css: cssEscape(current.ch), license: "Unicode character",
    }, null, 2);
    return;
  }
  const set = setOf(current.p);
  const id = `${current.p}:${current.n}`;
  const opts = (view.stroke !== null ? L.optStroke(view.stroke) : "") + (view.size !== 24 ? L.optSize(view.size) : "")
    + (view.color ? L.optColor(view.color) : "") + (view.mirror ? L.optMirror : "");
  $("agentPrompt").textContent = L.prompt(id, set.n, set.l || "?", opts);
  const flags = ["--format tsx", "--out src/icons"];
  if (view.stroke !== null) flags.push(`--stroke ${view.stroke}`);
  if (view.size !== 24) flags.push(`--size ${view.size}`);
  if (view.color) flags.push(`--color "${view.color}"`);
  if (view.mirror) flags.push("--mirror");
  $("agentCmd").textContent = `python scripts/get.py ${id} \\\n  ${flags.join(" ")}`;
  const cat = (k) => (k >= 0 ? meta.categories[k][0] : null);
  $("agentJson").textContent = JSON.stringify({
    id, set: set.n, shape: meta.shapes[current.sh], color: meta.colors[current.co], density: current.d >= 0 ? meta.density[current.d] : null, weight: current.w >= 0 ? current.w / 10 : null,
    corners: current.c >= 0 ? meta.corners[current.c] : null, category: [cat(current.k), cat(current.k2)].filter(Boolean),
    license: set.l, license_tier: meta.tiers[set.t], grid: set.g || null,
  }, null, 2);
}

function renderTabs() {
  const L = t();
  $("tabs").innerHTML = Object.entries(L.tabs).map(([k, label]) => `<button type="button" role="tab" data-k="${k}" aria-selected="${tab === k}">${esc(label)}</button>`).join("");
  $("tabs").querySelectorAll("button").forEach((b) => b.addEventListener("click", () => { tab = b.dataset.k; renderTabs(); }));
  $("paneSame").hidden = tab !== "same";
  $("paneAgent").hidden = tab !== "agent";
  $("paneDetails").hidden = tab !== "details";
}

function renderControls() {
  const L = t();
  $("swatches").innerHTML = SWATCHES.map((c) => `<button class="swatch" type="button" data-c="${c || ""}" style="--sw:${c || "var(--ink)"}" aria-label="${c || "currentColor"}" aria-pressed="${view.color === c}"></button>`).join("")
    + `<label class="swatch custom">+<input type="color" aria-label="Custom colour"></label>`;
  $("swatches").querySelectorAll("button").forEach((b) => b.addEventListener("click", () => { view.color = b.dataset.c || null; renderControls(); refreshPreview(); }));
  $("swatches").querySelector("input").addEventListener("input", (e) => { view.color = e.target.value; refreshPreview(); });
  $("sizeOpts").innerHTML = SIZES.map((s) => `<button type="button" data-s="${s}" aria-checked="${view.size === s}">${s}</button>`).join("");
  $("sizeOpts").querySelectorAll("button").forEach((b) => b.addEventListener("click", () => { view.size = +b.dataset.s; renderControls(); refreshAgent(); }));
  const g = current?.g;
  $("copySvg").innerHTML = `${ui("copy")}<span>${esc(g ? L.copyChar : L.copySvg)}</span>`;
  $("copyJsx").innerHTML = g ? `<span>${esc(L.copyHtml)}</span>` : `${ui("react")}<span>${esc(L.copyJsx)}</span>`;
  $("download").innerHTML = ui("download");
  $("download").setAttribute("aria-label", L.download);
  $("close").innerHTML = ui("close");
  $("close").setAttribute("aria-label", L.close);
  document.querySelectorAll("[data-copy]").forEach((b) => { b.innerHTML = `${ui("copy")}<span>${esc(L.copy)}</span>`; });
}

const htmlEntity = (ch) => [...ch].map((c) => `&#x${c.codePointAt(0).toString(16).toUpperCase()};`).join("");
const cssEscape = (ch) => [...ch].map((c) => `\\${c.codePointAt(0).toString(16).toUpperCase()}`).join("");

function openGlyph(it, user) {
  const L = t();
  $("inspector").classList.add("is-glyph");
  $("dIcon").innerHTML = `<span class="big-ch${it.e ? " emoji" : ""}${it.w ? " wide" : ""}" lang="ar" dir="rtl">${esc(it.ch)}</span>`;
  $("dName").textContent = it.n;
  $("dSet").textContent = L.glyphBy;
  const facts = [[L.gType, L.gTypeV], [L.gCode, it.cp], [L.gName, it.un], [L.gHtml, htmlEntity(it.ch)], [L.gCss, `content: "${cssEscape(it.ch)}"`]];
  $("dFacts").innerHTML = facts.map(([k, v]) => `<div><dt>${esc(k)}</dt><dd dir="ltr">${esc(v)}</dd></div>`).join("");
  $("dLicense").textContent = L.gLicence;
  document.querySelector('[data-i18n="metadata"]').textContent = L.glyphMeta;
  $("dTerms").textContent = it.e ? "" : L.gFont;
  const issue = new URLSearchParams({ title: `Glyph: ${it.n}`, body: `Glyph: ${it.ch} ${it.cp} unicode:${it.n}\n\nWhat is wrong:\n` });
  $("report").href = `https://github.com/${REPO}/issues/new?${issue}`;
  renderControls();
  refreshAgent();
  loadGlyphAlts(it);
  $("inspector").setAttribute("aria-hidden", "false");
  if (!desktop() && user) {
    $("scrim").hidden = false;
    $("close").focus({ preventScroll: true });
  }
}

// icons that mean the same thing as a glyph
async function loadGlyphAlts(it) {
  const ul = $("alts");
  ul.innerHTML = "";
  // the glyph's own name ("star-and-crescent", "prayer-beads") as a search: every word must match
  const word = it.n.split("-").filter((w) => !["and", "of", "as", "wa", "al", "up"].includes(w)).join(" ");
  const res = await ask({ type: "search", query: word, filters: { ...EMPTY, kind: "icon", commercial: state.commercial }, limit: 11 });
  if (!current || current.n !== it.n) return;
  $("noAlts").hidden = res.items.length > 0;
  $("noAlts").textContent = t().noGlyphAlts;
  ul.innerHTML = `<li><button class="alt glyph${it.w ? " wide" : ""}" type="button" aria-current="true" style="border:2px solid var(--ink)"><span class="ch" lang="ar">${esc(it.ch)}</span></button></li>`
    + res.items.map((a) => `<li><button class="alt" type="button" data-p="${esc(a.p)}" data-n="${esc(a.n)}" title="${esc(a.p + ":" + a.n)}"><span class="ic"></span></button></li>`).join("");
  ul.querySelectorAll(".alt[data-p]").forEach((b, i) => b.addEventListener("click", () => open(res.items[i], true)));
  for (const p of new Set(res.items.map((a) => a.p))) {
    const names = res.items.filter((a) => a.p === p).map((a) => a.n);
    fetchIcons(p, names).then(() => names.forEach((n) => paint(p, n)));
  }
}

async function open(it, user) {
  current = { ...it, pinned: user };
  const L = t();
  document.querySelectorAll(".tile[aria-current]").forEach((b) => b.removeAttribute("aria-current"));
  document.querySelector(`.tile[data-p="${it.p}"][data-n="${CSS.escape(it.n)}"]`)?.setAttribute("aria-current", "true");
  if (it.g) return openGlyph(it, user);
  $("inspector").classList.remove("is-glyph");
  $("noAlts").textContent = L.noAlts;
  document.querySelector('[data-i18n="metadata"]').textContent = L.metadata;
  const set = setOf(it.p);
  view.stroke = null; view.mirror = false;
  $("dMirror").checked = false;
  document.querySelectorAll(".tile[aria-current]").forEach((b) => b.removeAttribute("aria-current"));
  document.querySelector(`.tile[data-p="${it.p}"][data-n="${CSS.escape(it.n)}"]`)?.setAttribute("aria-current", "true");
  await fetchIcons(it.p, [it.n]);
  if (current.p !== it.p || current.n !== it.n) return;
  const ic = cache.get(`${it.p}:${it.n}`);
  $("dName").textContent = it.n;
  $("dSet").textContent = L.setBy(set.n, set.l || "?");
  const catName = (k) => (lang === "ar" ? meta.categories[k][2] : meta.categories[k][1]);
  const facts = [
    [L.fShape, L.shapes[meta.shapes[it.sh]] || "-"],
    [L.fColor, L.colors[meta.colors[it.co]] || "-"],
    [L.fDensity, it.d >= 0 ? L.densities[meta.density[it.d]] : "-"],
    [L.fWeight, it.w >= 0 ? (it.w / 10).toFixed(1) : "-"],
    [L.fCorners, it.c >= 0 ? L.cornersL[meta.corners[it.c]] : "-"],
    [L.fGrid, set.g ? `${set.g}px` : "-"],
    [L.fCat, [it.k, it.k2].filter((k) => k >= 0).map(catName).join(lang === "ar" ? "، " : ", ")],
    [L.fLicence, set.l || "?"],
  ];
  $("dFacts").innerHTML = facts.map(([k, v]) => `<div><dt>${esc(k)}</dt><dd>${esc(v)}</dd></div>`).join("");
  const tier = meta.tiers[set.t];
  const extra = tier === "attribution" ? L.credit : tier === "non-commercial" ? L.noncom : tier === "share-alike" ? L.share : "";
  $("dLicense").innerHTML = `${esc(L.licLine(set.l || "?"))} ${extra ? `<strong>${esc(extra)}</strong>` : ""}`;
  const words = it.n.split(/[-_]/).flatMap((w) => terms[w] || []);
  $("dTerms").textContent = words.length ? L.terms([...new Set(words)].slice(0, 6).join(lang === "ar" ? "، " : ", ")) : "";
  const strokeIcon = !!ic && ic.body.includes("stroke-width");
  $("strokeWrap").hidden = !strokeIcon;
  if (strokeIcon) $("dStroke").value = it.w >= 0 ? (Math.round(it.w / 2.5) / 4).toFixed(2) : "2";
  const issue = new URLSearchParams({
    title: `Label: ${it.p}:${it.n}`,
    body: `Icon: ${it.p}:${it.n}\nCurrent: shape=${meta.shapes[it.sh]}, color=${meta.colors[it.co]}, density=${it.d >= 0 ? meta.density[it.d] : "-"}, corners=${it.c >= 0 ? meta.corners[it.c] : "-"}, category=${meta.categories[it.k][0]}\n\nWhat it should be:\n`,
  });
  $("report").href = `https://github.com/${REPO}/issues/new?${issue}`;
  renderControls();
  refreshPreview();
  loadAlts(it);
  $("inspector").setAttribute("aria-hidden", "false");
  if (!desktop() && user) {
    $("scrim").hidden = false;
    $("close").focus({ preventScroll: true });
  }
}

async function loadAlts(it) {
  const ul = $("alts");
  ul.innerHTML = "";
  const res = await ask({ type: "alts", p: it.p, concept: it.concept, commercial: state.commercial });
  if (!current || current.n !== it.n || current.p !== it.p) return;
  const items = [it, ...res.items].slice(0, 12);
  $("noAlts").hidden = res.items.length > 0;
  ul.innerHTML = items.map((a, i) => `<li><button class="alt" type="button" data-p="${esc(a.p)}" data-n="${esc(a.n)}" title="${esc(a.p + ":" + a.n)}" ${i === 0 ? 'aria-current="true" style="border:2px solid var(--ink)"' : ""}><span class="ic"></span></button></li>`).join("");
  ul.querySelectorAll(".alt").forEach((b, i) => b.addEventListener("click", () => i && open(items[i], true)));
  for (const p of new Set(items.map((a) => a.p))) {
    const names = items.filter((a) => a.p === p).map((a) => a.n);
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
$("copySvg").addEventListener("click", () => current && copy(current.g ? current.ch : viewSvg(true)));
$("copyJsx").addEventListener("click", () => current && copy(current.g ? htmlEntity(current.ch) : toJsx(viewSvg(), current.n)));
$("download").addEventListener("click", () => {
  if (!current || current.g) return;
  const a = document.createElement("a");
  a.href = URL.createObjectURL(new Blob([viewSvg(true)], { type: "image/svg+xml" }));
  a.download = `${current.p}-${current.n}.svg`;
  a.click();
  setTimeout(() => URL.revokeObjectURL(a.href), 1000);
  toast(t().downloaded);
});
document.querySelectorAll("[data-copy]").forEach((b) => b.addEventListener("click", () => copy($(b.dataset.copy).textContent)));

// ---------------------------------------------------------------- search hint and focus
let hintIdx = 0, hintTimer = null;
function renderHint() {
  const words = localWords(lang);
  $("qHintText").textContent = t().hint;
  $("qWord").textContent = words[hintIdx % words.length];
  $("qHint").hidden = !!$("q").value;
  clearInterval(hintTimer);
  if (reduced()) return;
  hintTimer = setInterval(() => {
    if ($("q").value) return;
    const el = $("qWord");
    el.classList.add("out");
    setTimeout(() => { hintIdx++; el.textContent = localWords(lang)[hintIdx % words.length]; el.classList.remove("out"); }, 260);
  }, 2400);
}
$("q").addEventListener("input", () => { $("qHint").hidden = !!$("q").value; });

// the search is ready for typing as soon as it is on screen (not on touch screens,
// where focusing would open the keyboard by itself)
const fine = matchMedia("(pointer: fine)").matches;
const typingElsewhere = () => /INPUT|TEXTAREA|SELECT/.test(document.activeElement?.tagName || "") || document.activeElement?.isContentEditable;
if (fine) {
  new IntersectionObserver((entries) => {
    for (const e of entries) {
      if (e.isIntersecting && !typingElsewhere() && !openPop) $("q").focus({ preventScroll: true });
    }
  }, { threshold: 0.6 }).observe(document.querySelector(".search"));
}
// typing anywhere goes into the search
document.addEventListener("keydown", (e) => {
  if (e.key.length !== 1 || e.ctrlKey || e.metaKey || e.altKey || typingElsewhere() || e.key === "/") return;
  $("q").focus({ preventScroll: true });
  if (!desktop() || $("browse").getBoundingClientRect().top > innerHeight) $("browse").scrollIntoView({ behavior: reduced() ? "auto" : "smooth", block: "start" });
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
  renderTheme();
  $("q").placeholder = "";
  renderHint();
  $("lede").innerHTML = L.lede;
  $("tag").textContent = meta ? L.tag(fmt(meta.icons), fmt(meta.sets)) : L.loading;
  $("installCopy").innerHTML = `${ui("copy")}<span>${esc(L.installCopy)}</span>`;
  $("copyCmd").innerHTML = ui("copy");
  $("copyCmd").setAttribute("aria-label", L.copyCmd);
  $("copyCmd").title = L.copyCmd;
  $("next").innerHTML = ui("next");
  $("next").setAttribute("aria-label", L.next);
  $("footText").textContent = meta ? L.foot(meta.version) : "";
  renderTabs();
  renderControls();
  renderStep(false);
  if (meta) { renderFilters(); run(); loadDemo(); }
  if (current) open(current, current.pinned);
}
// light / dark: follows the device until the visitor picks one, then remembers it
const isDark = () => (document.documentElement.dataset.theme || (matchMedia("(prefers-color-scheme: dark)").matches ? "dark" : "light")) === "dark";
function renderTheme() {
  const dark = isDark();
  $("theme").innerHTML = ui(dark ? "sun" : "moon");
  const label = dark ? t().themeLight : t().themeDark;
  $("theme").setAttribute("aria-label", label);
  $("theme").title = label;
  document.querySelectorAll('meta[name="theme-color"]').forEach((m) => m.setAttribute("content", dark ? "#0E0E10" : "#FFFFFF"));
}
$("theme").addEventListener("click", () => {
  const next = isDark() ? "light" : "dark";
  document.documentElement.dataset.theme = next;
  try { localStorage.setItem("theme", next); } catch { /* private mode */ }
  renderTheme();
});
matchMedia("(prefers-color-scheme: dark)").addEventListener("change", renderTheme);

$("lang").addEventListener("click", () => {
  lang = lang === "ar" ? "en" : "ar";
  try { localStorage.setItem("lang", lang); } catch { /* private mode */ }
  applyLang();
});

$("searchIcon").innerHTML = ui("search");
$("gh").innerHTML = ui("github");
applyLang();
$("status").textContent = t().loading;
worker.postMessage({ type: "load", base: new URL("data/", location.href).href, v: BUILD });
