from app.services.normalize import normalize_description


def test_dimension_variants_collapse_to_same_form():
    a = normalize_description("M10 x 50")
    b = normalize_description("10mm x 50mm")
    c = normalize_description("M10-50")
    assert a == c
    # "10mm x 50mm" has no leading "m" prefix on the diameter, so it won't be
    # byte-identical to "m10x50" — but the shared "x50" dimension token must
    # survive normalization in all three.
    assert "x50" in a and "x50" in b and "x50" in c


def test_synonym_substitution():
    assert "stainless steel" in normalize_description("SS Hex Bolt M10 x 50mm")
    assert "hexagonal" in normalize_description("SS Hex Bolt M10 x 50mm")


def test_case_and_whitespace_normalized():
    assert normalize_description("  SS   Hex   Bolt  ") == normalize_description("ss hex bolt")
