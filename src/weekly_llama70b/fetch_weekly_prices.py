import yfinance as yf
import pandas as pd
from pathlib import Path
from datetime import datetime, timedelta

nifty_tickers = [
    "ADANIENT.NS", "ADANIPORTS.NS", "APOLLOHOSP.NS", "ASIANPAINT.NS",
    "AXISBANK.NS", "BAJAJ-AUTO.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS",
    "BPCL.NS", "BHARTIARTL.NS", "BRITANNIA.NS", "CIPLA.NS", "COALINDIA.NS",
    "DIVISLAB.NS", "DRREDDY.NS", "EICHERMOT.NS", "GRASIM.NS", "HCLTECH.NS",
    "HDFCBANK.NS", "HDFCLIFE.NS", "HEROMOTOCO.NS", "HINDALCO.NS", "HINDUNILVR.NS",
    "ICICIBANK.NS", "ITC.NS", "INDUSINDBK.NS", "INFY.NS", "JSWSTEEL.NS",
    "KOTAKBANK.NS", "LTIM.NS", "LT.NS", "M&M.NS", "MARUTI.NS", "NTPC.NS",
    "NESTLEIND.NS", "ONGC.NS", "POWERGRID.NS", "RELIANCE.NS", "SBILIFE.NS",
    "SHRIRAMFIN.NS", "SBIN.NS", "SUNPHARMA.NS", "TCS.NS", "TATACONSUM.NS",
    "TATAMOTORS.NS", "TATASTEEL.NS", "TECHM.NS", "TITAN.NS", "ULTRACEMCO.NS", "WIPRO.NS"
]

output_base = Path("data/prices/weekly")
output_base.mkdir(parents=True, exist_ok=True)

start_date = pd.to_datetime("2021-01-01")
end_date = pd.to_datetime("2024-01-01")

def fetch_all_data():
    print(f"[INFO] Downloading data from {start_date.date()} to {end_date.date()}...")
    all_data = yf.download(nifty_tickers, start=start_date, end=end_date, group_by='ticker', auto_adjust=False)
    return all_data

def process_weekly_data(all_data):
    for single_date in pd.date_range(start=start_date, end=end_date, freq='W-SUN'):
        week_start = single_date - timedelta(days=6)  # previous Monday
        week_end = single_date  # current Sunday

        folder_name = single_date.strftime('%Y-%m-%d')
        out_folder = output_base / folder_name
        out_folder.mkdir(parents=True, exist_ok=True)

        for ticker in nifty_tickers:
            try:
                df = all_data[ticker].copy()
                df_week = df.loc[(df.index >= week_start) & (df.index <= week_end)]
                if df_week.empty:
                    print(f"[WARNING] No data for {ticker} in {folder_name}")
                    continue

                out_path = out_folder / f"{ticker.replace('.NS', '')}.csv"
                df_week.to_csv(out_path, index_label="Date")
                print(f"[hehe] Saved {ticker} for week ending {folder_name}")

            except Exception as e:
                print(f"[ERROR] {ticker} in {folder_name}: {e}")

if __name__ == "__main__":
    data = fetch_all_data()
    process_weekly_data(data)
