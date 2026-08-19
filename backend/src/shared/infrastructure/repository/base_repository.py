from abc import ABC, abstractmethod
from typing import Any, TypeVar

from sqlalchemy import text
from sqlalchemy.ext.asyncio import AsyncSession

from src.shared.domain.entity.base_entity import BaseEntity

TEntity = TypeVar("TEntity", bound=BaseEntity)


def _build_conditions(criteria: dict) -> tuple[str, dict]:
    params: dict[str, Any] = {}
    conditions: list[str] = []
    ops = {
        "gt": ">",
        "gte": ">=",
        "lt": "<",
        "lte": "<=",
        "ne": "!=",
        "in_": "IN",
        "ilike": "ILIKE",
    }

    for key, value in criteria.items():
        if "__" in key:
            field, op = key.rsplit("__", 1)
            if op in ops:
                conditions.append(f"{field} {ops[op]} :{key.replace('.', '_')}")
                if op == "in_":
                    params[key.replace(".", "_")] = tuple(value)
                elif op == "ilike":
                    params[key.replace(".", "_")] = f"%{value}%"
                else:
                    params[key.replace(".", "_")] = value
                continue

        if value is None:
            conditions.append(f"{key} IS NULL")
        else:
            conditions.append(f"{key} = :{key.replace('.', '_')}")
            params[key.replace(".", "_")] = value

    return " AND ".join(conditions), params


class BaseRepository[TEntity](ABC):
    auto_filter_deleted: bool = False

    def __init__(self, session: AsyncSession, table_name: str):
        self.session = session
        self.table_name = table_name

    @abstractmethod
    def to_row(self, entity: TEntity) -> dict: ...

    @abstractmethod
    def to_entity(self, row: dict) -> TEntity: ...

    async def _get_row_map_by_id(self, entity_id: int) -> dict | None:
        sql = text(f"SELECT * FROM {self.table_name} WHERE id = :id LIMIT 1")
        result = await self.session.execute(sql, {"id": entity_id})
        row = result.mappings().one_or_none()
        return dict(row) if row else None

    async def add(self, entity: TEntity, *, audit: bool = True) -> TEntity:
        row = {k: v for k, v in self.to_row(entity).items() if k != "id"}
        columns = ", ".join(row.keys())
        placeholders = ", ".join(f":{k}" for k in row.keys())
        sql = text(
            f"INSERT INTO {self.table_name} ({columns}) VALUES ({placeholders}) RETURNING *"
        )
        result = await self.session.execute(sql, row)
        await self.session.flush()
        inserted = result.mappings().one()
        return self.to_entity(dict(inserted))

    async def get_by_id(self, entity_id: int) -> TEntity | None:
        return await self.get_by(id=entity_id)

    async def get_by_uuid(self, entity_uuid: str) -> TEntity | None:
        return await self.get_by(uuid=entity_uuid)

    async def get_by(self, **criteria) -> TEntity | None:
        if self.auto_filter_deleted and "deleted_at" not in criteria:
            criteria["deleted_at"] = None
        conditions, params = _build_conditions(criteria)
        sql = text(
            f"SELECT * FROM {self.table_name} WHERE {conditions} LIMIT 1"
        )
        result = await self.session.execute(sql, params)
        row = result.mappings().one_or_none()
        return self.to_entity(dict(row)) if row else None

    async def update(self, entity: TEntity, *, audit: bool = True) -> TEntity:
        entity_id = getattr(entity, "id", None)
        row = self.to_row(entity)
        updates = {k: v for k, v in row.items() if k != "id"}
        set_clause = ", ".join(f"{k} = :{k}" for k in updates)
        sql = text(
            f"UPDATE {self.table_name} SET {set_clause} WHERE id = :id RETURNING *"
        )
        result = await self.session.execute(sql, {**updates, "id": entity_id})
        await self.session.flush()
        updated = result.mappings().one_or_none()
        if updated is None:
            from src.shared.exceptions.base_exceptions import ServerError
            raise ServerError(error=f"Entity with id={entity_id} not found in {self.table_name}")
        return self.to_entity(dict(updated))

    async def delete(self, entity_id: int, audit: bool = True) -> None:
        sql = text(f"DELETE FROM {self.table_name} WHERE id = :id")
        await self.session.execute(sql, {"id": entity_id})

    async def filter(self, **criteria) -> list[TEntity]:
        if self.auto_filter_deleted and "deleted_at" not in criteria:
            criteria["deleted_at"] = None
        if not criteria:
            sql = text(f"SELECT * FROM {self.table_name}")
            result = await self.session.execute(sql)
        else:
            conditions, params = _build_conditions(criteria)
            sql = text(
                f"SELECT * FROM {self.table_name} WHERE {conditions}"
            )
            result = await self.session.execute(sql, params)
        rows = result.mappings().all()
        return [self.to_entity(dict(row)) for row in rows]
