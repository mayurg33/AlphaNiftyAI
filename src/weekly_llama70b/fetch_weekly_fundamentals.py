import os
import json
from pathlib import Path
from datetime import datetime

# List of tickers
nifty_tickers = [
    "ADANIENT.NS", "ADANIPORTS.NS", "APOLLOHOSP.NS", "ASIANPAINT.NS", "AXISBANK.NS", "BAJAJ-AUTO.NS",
    "BAJFINANCE.NS", "BAJAJFINSV.NS", "BPCL.NS", "BHARTIARTL.NS", "BRITANNIA.NS", "CIPLA.NS",
    "COALINDIA.NS", "DIVISLAB.NS", "DRREDDY.NS", "EICHERMOT.NS", "GRASIM.NS", "HCLTECH.NS",
    "HDFCBANK.NS", "HDFCLIFE.NS", "HEROMOTOCO.NS", "HINDALCO.NS", "HINDUNILVR.NS", "ICICIBANK.NS",
    "ITC.NS", "INDUSINDBK.NS", "INFY.NS", "JSWSTEEL.NS", "KOTAKBANK.NS", "LTIM.NS", "LT.NS",
    "M&M.NS", "MARUTI.NS", "NTPC.NS", "NESTLEIND.NS", "ONGC.NS", "POWERGRID.NS", "RELIANCE.NS",
    "SBILIFE.NS", "SHRIRAMFIN.NS", "SBIN.NS", "SUNPHARMA.NS", "TCS.NS", "TATACONSUM.NS",
    "TATAMOTORS.NS", "TATASTEEL.NS", "TECHM.NS", "TITAN.NS", "ULTRACEMCO.NS", "WIPRO.NS"
]

# Paths
monthly_base = Path("data/fundamentals")
weekly_output_base = Path("data/fundamentals/weekly")
weekly_output_base.mkdir(parents=True, exist_ok=True)

# Get available months
months_available = sorted(os.listdir(monthly_base))

# Filter YYYY-MM only
months_available = [m for m in months_available if m[:4].isdigit() and m[4] == "-"]

def find_latest_month(week_str):
    week_date = datetime.strptime(week_str, "%Y-%m-%d")
    valid_months = [
        m for m in months_available
        if datetime.strptime(m, "%Y-%m") <= week_date
    ]
    return max(valid_months) if valid_months else None

def generate_weekly_fundamentals():
    # Loop over week folders from weekly prices
    weekly_price_dir = Path("data/prices/weekly")
    week_folders = sorted([f for f in weekly_price_dir.iterdir() if f.is_dir()])

    for week_path in week_folders:
        week_str = week_path.name
        latest_month = find_latest_month(week_str)
        if not latest_month:
            print(f"[SKIP] No fundamentals available before {week_str}")
            continue

        for ticker in nifty_tickers:
            json_file = monthly_base / latest_month / f"{ticker}_{latest_month}.json"
            if not json_file.exists():
                print(f"[MISS] {ticker} not found for {latest_month}")
                continue

            with open(json_file, "r") as f:
                data = json.load(f)

            week_dir = weekly_output_base / week_str
            week_dir.mkdir(parents=True, exist_ok=True)

            output_path = week_dir / f"{ticker.replace('.NS', '')}.json"
            with open(output_path, "w") as f:
                json.dump(data, f, indent=2)
            print(f"[OK] {ticker} => {week_str}")

if __name__ == "__main__":
    generate_weekly_fundamentals()
