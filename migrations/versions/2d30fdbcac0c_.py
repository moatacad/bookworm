"""empty message

Revision ID: 2d30fdbcac0c
Revises: 5ffe17823a12
Create Date: 2023-09-20 13:21:25.870543

"""
from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision = '2d30fdbcac0c'
down_revision = '5ffe17823a12'
branch_labels = None
depends_on = None


def upgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.create_table('contactus',
    sa.Column('contact_id', sa.Integer(), autoincrement=True, nullable=False),
    sa.Column('contact_email', sa.String(length=100), nullable=False),
    sa.PrimaryKeyConstraint('contact_id')
    )
    # ### end Alembic commands ###


def downgrade():
    # ### commands auto generated by Alembic - please adjust! ###
    op.drop_table('contactus')
    # ### end Alembic commands ###