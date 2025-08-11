import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

PRICE_FOLDER = "data/prices/weekly"
SIGNAL_FOLDER = "results/signals/weekly"
BENCHMARK = "NSEI"
TRAILING_STOP_LOSS = 0.05  # 5%
VOLATILITY_WEIGHT_POWER = 1.0  # Inverse weighting by volatility

def get_next_week_date(week_str):
    return (datetime.strptime(week_str, "%Y-%m-%d") + timedelta(days=7)).strftime("%Y-%m-%d")

def get_weekly_return_and_volatility(price_path):
    try:
        df = pd.read_csv(price_path)
        returns = df['Close'].pct_change().dropna()
        ret = (df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0]
        vol = np.std(returns)
        return ret, vol, df['Close']
    except:
        return None, None, None

def backtest_nifty_plus():
    weeks = sorted(os.listdir(SIGNAL_FOLDER))
    portfolio_returns = []
    benchmark_returns = []
    valid_weeks = []
    portfolios = {}

    for week in weeks:
        signal_dir = os.path.join(SIGNAL_FOLDER, week)
        if not os.path.isdir(signal_dir):
            continue

        next_week = get_next_week_date(week)
        next_week_price_dir = os.path.join(PRICE_FOLDER, next_week)
        if not os.path.exists(next_week_price_dir):
            print(f"[SKIP] No price data for next week: {next_week}")
            continue

        selected = []
        for file in os.listdir(signal_dir):
            if not file.endswith(".json"):
                continue
            ticker = file.replace(".json", "")
            try:
                with open(os.path.join(signal_dir, file)) as f:
                    data = json.load(f)
                    if data.get("decision", "").upper() == "BUY":
                        selected.append(ticker)
            except:
                continue

        scores = []
        for ticker in selected:
            price_path = os.path.join(next_week_price_dir, f"{ticker}.csv")
            ret, vol, close_series = get_weekly_return_and_volatility(price_path)
            if ret is not None and vol is not None and vol > 0:
                # Trailing stop-loss check
                peak = close_series.cummax()
                drawdown = (peak - close_series) / peak
                if drawdown.max() > TRAILING_STOP_LOSS:
                    continue
                weight = 1 / (vol ** VOLATILITY_WEIGHT_POWER)
                scores.append((ticker, ret, weight))

        if not scores:
            portfolio_returns.append(0)
            benchmark_returns.append(0)
            valid_weeks.append(week)
            portfolios[week] = []
            continue

        df_scores = pd.DataFrame(scores, columns=["ticker", "return", "weight"])
        df_scores["weight"] = df_scores["weight"] / df_scores["weight"].sum()
        weighted_return = (df_scores["return"] * df_scores["weight"]).sum()

        benchmark_path = os.path.join(next_week_price_dir, f"{BENCHMARK}.csv")
        benchmark_return, _, _ = get_weekly_return_and_volatility(benchmark_path)
        benchmark_return = benchmark_return or 0

        portfolio_returns.append(weighted_return)
        benchmark_returns.append(benchmark_return)
        valid_weeks.append(week)
        portfolios[week] = df_scores["ticker"].tolist()

        print(f"\n Week: {week} |  Return: {weighted_return:.2%} |  Benchmark: {benchmark_return:.2%}")
        print(f" Portfolio: {df_scores['ticker'].tolist()}")

    df = pd.DataFrame({
        "week": valid_weeks,
        "strategy_return": portfolio_returns,
        "benchmark_return": benchmark_returns
    })

    df["excess_return"] = df["strategy_return"] - df["benchmark_return"]
    df["cumulative_strategy"] = (1 + df["strategy_return"]).cumprod()
    df["cumulative_benchmark"] = (1 + df["benchmark_return"]).cumprod()

    # Metrics
    final_return = df["cumulative_strategy"].iloc[-1] - 1
    benchmark_final = df["cumulative_benchmark"].iloc[-1] - 1
    volatility = np.std(df["strategy_return"])
    sharpe = np.mean(df["strategy_return"]) / (volatility + 1e-8)
    downside = np.std([r for r in df["strategy_return"] if r < 0]) or 1e-8
    sortino = np.mean(df["strategy_return"]) / downside
    max_dd = df["cumulative_strategy"].expanding().max() - df["cumulative_strategy"]
    max_drawdown = max_dd.max() / df["cumulative_strategy"].expanding().max()

    # Save
    os.makedirs("results/backtests", exist_ok=True)
    df.to_csv("results/backtests/nifty_plus.csv", index=False)
    with open("results/backtests/nifty_plus_portfolio.json", "w") as f:
        json.dump(portfolios, f, indent=2)

    # Summary
    print("\n NIFTY++ Backtest Complete")
    print(df.tail())
    print(f"\n Final Strategy Return: {final_return:.2%}")
    print(f" Final Benchmark Return: {benchmark_final:.2%}")
    print(f" Volatility: {volatility:.2%}")
    print(f"  Sharpe Ratio: {sharpe:.2f}")
    print(f" Sortino Ratio: {sortino:.2f}")
    print(f" Max Drawdown: {max_drawdown:.2%}")

if __name__ == "__main__":
    backtest_nifty_plus()
