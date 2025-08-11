import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta

PRICE_FOLDER = "data/prices/weekly"
SIGNAL_FOLDER = "results/signals/weekly"
MARKETCAP_FILE = "data/market_cap/marketcap.csv"
BENCHMARK = "NSEI"
TOP_N =5
CONFIDENCE_THRESHOLD = 7
STOP_LOSS_THRESHOLD = 0.05  # 5%

def get_next_week_date(week_str):
    return (datetime.strptime(week_str, "%Y-%m-%d") + timedelta(days=7)).strftime("%Y-%m-%d")

def get_weekly_return_and_drawdown(price_path):
    df = pd.read_csv(price_path)
    if df.empty or len(df) < 2:
        return None, None, None

    returns = df['Close'].pct_change().dropna()
    weekly_return = (df['Close'].iloc[-1] - df['Close'].iloc[0]) / df['Close'].iloc[0]
    volatility = np.std(returns)

    peak = df['Close'].cummax()
    drawdown = (peak - df['Close']) / peak
    max_drawdown = drawdown.max()

    return weekly_return, volatility, max_drawdown

def get_marketcap_for_week(tickers, week_date_str, marketcap_df):
    week_date = datetime.strptime(week_date_str, "%Y-%m-%d")
    month_str = week_date.strftime("%Y-%m")
    sub = marketcap_df[marketcap_df["Month"] == month_str]
    sub = sub[sub["Ticker"].isin(tickers)]
    return sub.sort_values("MarketCap", ascending=False)

def calculate_drawdown(cumulative_returns):
    peak = cumulative_returns.expanding(min_periods=1).max()
    drawdown = (cumulative_returns - peak) / peak
    return drawdown.min()

def backtest_topn_cap_gpt_stoploss():
    marketcap_df = pd.read_csv(MARKETCAP_FILE)
    weeks = sorted(os.listdir(SIGNAL_FOLDER))
    strategy_returns, benchmark_returns, valid_weeks = [], [], []
    weekly_portfolios = {}

    for week in weeks:
        signal_path = os.path.join(SIGNAL_FOLDER, week)
        if not os.path.isdir(signal_path):
            continue

        next_week = get_next_week_date(week)
        price_dir = os.path.join(PRICE_FOLDER, next_week)
        if not os.path.exists(price_dir):
            print(f"[SKIP] No price data for next week: {next_week}")
            continue

        candidates = []
        for filename in os.listdir(signal_path):
            if not filename.endswith(".json"): continue
            ticker = filename.replace(".json", "")
            try:
                with open(os.path.join(signal_path, filename)) as f:
                    data = json.load(f)
                    if data.get("decision", "").strip().upper() == "BUY" and data.get("confidence", 0) >= CONFIDENCE_THRESHOLD:
                        candidates.append(ticker)
            except Exception as e:
                print(f"[ERROR] {filename}: {e}")
                continue

        if not candidates:
            strategy_returns.append(0)
            benchmark_returns.append(0)
            valid_weeks.append(week)
            weekly_portfolios[week] = []
            print(f"[{week}] No qualifying stocks.")
            continue

        topn_df = get_marketcap_for_week(candidates, week, marketcap_df)
        topn_tickers = topn_df["Ticker"].head(TOP_N).tolist()

        returns = []
        filtered_portfolio = []
        for ticker in topn_tickers:
            price_path = os.path.join(price_dir, f"{ticker}.csv")
            if not os.path.exists(price_path):
                continue
            try:
                ret, vol, drawdown = get_weekly_return_and_drawdown(price_path)
                if ret is not None and drawdown is not None and drawdown <= STOP_LOSS_THRESHOLD:
                    returns.append(ret)
                    filtered_portfolio.append(ticker)
                else:
                    print(f" Skipping {ticker} due to stop-loss violation (Drawdown: {drawdown:.2%})")
            except:
                continue

        avg_return = np.mean(returns) if returns else 0
        strategy_returns.append(avg_return)

        benchmark_path = os.path.join(price_dir, f"{BENCHMARK}.csv")
        benchmark_return = get_weekly_return_and_drawdown(benchmark_path)[0] or 0
        benchmark_returns.append(benchmark_return)

        valid_weeks.append(week)
        weekly_portfolios[week] = filtered_portfolio

        print(f"\nWeek: {week}")
        print(f"Strategy Return: {avg_return:.2%} | Benchmark: {benchmark_return:.2%}")
        print(f" Portfolio: {filtered_portfolio}")

    df = pd.DataFrame({
        "week": valid_weeks,
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

    os.makedirs("results/backtests", exist_ok=True)
    df.to_csv("results/backtests/top10_cap_gpt_stoploss.csv", index=False)
    with open("results/backtests/topn_cap_gpt_stoploss_portfolio.json", "w") as f:
        json.dump(weekly_portfolios, f, indent=2)

    print("\n MS-TopN-Cap-GPT with Stop-Loss Backtest Complete.")
    print(df.tail())
    print(f"\n Final Strategy Return: {final_return:.2%}")
    print(f" Final Benchmark Return: {benchmark_final:.2%}")
    print(f" Strategy Volatility: {volatility:.2%}")
    print(f"  Sharpe Ratio: {sharpe:.2f}")
    print(f" Sortino Ratio: {sortino:.2f}")
    print(f" Max Drawdown: {max_dd:.2%}")
    print(f" Win Rate (vs Benchmark): {win_rate:.2%}")

if __name__ == "__main__":
    backtest_topn_cap_gpt_stoploss()
