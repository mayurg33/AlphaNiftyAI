import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

PRICE_FOLDER = "data/prices/weekly"
SIGNAL_FOLDER = "results/signals/weekly"
BENCHMARK = "NSEI"
TRAILING_STOP_LOSS = 0.05

def get_next_week_date(week_str):
    week_date = datetime.strptime(week_str, "%Y-%m-%d")
    next_week = week_date + timedelta(days=7)
    return next_week.strftime("%Y-%m-%d")

def get_weekly_return_and_volatility(price_path):
    df = pd.read_csv(price_path)
    returns = df['Close'].pct_change().dropna()
    weekly_return = (df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0]
    volatility = np.std(returns)
    close_series = df['Close']
    peak = close_series.cummax()
    drawdown = (peak - close_series) / peak
    max_drawdown = drawdown.max()
    return weekly_return, volatility, max_drawdown

def backtest_nifty_plus_simple_average():
    weeks = sorted(os.listdir(SIGNAL_FOLDER))
    strategy_returns = []
    benchmark_returns = []
    valid_weeks = []
    portfolios = {}

    for week in weeks:
        next_week = get_next_week_date(week)
        signal_dir = os.path.join(SIGNAL_FOLDER, week)
        price_dir = os.path.join(PRICE_FOLDER, next_week)

        if not os.path.exists(price_dir):
            print(f"[SKIP] Missing price data for next week: {next_week}")
            continue

        buy_returns = []
        portfolio = []

        for file in os.listdir(signal_dir):
            if not file.endswith(".json"):
                continue
            ticker = file.replace(".json", "")
            signal_path = os.path.join(signal_dir, file)

            try:
                with open(signal_path) as f:
                    signal = json.load(f).get("decision", "").strip().upper()
            except:
                continue

            if signal != "BUY":
                continue

            price_csv = os.path.join(price_dir, f"{ticker}.csv")
            if not os.path.exists(price_csv):
                continue

            try:
                ret, vol, drawdown = get_weekly_return_and_volatility(price_csv)
            except:
                continue

            if drawdown > TRAILING_STOP_LOSS:
                continue

            buy_returns.append(ret)
            portfolio.append(ticker)

        # Equal weight average return
        avg_return = np.mean(buy_returns) if buy_returns else 0

        # Benchmark return
        benchmark_path = os.path.join(price_dir, f"{BENCHMARK}.csv")
        try:
            bench_return, _, _ = get_weekly_return_and_volatility(benchmark_path)
        except:
            bench_return = 0

        strategy_returns.append(avg_return)
        benchmark_returns.append(bench_return)
        valid_weeks.append(week)
        portfolios[week] = portfolio

        print(f"[{week}] Strategy: {avg_return:.2%} | Benchmark: {bench_return:.2%} | Portfolio: {portfolio}")

    df = pd.DataFrame({
        "week": valid_weeks,
        "strategy_return": strategy_returns,
        "benchmark_return": benchmark_returns
    })

    df["excess_return"] = df["strategy_return"] - df["benchmark_return"]
    df["cumulative_strategy"] = (1 + df["strategy_return"]).cumprod()
    df["cumulative_benchmark"] = (1 + df["benchmark_return"]).cumprod()

    final_strategy_return = df["cumulative_strategy"].iloc[-1] - 1
    final_benchmark_return = df["cumulative_benchmark"].iloc[-1] - 1
    volatility = np.std(df["strategy_return"])* np.sqrt(64)
    sharpe = (final_strategy_return-0.06)/volatility
    sortino = (final_strategy_return-0.06) / ((np.std([r for r in df["strategy_return"] if r < 0]))*np.sqrt(64))
    max_drawdown = ((df["cumulative_strategy"] - df["cumulative_strategy"].cummax()) / df["cumulative_strategy"].cummax()).min()
    win_rate = np.mean(df["strategy_return"] > df["benchmark_return"])

    # Save
    os.makedirs("results/backtests", exist_ok=True)
    df.to_csv("results/backtests/nifty_plus_simple.csv", index=False)
    with open("results/backtests/nifty_plus_portfolio_simple.json", "w") as f:
        json.dump(portfolios, f, indent=2)

    # Summary
    print("\n NIFTY++ (Equal Weight, Stop-Loss) Backtest Complete.")
    print(df.tail())
    print(f"\n Final Strategy Return: {final_strategy_return:.2%}")
    print(f" Final Benchmark Return: {final_benchmark_return:.2%}")
    print(f" Strategy Volatility: {volatility:.2%}")
    print(f" Sharpe Ratio: {sharpe:.2f}")
    print(f" Sortino Ratio: {sortino:.2f}")
    print(f" Max Drawdown: {max_drawdown:.2%}")
    print(f" Win Rate (vs Benchmark): {win_rate:.2%}")
    # print(f" rsf (vs Benchmark): {strmeanreturn:.2f}")
    # print(np.std(df["strategy_return"]))
if __name__ == "__main__":
    backtest_nifty_plus_simple_average()
