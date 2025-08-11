import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

PRICE_FOLDER = "data/prices/weekly"
SIGNAL_FOLDER = "results/signals/weekly"
BENCHMARK = "NSEI"

def get_next_week_date(week_str):
    return (datetime.strptime(week_str, "%Y-%m-%d") + timedelta(days=7)).strftime("%Y-%m-%d")

def get_weekly_return(price_path):
    try:
        df = pd.read_csv(price_path)
        return (df["Close"].iloc[-1] - df["Close"].iloc[0]) / df["Close"].iloc[0]
    except:
        return None

def calculate_drawdown(cumulative_returns):
    peak = cumulative_returns.expanding(min_periods=1).max()
    drawdown = (cumulative_returns - peak) / peak
    return drawdown.min()

def backtest_ms():
    weeks = sorted(os.listdir(SIGNAL_FOLDER))
    portfolio = set()
    results = []

    for i in range(len(weeks) - 1):
        current_week = weeks[i]
        next_week = get_next_week_date(current_week)
        signal_path = os.path.join(SIGNAL_FOLDER, current_week)
        next_price_path = os.path.join(PRICE_FOLDER, next_week)

        if not os.path.exists(next_price_path):
            print(f"[SKIP] Missing price data for next week: {next_week}")
            continue

        new_portfolio = set()
        returns = []

        for file in os.listdir(signal_path):
            if not file.endswith(".json"):
                continue

            ticker = file.replace(".json", "")
            json_path = os.path.join(signal_path, file)

            try:
                with open(json_path) as f:
                    signal_data = json.load(f)
                    signal = signal_data["decision"].strip().upper()
            except Exception as e:
                print(f"[ERROR] {file}: {e}")
                continue

            if signal == "BUY":
                new_portfolio.add(ticker)
            elif signal == "HOLD" and ticker in portfolio:
                new_portfolio.add(ticker)
            # SELL: do not add

        for ticker in new_portfolio:
            price_file = os.path.join(next_price_path, f"{ticker}.csv")
            ret = get_weekly_return(price_file)
            if ret is not None:
                returns.append(ret)

        strategy_return = sum(returns) / len(returns) if returns else 0

        nifty_file = os.path.join(next_price_path, f"{BENCHMARK}.csv")
        benchmark_return = get_weekly_return(nifty_file) or 0

        results.append({
            "week": current_week,
            "strategy_return": strategy_return,
            "benchmark_return": benchmark_return,
            "buy_list": sorted(list(new_portfolio))
        })

        portfolio = new_portfolio  # update for next iteration
        print(f"\n[{current_week}]")
        print(f" Strategy Return: {strategy_return:.2%} | Benchmark: {benchmark_return:.2%}")
        print(f" Portfolio Stocks: {', '.join(sorted(new_portfolio)) or 'None'}")

    # ---- Save results ----
    df = pd.DataFrame(results)
    df["excess_return"] = df["strategy_return"] - df["benchmark_return"]
    df["cumulative_strategy"] = (1 + df["strategy_return"]).cumprod()
    df["cumulative_benchmark"] = (1 + df["benchmark_return"]).cumprod()

    # Metrics
    final_return = df["cumulative_strategy"].iloc[-1] - 1
    final_benchmark = df["cumulative_benchmark"].iloc[-1] - 1
    volatility = np.std(df["strategy_return"])* np.sqrt(64)
    sharpe = (final_return-0.06)/volatility
    sortino = (final_return-0.06) / ((np.std([r for r in df["strategy_return"] if r < 0]))*np.sqrt(64))
    drawdown = calculate_drawdown(df["cumulative_strategy"])
    winrate = np.mean(df["strategy_return"] > df["benchmark_return"])
    

    # Save CSV
    os.makedirs("results/backtests", exist_ok=True)
    df.to_csv("results/backtests/benchmark_weekly.csv", index=False)

    # Summary
    print("\n MarketSense Strategy Backtest Complete.")
    print(f" Final Strategy Return: {final_return:.2%}")
    print(f" Final Benchmark Return: {final_benchmark:.2%}")
    print(f" Volatility: {volatility:.2%}")
    print(f" Sharpe Ratio: {sharpe:.2f}")
    print(f" Sortino Ratio: {sortino:.2f}")
    print(f" Max Drawdown: {drawdown:.2%}")
    print(f" Win Rate: {winrate:.2%}")

if __name__ == "__main__":
    backtest_ms()
