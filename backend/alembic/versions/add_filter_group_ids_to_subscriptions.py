"""add filter_group_ids to subscriptions and rss_subscriptions

Revision ID: add_filter_group_ids_001
Revises: filter_rule_group_001
Create Date: 2025-11-29 13:00:00.000000

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import mysql

# revision identifiers, used by Alembic.
revision = 'add_filter_group_ids_001'
down_revision = 'filter_rule_group_001'
branch_labels = None
depends_on = None


def upgrade():
    """升级数据库结构"""
    
    # 1. 为订阅表添加filter_group_ids字段
    op.add_column('subscriptions', sa.Column('filter_group_ids', sa.JSON(), nullable=True))
    
    # 2. 将现有的filter_groups数据迁移到filter_group_ids
    connection = op.get_bind()
    
    # 3. 为RSS订阅表添加user_id字段
    op.add_column('rss_subscriptions', sa.Column('user_id', sa.Integer(), nullable=True))
    
    # 4. 为RSS订阅表添加filter_group_ids字段
    op.add_column('rss_subscriptions', sa.Column('filter_group_ids', sa.JSON(), nullable=True))
    
    # 迁移订阅数据 - 兼容SQLite和MySQL
    if connection.dialect.name == 'mysql':
        connection.execute("""
            UPDATE subscriptions 
            SET filter_group_ids = CASE 
                WHEN filter_groups IS NOT NULL THEN filter_groups
                ELSE JSON_ARRAY()
            END
            WHERE filter_group_ids IS NULL
        """)
        connection.execute("""
            UPDATE rss_subscriptions 
            SET user_id = 1, filter_group_ids = JSON_ARRAY()
            WHERE user_id IS NULL OR filter_group_ids IS NULL
        """)
    else:
        # SQLite使用字符串字面量
        connection.execute("""
            UPDATE subscriptions 
            SET filter_group_ids = CASE 
                WHEN filter_groups IS NOT NULL THEN filter_groups
                ELSE '[]'
            END
            WHERE filter_group_ids IS NULL
        """)
        connection.execute("""
            UPDATE rss_subscriptions 
            SET user_id = 1, filter_group_ids = '[]'
            WHERE user_id IS NULL OR filter_group_ids IS NULL
        """)
    
    # 6. 将字段设置为非空（SQLite兼容方式）
    # 注意：SQLite不支持直接修改列约束，我们在Python层面处理默认值


def downgrade():
    """降级数据库结构"""
    
    # 1. 移除filter_group_ids和user_id字段
    op.drop_column('rss_subscriptions', 'filter_group_ids')
    op.drop_column('rss_subscriptions', 'user_id')
    op.drop_column('subscriptions', 'filter_group_ids')
