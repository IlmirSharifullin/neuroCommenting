"""add answer_posts

Revision ID: abafcdeeb9f1
Revises: a619e4274e62
Create Date: 2023-12-28 09:42:30.802885

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = 'abafcdeeb9f1'
down_revision: Union[str, None] = 'a619e4274e62'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('client', sa.Column('answer_posts', sa.Integer(), nullable=True))
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_column('client', 'answer_posts')
    # ### end Alembic commands ###
