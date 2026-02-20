from dataclasses import dataclass
from datetime import datetime
from typing import Optional

import asyncpg


@dataclass
class ModerationResult:
    id: int
    item_id: int
    status: str
    is_violation: Optional[bool]
    probability: Optional[float]
    error_message: Optional[str]
    created_at: datetime
    processed_at: Optional[datetime]


class ModerationResultRepository:
    def __init__(self, conn: asyncpg.Connection) -> None:
        self._conn = conn

    async def create_pending(self, item_id: int) -> ModerationResult:
        row = await self._conn.fetchrow(
            """
            INSERT INTO moderation_results (item_id, status)
            VALUES ($1, 'pending')
            RETURNING id, item_id, status, is_violation, probability, error_message, created_at, processed_at
            """,
            item_id,
        )
        return self._row_to_model(row)

    async def update_result(
        self,
        task_id: int,
        *,
        status: str,
        is_violation: Optional[bool],
        probability: Optional[float],
        error_message: Optional[str],
    ) -> None:
        await self._conn.execute(
            """
            UPDATE moderation_results
            SET status = $2,
                is_violation = $3,
                probability = $4,
                error_message = $5,
                processed_at = NOW()
            WHERE id = $1
            """,
            task_id,
            status,
            is_violation,
            probability,
            error_message,
        )

    async def get(self, task_id: int) -> Optional[ModerationResult]:
        row = await self._conn.fetchrow(
            """
            SELECT id, item_id, status, is_violation, probability,
                   error_message, created_at, processed_at
            FROM moderation_results
            WHERE id = $1
            """,
            task_id,
        )
        if row is None:
            return None
        return self._row_to_model(row)

    async def delete_by_item_id(self, item_id: int) -> None:
        await self._conn.execute(
            """
            DELETE FROM moderation_results
            WHERE item_id = $1
            """,
            item_id,
        )

    @staticmethod
    def _row_to_model(row: asyncpg.Record) -> ModerationResult:
        return ModerationResult(
            id=row["id"],
            item_id=row["item_id"],
            status=row["status"],
            is_violation=row["is_violation"],
            probability=row["probability"],
            error_message=row["error_message"],
            created_at=row["created_at"],
            processed_at=row["processed_at"],
        )



