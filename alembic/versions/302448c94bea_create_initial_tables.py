"""Create initial tables

Revision ID: 302448c94bea
Revises:
Create Date: 2024-01-09 14:52:19.784581

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = '302448c94bea'
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "users",
        sa.Column("id", sa.Integer(), nullable=False, primary_key=True),
        sa.Column("corp_id", sa.String(length=255), nullable=False),
        sa.Column("password", sa.String(length=255), nullable=False),
        sa.Column("created_at", sa.DateTime, server_default=sa.func.now()),
        sa.Column("updated_at", sa.DateTime, server_default=sa.func.now(), server_onupdate=sa.func.now()),
        mysql_charset='utf8mb4'
    )

    op.create_table(
        'billing_info',
        sa.Column('id', sa.Integer(), nullable=False, primary_key=True),

        # type: 1-request, 2-result
        sa.Column('type', sa.String(length=255), nullable=True),

        # res_tcode
        sa.Column('res_tcode', sa.String(length=255), nullable=True),

        # res_scode
        sa.Column('res_scode', sa.String(length=255), nullable=True),

        # res_sdiv
        sa.Column('res_sdiv', sa.String(length=255), nullable=True),

        # inquiry_no
        sa.Column('inquiry_no', sa.String(length=255), nullable=True),

        # torihiki_detail
        sa.Column('torihiki_detail', sa.String(length=255), nullable=True),

        # torihiki_amount
        sa.Column('torihiki_amount', sa.Integer(), nullable=True),

        # payment_date
        sa.Column('payment_date', sa.String(length=255), nullable=True),

        # barcode_inf
        sa.Column('barcode_inf', sa.String(length=255), nullable=True),

        # free_col
        sa.Column('free_col', sa.String(length=255), nullable=True),

        # link_url
        sa.Column('link_url', sa.String(length=255), nullable=True),

        # sms_type
        sa.Column('sms_type', sa.String(length=255), nullable=True),

        # sms_retype
        sa.Column('sms_retype', sa.String(length=255), nullable=True),

        # sms_phone_num
        sa.Column('sms_phone_num', sa.String(length=255), nullable=True),

        # get_user_num
        sa.Column('get_user_num', sa.String(length=255), nullable=True),

        # sms_msg
        sa.Column('sms_msg', sa.String(length=255), nullable=True),

        # barcode_url
        sa.Column('barcode_url', sa.String(length=255), nullable=True),

        sa.Column('created_at', sa.DateTime, server_default=sa.func.now()),
        sa.Column('updated_at', sa.DateTime, server_default=sa.func.now(), server_onupdate=sa.func.now()),

        mysql_charset='utf8mb4'
    )


def downgrade() -> None:
    op.drop_table('billing_info')
