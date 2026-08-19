import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects.postgresql import TIMESTAMP
from sqlalchemy.exc import OperationalError


class BaseMigration:
    """
    This class acts as a base for every migration files
    """

    # attributes
    table_name: str
    fields: list
    added_column: list
    create_new_table: bool
    revision: str
    down_revision: str | None

    def __init__(self, revision: str, down_revision: str | None):
        self.revision = revision
        self.down_revision = down_revision
        self.fields = []
        self.added_column = []
        self.create_whole_table = True  # by default set the create table true

    def add_column(self, col: sa.Column):
        """
        This function is used to add column
        """
        self.added_column.append(col)

    def upgrade(self) -> None:
        """
        This function is going to create a table
        """
        if not self.table_name:
            raise OperationalError(
                "table name must be set", params=None, orig=BaseException()
            )
        if self.create_whole_table:
            if not self.fields:
                raise OperationalError(
                    "table fields must be set", params=None, orig=BaseException()
                )
            op.create_table(self.table_name, *self.fields)
            return None

        if not self.added_column:
            raise OperationalError(
                "added columns must be set", params=None, orig=BaseException()
            )
        for col in self.added_column:
            op.add_column(self.table_name, col)
        return None

    def downgrade(self) -> None:
        """
        This function is going to drop a table
        """
        if not self.table_name:
            raise OperationalError(
                "table name must be set", params=None, orig=BaseException()
            )
        if self.create_whole_table:
            op.drop_table(self.table_name)
            return None

        for col in reversed(self.added_column):  # FIFO
            op.drop_column(self.table_name, col.name)
        return None

    def integer(self, name: str, **kwargs):
        co = sa.Column(name, sa.Integer(), **kwargs)
        self.fields.append(co)
        return co

    def biginteger(self, name: str, **kwargs):
        co = sa.Column(name, sa.BigInteger(), **kwargs)
        self.fields.append(co)
        return co

    def string(self, name: str, length=255, nullable=True, default=None, **kwargs):
        co = sa.Column(
            name, sa.String(length=length), nullable=nullable, default=default, **kwargs
        )
        self.fields.append(co)
        return co

    def text(self, name: str, nullable=True, default=None, **kwargs):
        co = sa.Column(name, sa.Text(), nullable=nullable, default=default, **kwargs)
        self.fields.append(co)
        return co

    def boolean(self, name: str, **kwargs):
        co = sa.Column(name, sa.Boolean(), **kwargs)
        self.fields.append(co)
        return co

    def json(self, name: str, **kwargs):
        co = sa.Column(name, sa.JSON(), **kwargs)
        self.fields.append(co)
        return co

    def array(self, name: str, **kwargs):
        co = sa.Column(name, sa.ARRAY(sa.String), **kwargs)
        self.fields.append(co)

    def primary_key(self, name: str = "id", **kwargs):
        co = sa.Column(name, sa.Integer(), primary_key=True, **kwargs)
        self.fields.append(co)
        return co

    def foreign(self, name: str, table: str, ondelete=None, **kwargs):
        kwargs.setdefault("nullable", True)
        table = f"{table}.id"  # by default it will be id
        co = sa.Column(
            name,
            sa.Integer(),
            sa.ForeignKey(table, ondelete=ondelete),
            **kwargs,
        )
        self.fields.append(co)
        return co

    def date_time(self, name: str, **kwargs):
        co = sa.Column(name, sa.DateTime(timezone=True), **kwargs)
        self.fields.append(co)
        return co

    def date(self, name: str, **kwargs):
        co = sa.Column(name, sa.Date, **kwargs)
        self.fields.append(co)
        return co

    def unique_constraint(self, *columns, name: str | None = None):
        co = sa.UniqueConstraint(*columns, name=name)
        self.fields.append(co)
        return co

    def timestamp_columns(self):
        self.date_time(
            name="created_at",
            nullable=False,
            server_default=sa.func.now(),
        )
        self.date_time(name="updated_at", nullable=True)

    def base_columns(self):
        self.primary_key(name="id")
        self.fields.append(
            sa.Column(
                "uuid",
                sa.String(length=255),
                nullable=False,
                unique=True,
                index=True,
            )
        )
        self.timestamp_columns()

    def bulk_insert_data(self, rows: list[dict]):
        if not self.table_name:
            raise OperationalError(
                "table name must be set", params=None, orig=BaseException()
            )
        if not rows or not isinstance(rows, list):
            raise ValueError(
                "bulk_insert_data requires a non-empty list of dictionaries"
            )

        metadata = sa.MetaData()
        cols = [col for col in self.fields if isinstance(col, sa.Column)]
        table = sa.Table(self.table_name, metadata, *cols)

        op.bulk_insert(table, rows)

    def float(self, name: str, **kwargs):
        co = sa.Column(name, sa.Float(), **kwargs)
        self.fields.append(co)
        return co

    def audit_mixin_columns(self):
        self.fields.append(
            sa.Column(
                "created_by_id",
                sa.Integer(),
                sa.ForeignKey("sys_auth_users.id"),
                nullable=True,
            )
        )
        self.fields.append(
            sa.Column(
                "updated_by_id",
                sa.Integer(),
                sa.ForeignKey("sys_auth_users.id"),
                nullable=True,
            )
        )

    def tenant_mixin_columns(self):
        self.fields.append(
            sa.Column(
                "organization_id",
                sa.Integer(),
                sa.ForeignKey("org_organizations.id", ondelete="CASCADE"),
                nullable=False,
                index=True,
            )
        )

    def soft_delete_mixin_column(self):
        self.fields.append(
            sa.Column(
                "deleted_at",
                TIMESTAMP(timezone=True),
                nullable=True,
            )
        )
