from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity

from app.config import settings


def attribute_similarity(attrs_a: dict, attrs_b: dict) -> float:
    important_attributes = [
        "material",
        "type",
        "diameter",
        "length",
        "standard",
        "viscosity_grade",
        "nlgi_grade",
        "welding_grade",
        "quantity",
        "quantity_unit",
    ]

    scores = []

    for key in important_attributes:
        value_a = attrs_a.get(key)
        value_b = attrs_b.get(key)

        if value_a and value_b:
            scores.append(
                1.0
                if str(value_a).lower() == str(value_b).lower()
                else 0.0
            )

    if not scores:
        return 0.0

    return sum(scores) / len(scores)


def _normalize_type(value: str | None) -> str:
    if not value:
        return ""

    return " ".join(str(value).lower().strip().split())


def detect_conflict(attrs_a: dict, attrs_b: dict) -> str | None:
    """
    Detect hard attribute conflicts that strongly indicate
    two records should NOT represent the same material.
    """

    type_a = _normalize_type(attrs_a.get("type"))
    type_b = _normalize_type(attrs_b.get("type"))

    # Completely different material types should not match.
    incompatible_types = {
        frozenset({"hex bolt", "hex nut"}),
        frozenset({"bolt", "nut"}),
        frozenset({"hex bolt", "nut"}),
        frozenset({"bolt", "hex nut"}),
        frozenset({"pipe", "elbow"}),
        frozenset({"pipe", "tee"}),
        frozenset({"pipe", "coupling"}),
        frozenset({"pipe", "reducer"}),
        frozenset({"pipe", "valve"}),
        frozenset({"hose", "pipe"}),
        frozenset({"hydraulic hose", "pipe"}),
        frozenset({"washer", "nut"}),
        frozenset({"washer", "bolt"}),
        frozenset({"bearing", "bolt"}),
        frozenset({"bearing", "nut"}),
        frozenset({"bearing", "washer"}),
        frozenset({"grease", "oil"}),
        frozenset({"hydraulic oil", "grease"}),
        frozenset({"welding electrode", "bolt"}),
        frozenset({"welding electrode", "nut"}),
        frozenset({"welding electrode", "washer"}),
        frozenset({"sealant", "bolt"}),
        frozenset({"sealant", "nut"}),
        frozenset({"sealant", "washer"}),
    }

    if type_a and type_b and frozenset({type_a, type_b}) in incompatible_types:
        return f"type mismatch: {type_a} vs {type_b}"

    # Diameter mismatch.
    diameter_a = attrs_a.get("diameter")
    diameter_b = attrs_b.get("diameter")

    if diameter_a and diameter_b:
        if str(diameter_a).lower() != str(diameter_b).lower():
            return f"diameter mismatch: {diameter_a} vs {diameter_b}"

    # Length mismatch.
    length_a = attrs_a.get("length")
    length_b = attrs_b.get("length")

    if length_a and length_b:
        if str(length_a).lower() != str(length_b).lower():
            return f"length mismatch: {length_a} vs {length_b}"

    # Welding electrode grade mismatch.
    welding_a = attrs_a.get("welding_grade")
    welding_b = attrs_b.get("welding_grade")

    if welding_a and welding_b:
        if str(welding_a).lower() != str(welding_b).lower():
            return f"welding grade mismatch: {welding_a} vs {welding_b}"

    # Lubricant grade conflicts.
    nlgi_a = attrs_a.get("nlgi_grade")
    nlgi_b = attrs_b.get("nlgi_grade")

    if nlgi_a and nlgi_b:
        if str(nlgi_a).lower() != str(nlgi_b).lower():
            return f"NLGI grade mismatch: {nlgi_a} vs {nlgi_b}"

    viscosity_a = attrs_a.get("viscosity_grade")
    viscosity_b = attrs_b.get("viscosity_grade")

    if viscosity_a and viscosity_b:
        if str(viscosity_a).lower() != str(viscosity_b).lower():
            return (
                f"viscosity grade mismatch: "
                f"{viscosity_a} vs {viscosity_b}"
            )

    return None


def rule_score(conflict_reason: str | None) -> float:
    return 0.0 if conflict_reason else 1.0


def hybrid_confidence(
    semantic: float,
    attribute: float,
    rule: float,
) -> float:
    return round(
        settings.WEIGHT_SEMANTIC * semantic
        + settings.WEIGHT_ATTRIBUTE * attribute
        + settings.WEIGHT_RULE * rule,
        4,
    )


def _embed_tfidf(texts: list[str]):
    vectorizer = TfidfVectorizer(
        analyzer="char_wb",
        ngram_range=(2, 4),
    )

    return vectorizer.fit_transform(texts).toarray()


def get_embeddings(texts: list[str]):
    return _embed_tfidf(texts)


def semantic_similarity_matrix(descriptions: list[str]):
    if len(descriptions) < 2:
        return []

    return cosine_similarity(
        get_embeddings(descriptions)
    )


def semantic_similarity(text_a: str, text_b: str) -> float:
    if not text_a or not text_b:
        return 0.0

    matrix = semantic_similarity_matrix(
        [text_a, text_b]
    )

    return float(matrix[0][1])


def attribute_score(attrs_a: dict, attrs_b: dict) -> float:
    return attribute_similarity(attrs_a, attrs_b)


def detect_rule_score(
    attrs_a: dict,
    attrs_b: dict,
) -> float:
    conflict = detect_conflict(attrs_a, attrs_b)
    return rule_score(conflict)


def match_decision(
    semantic: float,
    attribute: float,
    rule: float,
    conflict_reason: str | None = None,
):
    confidence = hybrid_confidence(
        semantic,
        attribute,
        rule,
    )

    if conflict_reason:
        return "NO_MATCH"

    if confidence >= 0.85:
        return "MATCH"

    if confidence >= 0.65:
        return "REVIEW"

    return "NO_MATCH"


def has_attribute_conflict(
    attrs_a: dict,
    attrs_b: dict,
) -> bool:
    return detect_conflict(attrs_a, attrs_b) is not None