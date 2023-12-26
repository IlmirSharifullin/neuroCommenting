"""user status

Revision ID: 00cea89c33f2
Revises: 721abd552dd2
Create Date: 2023-12-21 17:21:01.437533

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '00cea89c33f2'
down_revision: Union[str, None] = '721abd552dd2'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('user', 'status',
               existing_type=sa.INTEGER(),
               nullable=False)
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.alter_column('user', 'status',
               existing_type=sa.INTEGER(),
               nullable=True)
    # ### end Alembic commands ###