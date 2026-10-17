#!/usr/bin/env python3
"""Write sources/glyphs/unicode.json: Unicode characters offered as glyphs.

A glyph stays a character: agents paste "ﷺ" into text the way they paste an
emoji, and the page shows it as text. Nothing is converted into a drawing.
This first catalogue covers Islamic and Arabic characters that no icon library
draws (honorific ligatures, Quranic marks) and the related emoji.

    python scripts/make_glyph_catalog.py
"""

import json
import re
import unicodedata
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "sources" / "glyphs" / "unicode.json"

ISLAMIC = (
    list(range(0xFDF0, 0xFDFE)) + [0xFDCF, 0xFDFE, 0xFDFF] + list(range(0xFD40, 0xFD50))
    + [0x06DD, 0x06DE, 0x06E9, 0xFD3E, 0xFD3F, 0x060E, 0x060F, 0x066D]
)
EMOJI = [0x1F54C, 0x1F54B, 0x1F6D0, 0x1F4FF, 0x1F319, 0x262A, 0x262B, 0x1F932, 0x1F9D5]

# cp: (name, english words it answers to, arabic words it answers to)
INFO = {
    0xFDF0: ("salla-stop-sign", ["salla", "waqf"], ["صلي", "علامة وقف"]),
    0xFDF1: ("qala-stop-sign", ["qala", "waqf"], ["قلي", "علامة وقف"]),
    0xFDF2: ("allah", ["allah", "god", "jalala"], ["الله", "لفظ الجلالة", "اسم الجلالة"]),
    0xFDF3: ("akbar", ["akbar", "takbir"], ["أكبر", "الله أكبر", "تكبير"]),
    0xFDF4: ("muhammad", ["muhammad", "mohammad", "prophet"], ["محمد", "النبي محمد"]),
    0xFDF5: ("salam", ["salam", "peace"], ["صلعم", "سلام"]),
    0xFDF6: ("rasul", ["rasul", "messenger", "prophet"], ["رسول", "الرسول"]),
    0xFDF7: ("alayhi", ["alayhi"], ["عليه"]),
    0xFDF8: ("wasallam", ["wasallam", "sallam"], ["وسلم"]),
    0xFDF9: ("salla", ["salla"], ["صلى"]),
    0xFDFA: ("sallallahu-alayhi-wasallam", ["sallallahu", "pbuh", "saw", "salawat", "honorific"],
             ["صلى الله عليه وسلم", "الصلاة على النبي", "صلعم", "عليه الصلاة والسلام"]),
    0xFDFB: ("jalla-jalaluhu", ["jalla", "jalaluhu", "honorific"], ["جل جلاله", "جل وعلا"]),
    0xFDFC: ("rial-sign", ["rial", "riyal", "currency"], ["ريال", "علامة الريال"]),
    0xFDFD: ("bismillah", ["bismillah", "basmala", "basmalah"],
             ["بسم الله الرحمن الرحيم", "بسملة", "بسم الله"]),
    0xFDCF: ("salamuhu-alayna", ["salamuhu", "honorific"], ["سلامه علينا"]),
    0xFDFE: ("subhanahu-wa-taala", ["subhanahu", "taala", "swt", "honorific"], ["سبحانه وتعالى", "سبحانه"]),
    0xFDFF: ("azza-wa-jall", ["azza", "jall", "honorific"], ["عز وجل"]),
    0xFD40: ("rahimahullah", ["rahimahu", "rahimahullah", "honorific"], ["رحمه الله", "رحمة الله عليه"]),
    0xFD41: ("radiallahu-anhu", ["radi", "radiallahu", "anhu", "honorific"], ["رضي الله عنه"]),
    0xFD42: ("radiallahu-anha", ["radi", "radiallahu", "anha", "honorific"], ["رضي الله عنها"]),
    0xFD43: ("radiallahu-anhum", ["radi", "radiallahu", "anhum", "honorific"], ["رضي الله عنهم"]),
    0xFD44: ("radiallahu-anhuma", ["radi", "radiallahu", "anhuma", "honorific"], ["رضي الله عنهما"]),
    0xFD45: ("radiallahu-anhunna", ["radi", "radiallahu", "anhunna", "honorific"], ["رضي الله عنهن"]),
    0xFD46: ("sallallahu-alayhi-wa-alih", ["sallallahu", "alih", "honorific"], ["صلى الله عليه وآله"]),
    0xFD47: ("alayhi-as-salam", ["alayhi", "salam", "honorific"], ["عليه السلام"]),
    0xFD48: ("alayhim-as-salam", ["alayhim", "salam", "honorific"], ["عليهم السلام"]),
    0xFD49: ("alayhima-as-salam", ["alayhimaa", "salam", "honorific"], ["عليهما السلام"]),
    0xFD4A: ("alayhi-as-salatu-was-salam", ["alayhi", "salatu", "salam", "honorific"], ["عليه الصلاة والسلام"]),
    0xFD4B: ("quddisa-sirruh", ["quddisa", "honorific"], ["قدس سره"]),
    0xFD4C: ("sallallahu-alayhi-wa-alihi-wa-sallam", ["sallallahu", "alih", "honorific"],
             ["صلى الله عليه وآله وسلم"]),
    0xFD4D: ("alayha-as-salam", ["alayhaa", "salam", "honorific"], ["عليها السلام"]),
    0xFD4E: ("tabaraka-wa-taala", ["tabaaraka", "taala", "honorific"], ["تبارك وتعالى"]),
    0xFD4F: ("rahimahumullah", ["rahimahum", "honorific"], ["رحمهم الله"]),
    0x06DD: ("end-of-ayah", ["ayah", "verse"], ["نهاية الآية", "رقم الآية", "آية"]),
    0x06DE: ("rub-el-hizb", ["hizb", "octagram"], ["ربع الحزب", "حزب", "نجمة ثمانية"]),
    0x06E9: ("sajdah", ["sajdah", "sujood", "prostration"], ["سجدة", "سجود", "موضع السجدة"]),
    0xFD3E: ("ornate-parenthesis-left", ["ornate", "parenthesis", "bracket"], ["قوس مزخرف", "أقواس قرآنية"]),
    0xFD3F: ("ornate-parenthesis-right", ["ornate", "parenthesis", "bracket"], ["قوس مزخرف", "أقواس قرآنية"]),
    0x060E: ("poetic-verse-sign", ["poetry", "verse", "poem"], ["بيت شعر", "شعر", "قصيدة"]),
    0x060F: ("misra-sign", ["misra", "poetry", "verse"], ["مصراع", "شطر"]),
    0x066D: ("arabic-five-pointed-star", ["star", "asterisk"], ["نجمة", "نجمة خماسية"]),
    0x1F54C: ("mosque", ["mosque", "masjid", "islam", "muslim"], ["مسجد", "جامع", "مساجد"]),
    0x1F54B: ("kaaba", ["kaaba", "mecca", "makkah", "hajj", "umrah"], ["الكعبة", "مكة", "حج", "عمرة"]),
    0x1F6D0: ("place-of-worship", ["worship", "prayer", "pray"], ["مكان عبادة", "عبادة", "مصلى"]),
    0x1F4FF: ("prayer-beads", ["prayer", "beads", "tasbih", "misbaha", "rosary"], ["سبحة", "مسبحة", "تسبيح"]),
    0x1F319: ("crescent-moon", ["crescent", "moon", "ramadan", "hilal", "night"], ["هلال", "رمضان", "قمر"]),
    0x262A: ("star-and-crescent", ["crescent", "star", "islam", "muslim"], ["هلال ونجمة", "إسلام", "مسلم"]),
    0x262B: ("farsi-symbol", ["farsi", "iran"], ["شعار إيران"]),
    0x1F932: ("palms-up-dua", ["dua", "supplication", "palms", "pray"], ["دعاء", "رفع اليدين", "يدعو"]),
    0x1F9D5: ("woman-hijab", ["hijab", "headscarf", "woman", "muslim"], ["حجاب", "محجبة", "امرأة محجبة"]),
}
WIDE = {0xFDFD}  # drawn far wider than tall: shown smaller in grids


def slug(cp: int) -> str:
    if cp in INFO:
        return INFO[cp][0]
    n = unicodedata.name(chr(cp), f"u{cp:04x}").lower()
    n = re.sub(r"^arabic (ligature )?|( isolated form)$", "", n)
    return re.sub(r"[^a-z0-9]+", "-", n).strip("-")


def main():
    out = []
    for cp in ISLAMIC + EMOJI:
        try:
            uname = unicodedata.name(chr(cp))
        except ValueError:
            continue  # not assigned in this Python's Unicode version
        _, en, ar = INFO.get(cp, ("", [], []))
        out.append({"name": slug(cp), "char": chr(cp), "cp": f"U+{cp:04X}", "unicode_name": uname,
                    "en": en, "ar": ar, "cat": "culture", "kind": "emoji" if cp in EMOJI else "text",
                    **({"wide": True} if cp in WIDE else {})})
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(out, ensure_ascii=False, indent=1) + "\n")
    print(f"{len(out)} glyphs -> {OUT.relative_to(ROOT)}")


if __name__ == "__main__":
    main()
