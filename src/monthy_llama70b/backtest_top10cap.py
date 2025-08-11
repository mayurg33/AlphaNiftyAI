# src/backtest_simple_top10cap.py

import os
import pandas as pd
import numpy as np
from pathlib import Path

signal_dir = Path("results/signals")
price_dir = Path("data/prices")
marketcap_path = Path("data/market_cap/marketcap.csv")  # must exist
output_path = Path("results/backtest_simple_top10cap")
output_path.mkdir(parents=True, exist_ok=True)

initial_cash = 100000
balance = initial_cash
equity_curve = []
benchmark_curve = []

months = [f"2024-{str(m).zfill(2)}" for m in range(3, 13)] + [f"2025-{str(m).zfill(2)}" for m in range(1, 6)]

# Load market cap
marketcap_df = pd.read_csv(marketcap_path)
marketcap_df.set_index("Ticker", inplace=True)

for i in range(1, len(months)):
    signal_month = months[i - 1]   # ← use previous month signal
    price_month = months[i]       # ← use current month price

    try:
        signal_path = signal_dir / signal_month
        price_path = price_dir / price_month

        # Find BUY signals from previous month
        buys = []
        for file in os.listdir(signal_path):
            if file.endswith(".txt"):
                with open(signal_path / file, "r") as f:
                    if "BUY" in f.readline().upper():
                        buys.append(file.replace(".txt", ""))

        if not buys:
            print(f"[SKIP] No BUYs in {signal_month}")
            continue

        # Select top 10 by market cap
        # print(buys)
        valid_buys = [s for s in buys if s in marketcap_df.index]
        cap_filtered = marketcap_df.loc[valid_buys].sort_values(by="MarketCap", ascending=False)
        top10 = cap_filtered.head(3).index.tolist()
        print(top10)

        if len(top10) < 2:
            print(f"[SKIP] <2 valid BUYs in {signal_month}")
            continue

        # Load price data for selected stocks in this month
        price_df = pd.DataFrame()
        for ticker in top10:
            filepath = price_path / f"{ticker}.csv"
            if filepath.exists():
                df = pd.read_csv(filepath, index_col="Date", parse_dates=True)
                price_df[ticker] = df["Close"]
                # print({ticker})

        price_df.dropna(inplace=True)
        

        if price_df.empty:
            print(f"[SKIP] No price data found in {price_month}")
            continue

        # Compute portfolio value
        weights = np.ones(price_df.shape[1]) / price_df.shape[1]
        normed = price_df / price_df.iloc[0]
        portfolio_value = normed.dot(weights) * balance
        monthly_return = (portfolio_value.iloc[-1] - balance) / balance * 100
        balance = portfolio_value.iloc[-1]

        equity_curve.append((price_month, monthly_return, balance))

        # Benchmark return (NSEI)
        benchmark_file = price_path / "NSEI.csv"
        if benchmark_file.exists():
            nse = pd.read_csv(benchmark_file, index_col="Date", parse_dates=True)["Close"]
            nse_ret = (nse.iloc[-1] - nse.iloc[0]) / nse.iloc[0] * 100
            benchmark_curve.append((price_month, nse_ret))
        else:
            benchmark_curve.append((price_month, np.nan))

        print(f"[ok] {price_month}: {monthly_return:.2f}%")

    except Exception as e:
        print(f"[ERROR] {price_month}: {e}")

# Save monthly results
df_results = pd.DataFrame(equity_curve, columns=["Month", "Strategy Return (%)", "Portfolio Value"])
df_results["Benchmark Return (%)"] = [x[1] for x in benchmark_curve]
df_results.to_csv(output_path / "top10cap_monthly_returns.csv", index=False)

# === Compute overall metrics ===
returns = df_results["Strategy Return (%)"] / 100
total_return = (df_results["Portfolio Value"].iloc[-1] - initial_cash) / initial_cash * 100
sharpe = returns.mean() / returns.std()
sortino = returns.mean() / returns[returns < 0].std()
volatility = returns.std() * np.sqrt(12)
win_rate = (returns > 0).sum() / len(returns) * 100
max_dd = ((df_results["Portfolio Value"].cummax() - df_results["Portfolio Value"]) / df_results["Portfolio Value"].cummax()).max() * 100

# Print stats
print("\n=== Strategy: NSE-Top10-Cap")
print(f"Total Return (%):     {total_return:.2f}")
print(f"Sharpe Ratio:         {sharpe:.2f}")
print(f"Sortino Ratio:        {sortino:.2f}")
print(f"Volatility (%):       {volatility:.2f}")
print(f"Win Rate (%):         {win_rate:.2f}")
print(f"Max Drawdown (%):     {max_dd:.2f}")
