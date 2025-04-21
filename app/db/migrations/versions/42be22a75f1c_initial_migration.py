"""Initial migration with user, activity, stream, and PR tables

Revision ID: 42be22a75f1c
Revises: 
Create Date: 2025-04-20

"""
from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

# revision identifiers, used by Alembic.
revision = '42be22a75f1c'
down_revision = None
branch_labels = None
depends_on = None


def upgrade() -> None:
    # Create users table
    op.create_table('users',
        sa.Column('id', postgresql.UUID(), nullable=False),
        sa.Column('strava_athlete_id', sa.Integer(), nullable=True),
        sa.Column('access_token', sa.String(), nullable=True),
        sa.Column('refresh_token', sa.String(), nullable=True),
        sa.Column('token_expires_at', sa.DateTime(), nullable=True),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_users_strava_athlete_id'), 'users', ['strava_athlete_id'], unique=True)

    # Create activities table
    op.create_table('activities',
        sa.Column('id', postgresql.UUID(), nullable=False),
        sa.Column('user_id', postgresql.UUID(), nullable=True),
        sa.Column('strava_id', sa.BigInteger(), nullable=True),
        sa.Column('name', sa.String(), nullable=True),
        sa.Column('start_time', sa.DateTime(), nullable=True),
        sa.Column('distance_m', sa.Float(), nullable=True),
        sa.Column('moving_time_s', sa.Integer(), nullable=True),
        sa.Column('elev_gain_m', sa.Float(), nullable=True),
        sa.Column('avg_power', sa.Float(), nullable=True),
        sa.Column('avg_hr', sa.Float(), nullable=True),
        sa.Column('tss', sa.Float(), nullable=True),
        sa.Column('np', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_activities_strava_id'), 'activities', ['strava_id'], unique=True)

    # Create streams table
    op.create_table('streams',
        sa.Column('id', postgresql.UUID(), nullable=False),
        sa.Column('activity_id', postgresql.UUID(), nullable=True),
        sa.Column('timestamp', sa.DateTime(), nullable=True),
        sa.Column('lat', sa.Float(), nullable=True),
        sa.Column('lon', sa.Float(), nullable=True),
        sa.Column('altitude', sa.Float(), nullable=True),
        sa.Column('distance', sa.Float(), nullable=True),
        sa.Column('velocity_smooth', sa.Float(), nullable=True),
        sa.Column('heartrate', sa.Integer(), nullable=True),
        sa.Column('cadence', sa.Integer(), nullable=True),
        sa.Column('watts', sa.Integer(), nullable=True),
        sa.Column('temp', sa.Float(), nullable=True),
        sa.Column('moving', sa.Integer(), nullable=True),
        sa.Column('grade_smooth', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['activity_id'], ['activities.id'], ),
        sa.PrimaryKeyConstraint('id')
    )
    op.create_index(op.f('ix_streams_timestamp'), 'streams', ['timestamp'], unique=False)

    # Create PR records table
    op.create_table('pr_records',
        sa.Column('id', postgresql.UUID(), nullable=False),
        sa.Column('user_id', postgresql.UUID(), nullable=True),
        sa.Column('activity_id', postgresql.UUID(), nullable=True),
        sa.Column('segment_type', sa.String(), nullable=True),
        sa.Column('segment_value', sa.Integer(), nullable=True),
        sa.Column('start_time', sa.DateTime(), nullable=True),
        sa.Column('end_time', sa.DateTime(), nullable=True),
        sa.Column('avg_power', sa.Float(), nullable=True),
        sa.Column('avg_hr', sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(['activity_id'], ['activities.id'], ),
        sa.ForeignKeyConstraint(['user_id'], ['users.id'], ),
        sa.PrimaryKeyConstraint('id')
    )


def downgrade() -> None:
    op.drop_table('pr_records')
    op.drop_index(op.f('ix_streams_timestamp'), table_name='streams')
    op.drop_table('streams')
    op.drop_index(op.f('ix_activities_strava_id'), table_name='activities')
    op.drop_table('activities')
    op.drop_index(op.f('ix_users_strava_athlete_id'), table_name='users')
    op.drop_table('users')