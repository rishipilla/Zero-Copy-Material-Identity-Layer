from sqlalchemy import BigInteger, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.models.material import Base


class MaterialAttribute(Base):
    __tablename__ = "material_attributes"

    material_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    attribute_name: Mapped[str] = mapped_column(
        String(255),
        primary_key=True,
    )

    attribute_value: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    normalized_value: Mapped[str | None] = mapped_column(
        Text,
        nullable=True,
    )

    unit: Mapped[str | None] = mapped_column(
        String(100),
        nullable=True,
    )