from dataclasses import dataclass
from typing import Optional

import asyncpg


@dataclass
class User:
    id: int
    is_verified_seller: bool


class UserRepository:
    def __init__(self, conn: asyncpg.Connection) -> None:
        self._conn = conn

    async def create(self, is_verified_seller: bool) -> User:
        user_id = await self._conn.fetchval(
            "INSERT INTO users (is_verified_seller) VALUES ($1) RETURNING id",
            is_verified_seller,
        )
        return User(id=user_id, is_verified_seller=is_verified_seller)

    async def get(self, user_id: int) -> Optional[User]:
        row = await self._conn.fetchrow(
            "SELECT id, is_verified_seller FROM users WHERE id = $1",
            user_id,
        )
        if row is None:
            return None
        return User(
            id=row["id"],
            is_verified_seller=bool(row["is_verified_seller"]),
        )


