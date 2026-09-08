import re

"""
Rule-based material attribute extraction.

The extractor converts free-text ERP descriptions into a stable
attribute dictionary used by the matching engine.

Examples:

    SS hex bolt M10 x 50 mm DIN 933
    -> material=stainless steel
       type=hex bolt
       diameter=10mm
       length=50mm
       standard=DIN 933

    Pneumatic Cylinder 50mm Bore
    -> type=pneumatic cylinder
       diameter=50mm

    Hydraulic Hose 1/2 inch
    -> type=hydraulic hose
       diameter=1/2in

    12 inch Hacksaw Blade
    -> type=hacksaw blade
       length=12in

The extractor is dependency-free and works offline.
"""


# ---------------------------------------------------------------------------
# MATERIAL
# ---------------------------------------------------------------------------

MATERIAL_PATTERNS = [
    (re.compile(r"\bstainless[\s-]+steel\b|\bss\b", re.I), "stainless steel"),
    (re.compile(r"\bmild[\s-]+steel\b|\bms\b", re.I), "mild steel"),
    (re.compile(r"\bcarbon[\s-]+steel\b|\bcs\b", re.I), "carbon steel"),
    (re.compile(r"\bgalvani[sz]ed(?:\s+iron)?\b|\bgi\b", re.I), "galvanized iron"),
    (re.compile(r"\bbrass\b", re.I), "brass"),
    (re.compile(r"\baluminium\b|\baluminum\b", re.I), "aluminium"),
    (re.compile(r"\bcopper\b", re.I), "copper"),
    (re.compile(r"\bpvc\b", re.I), "pvc"),
]


# ---------------------------------------------------------------------------
# TYPE
# ---------------------------------------------------------------------------

TYPE_PATTERNS = [
    (re.compile(r"\bhex(?:agonal)?\s+bolt\b", re.I), "hex bolt"),
    (re.compile(r"\bhex(?:agonal)?\s+nut\b", re.I), "hex nut"),
    (re.compile(r"\bcountersunk\s+screw\b|\bcsk\s+screw\b", re.I), "countersunk screw"),
    (re.compile(r"\bbolt\b", re.I), "bolt"),
    (re.compile(r"\bnut\b", re.I), "nut"),
    (re.compile(r"\bwasher\b", re.I), "washer"),
    (re.compile(r"\bscrew\b", re.I), "screw"),
    (re.compile(r"\bstud\b", re.I), "stud"),

    (re.compile(r"\bangle(?:\s+bar)?\b", re.I), "angle bar"),
    (re.compile(r"\bchannel\b", re.I), "channel"),
    (re.compile(r"\bflat\s+bar\b", re.I), "flat bar"),
    (re.compile(r"\bplate\b", re.I), "plate"),

    (re.compile(r"\btaper\s+roller\s+bearing\b", re.I), "taper roller bearing"),
    (re.compile(r"\broller\s+bearing\b", re.I), "roller bearing"),
    (re.compile(r"\bball\s+bearing\b", re.I), "ball bearing"),
    (re.compile(r"\bbearing\b", re.I), "bearing"),

    (re.compile(r"\bgate\s+valve\b", re.I), "gate valve"),
    (re.compile(r"\bball\s+valve\b", re.I), "ball valve"),
    (re.compile(r"\bcheck\s+valve\b", re.I), "check valve"),

    (re.compile(r"\belbow\b", re.I), "elbow"),
    (re.compile(r"\bpipe\b", re.I), "pipe"),
    (re.compile(r"\bconduit\b", re.I), "conduit"),

    (re.compile(r"\bhydraulic\s+hose\b|\bhose\b", re.I), "hydraulic hose"),
    (re.compile(r"\bpneumatic\s+cylinder\b|\bcylinder\b", re.I), "pneumatic cylinder"),

    (re.compile(r"\bhydraulic\s+oil\b", re.I), "hydraulic oil"),
    (re.compile(r"\bled\s+tube\b|\btube\s+light\b", re.I), "led tube light"),

    (re.compile(r"\bmcb\b", re.I), "mcb"),
    (re.compile(r"\bcable\b", re.I), "cable"),

    (re.compile(r"\bwelding\s+(?:electrode|rod)\b", re.I), "welding electrode"),
    (
        re.compile(
            r"\belectrode\b|\bwelder\s+rod\b|\bwelding\s+rod\b",
            re.I,
        ),
        "welding electrode",
    ),

    (re.compile(r"\bepoxy\s+adhesive\b|\btwo[\s-]+part\s+epoxy\b", re.I), "epoxy adhesive"),
    (re.compile(r"\bsilicone\s+sealant\b|\bsealant\b", re.I), "silicone sealant"),
    (re.compile(r"\badhesive\b", re.I), "adhesive"),

    (re.compile(r"\bgrease\b", re.I), "grease"),
    (re.compile(r"\boil\b", re.I), "oil"),

    (re.compile(r"\bsafety\s+helmet\b|\bhelmet\b", re.I), "safety helmet"),
    (re.compile(r"\bhacksaw\s+blade\b", re.I), "hacksaw blade"),
    (re.compile(r"\bblade\b", re.I), "blade"),
]


# ---------------------------------------------------------------------------
# DIMENSIONS
# ---------------------------------------------------------------------------

# M10 x 50
_DIM_RE = re.compile(
    r"""
    \b
    M?(\d+(?:\.\d+)?)
    \s*(?:mm)?
    \s*[xX×\-]\s*
    (\d+(?:\.\d+)?)
    \s*(?:mm)?
    \b
    """,
    re.I | re.X,
)


# 40 x 40 x 5
_THREE_DIM_RE = re.compile(
    r"""
    \b
    (\d+(?:\.\d+)?)\s*(?:mm)?
    \s*[xX×]\s*
    (\d+(?:\.\d+)?)\s*(?:mm)?
    \s*[xX×]\s*
    (\d+(?:\.\d+)?)\s*(?:mm)?
    \b
    """,
    re.I | re.X,
)


# 50mm Bore
_BORE_RE = re.compile(
    r"\b(\d+(?:\.\d+)?)\s*mm\s+bore\b",
    re.I,
)


# Fractions such as:
# 1/2 inch
# 3/4"
_FRACTION_SIZE_RE = re.compile(
    r"""
    \b
    (\d+\s*/\s*\d+)
    \s*(mm|cm|inch|in|")
    \b
    """,
    re.I | re.X,
)


# Whole numbers such as:
# 12 inch
# 4"
# 25mm
_SINGLE_SIZE_RE = re.compile(
    r"""
    \b
    (\d+(?:\.\d+)?)
    \s*(mm|cm|inch|in|")
    \b
    """,
    re.I | re.X,
)


# ---------------------------------------------------------------------------
# STANDARDS / SPECIALIZED ATTRIBUTES
# ---------------------------------------------------------------------------

_STANDARD_RE = re.compile(
    r"\b(DIN|ISO|ANSI|BS|IS)\s*[- ]?\s*(\d+)\b",
    re.I,
)

_VG_RE = re.compile(
    r"\b(?:ISO\s*)?VG\s*(\d+)\b",
    re.I,
)

_NLGI_RE = re.compile(
    r"\bNLGI[\s-]*(\d+)\b",
    re.I,
)

_WELDING_GRADE_RE = re.compile(
    r"\bE\d{4}\b",
    re.I,
)


# Quantity:
# 300ml
# 400 gm
# 1 kg
# 20W
# 32A
_QUANTITY_RE = re.compile(
    r"\b(\d+(?:\.\d+)?)\s*(ml|l|gm|g|kg|w|a)\b",
    re.I,
)


# ---------------------------------------------------------------------------
# HELPERS
# ---------------------------------------------------------------------------

def _normalize_fraction(value: str) -> str:
    return re.sub(r"\s+", "", value)


def _normalize_unit(unit: str) -> str:
    unit = unit.lower()

    if unit in {"inch", "in", '"'}:
        return "in"

    return unit


def _format_size(value: str, unit: str) -> str:
    value = value.strip()
    unit = _normalize_unit(unit)

    return f"{value}{unit}"


def _extract_type(text: str) -> str | None:
    return next(
        (
            label
            for pattern, label in TYPE_PATTERNS
            if pattern.search(text)
        ),
        None,
    )


def _extract_dimensions(
    text: str,
    type_: str | None,
) -> tuple[str | None, str | None]:
    """
    Returns:
        diameter, length
    """

    # ---------------------------------------------------------------
    # Bore
    # ---------------------------------------------------------------

    bore_match = _BORE_RE.search(text)

    if bore_match:
        return f"{bore_match.group(1)}mm", None


    # ---------------------------------------------------------------
    # Fastener / profile dimensions
    #
    # M10 x 50
    # M10-50
    # 40 x 40 x 5
    # ---------------------------------------------------------------

    dim_match = _DIM_RE.search(text)

    if dim_match:
        return (
            f"{dim_match.group(1)}mm",
            f"{dim_match.group(2)}mm",
        )


    three_dim_match = _THREE_DIM_RE.search(text)

    if three_dim_match:
        return (
            f"{three_dim_match.group(1)}mm",
            f"{three_dim_match.group(2)}mm",
        )


    # ---------------------------------------------------------------
    # Fractional dimensions
    #
    # IMPORTANT:
    # This must happen BEFORE the normal single-size regex.
    #
    # Otherwise:
    #     1/2 inch
    #
    # would incorrectly become:
    #     2in
    # ---------------------------------------------------------------

    fraction_match = _FRACTION_SIZE_RE.search(text)

    if fraction_match:
        value = _normalize_fraction(fraction_match.group(1))
        size = _format_size(value, fraction_match.group(2))

        if type_ in {
            "hacksaw blade",
            "blade",
            "hydraulic hose",
            "pipe",
            "conduit",
            "cable",
        }:
            return size, None

        return size, None


    # ---------------------------------------------------------------
    # Whole-number dimensions
    # ---------------------------------------------------------------

    single_match = _SINGLE_SIZE_RE.search(text)

    if single_match:
        size = _format_size(
            single_match.group(1),
            single_match.group(2),
        )

        # A blade/hose/pipe size is generally more useful as length/
        # nominal size than as a bolt-style diameter.
        if type_ in {
            "hacksaw blade",
            "blade",
        }:
            return None, size

        return size, None


    return None, None


# ---------------------------------------------------------------------------
# MAIN EXTRACTION
# ---------------------------------------------------------------------------

def extract_attributes(raw_description: str) -> dict:
    text = raw_description or ""

    type_ = _extract_type(text)


    # ---------------------------------------------------------------
    # Material
    # ---------------------------------------------------------------

    material = next(
        (
            label
            for pattern, label in MATERIAL_PATTERNS
            if pattern.search(text)
        ),
        None,
    )


    # ---------------------------------------------------------------
    # Dimensions
    # ---------------------------------------------------------------

    diameter, length = _extract_dimensions(
        text,
        type_,
    )


    # ---------------------------------------------------------------
    # Standard
    # ---------------------------------------------------------------

    standard = None

    standard_match = _STANDARD_RE.search(text)

    if standard_match:
        standard = (
            f"{standard_match.group(1).upper()} "
            f"{standard_match.group(2)}"
        )


    # ---------------------------------------------------------------
    # Hydraulic oil grade
    # ---------------------------------------------------------------

    viscosity_grade = None

    vg_match = _VG_RE.search(text)

    if vg_match:
        viscosity_grade = f"VG {vg_match.group(1)}"


    # ---------------------------------------------------------------
    # Grease grade
    # ---------------------------------------------------------------

    nlgi_grade = None

    nlgi_match = _NLGI_RE.search(text)

    if nlgi_match:
        nlgi_grade = f"NLGI {nlgi_match.group(1)}"


    # ---------------------------------------------------------------
    # Welding grade
    # ---------------------------------------------------------------

    welding_grade = None

    welding_match = _WELDING_GRADE_RE.search(text)

    if welding_match:
        welding_grade = welding_match.group(0).upper()


    # ---------------------------------------------------------------
    # Quantity
    # ---------------------------------------------------------------

    quantity = None

    quantity_unit = None

    quantity_match = _QUANTITY_RE.search(text)

    if quantity_match:
        quantity = quantity_match.group(1)
        quantity_unit = quantity_match.group(2).lower()


    # ---------------------------------------------------------------
    # Return stable attribute dictionary
    # ---------------------------------------------------------------

    return {
        "material": material,
        "type": type_,
        "diameter": diameter,
        "length": length,
        "standard": standard,
        "viscosity_grade": viscosity_grade,
        "nlgi_grade": nlgi_grade,
        "welding_grade": welding_grade,
        "quantity": quantity,
        "quantity_unit": quantity_unit,
    }


# ---------------------------------------------------------------------------
# DATABASE ROW CONVERSION
# ---------------------------------------------------------------------------

def attributes_to_rows(attrs: dict) -> list[dict]:
    rows = []

    for name, value in attrs.items():
        if value is None:
            continue

        rows.append(
            {
                "attribute_name": name,
                "attribute_value": str(value),
                "normalized_value": str(value).lower(),
            }
        )

    return rows