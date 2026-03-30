# HSI OrderBook — Project Documentation

## Project Overview

Real-time Hang Seng Index (HSI) futures order book analyzer. Streams from Futu OpenD, computes smart money signals, stores in PostgreSQL on AWS Lightsail.

- **GitHub**: https://github.com/tommytang2414/hsi-orderbook
- **Local path**: `C:\Users\user\HSIOrderBook`

---

## Architecture

```
Futu OpenD (127.0.0.1:11111)
    → collector.py (subscribe ORDER_BOOK)
    → analyzer.py (OBI + Z-score)
    → db.py → PostgreSQL (AWS Lightsail)
```

---

## Database

- **Host**: AWS Lightsail `ls-ac5c2f9fc26d9b2c22b69ec2a86778bc064634ea.cnuu2ssauco6.ap-southeast-1.rds.amazonaws.com`
- **Port**: 5432
- **Database**: `orderbook`
- **Credentials**: stored in `.env` (NEVER commit)

---

## Key Files

| File | Purpose |
|------|---------|
| `main.py` | Entry point |
| `collector.py` | Futu OpenD subscription + order book handler |
| `analyzer.py` | OBI, Z-score, signal generation |
| `db.py` | PostgreSQL inserts + table setup |
| `config.py` | All settings from `.env` |

---

## Signal Parameters (in `config.py`)

| Param | Value | Description |
|-------|-------|-------------|
| `ORDER_BOOK_LEVELS` | 5 | Bid/ask depth levels |
| `ZSCORE_THRESHOLD` | 2.5 | Volume spike threshold |
| `OBI_THRESHOLD` | 0.3 | Order book imbalance threshold |
| `MIN_SAMPLES_FOR_SIGNAL` | 30 | Min buffer size before signals |
| `SIGNAL_COOLDOWN_SEC` | 60 | Seconds between signals |

---

## Deployment

This project runs on a **Windows host** with Futu OpenD.

- **HK Market hours**: 9:30am-12pm / 1pm-4pm HKT
- **Collector runtime**: 10 hours per session (`COLLECTION_SLEEP_SEC`)
- **Restart**: `restart_daily.sh` kills/restarts via `start.sh`

---

## Troubleshooting

**`WSAECONNREFUSED` on 11111**
→ Futu OpenD not running. Start OpenD first.

**Protobuf error**
→ Run: `set PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python`

**DB connection timeout**
→ Check AWS Lightsail DB is `available` and `publicly-accessible: true`
