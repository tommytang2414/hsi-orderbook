"""
Quick analysis queries — run standalone to review today's signals and metrics.
Usage: python query.py
"""

import db


def show_signals(limit: int = 20):
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT ts, direction, reason, obi, bid_zscore, ask_zscore, best_bid, best_ask
        FROM signals
        ORDER BY ts DESC
        LIMIT %s
        """,
        (limit,),
    )
    rows = cursor.fetchall()
    cursor.close()
    conn.close()

    print(f"\n{'='*80}")
    print(f"  Last {limit} signals")
    print(f"{'='*80}")
    for r in rows:
        ts, direction, reason, obi, bid_z, ask_z, best_bid, best_ask = r
        print(
            f"[{ts.strftime('%Y-%m-%d %H:%M:%S')}] {direction:5s}  "
            f"OBI={float(obi):.3f}  BidZ={float(bid_z) if bid_z else 'N/A':.2f}  "
            f"Bid={best_bid}  Ask={best_ask}"
        )
        print(f"  Reason: {reason}")
    print()


def show_obi_trend(limit: int = 50):
    """Print OBI trend to spot sustained imbalance visually."""
    conn = db.get_connection()
    cursor = conn.cursor()
    cursor.execute(
        """
        SELECT ts, obi, total_bid_vol, total_ask_vol
        FROM orderbook_metrics
        ORDER BY ts DESC
        LIMIT %s
        """,
        (limit,),
    )
    rows = list(reversed(cursor.fetchall()))
    cursor.close()
    conn.close()

    print(f"\nOBI Trend (last {limit} ticks)")
    print("-" * 60)
    for r in rows:
        ts, obi, bid_vol, ask_vol = r
        obi_f = float(obi)
        bar_len = int(abs(obi_f) * 20)
        bar = "#" * bar_len
        direction = ">" if obi_f > 0 else "<"
        print(
            f"[{ts.strftime('%H:%M:%S')}] OBI={obi_f:+.3f} {direction * bar_len}"
        )
    print()


if __name__ == "__main__":
    show_signals()
    show_obi_trend()
