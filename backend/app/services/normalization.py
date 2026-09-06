import re


SYNONYMS = {
    "stainless steel": "ss",
    "stainless": "ss",
    "hexagonal": "hex",
    "hexagon": "hex",
}


def normalize_text(value: str) -> str:
    if not value:
        return ""

    text = value.lower().strip()

    # Normalize symbols
    text = text.replace("×", "x")
    text = text.replace("*", "x")

    # Normalize synonyms
    for source, target in SYNONYMS.items():
        text = text.replace(source, target)

    # Normalize dimensions:
    # 10mm x 50mm -> m10 x 50
    text = re.sub(
        r"\b(\d+(?:\.\d+)?)\s*mm\s*x\s*(\d+(?:\.\d+)?)\s*mm\b",
        r"m\1 x \2",
        text,
    )

    # M10-50 -> m10 x 50
    text = re.sub(
        r"\bm(\d+(?:\.\d+)?)\s*[-x]\s*(\d+(?:\.\d+)?)\b",
        r"m\1 x \2",
        text,
    )

    # Normalize DIN
    text = re.sub(
        r"\bdin\s*(\d+)\b",
        r"din \1",
        text,
    )

    # Remove remaining mm
    text = re.sub(
        r"(\d+(?:\.\d+)?)\s*mm\b",
        r"\1",
        text,
    )

    # Normalize whitespace
    text = re.sub(r"\s+", " ", text)

    # Put important components into a canonical order
    # so different word orders produce the same result.
    material = "ss" if " ss " in f" {text} " else ""
    item_type = "bolt" if "bolt" in text else ""
    
    diameter_match = re.search(r"\bm(\d+(?:\.\d+)?)\b", text)
    diameter = f"m{diameter_match.group(1)}" if diameter_match else ""

    length_match = re.search(
        r"\bm\d+(?:\.\d+)?\s*x\s*(\d+(?:\.\d+)?)\b",
        text,
    )
    length = f"x {length_match.group(1)}" if length_match else ""

    standard_match = re.search(r"\bdin\s*(\d+)\b", text)
    standard = f"din {standard_match.group(1)}" if standard_match else ""

    canonical_parts = [
        part
        for part in [material, item_type, diameter, length, standard]
        if part
    ]

    if canonical_parts:
        return " ".join(canonical_parts)

    return text


def extract_attributes(description: str) -> dict:
    normalized = normalize_text(description)

    attributes = {}

    lower_description = description.lower()

    # Material
    if (
        "stainless steel" in lower_description
        or " ss " in f" {lower_description} "
    ):
        attributes["material"] = "stainless steel"
    elif "steel" in lower_description:
        attributes["material"] = "steel"

    # Type
    if "bolt" in normalized:
        attributes["type"] = "bolt"
    elif "washer" in normalized:
        attributes["type"] = "washer"

    # Diameter
    diameter_match = re.search(
        r"\bm(\d+(?:\.\d+)?)\b",
        normalized,
    )

    if diameter_match:
        attributes["diameter"] = float(diameter_match.group(1))

    # Length
    length_match = re.search(
        r"\bm\d+(?:\.\d+)?\s*x\s*(\d+(?:\.\d+)?)\b",
        normalized,
    )

    if length_match:
        attributes["length"] = float(length_match.group(1))

    # Standard
    standard_match = re.search(
        r"\bdin\s*(\d+)\b",
        normalized,
    )

    if standard_match:
        attributes["standard"] = f"DIN {standard_match.group(1)}"

    return attributes