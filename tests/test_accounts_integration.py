import pytest

from db import get_connection
from repositories.accounts import AccountRepository


@pytest.mark.integration
@pytest.mark.asyncio
async def test_account_repository_crud_and_lookup() -> None:
    async with get_connection() as conn:
        repo = AccountRepository(conn)

        account = await repo.create(login="repo_user", password="repo_pass")
        assert account.id is not None
        assert account.login == "repo_user"
        assert account.is_blocked is False

        fetched = await repo.get_by_id(account.id)
        assert fetched is not None
        assert fetched.id == account.id

        by_credentials = await repo.get_by_login_password("repo_user", "repo_pass")
        assert by_credentials is not None
        assert by_credentials.id == account.id

        await repo.block(account.id)
        blocked = await repo.get_by_id(account.id)
        assert blocked is not None
        assert blocked.is_blocked is True

        await repo.delete(account.id)
        deleted = await repo.get_by_id(account.id)
        assert deleted is None
