import os
import json
import pandas as pd
import numpy as np
from datetime import datetime

PRICE_FOLDER = "data/prices/"
SIGNAL_FOLDER = "results/signals"
BENCHMARK = "^NSEI"
CONFIDENCE_THRESHOLD = 7

def get_next_month(month_str):
    dt = datetime.strptime(month_str, "%Y-%m")
    next_month = dt.month % 12 + 1
    next_year = dt.year + (dt.month // 12)
    return f"{next_year}-{next_month:02d}"

def get_monthly_return(price_path):
    try:
        df = pd.read_csv(price_path)
        return (df["Close"].iloc[-1] - df["Close"].iloc[0]) / df["Close"].iloc[0]
    except:
        return None

def calculate_drawdown(cumulative_returns):
    peak = cumulative_returns.expanding(min_periods=1).max()
    drawdown = (cumulative_returns - peak) / peak
    return drawdown.min()

def backtest_ms_high_gpt():
    months = sorted([m for m in os.listdir(SIGNAL_FOLDER) if m <= "2025-05"])
    strategy_returns, benchmark_returns, valid_months = [], [], []
    portfolios = {}

    for month in months:
        signal_dir = os.path.join(SIGNAL_FOLDER, month)
        next_month = get_next_month(month)
        next_price_dir = os.path.join(PRICE_FOLDER, next_month)

        if not os.path.exists(next_price_dir):
            print(f"[SKIP] No price data for {next_month}")
            continue

        portfolio = []
        for filename in os.listdir(signal_dir):
            if not filename.endswith(".json"): continue
            ticker = filename.replace(".json", "")
            path = os.path.join(signal_dir, filename)

            try:
                with open(path) as f:
                    data = json.load(f)
                    if isinstance(data, str):
                        data = json.loads(data)

                    if data.get("decision", "").upper() == "BUY" and int(data.get("confidence", 0)) <= CONFIDENCE_THRESHOLD:
                        portfolio.append(ticker)
            except Exception as e:
                print(f"[ERROR] {month} | {filename}: {e}")
                continue

        if not portfolio:
            strategy_returns.append(0)
            benchmark_returns.append(0)
            valid_months.append(month)
            portfolios[month] = []
            print(f"[{month}] No qualifying stocks.")
            continue

        returns = []
        for ticker in portfolio:
            price_path = os.path.join(next_price_dir, f"{ticker}.csv")
            ret = get_monthly_return(price_path)
            if ret is not None:
                returns.append(ret)

        avg_return = np.mean(returns) if returns else 0
        strategy_returns.append(avg_return)

        benchmark_path = os.path.join(next_price_dir, f"{BENCHMARK}.csv")
        bench_return = get_monthly_return(benchmark_path) or 0
        benchmark_returns.append(bench_return)

        valid_months.append(month)
        portfolios[month] = portfolio

        print(f"[{month}] Strategy Return: {avg_return:.2%} | Benchmark: {bench_return:.2%} | Portfolio: {portfolio}")

    df = pd.DataFrame({
        "month": valid_months,
        "strategy_return": strategy_returns,
        "benchmark_return": benchmark_returns
    })

    df["excess_return"] = df["strategy_return"] - df["benchmark_return"]
    df["cumulative_strategy"] = (1 + df["strategy_return"]).cumprod()
    df["cumulative_benchmark"] = (1 + df["benchmark_return"]).cumprod()

    final_return = df["cumulative_strategy"].iloc[-1] - 1
    benchmark_final = df["cumulative_benchmark"].iloc[-1] - 1
    volatility = np.std(df["strategy_return"])* np.sqrt(64)
    sharpe = (final_return-0.06)/volatility
    sortino = (final_return-0.06) / ((np.std([r for r in df["strategy_return"] if r < 0]))*np.sqrt(64))
    max_dd = calculate_drawdown(df["cumulative_strategy"])
    win_rate = np.mean(df["strategy_return"] > df["benchmark_return"])

    os.makedirs("results/backtests/monthly", exist_ok=True)
    df.to_csv("results/backtests/monthly/ms_high_gpt.csv", index=False)
    with open("results/backtests/monthly/ms_high_gpt_portfolio.json", "w") as f:
        json.dump(portfolios, f, indent=2)

    print("\n MS-High-GPT Backtest Complete.")
    print(df.tail())
    print(f"\n Final Strategy Return: {final_return:.2%}")
    print(f" Final Benchmark Return: {benchmark_final:.2%}")
    print(f" Strategy Volatility: {volatility:.2%}")
    print(f" Sharpe Ratio: {sharpe:.2f}")
    print(f" Sortino Ratio: {sortino:.2f}")
    print(f" Max Drawdown: {max_dd:.2%}")
    print(f" Win Rate (vs Benchmark): {win_rate:.2%}")

if __name__ == "__main__":
    backtest_ms_high_gpt()
