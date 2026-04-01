import sqlite3
from contextlib import contextmanager
from datetime import datetime, timedelta, timezone
from pathlib import Path

DB_PATH = Path(__file__).parent.parent / "data" / "digest.db"

KST = timezone(timedelta(hours=9))


def init_db() -> None:
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    with _conn() as conn:
        conn.execute("""
            CREATE TABLE IF NOT EXISTS sent_urls (
                url      TEXT PRIMARY KEY,
                sent_at  TEXT NOT NULL
            )
        """)


@contextmanager
def _conn():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    try:
        yield conn
        conn.commit()
    finally:
        conn.close()


def is_sent(url: str, within_days: int = 7) -> bool:
    """최근 within_days일 이내에 전송된 URL이면 True."""
    cutoff = (datetime.now(KST) - timedelta(days=within_days)).isoformat()
    with _conn() as conn:
        row = conn.execute(
            "SELECT 1 FROM sent_urls WHERE url = ? AND sent_at >= ?",
            (url, cutoff),
        ).fetchone()
    return row is not None


def mark_sent(url: str) -> None:
    """URL을 전송 이력에 기록한다."""
    with _conn() as conn:
        conn.execute(
            "INSERT OR REPLACE INTO sent_urls (url, sent_at) VALUES (?, ?)",
            (url, datetime.now(KST).isoformat()),
        )
