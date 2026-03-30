"""
Configuration for HSI Order Book Analyzer
Reads secrets from environment variables — never hardcode credentials.
"""

import os

# Futu OpenD settings
FUTU_HOST = os.getenv("FUTU_HOST", "127.0.0.1")
FUTU_PORT = int(os.getenv("FUTU_PORT", "11112"))
HSI_SYMBOL = "HK.HSImain"

# PostgreSQL connection params (avoids URL-encoding issues with special chars in passwords)
DB_PARAMS = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "dbname": os.getenv("DB_NAME", "postgres"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "sslmode": "require",
}

# Order book collection settings
ORDER_BOOK_LEVELS = int(os.getenv("ORDER_BOOK_LEVELS", "5"))
COLLECTION_SLEEP_SEC = 60 * 60 * 10   # 10 hours (cover full HK trading session)

# Outlier detection settings
ZSCORE_WINDOW = 100
ZSCORE_THRESHOLD = 2.5
OBI_THRESHOLD = 0.3
MIN_SAMPLES_FOR_SIGNAL = 30

# Signal settings
SIGNAL_COOLDOWN_SEC = 60
