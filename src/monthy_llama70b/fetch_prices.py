import yfinance as yf
import os
from datetime import datetime

nifty_tickers = ["ADANIENT.NS", "ADANIPORTS.NS", "APOLLOHOSP.NS", "ASIANPAINT.NS",
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
    "TECHM.NS", "TITAN.NS", "ULTRACEMCO.NS", "WIPRO.NS"]  # full list as above
nifty_index = "^NSEI"

def fetch_all_prices():
    start = "2025-06-01"
    end = datetime.today().strftime("%Y-%m-%d")
    os.makedirs("data/prices", exist_ok=True)
    for ticker in nifty_tickers + [nifty_index]:
        try:
            df = yf.Ticker(ticker).history(start=start, end=end)
            df.to_csv(f"C:/Users/mayur/MarketSenseAI/data/prices/{ticker.replace('^','')}.csv")
            print(f"[OK] {ticker} saved.")
        except Exception as e:
            print(f"[ERROR] {ticker}: {e}")
if __name__ == "__main__":
    fetch_all_prices()