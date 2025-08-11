# src/fetch_prices_by_month.py
import os
import yfinance as yf
from datetime import datetime

nifty_tickers = [
    "ADANIENT.NS", "ADANIPORTS.NS", "APOLLOHOSP.NS", "ASIANPAINT.NS",
    "AXISBANK.NS", "BAJAJ-AUTO.NS", "BAJFINANCE.NS", "BAJAJFINSV.NS",
    "BPCL.NS", "BHARTIARTL.NS", "BRITANNIA.NS", "CIPLA.NS",
    "COALINDIA.NS", "DIVISLAB.NS", "DRREDDY.NS", "EICHERMOT.NS",
    "GRASIM.NS", "HCLTECH.NS", "HDFCBANK.NS", "HDFCLIFE.NS",
    "HEROMOTOCO.NS", "HINDALCO.NS", "HINDUNILVR.NS", "ICICIBANK.NS",
    "ITC.NS", "INDUSINDBK.NS", "INFY.NS", "JSWSTEEL.NS",
    "KOTAKBANK.NS", "LTIM.NS", "LT.NS", "M&M.NS", "MARUTI.NS",
    "NTPC.NS", "NESTLEIND.NS", "ONGC.NS", "POWERGRID.NS", "RELIANCE.NS",
    "SBILIFE.NS", "SHRIRAMFIN.NS", "SBIN.NS", "SUNPHARMA.NS",
    "TCS.NS", "TATACONSUM.NS", "TATAMOTORS.NS", "TATASTEEL.NS",
    "TECHM.NS", "TITAN.NS", "ULTRACEMCO.NS", "WIPRO.NS","^NSEI"
                 ]

def fetch_prices_by_month():
    os.makedirs("data/prices", exist_ok=True)
    for ticker in nifty_tickers:
        print(f"[FETCHING] {ticker}...")
        try:
            df = yf.Ticker(ticker).history(start="2024-06-01", end="2025-07-01")
            df["Month"] = df.index.to_series().dt.to_period("M").astype(str)
            for month, group in df.groupby("Month"):
                month_dir = os.path.join("data/prices", month)
                os.makedirs(month_dir, exist_ok=True)
                out_path = os.path.join(month_dir, f"{ticker.replace('.NS', '')}.csv")
                group.drop(columns=["Month"]).to_csv(out_path)
                print(f"[OK] Saved {ticker} for {month}")
        except Exception as e:
            print(f"[ERROR] {ticker}: {e}")

if __name__ == "__main__":
    fetch_prices_by_month()