from dataclasses import dataclass
from typing import Optional

import asyncpg

from repositories.accounts_storage import AccountStorage


@dataclass
class Account:
    id: int
    login: str
    password: str
    is_blocked: bool


class AccountRepository:
    def __init__(self, conn: asyncpg.Connection) -> None:
        self._storage = AccountStorage(conn)

    async def create(self, login: str, password: str) -> Account:
        account_id = await self._storage.create(login=login, password=password)
        account = await self.get_by_id(account_id)
        assert account is not None
        return account

    async def get_by_id(self, account_id: int) -> Optional[Account]:
        row = await self._storage.get_by_id(account_id)
        if row is None:
            return None
        return self._row_to_model(row)

    async def delete(self, account_id: int) -> None:
        await self._storage.delete(account_id)

    async def block(self, account_id: int) -> None:
        await self._storage.block(account_id)

    async def get_by_login_password(self, login: str, password: str) -> Optional[Account]:
        row = await self._storage.get_by_login_password(login=login, password=password)
        if row is None:
            return None
        return self._row_to_model(row)

    @staticmethod
    def _row_to_model(row: asyncpg.Record) -> Account:
        return Account(
            id=row["id"],
            login=row["login"],
            password=row["password"],
            is_blocked=bool(row["is_blocked"]),
        )
