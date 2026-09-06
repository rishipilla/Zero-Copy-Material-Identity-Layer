from app.services.extract import extract_attributes
from app.services.matching import (
    semantic_similarity_matrix, attribute_score, detect_conflict, rule_score, hybrid_confidence,
)


def test_extract_attributes_from_free_text():
    attrs = extract_attributes("SS hex bolt M10 x 50 mm DIN 933")
    assert attrs["material"] == "stainless steel"
    assert attrs["type"] == "hex bolt"
    assert attrs["diameter"] == "10mm"
    assert attrs["length"] == "50mm"
    assert attrs["standard"] == "DIN 933"


def test_semantic_similarity_high_for_near_duplicates():
    descriptions = [
        "ss hex bolt m10x50 din 933",
        "stainless steel hex bolt m10-50 din 933",
        "carbon steel pipe 2 inch schedule 40",
    ]
    sim = semantic_similarity_matrix(descriptions)
    assert sim[0][1] > sim[0][2]  # the two bolt descriptions are closer than bolt-vs-pipe


def test_conflict_detected_on_dimension_mismatch():
    attrs_a = extract_attributes("SS Hex Bolt M10 x 50mm DIN 933")
    attrs_b = extract_attributes("SS Hex Bolt M10 x 80mm DIN 933")
    conflict = detect_conflict(attrs_a, attrs_b)
    assert conflict is not None
    assert "length" in conflict
    assert rule_score(conflict) == 0.0


def test_no_conflict_for_true_duplicate():
    attrs_a = extract_attributes("SS Hex Bolt M10 x 50mm DIN 933")
    attrs_b = extract_attributes("Stainless Steel Hex Bolt M10-50 DIN 933")
    assert detect_conflict(attrs_a, attrs_b) is None
    assert attribute_score(attrs_a, attrs_b) == 1.0


def test_hybrid_confidence_penalizes_conflict():
    clean_confidence = hybrid_confidence(semantic=0.9, attribute=1.0, rule=1.0)
    conflicted_confidence = hybrid_confidence(semantic=0.9, attribute=0.5, rule=0.0)
    assert conflicted_confidence < clean_confidence
