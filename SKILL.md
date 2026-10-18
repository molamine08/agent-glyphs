---
name: agent-glyphs
description: Find, match and export icons from 400k+ open-source icons (every Iconify set plus open libraries outside Iconify, updated daily) classified by meaning (English and Arabic) and by visual style — outline/filled/duotone, stroke weight on a 24px grid, rounded vs sharp corners, curviness, stroke contrast, density. Use whenever a UI, app, website, deck or design needs icons, when someone asks for "an icon for X" (in any language, e.g. "أيقونة سلة"), wants icons that match an existing set or brand style, needs to fill gaps in their icon set, or asks which icon library to use. Prefer this over drawing icons by hand or guessing icon names.
---

# Agent Glyphs

An index of every open-source icon library: all Iconify sets plus open libraries
outside Iconify (prefix `x-…`), 400k+ icons. Each icon is measured from its actual
drawing and tagged with its meaning in English and Arabic. Icons are fetched from their
official source on demand (npm / Iconify API, or this project's release for `x-` sets),
with their licence.

All commands run from this skill's folder. The index (`data/atlas.db`, ~160 MB; a 33 MB download)
downloads automatically on first use. Style matching and previews need:
`pip install -r requirements.txt` (search and export alone need only Python 3.10+).

## Workflow

1. **Find the target style first — consistency beats the "best" single icon.**
   - The project already uses an icon library? Check `package.json` and stay in it
     with `--set` (see the mapping below). Mixing libraries is the most common icon mistake.
   - The person has their own icons (SVGs)? Run `scripts/match.py <folder>` to find
     the families that look like them, then search with `--like <folder>`.
   - Nothing yet? Ask, or choose a coherent family (e.g. `lucide`, `tabler`, `ph`)
     and keep every icon from it.
2. **Search** by meaning, with style filters:
   ```bash
   python scripts/search.py "shopping cart" --set lucide
   python scripts/search.py "محفظة" --shape outline --stroke light --corners rounded
   python scripts/search.py "notification" --like tabler          # ranked by look
   python scripts/search.py --cat finance --shape filled --limit 40
   python scripts/search.py "home" --shape outline --color duotone --density balanced
   ```
   Output: `prefix:name`, style, weight, corners, category, licence. Use only names
   returned by the search — never invent icon names.
3. **Show before choosing** when a person will judge the result (designers, unclear asks):
   `python scripts/preview.py lucide:house tabler:home -o choices.png` (or `--search "home"`),
   then look at the PNG yourself and share it.
4. **Export** into the project:
   ```bash
   python scripts/get.py lucide:house lucide:search --out src/icons            # SVG files
   python scripts/get.py ph:bell --format tsx --out src/components/icons        # React (jsx|tsx)
   python scripts/get.py tabler:wallet --stroke 1.5 --size 20 --color "#0F766E" # restyle
   python scripts/get.py mdi:home --stdout                                      # print inline
   ```
   `get.py` writes/updates `ATTRIBUTION.md` next to the files.
5. **Fill gaps in a set** in one step:
   `python scripts/match.py ./my-icons --need cart wallet "مسجد"` (or `match.py lucide --need ...`).

If the project already depends on the library's own package (e.g. `lucide-react`),
importing from that package is better than copying SVGs — use the search to find the
right name, then import it.

## Vocabulary (filters and fields)

| Field | Values | Meaning |
|---|---|---|
| `shape` | outline, filled, mixed | what the eye sees: lines only, filled areas, or lines with filled parts. An icon named "…-filled" that is drawn with lines is `outline` |
| `color` | mono, duotone, multicolor | one colour, a second lighter tone, or its own fixed colours (multicolor cannot be recoloured with CSS). Combines with `shape`: an outline icon can be duotone |
| `style` | outline, filled, mixed, duotone, multicolor | older single label (`--style`): the colour when it is not mono, else the shape |
| `weight` | number | stroke width as it would be on a 24px icon (Lucide = 2, Heroicons = 1.5) |
| `weight_class` | hairline <0.6, thin <1.1, light <1.4, regular <1.75, medium <2.25, bold <2.9, heavy; `solid` for filled |
| `stroke` | thin, light, regular, bold | stroke class on a 24px grid: thin < 1.25 (Phosphor Thin/Light), light ≈ 1.5 (Heroicons, Phosphor), regular ≈ 2 (Lucide, Tabler), bold > 2.15 (Phosphor Bold). `--stroke`; `--weight 1.5` still filters the exact value |
| `corners` | rounded, mixed, sharp | how real corners (two straight lines meeting) and line ends are drawn; circles and arcs do not count. An icon with no corners takes its family's value |
| `curves` | geometric, balanced, organic | share of the outline that is curved |
| `contrast_class` | monoline, moderate, high | variation between thick and thin parts |
| `density_class` | airy, balanced, heavy | how much of the canvas is ink (`--density`); keep one density so icons sit together |
| `container` | circle, square, none | icon drawn inside a circle or square |
| `complexity` | simple, medium, detailed | amount of detail |
| `cat`, `cat2` | arrows, interface, actions, status, communication, commerce, finance, business, media, files, text, design, devices, development, data, network, ai, security, people, health, transport, maps, weather, nature, food, buildings, home, time, education, sports, culture, tools, shapes, emoji, brands, flags, other |

An icon can have two content categories (`cat`, `cat2`); `--cat` matches either.
Each label has a confidence (`style_conf`, `weight_conf`, `corners_conf`: high / medium /
low). When a choice matters and confidence is not high, look at the preview.
Measured accuracy is in `ACCURACY.md`.

Common packages → `--set` prefix: lucide-react → `lucide` · @tabler/icons-react → `tabler` ·
@phosphor-icons/react → `ph` · @heroicons/react → `heroicons` · @mui/icons-material → `ic` ·
Material Symbols → `material-symbols` · @radix-ui/react-icons → `radix-icons` ·
iconoir-react → `iconoir` · remixicon → `ri` · react-feather → `feather` · bootstrap-icons → `bi` ·
Font Awesome 6 → `fa6-solid` / `fa6-regular` · @fluentui/react-icons → `fluent` ·
@mdi/js → `mdi` · hugeicons → `hugeicons` · simple-icons → `simple-icons` (brand logos).
Full list: `python scripts/sets.py` (filter with `--search`).

## Licences — always respect them

- Default results include only licences that allow commercial use: **permissive**
  (MIT, Apache, ISC, OFL, CC0…: no obligation beyond keeping the licence) and
  **attribution** (CC BY: credit the author — `get.py` writes it to `ATTRIBUTION.md`;
  tell the person).
- `--license any` also shows share-alike (GPL, CC BY-SA) and non-commercial sets.
  Use them only when the person explicitly accepts those terms.
- Brand logos (`cat=brands`) are trademarks: fine to refer to the brand, not to imply endorsement.

## Notes

- Right-to-left (Arabic) interfaces: directional icons (arrows, chevrons, back/next,
  send, undo/redo) must point the other way — export them with `get.py --mirror`.
  Do not mirror icons that show real-world objects or clocks/checkmarks.
- Glyphs are Unicode characters, not drawings: Islamic and Arabic characters that no icon library
  draws (﷽ ﷺ ﷻ ۞ ۩ ﴾ ﴿, honorifics such as ﵁ رضي الله عنه) and related emoji (🕌 🕋 📿 ☪).
  `search.py` returns them with the icons (prefix `unicode`, `"kind": "glyph"`, the `char` and its
  `codepoint`); `--kind glyph` returns glyphs only, `--kind icon` icons only. Put a glyph in the text
  as the character itself (or its HTML entity `&#xFDFA;` / CSS `content: "\FDFA"`), never as an image
  or SVG. `get.py unicode:<name>` prints the character. The character needs no licence; the font that
  draws it does (Noto Naskh Arabic, Amiri and Scheherazade New are OFL).
- Search by meaning, not exact names. Arabic and English words are expanded through ~3,900 concept
  groups: synonyms, plurals and dialect or loanwords (سيتنج → settings, داشبورد → dashboard,
  مسلمين → islam), and closely related things ("مسلم" also finds mosque, crescent, quran). Each JSON
  result has `"match": "same"` or `"related"`; same-meaning icons always rank first. Hamza, "ال",
  plurals and common suffixes do not matter (سلة = السلة = بالسلة).
- No network for the index? Set `AGENT_GLYPHS_DATA` to a folder containing `atlas.db`.
  Icons are fetched from npm (`@iconify-json/<prefix>`) or the Iconify API and cached in
  `~/.cache/agent-glyphs`; set `ICONIFY_JSON_DIR` to use local Iconify JSON files instead.
