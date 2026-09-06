"""
Attribute extraction: turn free text like

    "SS hex bolt M10 x 50 mm DIN 933"

into structured attributes: {material, type, diameter, length, standard}.

This is a rule-based (regex) extractor — deliberately dependency-free so the
whole pipeline runs offline. The AI Engineer agent slot in the build guide is
exactly this module: swap `extract_attributes` for an LLM/NER call later
without touching anything downstream, since callers only depend on the
returned dict shape.
"""
import re

MATERIAL_PATTERNS = [
    (re.compile(r"\bstainless steel\b|\bss\b", re.I), "stainless steel"),
    (re.compile(r"\bmild steel\b|\bms\b", re.I), "mild steel"),
    (re.compile(r"\bcarbon steel\b|\bcs\b", re.I), "carbon steel"),
    (re.compile(r"\bgalvani[sz]ed( iron)?\b|\bgi\b", re.I), "galvanized iron"),
    (re.compile(r"\bbrass\b", re.I), "brass"),
    (re.compile(r"\baluminium\b|\baluminum\b", re.I), "aluminium"),
]

TYPE_PATTERNS = [
    (re.compile(r"\bhex(agonal)?\s+bolt\b", re.I), "hex bolt"),
    (re.compile(r"\bcountersunk\s+screw\b|\bcsk\s+screw\b", re.I), "countersunk screw"),
    (re.compile(r"\bbolt\b", re.I), "bolt"),
    (re.compile(r"\bnut\b", re.I), "nut"),
    (re.compile(r"\bwasher\b", re.I), "washer"),
    (re.compile(r"\bscrew\b", re.I), "screw"),
]

# M10 x 50, M10-50, 10mm x 50mm, M10x50
_DIM_RE = re.compile(
    r"\bm?(\d+(?:\.\d+)?)\s*(?:mm)?\s*[x×\-]\s*(\d+(?:\.\d+)?)\s*(?:mm)?\b",
    re.I,
)
_STANDARD_RE = re.compile(r"\b(DIN|ISO|ANSI|BS|IS)\s*[- ]?\s*(\d+)\b", re.I)


def extract_attributes(raw_description: str) -> dict:
    text = raw_description or ""

    material = next((label for pat, label in MATERIAL_PATTERNS if pat.search(text)), None)
    type_ = next((label for pat, label in TYPE_PATTERNS if pat.search(text)), None)

    diameter = length = None
    dim_match = _DIM_RE.search(text)
    if dim_match:
        diameter = f"{dim_match.group(1)}mm"
        length = f"{dim_match.group(2)}mm"

    standard = None
    std_match = _STANDARD_RE.search(text)
    if std_match:
        standard = f"{std_match.group(1).upper()} {std_match.group(2)}"

    return {
        "material": material,
        "type": type_,
        "diameter": diameter,
        "length": length,
        "standard": standard,
    }


def attributes_to_rows(attrs: dict) -> list[dict]:
    """Flatten the extracted dict into material_attributes rows."""
    rows = []
    for name, value in attrs.items():
        if value is None:
            continue
        rows.append({"attribute_name": name, "attribute_value": value, "normalized_value": value})
    return rows
