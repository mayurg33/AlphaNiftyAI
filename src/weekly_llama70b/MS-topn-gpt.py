import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

PRICE_FOLDER = "data/prices/weekly"
SIGNAL_FOLDER = "results/signals/weekly"
BENCHMARK = "NSEI"
TOP_N = 10

def get_next_week_date(week_str):
    return (datetime.strptime(week_str, "%Y-%m-%d") + timedelta(days=7)).strftime("%Y-%m-%d")

def get_weekly_return(price_path):
    try:
        df = pd.read_csv(price_path)
        return (df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0]
    except:
        return None

def calculate_drawdown(cumulative_returns):
    peak = cumulative_returns.expanding(min_periods=1).max()
    drawdown = (cumulative_returns - peak) / peak
    return drawdown.min()

def backtest_topn_gpt():
    weeks = sorted(os.listdir(SIGNAL_FOLDER))
    strategy_returns = []
    benchmark_returns = []
    valid_weeks = []
    weekly_portfolios = {}

    for week in weeks:
        week_path = os.path.join(SIGNAL_FOLDER, week)
        if not os.path.isdir(week_path):
            continue

        next_week = get_next_week_date(week)
        next_week_price_dir = os.path.join(PRICE_FOLDER, next_week)
        if not os.path.exists(next_week_price_dir):
            print(f"[SKIP] No next week data for {next_week}")
            continue

        candidates = []

        for filename in os.listdir(week_path):
            if not filename.endswith(".json"):
                continue
            ticker = filename.replace(".json", "")
            with open(os.path.join(week_path, filename)) as f:
                try:
                    data = json.load(f)
                    if data["decision"].strip().upper() == "BUY":
                        candidates.append((ticker, data.get("confidence", 0)))
                except:
                    continue

        topn = sorted(candidates, key=lambda x: x[1], reverse=True)[:TOP_N]
        portfolio = [ticker for ticker, _ in topn]
        weekly_portfolios[week] = portfolio

        returns = []
        for ticker in portfolio:
            price_path = os.path.join(next_week_price_dir, f"{ticker}.csv")
            r = get_weekly_return(price_path)
            if r is not None:
                returns.append(r)

        avg_return = np.mean(returns) if returns else 0
        strategy_returns.append(avg_return)

        nifty_path = os.path.join(next_week_price_dir, f"{BENCHMARK}.csv")
        benchmark_return = get_weekly_return(nifty_path) or 0
        benchmark_returns.append(benchmark_return)
        valid_weeks.append(week)

        print(f"\nWeek: {week}")
        print(f" Strategy Return: {avg_return:.2%} | Benchmark Return: {benchmark_return:.2%}")
        print(f" Portfolio: {portfolio}")

    df = pd.DataFrame({
        "week": valid_weeks,
        "strategy_return": strategy_returns,
        "benchmark_return": benchmark_returns
    })

    df["excess_return"] = df["strategy_return"] - df["benchmark_return"]
    df["cumulative_strategy"] = (1 + df["strategy_return"]).cumprod()
    df["cumulative_benchmark"] = (1 + df["benchmark_return"]).cumprod()

    final_return = df["cumulative_strategy"].iloc[-1] - 1
    final_benchmark = df["cumulative_benchmark"].iloc[-1] - 1
    volatility = np.std(df["strategy_return"])* np.sqrt(64)
    sharpe = (final_return-0.06)/volatility
    sortino = (final_return-0.06) / ((np.std([r for r in df["strategy_return"] if r < 0]))*np.sqrt(64))
    max_dd = calculate_drawdown(df["cumulative_strategy"])
    win_rate = np.mean(df["strategy_return"] > df["benchmark_return"])

    os.makedirs("results/backtests", exist_ok=True)
    df.to_csv("results/backtests/topn_gpt.csv", index=False)
    with open("results/backtests/topn_gpt_portfolio.json", "w") as f:
        json.dump(weekly_portfolios, f, indent=2)

    print("\n MS-TopN-GPT Strategy Backtest Complete.")
    print(df.tail())
    print(f"\n Final Strategy Return: {final_return:.2%}")
    print(f" Final Benchmark Return: {final_benchmark:.2%}")
    print(f" Volatility: {volatility:.2%}")
    print(f"  Sharpe Ratio: {sharpe:.2f}")
    print(f" Sortino Ratio: {sortino:.2f}")
    print(f" Max Drawdown: {max_dd:.2%}")
    print(f" Win Rate: {win_rate:.2%}")

if __name__ == "__main__":
    backtest_topn_gpt()
