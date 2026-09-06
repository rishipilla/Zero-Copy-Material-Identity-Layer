"""
Normalization: turns inconsistent free-text descriptions like

    "M10 x 50"   "10mm x 50mm"   "M10-50"

into one canonical form, so the matching engine is comparing like with like
before it ever computes a similarity score.
"""
import re

# Synonym map: raw token (lowercased) -> canonical token
SYNONYMS = {
    "ss": "stainless steel",
    "s.s": "stainless steel",
    "stainless": "stainless steel",
    "ms": "mild steel",
    "cs": "carbon steel",
    "gi": "galvanized iron",
    "hex": "hexagonal",
    "hx": "hexagonal",
    "csk": "countersunk",
    "c'sunk": "countersunk",
    "dia": "diameter",
    "din": "din",
    "iso": "iso",
    "bsp": "bsp",
    "npt": "npt",
    "bolt": "bolt",
    "nut": "nut",
    "washer": "washer",
    "screw": "screw",
}

_WS_RE = re.compile(r"\s+")
_PUNCT_RE = re.compile(r"[.\u2013\u2014]")  # periods, en/em dash -> space (ascii '-' is a dim separator)

# Matches a full dimension pair anchored on digits on both sides, so it never
# eats the "x" inside an ordinary word like "hex": "M10 x 50 mm", "10mm x 50mm",
# "M10-50" all collapse to "...10x50...".
_DIM_RE = re.compile(
    r"(\d+(?:\.\d+)?)\s*(?:mm)?\s*[x×\-]\s*(\d+(?:\.\d+)?)\s*(?:mm)?",
    re.IGNORECASE,
)
# Any standalone unit-bearing number left over (e.g. "Washer 10mm") also loses its unit.
_UNIT_RE = re.compile(r"\b(\d+(?:\.\d+)?)\s*mm\b", re.IGNORECASE)


def normalize_description(raw: str) -> str:
    if not raw:
        return ""

    text = raw.strip().lower()
    text = _PUNCT_RE.sub(" ", text)
    text = _WS_RE.sub(" ", text).strip()

    # collapse dimension pairs first (digit-anchored, so word-internal "x" is untouched)
    text = _DIM_RE.sub(lambda m: f"{m.group(1)}x{m.group(2)}", text)
    text = _UNIT_RE.sub(r"\1", text)

    # token-level synonym substitution
    tokens = text.split(" ")
    normalized_tokens = [SYNONYMS.get(tok, tok) for tok in tokens]
    text = " ".join(normalized_tokens)

    return _WS_RE.sub(" ", text).strip()
