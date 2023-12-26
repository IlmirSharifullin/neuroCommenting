"""add invite hash, user table, session-user relation

Revision ID: 721abd552dd2
Revises: b405a76e913e
Create Date: 2023-12-21 17:13:06.648759

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '721abd552dd2'
down_revision: Union[str, None] = 'b405a76e913e'
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('user',
    sa.Column('chat_id', sa.Integer(), nullable=False),
    sa.Column('status', sa.Integer(), nullable=True),
    sa.PrimaryKeyConstraint('chat_id')
    )
    op.add_column('channel', sa.Column('invite_hash', sa.String(length=255), nullable=True))
    op.add_column('client', sa.Column('owner_id', sa.Integer(), nullable=True))
    op.create_foreign_key(None, 'client', 'user', ['owner_id'], ['chat_id'])
    op.drop_column('client', 'sex')
    op.drop_column('client', 'photo_path')
    # ### end Alembic commands ###


def downgrade() -> None:
    # ### commands auto generated by Alembic - please adjust! ###
    op.add_column('client', sa.Column('photo_path', sa.VARCHAR(length=255), autoincrement=False, nullable=True))
    op.add_column('client', sa.Column('sex', sa.SMALLINT(), autoincrement=False, nullable=True))
    op.drop_constraint(None, 'client', type_='foreignkey')
    op.drop_column('client', 'owner_id')
    op.drop_column('channel', 'invite_hash')
    op.drop_table('user')
    # ### end Alembic commands ###