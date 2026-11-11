"""Enable pgvector; backend owns schema migrations."""
from alembic import op

deployment_policy = "expand"
revision = "0001"
down_revision = None
branch_labels = None
depends_on = None


def upgrade():
    op.execute("CREATE EXTENSION IF NOT EXISTS vector")


def downgrade():
    raise RuntimeError("Destructive downgrade requires a reviewed restore plan")
