# src/weekly_llama70b/save_weekly_macro_summaries.py

import os
import shutil
from pathlib import Path
from datetime import datetime

# Paths
monthly_macro_dir = Path("results/summaries_macro")
weekly_folders = Path("data/prices/weekly")
output_dir = Path("results/summaries_macro/weekly")
output_dir.mkdir(parents=True, exist_ok=True)

# Get all available months with summaries
available_months = {
    m.name: m / "summary.txt"
    for m in monthly_macro_dir.iterdir()
    if m.is_dir() and (m / "summary.txt").exists()
}

# Convert to datetime for sorting
available_months_dt = sorted(
    [(datetime.strptime(m, "%Y-%m"), path) for m, path in available_months.items()],
    key=lambda x: x[0]
)

def find_latest_month_summary(week_date):
    for dt, path in reversed(available_months_dt):
        if dt <= week_date:
            return path
    return None

# Loop through each week and copy the most recent summary
for week_folder in sorted(weekly_folders.iterdir()):
    if not week_folder.is_dir():
        continue

    week_str = week_folder.name
    try:
        week_date = datetime.strptime(week_str, "%Y-%m-%d")
    except ValueError:
        continue

    summary_path = find_latest_month_summary(week_date)
    if summary_path:
        week_output_dir = output_dir / week_str
        week_output_dir.mkdir(parents=True, exist_ok=True)
        shutil.copy(summary_path, week_output_dir / "summary.txt")
        print(f"[OK] {week_str} <- {summary_path.parent.name}")
    else:
        print(f"[SKIP] No summary available before {week_str}")
