from sqlalchemy import BigInteger, String, Float
from sqlalchemy.orm import Mapped, mapped_column

from app.models.material import Base


class MaterialMatch(Base):
    __tablename__ = "material_matches"

    material_a: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    material_b: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    semantic_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    attribute_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    rule_score: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    final_confidence: Mapped[float | None] = mapped_column(
        Float,
        nullable=True,
    )

    status: Mapped[str] = mapped_column(
        String(50),
        nullable=False,
        default="pending",
    )