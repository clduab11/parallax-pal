"""${message}

Revision ID: ${up_revision}
Revises: ${down_revision | comma,n}
Create Date: ${create_date}

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
${imports if imports else ""}

# revision identifiers, used by Alembic.
revision: str = ${repr(up_revision)}
down_revision: Union[str, None] = ${repr(down_revision)}
branch_labels: Union[str, Sequence[str], None] = ${repr(branch_labels)}
depends_on: Union[str, Sequence[str], None] = ${repr(depends_on)}


def upgrade() -> None:
    """
    Upgrade database to this revision.
    
    This function should contain SQLAlchemy commands to modify the database
    schema, such as:
    - Create tables (op.create_table)
    - Add columns (op.add_column)
    - Modify columns (op.alter_column)
    - Create indexes (op.create_index)
    - Add constraints (op.create_foreign_key)
    """
    ${upgrades if upgrades else "pass"}


def downgrade() -> None:
    """
    Downgrade database from this revision.
    
    This function should contain SQLAlchemy commands to reverse the changes
    made in the upgrade function, such as:
    - Drop tables (op.drop_table)
    - Remove columns (op.drop_column)
    - Revert column modifications (op.alter_column)
    - Drop indexes (op.drop_index)
    - Remove constraints (op.drop_constraint)
    
    IMPORTANT: The operations should be in reverse order of the upgrade function.
    """
    ${downgrades if downgrades else "pass"}