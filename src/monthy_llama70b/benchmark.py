import os
import json
import pandas as pd
import numpy as np
from datetime import datetime
from dateutil.relativedelta import relativedelta

SIGNAL_FOLDER = "results/signals"
PRICE_FOLDER = "data/prices"
BENCHMARK = "^NSEI"

def get_next_month(month_str):
    dt = datetime.strptime(month_str, "%Y-%m")
    next_dt = dt + relativedelta(months=1)
    return next_dt.strftime("%Y-%m")

def get_monthly_return(price_path):
    try:
        df = pd.read_csv(price_path)
        return (df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0]
    except:
        return None

def is_valid_month_folder(name):
    try:
        dt = datetime.strptime(name, "%Y-%m")
        return dt <= datetime(2025, 5, 1)
    except:
        return False

def backtest_ms():
    all_folders = os.listdir(SIGNAL_FOLDER)
    months = sorted([
        folder for folder in all_folders
        if os.path.isdir(os.path.join(SIGNAL_FOLDER, folder)) and is_valid_month_folder(folder)
    ])

    strategy_returns = []
    benchmark_returns = []
    valid_months = []
    portfolios = {}

    for month in months:
        signal_path = os.path.join(SIGNAL_FOLDER, month)
        next_month = get_next_month(month)
        price_dir = os.path.join(PRICE_FOLDER, next_month)

        if not os.path.exists(price_dir):
            print(f"[SKIP] No price data for {next_month}")
            continue

        longs, shorts = [], []

        for file in os.listdir(signal_path):
            if not file.endswith(".json"):
                continue
            ticker = file.replace(".json", "")
            try:
                with open(os.path.join(signal_path, file)) as f:
                    data = json.load(f)
                    decision = data.get("decision", "").strip().upper()
                    if decision == "BUY":
                        longs.append(ticker)
                    elif decision == "SELL":
                        shorts.append(ticker)
            except Exception as e:
                print(f"[ERROR] {file}: {e}")
                continue

        long_returns, short_returns = [], []

        for ticker in longs:
            price_path = os.path.join(price_dir, f"{ticker}.csv")
            r = get_monthly_return(price_path)
            if r is not None:
                long_returns.append(r)

        for ticker in shorts:
            price_path = os.path.join(price_dir, f"{ticker}.csv")
            r = get_monthly_return(price_path)
            if r is not None:
                short_returns.append(-r)  # short = profit when stock falls

        long_avg = np.mean(long_returns) if long_returns else 0
        short_avg = np.mean(short_returns) if short_returns else 0
        strategy_return = (long_avg + short_avg) / 2
        strategy_returns.append(strategy_return)

        benchmark_path = os.path.join(price_dir, f"{BENCHMARK}.csv")
        bench_return = get_monthly_return(benchmark_path) or 0
        benchmark_returns.append(bench_return)

        valid_months.append(month)
        portfolios[month] = {"longs": longs, "shorts": shorts}

        print(f"\n[{month}] Strategy: {strategy_return:.2%} | Benchmark: {bench_return:.2%}")
        print(f"  Longs: {longs}")
        print(f"  Shorts: {shorts}")

    df = pd.DataFrame({
        "month": valid_months,
        "strategy_return": strategy_returns,
        "benchmark_return": benchmark_returns
    })

    df["excess_return"] = df["strategy_return"] - df["benchmark_return"]
    df["cumulative_strategy"] = (1 + df["strategy_return"]).cumprod()
    df["cumulative_benchmark"] = (1 + df["benchmark_return"]).cumprod()

    # Strategy Metrics
    final_return = df["cumulative_strategy"].iloc[-1] - 1
    final_benchmark = df["cumulative_benchmark"].iloc[-1] - 1
    volatility = np.std(df["strategy_return"])
    sharpe = np.mean(df["strategy_return"]) / (volatility + 1e-8)
    downside = np.std([r for r in df["strategy_return"] if r < 0]) or 1e-8
    sortino = np.mean(df["strategy_return"]) / downside
    max_dd = ((df["cumulative_strategy"] - df["cumulative_strategy"].cummax()) / df["cumulative_strategy"].cummax()).min()
    win_rate = np.mean(df["strategy_return"] > df["benchmark_return"])

    # Benchmark Metrics
    benchmark_volatility = np.std(df["benchmark_return"])*np.sqrt(15)
    benchmark_sharpe = (final_benchmark-0.06) / (benchmark_volatility )
    benchmark_downside = np.std([r for r in df["benchmark_return"] if r < 0]) or 1e-8
    benchmark_sortino = np.mean(df["benchmark_return"]) / benchmark_downside
    benchmark_max_dd = ((df["cumulative_benchmark"] - df["cumulative_benchmark"].cummax()) / df["cumulative_benchmark"].cummax()).min()

    # Save results
    os.makedirs("results/backtests_monthly", exist_ok=True)
    df.to_csv("results/backtests_monthly/ms_monthly.csv", index=False)
    with open("results/backtests_monthly/ms_monthly_portfolio.json", "w") as f:
        json.dump(portfolios, f, indent=2)

    # Print results
    print("\nMS (Monthly Long-Short) Backtest Complete.")
    print(df.tail())

    print(f"\nStrategy Metrics:")
    print(f" Final Strategy Return: {final_return:.2%}")
    print(f" Strategy Volatility: {volatility:.2%}")
    print(f"  Sharpe Ratio: {sharpe:.2f}")
    print(f" Sortino Ratio: {sortino:.2f}")
    print(f" Max Drawdown: {max_dd:.2%}")
    print(f" Win Rate vs Benchmark: {win_rate:.2%}")

    print(f"\nBenchmark Metrics:")
    print(f" Final Benchmark Return: {final_benchmark:.2%}")
    print(f" Benchmark Volatility: {benchmark_volatility:.2%}")
    print(f"  Sharpe Ratio: {benchmark_sharpe:.2f}")
    print(f" Sortino Ratio: {benchmark_sortino:.2f}")
    print(f" Max Drawdown: {benchmark_max_dd:.2%}")

if __name__ == "__main__":
    backtest_ms()
