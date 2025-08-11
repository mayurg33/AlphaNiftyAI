# src/split_news_by_week.py

import os
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta
import re

# Paths
input_base = Path("data/news")
output_base = Path("data/news/weekly")
output_base.mkdir(parents=True, exist_ok=True)

# Month folders to process
months = [f"2024-{str(m).zfill(2)}" for m in range(3, 13)] + [f"2025-{str(m).zfill(2)}" for m in range(1, 7)]

def parse_relative_date(raw, fallback_date):
    raw = str(raw).lower().strip()
    
    if re.match(r"\d{1,2} \w{3,9} \d{4}", raw):
        # Already a clean date like "1 Mar 2024"
        return pd.to_datetime(raw, errors='coerce')
    
    today = pd.to_datetime(fallback_date)

    if "day ago" in raw:
        n = int(re.search(r"\d+", raw)[0])
        return today - timedelta(days=n)
    elif "week ago" in raw:
        n = int(re.search(r"\d+", raw)[0])
        return today - timedelta(weeks=n)
    elif "month ago" in raw:
        n = 1 if "a month" in raw else int(re.search(r"\d+", raw)[0])
        return today - pd.DateOffset(months=n)
    elif "hour ago" in raw:
        return today
    else:
        return pd.NaT

def get_sunday(date):
    return (date + timedelta(days=(6 - date.weekday()))).strftime("%Y-%m-%d")

def split_monthly_news_to_weekly():
    for month in months:
        month_path = input_base / month
        if not month_path.exists():
            print(f"[SKIP] {month_path} does not exist")
            continue

        fallback_date = pd.to_datetime(f"{month}-28")  # Assume scrape was near end of month

        for file in os.listdir(month_path):
            if not file.endswith(".csv"):
                continue

            ticker = file.replace(".csv", "")
            df = pd.read_csv(month_path / file)

            # Fix vague dates
            df["ParsedDate"] = df["Date"].apply(lambda x: parse_relative_date(x, fallback_date))
            df = df.dropna(subset=["ParsedDate"])
            df["WeekEnd"] = df["ParsedDate"].apply(get_sunday)

            for week, group in df.groupby("WeekEnd"):
                week_folder = output_base / week
                week_folder.mkdir(parents=True, exist_ok=True)
                out_path = week_folder / f"{ticker}.csv"
                group.drop(columns=["WeekEnd", "ParsedDate"]).to_csv(out_path, index=False)
                print(f"[OK] {ticker} => {week}")

if __name__ == "__main__":
    split_monthly_news_to_weekly()
