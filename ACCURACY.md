# Accuracy

Measured on the index built from Iconify 2.2.544 (248 sets, 415,236 icons), October 2026.
Re-run: `python tests/review_sample.py --n 240 --seed <new seed>` and grade the sheets.

## 1. Stroke weight — automatic check against ground truth

75,715 outline icons declare their stroke width in the SVG source. The measured weight
(computed from the rendered drawing, without reading that attribute) was compared with it:

| Error | Share of icons |
|---|---|
| median error | 3% |
| within 10% | 88% |
| within 15% | 93% |
| within 25% | 96% |

Most of the remaining gap comes from icons that mix several stroke widths (the source only
gives the largest one). Published reference sets land within 0.05 of their spec:
Lucide/Tabler 2.0, Heroicons 1.5, Phosphor thin/light/regular/bold 0.75/1.125/1.5/2.25
(`tests/test_atlas.py`).

## 2. Visual labels — independent review of a random sample

240 icons drawn at random from the whole index, rendered as numbered sheets and graded by
a reviewer who had not seen the classifier ("correct" ÷ "correct + wrong"; unclear
thumbnails excluded):

| Label | Accuracy | Notes |
|---|---|---|
| Style (outline / filled / duotone / multicolor / mixed) | **94.9%** | main error: single-colour solid brand logos read as outline |
| Corners (rounded / mixed / sharp) | **96.4%** | polygon logos sometimes "mixed" instead of "sharp" |
| Content category — primary | **81.6%** | category follows the literal object (paper plane → transport) |
| Content category — primary or secondary | **89.5%** | `--cat` matches either |

A first review (before fixing the patterns it found) scored 87% / 90% / 81%; the fixes —
animated icons, line-style app-icon sets, grey two-tone icons, corner detection on a 3px
window, family consistency — took style and corners to the numbers above.

## 2b. Vision votes

Category accuracy above is from names only. `vision.yml` measures whether an open vision
model (CLIP) improves it on the same reviewer-graded icons (tuned on one half, reported on
the other) and adopts it only if it does — see `VISION_EVAL.md`.

## 3. Coverage

| | Icons |
|---|---|
| with at least one Arabic search term | 371,039 (89%) |
| with a content category other than "other" | 404,149 (97%) |

## Known limits

- Meaning comes from icon *names* (plus each set's own categories). An icon with a vague
  name gets a vague category. Arabic terms cover the 4,000 most frequent name words.
- Brand logos: the drawing style of solid single-colour logos is the least reliable label.
- Each label carries a confidence (`style_conf`, `weight_conf`, `corners_conf`); prefer
  `--min-conf high` when it matters, and look at `preview.py` before choosing.

Corrections are welcome: open an issue with `prefix:name` and the right label.
