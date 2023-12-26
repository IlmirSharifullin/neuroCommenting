"""add min/max answer time and proxy

Revision ID: b405a76e913e
Revises: 3b1efd0b9151
Create Date: 2023-12-20 17:18:50.989444

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'b405a76e913e'
down_revision: Union[str, None] = '3b1efd0b9151'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('client', sa.Column('proxy', sa.String(length=255), nullable=True))
    op.add_column('client', sa.Column('min_answer_time', sa.Integer(), nullable=True))
    op.add_column('client', sa.Column('max_answer_time', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('client', 'max_answer_time')
    op.drop_column('client', 'min_answer_time')
    op.drop_column('client', 'proxy')
    # ### end Alembic commands ###