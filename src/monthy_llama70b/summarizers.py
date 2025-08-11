# src/summarize_price_loop.py
import os
import pandas as pd
from groq import Groq
from datetime import datetime, timedelta

PRICE_DIR = "data/prices"
SUMMARY_DIR = "results/summaries_price"
os.makedirs(SUMMARY_DIR, exist_ok=True)

client = Groq(api_key="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")

def summarize_price_for_month(month_str):
    month_path = os.path.join(PRICE_DIR, month_str)
    output_path = os.path.join(SUMMARY_DIR, month_str)
    os.makedirs(output_path, exist_ok=True)

    for file in os.listdir(month_path):
        if not file.endswith(".csv"):
            continue
        symbol = file.replace(".csv", "")
        df = pd.read_csv(os.path.join(month_path, file))

        if df.empty or "Close" not in df.columns:
            print(f"[SKIP] No valid price data for {symbol} - {month_str}")
            continue

        df["Return"] = df["Close"].pct_change()
        volatility = df["Return"].std() * (252 ** 0.5) if not df["Return"].isna().all() else 0
        pct_return = ((df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0]) * 100

        # 3M, 6M, 12M returns (approximate using 21 trading days/month)
        summary_stats = {}
        for label, periods in {"3m": 63, "6m": 126, "12m": 252}.items():
            if len(df) >= periods:
                r = ((df['Close'].iloc[-1] - df['Close'].iloc[-periods]) / df['Close'].iloc[-periods]) * 100
                summary_stats[label] = r
            else:
                summary_stats[label] = float('nan')

        sharpe_ratio = (df["Return"].mean() / df["Return"].std()) * (252 ** 0.5) if df["Return"].std() else 0

        summary = f"Symbol: {symbol}\nMonth: {month_str}\n"
        summary += f"Start Price: {df['Close'].iloc[0]:.2f}\n"
        summary += f"End Price: {df['Close'].iloc[-1]:.2f}\n"
        summary += f"% Return: {pct_return:.2f}%\n"
        summary += f"3M Return: {summary_stats['3m']:.2f}%\n"
        summary += f"6M Return: {summary_stats['6m']:.2f}%\n"
        summary += f"12M Return: {summary_stats['12m']:.2f}%\n"
        summary += f"High: {df['High'].max():.2f}\nLow: {df['Low'].min():.2f}\n"
        summary += f"Volatility: {volatility:.4f}\nSharpe Ratio: {sharpe_ratio:.2f}\n"
        summary += f"Volume Avg: {df['Volume'].mean():.2f}\n"

        prompt = f"""
You are a financial analyst. Based on the following monthly stock price statistics, provide a one-paragraph summary and recommend whether to BUY, SELL or HOLD this stock.

{summary}

Respond in the format:
Final Decision: <BUY/SELL/HOLD>
Reason: <Short 1-2 sentence justification>
"""
        try:
            response = client.chat.completions.create(
                model="llama3-70b-8192",
                messages=[{"role": "user", "content": prompt}]
            )
            result = response.choices[0].message.content.strip()
            with open(os.path.join(output_path, f"{symbol}_price.txt"), "w", encoding="utf-8") as f:
                f.write(result)
            print(f"[OK] Price summarized for {symbol} - {month_str}")
        except Exception as e:
            print(f"[ERROR] {symbol} - {e}")

def summarize_all_price_months():
    start = datetime(2024, 3, 1)
    months = [(start + timedelta(days=30 * i)).strftime("%Y-%m") for i in range(15)]
    for month in months:
        summarize_price_for_month(month)

# To run:
summarize_all_price_months()