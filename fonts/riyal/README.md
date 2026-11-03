# Agent Glyphs Riyal

A tiny font that draws one character: the Saudi Riyal sign **⃁** (`U+20C1`, Unicode 17).
Most fonts do not draw it yet, so apps paste an SVG next to the number. That splits the
text, breaks right-to-left order and spacing, and screen readers skip it.

With this font the price stays **one string**. List it after your text font; the browser
or OS takes only the missing sign from it.

| Weight | Files |
|---|---|
| Regular (400) | `AgentGlyphsRiyal-Regular.woff2` / `.ttf` |
| Medium (500) | `AgentGlyphsRiyal-Medium.woff2` / `.ttf` |
| Bold (700) | `AgentGlyphsRiyal-Bold.woff2` / `.ttf` |

Sized to sit with digits (height of a digit, sits on the baseline) and to never make a
line taller (ascent 1250 / descent 600 at 1000 UPM). Each file is under 1 KB.

## Use

**Web**
```html
<link rel="stylesheet" href="fonts/riyal/riyal.css">
<style> body { font-family: "Your Font", "Agent Glyphs Riyal", sans-serif; } </style>
<p dir="rtl">باقي 45 &#x20C1; للشحن المجاني</p>
```

**Text order in Arabic (RTL):** write the number first, then the sign: `45 ⃁`.
It shows with the sign on the left of the number: **⃁ 45**.

**iOS (SwiftUI / UIKit):** add the TTF to the app, then make it a cascade font of your text font
(`UIFontDescriptor.AttributeName.cascadeList`). **Android:** a `FontFamily` fallback, or a
`TypefaceSpan` on the sign.

**Figma / design tools:** install the TTFs. Figma does not take a missing character from
another font by itself, so set the sign's range to "Agent Glyphs Riyal" inside the same
text layer (one layer, no vector).

**In code:** `"⃁"` (JS / Swift / Kotlin), `&#x20C1;` (HTML), `content: "\20C1"` (CSS).

## Build

```bash
pip install fonttools shapely svgpathtools brotli
python scripts/make_riyal_font.py
```

The outline is the official symbol published by the Saudi Central Bank (SAMA).
The font files are released under this repository's MIT licence.
