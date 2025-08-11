from datetime import datetime, timedelta
import pandas as pd
from pathlib import Path

PRICE_DIR = Path("data/prices/weekly")

def get_next_week_stock_return(ticker, article_date_str):
    try:
        article_date = pd.to_datetime(article_date_str)

        # ✅ Get the upcoming **Sunday** (week end)
        days_until_sunday = (6 - article_date.weekday())  # Sunday = 6
        next_sunday = (article_date + timedelta(days=days_until_sunday)).strftime("%Y-%m-%d")

        price_path = PRICE_DIR / next_sunday / f"{ticker}.csv"
        if not price_path.exists():
            print(f"[WARN] Price file not found: {price_path}")
            return None

        df = pd.read_csv(price_path, parse_dates=["Date"])
        df = df.sort_values("Date")
        if len(df) < 2:
            print(f"[WARN] Not enough price data in {price_path}")
            return None

        open_price = df.iloc[0]["Open"]
        close_price = df.iloc[-1]["Close"]

        return ((close_price - open_price) / open_price) * 100

    except Exception as e:
        print(f"[ERROR] Impact calc failed for {ticker} on {article_date_str}: {e}")
        return None

# get_next_week_stock_return()
impact = get_next_week_stock_return("ADANIENT", "2024-03-01")
print("Impact:", impact)