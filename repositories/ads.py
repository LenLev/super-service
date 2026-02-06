from dataclasses import dataclass
from typing import Optional

import asyncpg


@dataclass
class Ad:
    id: int
    seller_id: int
    title: str
    description: str
    category: int
    images_qty: int


class AdRepository:

    def __init__(self, conn: asyncpg.Connection) -> None:
        self._conn = conn

    async def create(
        self,
        seller_id: int,
        title: str,
        description: str,
        category: int,
        images_qty: int,
    ) -> Ad:
        row = await self._conn.fetchrow(
            """
            INSERT INTO ads (seller_id, title, description, category, images_qty)
            VALUES ($1, $2, $3, $4, $5)
            RETURNING id
            """,
            seller_id,
            title,
            description,
            category,
            images_qty,
        )
        ad_id = row["id"]
        return Ad(
            id=ad_id,
            seller_id=seller_id,
            title=title,
            description=description,
            category=category,
            images_qty=images_qty,
        )

    async def get(self, ad_id: int) -> Optional[Ad]:
        row = await self._conn.fetchrow(
            """
            SELECT id, seller_id, title, description, category, images_qty
            FROM ads
            WHERE id = $1
            """,
            ad_id,
        )
        if row is None:
            return None

        return Ad(
            id=row["id"],
            seller_id=row["seller_id"],
            title=row["title"],
            description=row["description"],
            category=row["category"],
            images_qty=row["images_qty"],
        )


