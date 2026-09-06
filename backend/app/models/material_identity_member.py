from sqlalchemy import BigInteger
from sqlalchemy.orm import Mapped, mapped_column

from app.models.material import Base


class MaterialIdentityMember(Base):
    __tablename__ = "material_identity_members"

    identity_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )

    material_id: Mapped[int] = mapped_column(
        BigInteger,
        primary_key=True,
    )