"""Quick test: verify DB connection and create tables."""
from dotenv import load_dotenv
load_dotenv()

import db
db.setup_tables()
print("DB connection OK.")
