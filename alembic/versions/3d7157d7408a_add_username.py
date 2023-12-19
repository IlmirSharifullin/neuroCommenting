"""add username

Revision ID: 3d7157d7408a
Revises: 7ad7750eb4da
Create Date: 2023-12-19 17:39:51.637215

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '3d7157d7408a'
down_revision: Union[str, None] = '7ad7750eb4da'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
