"""
Database operations for HSI Order Book Analyzer
"""

import psycopg2
from datetime import datetime
from config import DB_PARAMS


def get_connection():
    return psycopg2.connect(**DB_PARAMS)


def setup_tables():
    """Create tables if they don't exist."""
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orderbook_snapshots (
                id SERIAL PRIMARY KEY,
                ts TIMESTAMP NOT NULL,
                level INTEGER NOT NULL,
                bid NUMERIC,
                bid_volume NUMERIC,
                ask NUMERIC,
                ask_volume NUMERIC
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS orderbook_metrics (
                id SERIAL PRIMARY KEY,
                ts TIMESTAMP NOT NULL,
                best_bid NUMERIC,
                best_ask NUMERIC,
                spread NUMERIC,
                total_bid_vol NUMERIC,
                total_ask_vol NUMERIC,
                obi NUMERIC,
                bid_zscore NUMERIC,
                ask_zscore NUMERIC
            );
        """)
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS signals (
                id SERIAL PRIMARY KEY,
                ts TIMESTAMP NOT NULL,
                direction VARCHAR(5) NOT NULL,
                reason TEXT,
                obi NUMERIC,
                bid_zscore NUMERIC,
                ask_zscore NUMERIC,
                best_bid NUMERIC,
                best_ask NUMERIC
            );
        """)
        conn.commit()
        print("[DB] Tables ready.")
    except Exception as e:
        conn.rollback()
        raise
    finally:
        cursor.close()
        conn.close()


def insert_snapshot(ts: datetime, levels: list[dict]):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.executemany(
            "INSERT INTO orderbook_snapshots (ts, level, bid, bid_volume, ask, ask_volume) VALUES (%s, %s, %s, %s, %s, %s)",
            [(ts, l["level"], l["bid"], l["bid_volume"], l["ask"], l["ask_volume"]) for l in levels],
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def insert_metrics(ts: datetime, m: dict):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO orderbook_metrics
                (ts, best_bid, best_ask, spread, total_bid_vol, total_ask_vol, obi, bid_zscore, ask_zscore)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (ts, m["best_bid"], m["best_ask"], m["spread"],
             m["total_bid_vol"], m["total_ask_vol"],
             m["obi"], m["bid_zscore"], m["ask_zscore"]),
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()


def insert_signal(ts: datetime, direction: str, reason: str, m: dict):
    conn = get_connection()
    cursor = conn.cursor()
    try:
        cursor.execute(
            """
            INSERT INTO signals (ts, direction, reason, obi, bid_zscore, ask_zscore, best_bid, best_ask)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
            """,
            (ts, direction, reason, m["obi"], m["bid_zscore"], m["ask_zscore"], m["best_bid"], m["best_ask"]),
        )
        conn.commit()
    finally:
        cursor.close()
        conn.close()
