from pathlib import Path
from typing import Any, AsyncIterator, Optional

import asyncpg
import yaml
from contextlib import asynccontextmanager


BASE_DIR = Path(__file__).resolve().parent
PGMIGRATE_CONFIG_PATH = BASE_DIR / "migrations" / "pgmigrate.yml"

_pool: Optional[asyncpg.pool.Pool] = None
_pg_config: Optional[dict[str, Any]] = None


def _load_pg_config() -> dict[str, Any]:
    global _pg_config

    if _pg_config is None:
        with PGMIGRATE_CONFIG_PATH.open("r", encoding="utf-8") as f:
            raw = yaml.safe_load(f)

        conn_cfg = raw.get("connection", {})
        _pg_config = {
            "host": conn_cfg["host"],
            "port": conn_cfg["port"],
            "user": conn_cfg["username"],
            "password": conn_cfg["password"],
            "database": conn_cfg["database"],
        }

    return _pg_config


async def init_db() -> None:
    global _pool

    if _pool is None:
        config = _load_pg_config()
        _pool = await asyncpg.create_pool(**config)


async def close_db() -> None:
    global _pool

    if _pool is not None:
        await _pool.close()
        _pool = None


@asynccontextmanager
async def get_connection() -> AsyncIterator[asyncpg.Connection]:
    if _pool is None:
        await init_db()

    assert _pool is not None

    async with _pool.acquire() as conn:
        yield conn
