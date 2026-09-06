from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity


model = SentenceTransformer("all-MiniLM-L6-v2")


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