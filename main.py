"""
Entry point — HSI Order Book Smart Money Analyzer
Usage: python main.py
"""

from dotenv import load_dotenv
load_dotenv()  # Load .env before any other import reads env vars

from collector import run

if __name__ == "__main__":
    run()
