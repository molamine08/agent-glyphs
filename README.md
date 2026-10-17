# Icon Atlas

**Every open-source icon, searchable by what it means and by how it looks.**
An open agent skill for designers and vibe-coders: ~400,000 icons from ~250 libraries
(everything on [Iconify](https://iconify.design)), re-classified by meaning
(English **and Arabic**), drawing style, stroke weight, corner roundness, curviness,
stroke contrast and visual density — and kept up to date by a daily bot.

**Try it in the browser: https://molamine08.github.io/icone-atlas/**

[العربية ↓](#بالعربية)

```bash
python scripts/search.py "سلة التسوق" --style outline --weight 1.5 --corners rounded
python scripts/match.py ./my-icons --need wallet bell calendar     # "match my style"
python scripts/get.py lucide:house ph:bell --format tsx --out src/icons
```

## Why

Icon libraries are organised by *who made them*. People look for icons by *what they
mean* and *how they look*: "a 1.5px rounded outline wallet that fits next to my other
icons". Icon Atlas measures every icon from its rendered drawing, so a library whose
strokes were converted to shapes is measured the same way as a true stroke library,
and every number is normalised to a 24px grid.

![Search "محفظة" (wallet) across libraries](docs/demo-wallet.png)

## What is measured

| | How | Accuracy* |
|---|---|---|
| Stroke weight | 2 × ink area ÷ outline length, anti-aliased (sub-pixel) | median error 3%, 93% within 15% (75k icons) |
| Style (outline / filled / duotone / multicolour) | solid-area depth, colour and opacity layers, name hints, family consistency | 94.9% |
| Corners (rounded / mixed / sharp) | turning angle along the outline, outer corners only | 96.4% |
| Content category | name words vote (English→Arabic dictionary of 4,000 terms) + the set's own categories | 81.6% primary · 89.5% either of two |
| Curviness, contrast, density, padding, container, complexity | outline geometry and coverage | descriptive |

\* Weight: checked automatically against every icon that declares its stroke width.
Labels: independent review of a random sample of 240 icons. Details and known limits in
[ACCURACY.md](ACCURACY.md).

## Use it as a skill

Copy this folder into your agent's skills directory (Claude: Settings → Capabilities →
Skills, or `~/.claude/skills/icon-atlas`). The agent reads `SKILL.md`; the index
downloads itself on first use from the latest release.

## Looking at icons, not just their names

Categories come from icon names, so a paper plane can land in "transport" instead of
"send". `vision.yml` runs an open image-text model (CLIP ViT-B/32, free, no API key) on
GitHub Actions: it looks at one rendered icon per concept and votes on its category.

The votes are only used if they prove useful. Every run first scores reviewer-graded
icons (`tests/fixtures/gold_categories.json`): the vote weight is tuned on one half and
checked on the other, and it is adopted (`config.json → vision_weight`) only when it
improves both. Results are written to `VISION_EVAL.md`.

## How it stays up to date

Two GitHub Actions run every day:

1. **`daily-update.yml`** — checks npm for a new `@iconify/json` release. If there is
   one, it re-measures only the sets that changed (raw measurements are cached),
   rebuilds `atlas.db`, runs the tests, and publishes it as a release. `CHANGELOG.md`
   lists new and changed libraries. Fully automatic: Iconify's maintainers review every
   library before it reaches their package, and each carries its licence.
2. **`discover.yml`** — searches GitHub for icon libraries that are *not* indexed yet,
   checks their licence and SVG count, renders a preview, and opens a pull request that
   adds them to `sources/external.json` with `"approved": false`.
   **Nothing is added automatically.** A maintainer sets `"approved": true` on the ones
   worth keeping and merges; the next daily update converts and indexes them.

Libraries with non-commercial or missing licences are never proposed.

## Licences

- Code: MIT (see `LICENSE`).
- Icons are **not** redistributed by this repo. `get.py` fetches each icon from its
  official package on npm (or the Iconify API) and records its licence in
  `ATTRIBUTION.md`. Default search results only include licences that allow commercial
  use; CC BY icons require credit to the author. Brand logos are trademarks.
- The index (`atlas.db`) contains measurements, names and licence metadata.

## Contributing

- Wrong label? Open an issue with the icon reference (`prefix:name`) and what it should be.
- Better Arabic term? Edit `scripts/atlas/terms_ar.json`.
- Thresholds live in `scripts/atlas/classify.py`; the calibration contract in `tests/`.

---

## بالعربية

**كل الأيقونات المفتوحة المصدر، قابلة للبحث بالمعنى وبالشكل.**
مهارة مفتوحة المصدر للمصممين ومطوّري الـ vibe coding: قرابة 400 ألف أيقونة من نحو 250 مكتبة،
مُعاد تصنيفها حسب المعنى (بالعربية والإنجليزية)، ونمط الرسم، وسُمك الخط، وانحناء الزوايا،
ونسبة المنحنيات، وتباين السُّمك، والكثافة البصرية، مع بوت يحدّثها يومياً.

- **جرّبها في المتصفح:** https://molamine08.github.io/icone-atlas/
- **البحث بالعربية:** `python scripts/search.py "محفظة" --style outline --weight 1.5`
  ويفهم الكلمة مع «ال» أو بدونها، وبالهمزة أو بدونها.
- **طابق أسلوبي:** `python scripts/match.py ./أيقوناتي --need سلة جرس تقويم`
  يجد المكتبات الأقرب لأيقوناتك، ثم يكمل الناقص بنفس الشكل.
- **التصدير:** `python scripts/get.py lucide:house --format tsx --out src/icons`
  كملفات SVG أو مكونات React، مع ملف نسب الحقوق تلقائياً.

**التحديث اليومي:** بوت يضيف ويصنّف تلقائياً كل ما يصدر في Iconify، وبوت ثانٍ يكتشف
مكتبات جديدة خارجها ويفتح طلب مراجعة، ولا يُضاف شيء منها إلا بموافقة صاحب المستودع.

**الدقة:** سُمك الخط بمتوسط خطأ 3%، النمط 94.9%، الزوايا 96.4%، التصنيف 81.6% (89.5% مع التصنيف الثاني). التفاصيل في ACCURACY.md.

**النظر إلى الأيقونة لا اسمها فقط:** نموذج رؤية مفتوح ومجاني (CLIP) يعمل على GitHub Actions، ينظر إلى كل أيقونة ويصوّت على تصنيفها. لا يُعتمد صوته إلا إذا أثبت على أيقونات راجعها مراجع مستقل أنه يحسّن الدقة، والنتيجة تُنشر في VISION_EVAL.md.

**الرخص:** النتائج الافتراضية تشمل فقط الرخص التي تسمح بالاستخدام التجاري. أيقونات CC BY
تتطلب ذكر صاحبها، وملف `ATTRIBUTION.md` يُكتب تلقائياً.
