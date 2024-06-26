"""add serial number

Revision ID: d4aef431a1d7
Revises: abc17aafaa4d
Create Date: 2024-01-12 16:53:37.876501

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'd4aef431a1d7'
down_revision: Union[str, None] = 'abc17aafaa4d'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('poem', sa.Column('serial_number', sa.Integer(), nullable=False))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('poem', 'serial_number')
    # ### end Alembic commands ###
