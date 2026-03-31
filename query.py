"""
Query order book snapshots from database.
Usage: python query.py
"""

import db


def show_snapshots(limit: int = 20):
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("""
        SELECT ts, level, bid, bid_volume, ask, ask_volume
        FROM orderbook_snapshots
        ORDER BY ts DESC
        LIMIT %s
    """, (limit,))
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    print(f"\nLast {limit} order book snapshots")
    print("=" * 70)
    for r in rows:
        ts, level, bid, bid_vol, ask, ask_vol = r
        print(f"[{ts.strftime('%Y-%m-%d %H:%M:%S')}] L{level} Bid:{bid}({bid_vol}) Ask:{ask}({ask_vol})")
    print()


def show_summary():
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM orderbook_snapshots")
    total = cursor.fetchone()[0]
    cursor.execute("SELECT MIN(ts), MAX(ts) FROM orderbook_snapshots")
    time_range = cursor.fetchall()[0]
    cursor.close()
    conn.close()

    print(f"\nSummary")
    print("=" * 70)
    print(f"Total snapshots: {total}")
    print(f"Time range: {time_range[0]} to {time_range[1]}")
    print()


if __name__ == "__main__":
    show_summary()
    show_snapshots()
