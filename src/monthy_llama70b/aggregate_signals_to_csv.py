# src/aggregate_signals_to_csv.py
import os
import pandas as pd
from pathlib import Path
import re

signal_dir = Path("results/signals")
out_path = signal_dir / "signals_summary.csv"

all_records = []

for month_dir in signal_dir.iterdir():
    if not month_dir.is_dir():
        continue
    month = month_dir.name
    for file in month_dir.glob("*.txt"):
        ticker = file.stem
        try:
            with open(file, "r", encoding="utf-8") as f:
                content = f.read()
            # Extract Signal and Reason
            signal_match = re.search(r"Signal:\s*(BUY|SELL|HOLD)", content, re.IGNORECASE)
            reason_match = re.search(r"Reason:\s*(.+?)\n", content, re.IGNORECASE)

            signal = signal_match.group(1).upper() if signal_match else "UNKNOWN"
            reason = reason_match.group(1).strip() if reason_match else "Not found"

            all_records.append({
                "Month": month,
                "Ticker": ticker,
                "Signal": signal,
                "Reason": reason
            })
        except Exception as e:
            print(f"[ERROR] {file}: {e}")

# Convert to CSV
df = pd.DataFrame(all_records)
df.to_csv(out_path, index=False)
print(f"[done] Saved signal summary to {out_path}")
