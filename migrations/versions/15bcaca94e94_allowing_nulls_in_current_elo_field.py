"""allowing nulls in current elo field

Revision ID: 15bcaca94e94
Revises: 8574e08bdf51
Create Date: 2026-03-10 20:32:54.429080

"""

from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa


# revision identifiers, used by Alembic.
revision: str = "15bcaca94e94"
down_revision: Union[str, None] = "8574e08bdf51"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # This migration was auto-generated with full table recreations that already
    # exist from earlier migrations. The tables & columns are already present, so
    # this is intentionally a no-op.
    pass


def downgrade() -> None:
    # No-op to match upgrade.
    pass
