"""
Futu OpenD order book collector for HSI futures.
Streams real-time order book data, computes metrics, and generates signals.
"""

import time
from datetime import datetime, time as dtime
import pytz
from futu import OpenQuoteContext, OrderBookHandlerBase, SubType, RET_OK, RET_ERROR

from config import FUTU_HOST, FUTU_PORT, HSI_SYMBOL, ORDER_BOOK_LEVELS, SIGNAL_COOLDOWN_SEC
from analyzer import compute_metrics, generate_signal, reset_buffers
import db

HK_TZ = pytz.timezone("Asia/Hong_Kong")

MARKET_MORNING_START = dtime(9, 30)
MARKET_MORNING_END = dtime(12, 0)
MARKET_AFTERNOON_START = dtime(13, 0)
MARKET_AFTERNOON_END = dtime(16, 0)
CLEANUP_INTERVAL_SEC = 300


def is_market_open() -> bool:
    now = datetime.now(HK_TZ)
    if now.weekday() >= 5:
        return False
    current_time = now.time()
    morning = MARKET_MORNING_START <= current_time < MARKET_MORNING_END
    afternoon = MARKET_AFTERNOON_START <= current_time < MARKET_AFTERNOON_END
    return morning or afternoon


def cleanup_invalid_data():
    conn = db.get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            DELETE FROM orderbook_snapshots 
            WHERE (
                EXTRACT(DOW FROM ts) IN (0, 6)
                OR (EXTRACT(HOUR FROM ts) < 9)
                OR (EXTRACT(HOUR FROM ts) >= 12 AND EXTRACT(HOUR FROM ts) < 13)
                OR (EXTRACT(HOUR FROM ts) >= 16)
                OR (EXTRACT(HOUR FROM ts) = 9 AND EXTRACT(MINUTE FROM ts) < 30)
            )
        """)
        deleted_snap = cur.rowcount

        cur.execute("""
            DELETE FROM orderbook_metrics 
            WHERE (
                EXTRACT(DOW FROM ts) IN (0, 6)
                OR (EXTRACT(HOUR FROM ts) < 9)
                OR (EXTRACT(HOUR FROM ts) >= 12 AND EXTRACT(HOUR FROM ts) < 13)
                OR (EXTRACT(HOUR FROM ts) >= 16)
                OR (EXTRACT(HOUR FROM ts) = 9 AND EXTRACT(MINUTE FROM ts) < 30)
            )
        """)
        deleted_met = cur.rowcount

        cur.execute("""
            DELETE FROM signals 
            WHERE (
                EXTRACT(DOW FROM ts) IN (0, 6)
                OR (EXTRACT(HOUR FROM ts) < 9)
                OR (EXTRACT(HOUR FROM ts) >= 12 AND EXTRACT(HOUR FROM ts) < 13)
                OR (EXTRACT(HOUR FROM ts) >= 16)
                OR (EXTRACT(HOUR FROM ts) = 9 AND EXTRACT(MINUTE FROM ts) < 30)
            )
        """)
        deleted_sig = cur.rowcount

        conn.commit()
        if deleted_snap > 0 or deleted_met > 0 or deleted_sig > 0:
            print(f"[Cleanup] Removed {deleted_snap} snapshots, {deleted_met} metrics, {deleted_sig} signals")
    except Exception as e:
        conn.rollback()
        print(f"[Cleanup] Error: {e}")
    finally:
        cur.close()
        conn.close()


class HSIOrderBookHandler(OrderBookHandlerBase):
    def __init__(self):
        super().__init__()
        self._last_signal_ts: datetime | None = None

    def on_recv_rsp(self, rsp_pb):
        ret_code, data = super().on_recv_rsp(rsp_pb)
        if ret_code != RET_OK:
            print(f"[OrderBook] Error: {data}")
            return RET_ERROR, data

        try:
            self._process(data)
        except Exception as e:
            print(f"[OrderBook] Processing error: {e}")

        return RET_OK, data

    def _process(self, data: dict):
        ts = datetime.now(HK_TZ)

        if not is_market_open():
            return

        # Parse bid/ask levels
        raw_bids = data.get("Bid", [])
        raw_asks = data.get("Ask", [])
        n_levels = min(ORDER_BOOK_LEVELS, len(raw_bids), len(raw_asks))
        if n_levels == 0:
            print("[OrderBook] Empty order book received, skipping.")
            return

        levels = []
        for i in range(n_levels):
            levels.append({
                "level": i + 1,
                "bid": float(raw_bids[i][0]),
                "bid_volume": float(raw_bids[i][1]),
                "ask": float(raw_asks[i][0]),
                "ask_volume": float(raw_asks[i][1]),
            })

        # Persist raw snapshot
        db.insert_snapshot(ts, levels)

        # Compute derived metrics
        metrics = compute_metrics(levels)
        db.insert_metrics(ts, metrics)

        # Console output
        self._print_status(ts, metrics)

        # Signal generation with cooldown
        direction, reason = generate_signal(metrics)
        if direction and self._cooldown_ok(ts):
            self._last_signal_ts = ts
            db.insert_signal(ts, direction, reason, metrics)
            self._print_signal(ts, direction, reason, metrics)

    def _cooldown_ok(self, ts: datetime) -> bool:
        if self._last_signal_ts is None:
            return True
        elapsed = (ts - self._last_signal_ts).total_seconds()
        return elapsed >= SIGNAL_COOLDOWN_SEC

    @staticmethod
    def _print_status(ts: datetime, m: dict):
        bid_z = f"{m['bid_zscore']:.2f}" if m["bid_zscore"] is not None else "N/A"
        ask_z = f"{m['ask_zscore']:.2f}" if m["ask_zscore"] is not None else "N/A"
        print(
            f"[{ts.strftime('%H:%M:%S')}] "
            f"Bid {m['best_bid']} ({m['total_bid_vol']:.0f}, Z={bid_z}) | "
            f"Ask {m['best_ask']} ({m['total_ask_vol']:.0f}, Z={ask_z}) | "
            f"Spread {m['spread']} | OBI {m['obi']:.3f}"
        )

    @staticmethod
    def _print_signal(ts: datetime, direction: str, reason: str, m: dict):
        tag = ">>> LONG <<<" if direction == "LONG" else "<<< SHORT >>>"
        print(f"\n{'='*60}")
        print(f"  SIGNAL: {tag}")
        print(f"  Time  : {ts.strftime('%Y-%m-%d %H:%M:%S')}")
        print(f"  Reason: {reason}")
        print(f"  Bid   : {m['best_bid']}  Ask: {m['best_ask']}")
        print(f"  OBI   : {m['obi']:.4f}")
        print(f"{'='*60}\n")


def run():
    reset_buffers()
    db.setup_tables()

    print(f"[Collector] Connecting to Futu OpenD at {FUTU_HOST}:{FUTU_PORT}...")
    ctx = OpenQuoteContext(host=FUTU_HOST, port=FUTU_PORT)

    handler = HSIOrderBookHandler()
    ctx.set_handler(handler)

    ret, data = ctx.subscribe([HSI_SYMBOL], [SubType.ORDER_BOOK])
    if ret != RET_OK:
        print(f"[Collector] Subscribe failed: {data}")
        ctx.close()
        return

    print(f"[Collector] Subscribed to {HSI_SYMBOL} order book. Streaming...")

    try:
        from config import COLLECTION_SLEEP_SEC
        import threading

        def periodic_cleanup():
            while True:
                time.sleep(CLEANUP_INTERVAL_SEC)
                if is_market_open():
                    cleanup_invalid_data()

        cleanup_thread = threading.Thread(target=periodic_cleanup, daemon=True)
        cleanup_thread.start()

        time.sleep(COLLECTION_SLEEP_SEC)
    except KeyboardInterrupt:
        print("\n[Collector] Stopped by user.")
    finally:
        ctx.close()
        print("[Collector] Connection closed.")
