"""add role

Revision ID: 7b9bb47e3eae
Revises: 2168b1cc57de
Create Date: 2023-12-12 13:10:54.802276

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '7b9bb47e3eae'
down_revision: Union[str, None] = '2168b1cc57de'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('client', sa.Column('role', sa.String(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('client', 'role')
    # ### end Alembic commands ###
