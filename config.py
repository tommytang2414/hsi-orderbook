"""
Configuration for HSI Order Book Collector
Reads secrets from environment variables — never hardcode credentials.
"""

import os

FUTU_HOST = os.getenv("FUTU_HOST", "127.0.0.1")
FUTU_PORT = int(os.getenv("FUTU_PORT", "11112"))
HSI_SYMBOL = "HK.HSImain"

DB_PARAMS = {
    "host": os.getenv("DB_HOST"),
    "port": int(os.getenv("DB_PORT", "5432")),
    "dbname": os.getenv("DB_NAME", "postgres"),
    "user": os.getenv("DB_USER"),
    "password": os.getenv("DB_PASSWORD"),
    "sslmode": "require",
}

ORDER_BOOK_LEVELS = int(os.getenv("ORDER_BOOK_LEVELS", "5"))
COLLECTION_SLEEP_SEC = 60 * 60 * 10
