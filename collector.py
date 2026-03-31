"""
Futu OpenD order book collector for HSI futures.
Streams real-time order book data and stores raw snapshots.
"""

import time
from datetime import datetime
import pytz
from futu import OpenQuoteContext, OrderBookHandlerBase, SubType, RET_OK, RET_ERROR

from config import FUTU_HOST, FUTU_PORT, HSI_SYMBOL, ORDER_BOOK_LEVELS
import db

HK_TZ = pytz.timezone("Asia/Hong_Kong")


class HSIOrderBookHandler(OrderBookHandlerBase):
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

        db.insert_snapshot(ts, levels)
        self._print_status(ts, levels)

    @staticmethod
    def _print_status(ts: datetime, levels: list):
        best = levels[0]
        total_bid = sum(l["bid_volume"] for l in levels)
        total_ask = sum(l["ask_volume"] for l in levels)
        spread = best["ask"] - best["bid"]
        print(
            f"[{ts.strftime('%H:%M:%S')}] "
            f"Bid {best['bid']} ({total_bid:.0f}) | "
            f"Ask {best['ask']} ({total_ask:.0f}) | "
            f"Spread {spread}"
        )


def run():
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
        time.sleep(COLLECTION_SLEEP_SEC)
    except KeyboardInterrupt:
        print("\n[Collector] Stopped by user.")
    finally:
        ctx.close()
        print("[Collector] Connection closed.")
