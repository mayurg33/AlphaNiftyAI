# src/fetch_fundamentals.py
import os
import yfinance as yf
import pandas as pd
import json

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
    "TECHM.NS", "TITAN.NS", "ULTRACEMCO.NS", "WIPRO.NS"
]

def convert_df_to_serializable_dict(df):
    if df.empty:
        return {}
    df = df.fillna(0).astype(str)
    df.index = df.index.astype(str)
    df.columns = df.columns.astype(str)
    return df.to_dict()

def fetch_all_fundamentals(month_str):
    os.makedirs("data/fundamentals", exist_ok=True)
    for ticker in nifty_tickers:
        try:
            print(f"[Fetching Fundamentals] {ticker}")
            stock = yf.Ticker(ticker)
            info = stock.info
            metrics = {
                "symbol": ticker,
                "companyName": info.get("longName"),
                "sector": info.get("sector"),
                "industry": info.get("industry"),
                "marketCap": info.get("marketCap"),
                "trailingPE": info.get("trailingPE"),
                "forwardPE": info.get("forwardPE"),
                "bookValue": info.get("bookValue"),
                "dividendYield": info.get("dividendYield"),
                "returnOnEquity": info.get("returnOnEquity"),
                "ebitdaMargins": info.get("ebitdaMargins"),
                "grossMargins": info.get("grossMargins"),
                "profitMargins": info.get("profitMargins"),
                "revenueGrowth": info.get("revenueGrowth"),
                "earningsGrowth": info.get("earningsGrowth"),
                "debtToEquity": info.get("debtToEquity")
            }
            fundamentals = {
                "metrics": metrics,
                "balance_sheet": convert_df_to_serializable_dict(stock.quarterly_balance_sheet),
                "income_stmt": convert_df_to_serializable_dict(stock.quarterly_income_stmt),
                "cashflow": convert_df_to_serializable_dict(stock.quarterly_cashflow)
            }
            with open(f"data/fundamentals/{ticker}_{month_str}.json", 'w') as f:
                json.dump(fundamentals, f, indent=2)
        except Exception as e:
            print(f"[ERROR] {ticker}: {e}")