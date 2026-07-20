"""add merchant and device enums to transactions

Revision ID: becd46a91eb9
Revises: 09b023cb69d8
Create Date: 2026-07-19 20:26:21.703603
"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql


# revision identifiers, used by Alembic.
revision: str = "becd46a91eb9"
down_revision: Union[str, Sequence[str], None] = "09b023cb69d8"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


merchant_category_enum = postgresql.ENUM(
    "SHOPPING",
    "TRAVEL",
    "FOOD",
    "HEALTHCARE",
    "UTILITIES",
    "ENTERTAINMENT",
    "EDUCATION",
    "FUEL",
    "OTHER",
    name="merchantcategory",
)

device_type_enum = postgresql.ENUM(
    "ANDROID",
    "IOS",
    "WINDOWS",
    "MACOS",
    "LINUX",
    "WEB",
    "OTHER",
    name="devicetype",
)


def upgrade() -> None:
    """Upgrade schema."""

    bind = op.get_bind()

    merchant_category_enum.create(bind, checkfirst=True)
    device_type_enum.create(bind, checkfirst=True)

    op.add_column(
        "transactions",
        sa.Column(
            "origin_country",
            sa.String(2),
            nullable=False,
            server_default="IN",
        ),
    )

    op.add_column(
        "transactions",
        sa.Column(
            "destination_country",
            sa.String(2),
            nullable=False,
            server_default="IN",
        ),
    )

    op.add_column(
        "transactions",
        sa.Column(
            "merchant_category",
            merchant_category_enum,
            nullable=False,
            server_default="OTHER",
        ),
    )

    op.add_column(
        "transactions",
        sa.Column(
            "device_type",
            device_type_enum,
            nullable=False,
            server_default="OTHER",
        ),
    )

    op.add_column(
        "transactions",
        sa.Column(
            "device_id_hash",
            sa.String(128),
            nullable=False,
            server_default="UNKNOWN",
        ),
    )

    op.alter_column("transactions", "origin_country", server_default=None)
    op.alter_column("transactions", "destination_country", server_default=None)
    op.alter_column("transactions", "merchant_category", server_default=None)
    op.alter_column("transactions", "device_type", server_default=None)
    op.alter_column("transactions", "device_id_hash", server_default=None)


def downgrade() -> None:
    """Downgrade schema."""

    op.drop_column("transactions", "device_id_hash")
    op.drop_column("transactions", "device_type")
    op.drop_column("transactions", "merchant_category")
    op.drop_column("transactions", "destination_country")
    op.drop_column("transactions", "origin_country")

    bind = op.get_bind()

    device_type_enum.drop(bind, checkfirst=True)
    merchant_category_enum.drop(bind, checkfirst=True)