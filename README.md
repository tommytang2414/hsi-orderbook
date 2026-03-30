# HSI OrderBook — Smart Money Analyzer

Real-time Hang Seng Index (HSI) futures order book analyzer. Streams order book data from Futu OpenD, computes OBI + Z-score signals, stores in PostgreSQL.

## Setup

### 1. Futu OpenD

Install and run Futu OpenD on the host. Ensure:
- `127.0.0.1:11111` is accessible
- HK.HSImain futures data is enabled

### 2. Database

PostgreSQL on AWS Lightsail. Copy `.env.example` to `.env` and fill in credentials:

```bash
cp .env.example .env
```

### 3. Python environment

```bash
pip install -r requirements.txt
```

On first run, protobuf conflict may require:

```bash
set PROTOCOL_BUFFERS_PYTHON_IMPLEMENTATION=python
```

## Run

```bash
python main.py
```

Collector streams order book data for 10 hours (HK trading session). Keyboard interrupt to stop early.

## Data

| Table | Description |
|-------|-------------|
| `orderbook_snapshots` | Raw bid/ask levels per snapshot |
| `orderbook_metrics` | Computed OBI, spread, z-scores |
| `signals` | LONG/SHORT signals when triggered |

## Signal Logic

- **LONG**: Bid volume spike (Z>2.5) + OBI>0.3, **or** sustained OBI>0.5
- **SHORT**: Ask volume spike (Z>2.5) + OBI<-0.3, **or** sustained OBI<-0.5
- 60-second signal cooldown
