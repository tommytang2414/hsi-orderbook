"""
Outlier detection and signal generation for HSI order book.

Strategy — "Follow the Smart Money":
  1. Order Book Imbalance (OBI): measures directional pressure
       OBI = (total_bid_vol - total_ask_vol) / (total_bid_vol + total_ask_vol)
       OBI close to +1 → buyers dominate → LONG
       OBI close to -1 → sellers dominate → SHORT

  2. Volume Z-score: flags abnormally large orders (big players stepping in)
       Z = (x - rolling_mean) / rolling_std
       High bid Z-score + high OBI → strong LONG signal
       High ask Z-score + low OBI → strong SHORT signal

  3. Spread monitoring: unusually narrow/wide spread can precede big moves
"""

import statistics
from datetime import datetime
from config import ZSCORE_WINDOW, ZSCORE_THRESHOLD, OBI_THRESHOLD, MIN_SAMPLES_FOR_SIGNAL

# In-memory rolling buffers (avoids hitting DB every tick)
_bid_vol_buffer: list[float] = []
_ask_vol_buffer: list[float] = []


def update_buffers(total_bid_vol: float, total_ask_vol: float):
    """Add latest volumes to rolling buffers, trim to window size."""
    _bid_vol_buffer.append(total_bid_vol)
    _ask_vol_buffer.append(total_ask_vol)
    if len(_bid_vol_buffer) > ZSCORE_WINDOW:
        _bid_vol_buffer.pop(0)
    if len(_ask_vol_buffer) > ZSCORE_WINDOW:
        _ask_vol_buffer.pop(0)


def _zscore(series: list[float], current: float) -> float | None:
    """Compute Z-score of current value relative to the series."""
    if len(series) < 5:
        return None
    mean = statistics.mean(series)
    try:
        std = statistics.stdev(series)
    except statistics.StatisticsError:
        return None
    if std == 0:
        return 0.0
    return (current - mean) / std


def compute_metrics(levels: list[dict]) -> dict:
    """
    Compute all metrics from a raw order book snapshot.

    levels: list of dicts sorted by level (1 = best)
        keys: level, bid, bid_volume, ask, ask_volume
    Returns a metrics dict ready for DB insertion and signal generation.
    """
    best = levels[0]
    total_bid_vol = sum(l["bid_volume"] for l in levels if l["bid_volume"])
    total_ask_vol = sum(l["ask_volume"] for l in levels if l["ask_volume"])

    # Order Book Imbalance
    total = total_bid_vol + total_ask_vol
    obi = (total_bid_vol - total_ask_vol) / total if total > 0 else 0.0

    # Update rolling buffers BEFORE computing Z-scores
    update_buffers(total_bid_vol, total_ask_vol)

    bid_zscore = _zscore(_bid_vol_buffer, total_bid_vol)
    ask_zscore = _zscore(_ask_vol_buffer, total_ask_vol)

    return {
        "best_bid": best["bid"],
        "best_ask": best["ask"],
        "spread": best["ask"] - best["bid"] if best["ask"] and best["bid"] else None,
        "total_bid_vol": total_bid_vol,
        "total_ask_vol": total_ask_vol,
        "obi": obi,
        "bid_zscore": bid_zscore,
        "ask_zscore": ask_zscore,
    }


def generate_signal(metrics: dict) -> tuple[str | None, str | None]:
    """
    Determine if there is a LONG or SHORT signal.
    Returns (direction, reason) or (None, None).

    Signal logic:
      LONG  — big bid volume spike AND OBI above threshold
              → big money absorbing supply / aggressively buying
      SHORT — big ask volume spike AND OBI below negative threshold
              → big money aggressively selling / pushing price down
      LONG  — OBI alone strongly positive (no outlier needed, sustained imbalance)
      SHORT — OBI alone strongly negative
    """
    if len(_bid_vol_buffer) < MIN_SAMPLES_FOR_SIGNAL:
        return None, None

    obi = metrics["obi"]
    bid_z = metrics["bid_zscore"]
    ask_z = metrics["ask_zscore"]

    reasons = []
    direction = None

    # Strong outlier signal
    if bid_z is not None and bid_z > ZSCORE_THRESHOLD and obi > OBI_THRESHOLD:
        direction = "LONG"
        reasons.append(f"Bid volume spike Z={bid_z:.2f}, OBI={obi:.3f}")

    elif ask_z is not None and ask_z > ZSCORE_THRESHOLD and obi < -OBI_THRESHOLD:
        direction = "SHORT"
        reasons.append(f"Ask volume spike Z={ask_z:.2f}, OBI={obi:.3f}")

    # Sustained imbalance signal (higher threshold, no outlier required)
    elif obi > 0.5:
        direction = "LONG"
        reasons.append(f"Sustained bid dominance OBI={obi:.3f}")

    elif obi < -0.5:
        direction = "SHORT"
        reasons.append(f"Sustained ask dominance OBI={obi:.3f}")

    return direction, "; ".join(reasons) if reasons else None


def reset_buffers():
    """Call at session start to clear stale data from previous day."""
    _bid_vol_buffer.clear()
    _ask_vol_buffer.clear()
