# src/fetch_market_cap_monthly.py

import yfinance as yf
import pandas as pd
from datetime import datetime
from dateutil.relativedelta import relativedelta
import os

tickers = [
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
    "TECHM.NS", "TITAN.NS", "ULTRACEMCO.NS", "WIPRO.NS"
]

start_month = datetime(2024, 3, 1)
end_month = datetime(2025, 5, 1)

output = []

month = start_month
while month <= end_month:
    print(f"[FETCHING] Market caps for {month.strftime('%Y-%m')}")
    for ticker in tickers:
        try:
            info = yf.Ticker(ticker).info
            market_cap = info.get("marketCap", None)
            if market_cap:
                output.append({
                    "Month": month.strftime("%Y-%m"),
                    "Ticker": ticker.replace(".NS", ""),
                    "MarketCap": market_cap
                })
        except Exception as e:
            print(f"[ERROR] {ticker} in {month.strftime('%Y-%m')}: {e}")
    month += relativedelta(months=1)

df = pd.DataFrame(output)
os.makedirs("data/market_cap", exist_ok=True)
df.to_csv("data/market_cap/marketcap.csv", index=False)
print("[✓] Cleaned marketcap.csv saved.")
