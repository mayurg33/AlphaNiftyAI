# loop_15_months.py
from datetime import datetime, timedelta
import os

from src.summarizers import run_price_summaries
from src.signal_generator import generate_signals

start_date = datetime(2023, 3, 1)
months = [(start_date + timedelta(days=30 * i)).strftime("%Y-%m") for i in range(15)]

for month in months:
    print(f"\n[LOOP] Running pipeline for {month}")

    try:
        run_price_summaries(month)
    except Exception as e:
        print(f"[ERROR] Summarizer failed for {month}: {e}")
        continue

    try:
        generate_signals(month)
    except Exception as e:
        print(f"[ERROR] Signal generation failed for {month}: {e}")
        continue

print("\n[✓] Loop over 15 months complete.")
print("Now run: run_backtest() and run_bootstrap_test() to evaluate the full pipeline.")
