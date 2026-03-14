from typing import Optional

import asyncpg


class AccountStorage:
    def __init__(self, conn: asyncpg.Connection) -> None:
        self._conn = conn

    async def create(self, login: str, password: str) -> int:
        return await self._conn.fetchval(
            """
            INSERT INTO account (login, password)
            VALUES ($1, $2)
            RETURNING id
            """,
            login,
            password,
        )

    async def get_by_id(self, account_id: int) -> Optional[asyncpg.Record]:
        return await self._conn.fetchrow(
            """
            SELECT id, login, password, is_blocked
            FROM account
            WHERE id = $1
            """,
            account_id,
        )

    async def delete(self, account_id: int) -> None:
        await self._conn.execute(
            """
            DELETE FROM account
            WHERE id = $1
            """,
            account_id,
        )

    async def block(self, account_id: int) -> None:
        await self._conn.execute(
            """
            UPDATE account
            SET is_blocked = TRUE
            WHERE id = $1
            """,
            account_id,
        )

    async def get_by_login_password(self, login: str, password: str) -> Optional[asyncpg.Record]:
        return await self._conn.fetchrow(
            """
            SELECT id, login, password, is_blocked
            FROM account
            WHERE login = $1 AND password = $2
            """,
            login,
            password,
        )
