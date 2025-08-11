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

def get_weekly_return_with_trailing_stop(price_path, stop_loss=TRAILING_STOP_LOSS):
    df = pd.read_csv(price_path)
    if df.empty or len(df) < 2:
        return None, None, None

    entry_price = df['Close'].iloc[0]
    max_price = entry_price
    exit_price = df['Close'].iloc[-1]  # default: last day

    for i in range(1, len(df)):
        price = df['Close'].iloc[i]
        max_price = max(max_price, price)
        drawdown = (max_price - price) / max_price
        if drawdown > stop_loss:
            exit_price = price
            df = df.iloc[:i+1]  # truncate till stop-loss breach day
            break

    weekly_return = (exit_price - entry_price) / entry_price
    returns = df['Close'].pct_change().dropna()
    volatility = returns.std() if not returns.empty else 0
    max_drawdown = ((df['Close'].cummax() - df['Close']) / df['Close'].cummax()).max()

    return weekly_return, volatility, max_drawdown

def backtest_nifty_plus_with_stoploss():
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
                ret, vol, drawdown = get_weekly_return_with_trailing_stop(price_csv)
            except:
                continue

            if drawdown is None or drawdown > TRAILING_STOP_LOSS:
                continue

            buy_returns.append(ret)
            portfolio.append(ticker)

        avg_return = np.mean(buy_returns) if buy_returns else 0

        benchmark_path = os.path.join(price_dir, f"{BENCHMARK}.csv")
        try:
            bench_return, _, _ = get_weekly_return_with_trailing_stop(benchmark_path, stop_loss=1.0)  # no stop-loss on benchmark
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
    volatility = np.std(df["strategy_return"])
    sharpe = np.mean(df["strategy_return"]) / (volatility + 1e-8)
    downside = np.std([r for r in df["strategy_return"] if r < 0]) or 1e-8
    sortino = np.mean(df["strategy_return"]) / downside
    max_drawdown = ((df["cumulative_strategy"] - df["cumulative_strategy"].cummax()) / df["cumulative_strategy"].cummax()).min()
    win_rate = np.mean(df["strategy_return"] > df["benchmark_return"])

    os.makedirs("results/backtests", exist_ok=True)
    df.to_csv("results/backtests/nifty_plus_stoploss.csv", index=False)
    with open("results/backtests/nifty_plus_portfolio_stoploss.json", "w") as f:
        json.dump(portfolios, f, indent=2)

    print("\n NIFTY++ Backtest with Stop-Loss Complete.")
    print(df.tail())
    print(f"\n Final Strategy Return: {final_strategy_return:.2%}")
    print(f" Final Benchmark Return: {final_benchmark_return:.2%}")
    print(f" Strategy Volatility: {volatility:.2%}")
    print(f" Sharpe Ratio: {sharpe:.2f}")
    print(f" Sortino Ratio: {sortino:.2f}")
    print(f" Max Drawdown: {max_drawdown:.2%}")
    print(f" Win Rate (vs Benchmark): {win_rate:.2%}")

if __name__ == "__main__":
    backtest_nifty_plus_with_stoploss()
