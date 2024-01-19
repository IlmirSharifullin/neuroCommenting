"""changed is_viewed_to_is_sent

Revision ID: b19a77596bf9
Revises: d4aef431a1d7
Create Date: 2024-01-12 19:05:35.678248

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b19a77596bf9'
down_revision: Union[str, None] = 'd4aef431a1d7'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('poem', sa.Column('is_sent', sa.Boolean(), nullable=True))
    op.drop_column('poem', 'is_viewed')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('poem', sa.Column('is_viewed', sa.BOOLEAN(), autoincrement=False, nullable=True))
    op.drop_column('poem', 'is_sent')
    # ### end Alembic commands ###