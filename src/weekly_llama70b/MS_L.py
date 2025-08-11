import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

PRICE_FOLDER = "data/prices/weekly"
SIGNAL_FOLDER = "results/signals/weekly"
BENCHMARK = "NSEI"

def get_next_week_date(week_str):
    week_date = datetime.strptime(week_str, "%Y-%m-%d")
    next_week = week_date + timedelta(days=7)
    return next_week.strftime("%Y-%m-%d")

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

def backtest_buy_only():
    weeks = sorted(os.listdir(SIGNAL_FOLDER))
    portfolio_returns = []
    benchmark_returns = []
    valid_weeks = []
    companies_bought_all = []

    for week in weeks:
        tickers_path = os.path.join(SIGNAL_FOLDER, week)
        if not os.path.isdir(tickers_path):
            continue

        next_week = get_next_week_date(week)
        next_week_price_dir = os.path.join(PRICE_FOLDER, next_week)

        if not os.path.exists(next_week_price_dir):
            print(f"[SKIP] No price data for next week: {next_week}")
            continue

        returns_this_week = []
        companies_bought = []

        for signal_file in os.listdir(tickers_path):
            if not signal_file.endswith(".json"):
                continue

            ticker = signal_file.replace(".json", "")
            signal_path = os.path.join(tickers_path, signal_file)

            try:
                with open(signal_path) as f:
                    signal_data = json.load(f)
                    signal = signal_data.get("decision", "").strip().upper()
            except Exception as e:
                print(f"[ERROR] {signal_path}: {e}")
                continue

            if signal != "BUY":
                continue

            price_csv = os.path.join(next_week_price_dir, f"{ticker}.csv")
            ret = get_weekly_return(price_csv)
            if ret is not None:
                returns_this_week.append(ret)
                companies_bought.append(ticker)

        if returns_this_week:
            avg_return = sum(returns_this_week) / len(returns_this_week)
        else:
            avg_return = 0

        nifty_path = os.path.join(next_week_price_dir, f"{BENCHMARK}.csv")
        nifty_return = get_weekly_return(nifty_path) or 0

        portfolio_returns.append(avg_return)
        benchmark_returns.append(nifty_return)
        valid_weeks.append(week)
        companies_bought_all.append(", ".join(companies_bought))

        print(f"\n[{week}]")
        print(f" Strategy Return: {avg_return:.2%}")
        print(f" Benchmark Return: {nifty_return:.2%}")
        print(f" Bought Companies: {companies_bought if companies_bought else 'None'}")

    # Create DataFrame
    df = pd.DataFrame({
        "week": valid_weeks,
        "strategy_return": portfolio_returns,
        "benchmark_return": benchmark_returns,
        "bought_companies": companies_bought_all
    })

    df["excess_return"] = df["strategy_return"] - df["benchmark_return"]
    df["cumulative_strategy"] = (1 + df["strategy_return"]).cumprod()
    df["cumulative_benchmark"] = (1 + df["benchmark_return"]).cumprod()

    final_strategy_return = df["cumulative_strategy"].iloc[-1] - 1
    final_benchmark_return = df["cumulative_benchmark"].iloc[-1] - 1

    volatility = np.std(df["strategy_return"])* np.sqrt(64)
    sharpe = (final_strategy_return-0.06)/volatility
    sortino = (final_strategy_return-0.06) / ((np.std([r for r in df["strategy_return"] if r < 0]))*np.sqrt(64))

    max_drawdown = calculate_drawdown(df["cumulative_strategy"])
    win_rate = np.mean(df["strategy_return"] > df["benchmark_return"])

    os.makedirs("results/backtests", exist_ok=True)
    df.to_csv("results/backtests/buy_only_ms_l.csv", index=False)

    print("\n Final Metrics:")
    print(f" Final Strategy Return: {final_strategy_return:.2%}")
    print(f" Final Benchmark Return: {final_benchmark_return:.2%}")
    print(f" Strategy Volatility: {volatility:.2%}")
    print(f" Sharpe Ratio: {sharpe:.2f}")
    print(f" Sortino Ratio: {sortino:.2f}")
    print(f" Max Drawdown: {max_drawdown:.2%}")
    print(f" Win Rate: {win_rate:.2%}")

if __name__ == "__main__":
    backtest_buy_only()
