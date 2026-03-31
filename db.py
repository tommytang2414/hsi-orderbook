"""
Database operations for HSI Order Book Collector
"""

import psycopg2
from datetime import datetime
from config import DB_PARAMS


def get_connection():
    return psycopg2.connect(**DB_PARAMS)


def setup_tables():
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
