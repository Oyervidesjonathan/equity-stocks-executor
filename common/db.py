from __future__ import annotations

import os
import psycopg
from urllib.parse import urlparse, urlunparse

RAW_DATABASE_URL = os.getenv("DATABASE_URL")
if not RAW_DATABASE_URL:
    raise RuntimeError("DATABASE_URL missing")

def _normalized_dsn(dsn: str) -> str:
    u = urlparse(dsn)
    if (u.path or "") in ("", "/"):
        return urlunparse(u._replace(path="/railway"))
    return dsn

DATABASE_URL = _normalized_dsn(RAW_DATABASE_URL)

def get_conn():
    return psycopg.connect(DATABASE_URL, autocommit=True)
