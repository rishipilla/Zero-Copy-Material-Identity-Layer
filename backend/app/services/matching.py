from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
import numpy as np

from app.config import settings


def semantic_similarity(text_a: str, text_b: str) -> float:
    """
    Calculate semantic similarity between two material descriptions.
    Returns a score between 0 and 1.
    """

    if not text_a or not text_b:
        return 0.0

    embeddings = model.encode([text_a, text_b])

    score = cosine_similarity(
        [embeddings[0]],
        [embeddings[1]],
    )[0][0]

    return max(0.0, min(1.0, float(score)))


def attribute_similarity(
    attributes_a: dict,
    attributes_b: dict,
) -> float:
    """
    Compare structured material attributes.
    Returns a score between 0 and 1.
    """

    important_attributes = [
        "material",
        "type",
        "diameter",
        "length",
        "standard",
    ]

    scores = []

    for attribute in important_attributes:
        value_a = attributes_a.get(attribute)
        value_b = attributes_b.get(attribute)

        if value_a is None and value_b is None:
            continue

        if value_a is None or value_b is None:
            scores.append(0.0)
            continue

        if str(value_a).lower() == str(value_b).lower():
            scores.append(1.0)
        else:
            scores.append(0.0)

    if not scores:
        return 0.0

    return sum(scores) / len(scores)


def hybrid_score(
    semantic_score: float,
    attribute_score: float,
    rule_score: float,
) -> float:
    """
    Calculate the final hybrid matching confidence.

    Prototype weights:
    - Semantic similarity: 50%
    - Attribute similarity: 30%
    - Rule compatibility: 20%
    """

    return (
        0.50 * semantic_score
        + 0.30 * attribute_score
        + 0.20 * rule_score
    )


def has_attribute_conflict(
    attributes_a: dict,
    attributes_b: dict,
) -> bool:
    """
    Detect hard conflicts in important material attributes.

    Returns True when both materials have an attribute
    but the values are different.
    """

    hard_attributes = [
        "material",
        "type",
        "diameter",
        "length",
        "standard",
    ]

    for attribute in hard_attributes:
        value_a = attributes_a.get(attribute)
        value_b = attributes_b.get(attribute)

        if value_a is None or value_b is None:
            continue

        if str(value_a).lower() != str(value_b).lower():
            return True

    return False


def match_decision(
    semantic_score: float,
    attribute_score: float,
    rule_score: float,
    has_conflict: bool,
) -> dict:
    """
    Decide whether two materials should match,
    be reviewed by a human, or not match.
    """

    # Never automatically merge materials
    # when a hard attribute conflict exists.
    if has_conflict:
        return {
            "decision": "NO_MATCH",
            "reason": "Hard attribute conflict detected.",
            "confidence": 0.0,
        }

    final_confidence = hybrid_score(
        semantic_score,
        attribute_score,
        rule_score,
    )

    if final_confidence >= 0.85:
        decision = "MATCH"
    elif final_confidence >= 0.65:
        decision = "REVIEW"
    else:
        decision = "NO_MATCH"

    return {
        "decision": decision,
        "reason": "Scores evaluated successfully.",
        "confidence": final_confidence,
    }


def _embed_tfidf(texts: list[str]) -> np.ndarray:
    if len(texts) < 2:
        return np.zeros((len(texts), 1))
    return TfidfVectorizer(analyzer="char_wb", ngram_range=(2, 4)).fit_transform(texts).toarray()


def get_embeddings(texts: list[str]) -> np.ndarray:
    return _embed_tfidf(texts)


def semantic_similarity_matrix(descriptions: list[str]) -> np.ndarray:
    if len(descriptions) < 2:
        return np.zeros((len(descriptions), len(descriptions)))
    return cosine_similarity(get_embeddings(descriptions))


def attribute_score(attrs_a: dict, attrs_b: dict) -> float:
    keys = {k for k in set(attrs_a) & set(attrs_b) if attrs_a.get(k) and attrs_b.get(k)}
    if not keys:
        return 0.0
    return sum(str(attrs_a[k]).lower() == str(attrs_b[k]).lower() for k in keys) / len(keys)


def detect_conflict(attrs_a: dict, attrs_b: dict) -> str | None:
    if attrs_a.get("diameter") and attrs_b.get("diameter") and attrs_a["diameter"] != attrs_b["diameter"]:
        return f"diameter mismatch: {attrs_a['diameter']} vs {attrs_b['diameter']}"
    if attrs_a.get("length") and attrs_b.get("length") and attrs_a["length"] != attrs_b["length"]:
        return f"length mismatch: {attrs_a['length']} vs {attrs_b['length']}"
    return None


def rule_score(conflict_reason: str | None) -> float:
    return 0.0 if conflict_reason else 1.0


def hybrid_confidence(semantic: float, attribute: float, rule: float) -> float:
    return round(settings.WEIGHT_SEMANTIC * semantic + settings.WEIGHT_ATTRIBUTE * attribute + settings.WEIGHT_RULE * rule, 4)