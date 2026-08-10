"""UP 主采集状态记录与异常分类。"""

from datetime import datetime, timedelta
from typing import Optional, Tuple

import pymysql
from bilibili_api.exceptions import ApiException, NetworkException

from config import database_config


COOLDOWN_MINUTES = {
    403: 360,
    412: 360,
    429: 60,
}


def classify_exception(exception: Exception) -> Tuple[str, Optional[int]]:
    """将平台拒绝与普通服务异常分开。"""
    code = getattr(exception, "status", None)
    if code is None:
        code = getattr(exception, "code", None)
    if code in (403, 412, 429):
        return "risk_blocked", code
    if isinstance(exception, ApiException) and code == -404:
        return "not_found", code
    return "provider_error", code


def ensure_state_table() -> None:
    """按需创建采集状态表。"""
    connection = pymysql.connect(**database_config())
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                CREATE TABLE IF NOT EXISTS up_crawl_state (
                    uid BIGINT NOT NULL PRIMARY KEY,
                    status VARCHAR(32) NOT NULL,
                    source VARCHAR(64) NOT NULL,
                    error_code INT NULL,
                    last_error TEXT NULL,
                    attempts INT NOT NULL DEFAULT 0,
                    fetched_at DATETIME NULL,
                    next_retry_at DATETIME NULL,
                    updated_at DATETIME NOT NULL DEFAULT CURRENT_TIMESTAMP
                        ON UPDATE CURRENT_TIMESTAMP
                ) ENGINE=InnoDB DEFAULT CHARSET=utf8mb4
                """
            )
        connection.commit()
    finally:
        connection.close()


def record_crawl_state(
    uid: int,
    status: str,
    source: str,
    error_code: Optional[int] = None,
    last_error: Optional[str] = None,
) -> None:
    """写入一次采集状态，并为风控错误设置冷却时间。"""
    ensure_state_table()
    now = datetime.now()
    minutes = COOLDOWN_MINUTES.get(error_code or -1)
    next_retry = now + timedelta(minutes=minutes) if minutes else None
    fetched_at = now if status in ("success", "partial") else None
    connection = pymysql.connect(**database_config())
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                """
                INSERT INTO up_crawl_state
                    (uid, status, source, error_code, last_error, attempts,
                     fetched_at, next_retry_at)
                VALUES (%s, %s, %s, %s, %s, 1, %s, %s)
                ON DUPLICATE KEY UPDATE
                    status = VALUES(status), source = VALUES(source),
                    error_code = VALUES(error_code), last_error = VALUES(last_error),
                    attempts = attempts + 1, fetched_at = VALUES(fetched_at),
                    next_retry_at = VALUES(next_retry_at)
                """,
                (uid, status, source, error_code, last_error, fetched_at, next_retry),
            )
        connection.commit()
    finally:
        connection.close()


def is_retry_allowed(uid: int) -> bool:
    """判断 UID 是否已结束风控冷却期。"""
    ensure_state_table()
    connection = pymysql.connect(**database_config())
    try:
        with connection.cursor() as cursor:
            cursor.execute(
                "SELECT next_retry_at FROM up_crawl_state WHERE uid = %s", (uid,)
            )
            row = cursor.fetchone()
        return retry_time_passed(row[0] if row else None, datetime.now())
    finally:
        connection.close()


def retry_time_passed(next_retry_at: Optional[datetime], now: datetime) -> bool:
    """判断状态记录中的下次重试时间是否已到。"""
    return next_retry_at is None or next_retry_at <= now
