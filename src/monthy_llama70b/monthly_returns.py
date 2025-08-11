# src/backtest_monthly_returns.py
import os
import pandas as pd
from pathlib import Path
from datetime import datetime
from dateutil.relativedelta import relativedelta

price_base = Path("data/prices")
signal_base = Path("results/signals")
benchmark = "^NSEI.csv"

# Define the full range of months
months = [f"2024-{str(m).zfill(2)}" for m in range(3, 13)] + [f"2025-{str(m).zfill(2)}" for m in range(1, 6)]
months_dt = [datetime.strptime(m, "%Y-%m") for m in months]

def extract_signal(filepath):
    with open(filepath, "r", encoding="utf-8") as f:
        for line in f:
            if line.startswith("Signal:"):
                return line.split(":")[1].strip()
    return "HOLD"

def get_monthly_return(price_path):
    df = pd.read_csv(price_path, index_col="Date", parse_dates=True)
    df = df.sort_index()
    if df.empty or len(df) < 2:
        return None
    start_price = df["Close"].iloc[0]
    end_price = df["Close"].iloc[-1]
    return ((end_price - start_price) / start_price) * 100

def run():
    monthly_returns = []

    for i in range(len(months_dt) - 1):  # last month can't have return data
        signal_month = months_dt[i].strftime("%Y-%m")
        price_month = months_dt[i + 1].strftime("%Y-%m")

        print(f"[PROCESSING] Signal: {signal_month} | Return: {price_month}")
        signal_path = signal_base / signal_month
        price_path = price_base / price_month

        tickers = [f.replace(".txt", "") for f in os.listdir(signal_path) if f.endswith(".txt")]

        returns = []
        for ticker in tickers:
            signal_file = signal_path / f"{ticker}.txt"
            signal = extract_signal(signal_file)
            if signal == "BUY":
                price_file = price_path / f"{ticker}.csv"
                if price_file.exists():
                    r = get_monthly_return(price_file)
                    print({ticker})
                    if r is not None:
                        returns.append(r)

        strategy_return = sum(returns) / len(returns) if returns else 0

        # Benchmark return
        bench_file = price_path / benchmark
        bench_return = get_monthly_return(bench_file) if bench_file.exists() else None

        monthly_returns.append({
            "Month": signal_month,  # signal from this month
            "Strategy Return (%)": round(strategy_return, 2),
            "Benchmark Return (%)": round(bench_return, 2) if bench_return is not None else "NA"
        })

    # Save to CSV
    df = pd.DataFrame(monthly_returns)
    df.to_csv("results/portfolio/monthly_returns_vs_benchmark.csv", index=False)
    print("  Saved: results/portfolio/monthly_returns_vs_benchmark.csv")

if __name__ == "__main__":
    run()
