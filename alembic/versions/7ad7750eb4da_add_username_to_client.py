"""add username to client

Revision ID: 7ad7750eb4da
Revises: 7b9bb47e3eae
Create Date: 2023-12-15 11:51:10.663830

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7ad7750eb4da'
down_revision: Union[str, None] = '7b9bb47e3eae'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    pass


def downgrade() -> None:
    pass
