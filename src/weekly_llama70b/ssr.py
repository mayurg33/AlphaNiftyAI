import os
import json
import pandas as pd
import numpy as np
from datetime import datetime, timedelta
from dateutil.relativedelta import relativedelta # To correctly get month from week_date_str

# --- Configuration ---
PRICE_FOLDER = "data/prices/weekly" # Assumes weekly price data is in these subfolders
SIGNAL_FOLDER = "results/signals/weekly" # Assumes weekly signal data is in these subfolders
MARKETCAP_FILE = "data/market_cap/marketcap.csv" # Market Cap data for monthly snapshots
BENCHMARK = "NSEI" # Benchmark ticker, assuming file is NSEI.csv
OUTPUT_FOLDER = "results/backtests" # Output folder for backtest results
OUTPUT_CSV_FILENAME = "topn_cap_gpt_weekly.csv"
OUTPUT_PORTFOLIO_FILENAME = "topn_cap_gpt_weekly_portfolio.json"

TOP_N = 10 # Select top N stocks based on confidence after filtering
CONFIDENCE_THRESHOLD = 5 # Minimum confidence score for a 'BUY' signal to be considered

# --- Helper Functions ---

def get_next_week_date(week_str):
    """Calculates the string representation of the week following the given week."""
    # week_str is typically 'YYYY-MM-DD' for the start of the week
    dt = datetime.strptime(week_str, "%Y-%m-%d")
    next_week_dt = dt + timedelta(days=7)
    return next_week_dt.strftime("%Y-%m-%d")

def get_weekly_return(price_path):
    """
    Calculates the weekly return from a stock's price CSV file.
    Assumes CSV has 'Date' and 'Close' columns.
    Returns the return as a decimal (e.g., 0.05 for 5%).
    Returns None if data is insufficient or file cannot be processed.
    """
    try:
        df = pd.read_csv(price_path, index_col="Date", parse_dates=True)
        df = df.sort_index() # Ensure data is sorted by date
        if df.empty or len(df) < 2:
            return None
        
        start_price = df['Close'].iloc[0]
        end_price = df['Close'].iloc[-1]
        
        return (end_price - start_price) / start_price
    except FileNotFoundError:
        # print(f"Warning: Price file not found: {price_path}") # Uncomment for debugging
        return None
    except KeyError:
        # print(f"Warning: 'Close' or 'Date' column missing in {price_path}.") # Uncomment for debugging
        return None
    except Exception as e:
        # print(f"An unexpected error occurred while processing {price_path}: {e}") # Uncomment for debugging
        return None

def calculate_drawdown(cumulative_returns):
    """Calculates the maximum drawdown given cumulative returns (decimal)."""
    peak = cumulative_returns.expanding(min_periods=1).max()
    drawdown = (cumulative_returns - peak) / peak
    return drawdown.min()

# --- Main Backtesting Function ---

def backtest_topn_cap_gpt_weekly():
    """
    Performs a weekly backtest selecting the top N BUY signals by confidence,
    and then weighting them by market capitalization.
    """
    
    try:
        marketcap_df = pd.read_csv(MARKETCAP_FILE)
    except FileNotFoundError:
        print(f"Error: Market cap file not found at {MARKETCAP_FILE}. Exiting.")
        return
    except Exception as e:
        print(f"Error loading market cap file: {e}. Exiting.")
        return

    # Get all weekly signal folders and sort them chronologically
    # Assumes week folders are named 'YYYY-MM-DD'
    weeks = sorted([w for w in os.listdir(SIGNAL_FOLDER) if os.path.isdir(os.path.join(SIGNAL_FOLDER, w))])

    strategy_returns, benchmark_returns, valid_weeks = [], [], []
    weekly_portfolios = {} # To store the selected tickers and their weights for each week

    print("Starting MS-TopN-Cap-GPT Weekly Backtest...\n")

    for week_str in weeks: # Renamed 'week' to 'week_str' for clarity
        signal_dir_for_week = os.path.join(SIGNAL_FOLDER, week_str)
        
        # Determine the price data directory for the *next* week (for calculating returns)
        next_week_str = get_next_week_date(week_str)
        price_dir_for_returns = os.path.join(PRICE_FOLDER, next_week_str)
        
        # Skip if price data for the next week is missing
        if not os.path.exists(price_dir_for_returns):
            print(f"[SKIP] No price data found for {next_week_str} (needed for returns from {week_str}'s signals).")
            continue

        candidate_signals = [] # List of (ticker, confidence_score) for BUY signals
        for filename in os.listdir(signal_dir_for_week):
            if not filename.endswith(".json"): continue
            
            ticker = filename.replace(".json", "")
            signal_file_path = os.path.join(signal_dir_for_week, filename)
            
            try:
                with open(signal_file_path, 'r') as f:
                    data = json.load(f)
                    
                # Handle cases where JSON might be stringified (from your monthly code)
                if isinstance(data, str): 
                    data = json.loads(data)

                decision = data.get("decision", "").strip().upper()
                confidence = int(data.get("confidence", 0))

                # Filter by decision and confidence threshold
                if decision == "BUY" and confidence >= CONFIDENCE_THRESHOLD:
                    candidate_signals.append((ticker, confidence))
            except json.JSONDecodeError:
                print(f"[ERROR] {week_str} | {filename}: Invalid JSON format. Skipping.")
                continue
            except Exception as e:
                print(f"[ERROR] {week_str} | {filename}: Problem reading or parsing signal file: {e}. Skipping.")
                continue

        # If no qualifying candidates, record zero return and continue to next week
        if not candidate_signals:
            strategy_returns.append(0)
            benchmark_returns.append(0) # Assuming benchmark also has 0 return if strategy is 0
            valid_weeks.append(week_str)
            weekly_portfolios[week_str] = []
            print(f"[{week_str}] No qualifying BUY signals found (min confidence {CONFIDENCE_THRESHOLD}).")
            continue

        # 1. Select TOP_N stocks based on confidence
        # Sort candidates by confidence in descending order and take the top N
        topn_confident_candidates = sorted(candidate_signals, key=lambda x: x[1], reverse=True)[:TOP_N]
        topn_tickers = [t for t, _ in topn_confident_candidates]

        # 2. Get Market Caps for the selected TOP_N stocks for the current week's month
        # Market cap data is typically monthly, so derive the month from the week_str
        current_month_for_mc = datetime.strptime(week_str, "%Y-%m-%d").strftime("%Y-%m")
        monthly_marketcap_df = marketcap_df[marketcap_df["Month"] == current_month_for_mc]
        
        # Filter market cap data for the selected top N tickers
        selected_tickers_market_cap = monthly_marketcap_df[monthly_marketcap_df["Ticker"].isin(topn_tickers)].copy()

        # Handle cases where market cap data is missing for selected tickers
        if selected_tickers_market_cap.empty or selected_tickers_market_cap["MarketCap"].sum() == 0:
            print(f"[{week_str}] No valid market cap data found for selected top {len(topn_tickers)} tickers. Strategy return is 0.")
            strategy_returns.append(0)
            benchmark_path = os.path.join(price_dir_for_returns, f"{BENCHMARK}.csv")
            benchmark_return = get_weekly_return(benchmark_path) or 0
            benchmark_returns.append(benchmark_return)
            valid_weeks.append(week_str)
            weekly_portfolios[week_str] = []
            continue
        
        # 3. Calculate Market Cap Weights
        selected_tickers_market_cap["Weight"] = selected_tickers_market_cap["MarketCap"] / selected_tickers_market_cap["MarketCap"].sum()

        # 4. Calculate Weighted Average Return for the strategy portfolio
        portfolio_weekly_returns = []
        portfolio_weights_normalized = []
        actual_portfolio_tickers = [] # To store tickers that actually had price data and contributed to return

        for _, row in selected_tickers_market_cap.iterrows():
            ticker = row["Ticker"]
            weight = row["Weight"]
            price_file_path = os.path.join(price_dir_for_returns, f"{ticker}.csv")
            
            stock_return = get_weekly_return(price_file_path)
            if stock_return is not None:
                portfolio_weekly_returns.append(stock_return)
                portfolio_weights_normalized.append(weight)
                actual_portfolio_tickers.append(ticker)
            # else:
                # print(f"   [INFO] No price data/return for {ticker} in {next_week_str}.") # Uncomment for verbose info
        
        # Re-normalize weights if some stocks were dropped due to missing price data
        if portfolio_weights_normalized:
            portfolio_weights_normalized = np.array(portfolio_weights_normalized) / np.sum(portfolio_weights_normalized)
            weighted_strategy_return = np.dot(portfolio_weekly_returns, portfolio_weights_normalized)
        else:
            weighted_strategy_return = 0 # If no stocks had valid returns, strategy return is 0

        strategy_returns.append(weighted_strategy_return)

        # Get Benchmark Return for the week
        benchmark_price_path = os.path.join(price_dir_for_returns, f"{BENCHMARK}.csv")
        benchmark_return = get_weekly_return(benchmark_price_path) or 0
        benchmark_returns.append(benchmark_return)

        valid_weeks.append(week_str)
        weekly_portfolios[week_str] = actual_portfolio_tickers # Store actual tickers included in the portfolio

        print(f"[{week_str}] Strategy Return: {weighted_strategy_return:.2%} | Benchmark: {benchmark_return:.2%} | Portfolio ({len(actual_portfolio_tickers)}/{len(topn_tickers)} selected): {actual_portfolio_tickers}")

    # --- Generate Final Report ---
    df = pd.DataFrame({
        "week": valid_weeks,
        "strategy_return": strategy_returns,
        "benchmark_return": benchmark_returns
    })

    df["excess_return"] = df["strategy_return"] - df["benchmark_return"]
    df["cumulative_strategy"] = (1 + df["strategy_return"]).cumprod()
    df["cumulative_benchmark"] = (1 + df["benchmark_return"]).cumprod()

    # --- Performance Statistics ---
    final_return = df["cumulative_strategy"].iloc[-1] - 1
    benchmark_final = df["cumulative_benchmark"].iloc[-1] - 1
    
    volatility = np.std(df["strategy_return"])
    # Add small epsilon to denominator to avoid division by zero
    sharpe = np.mean(df["strategy_return"]) / (volatility + 1e-8) if volatility else 0 
    
    downside_returns = [r for r in df["strategy_return"] if r < 0]
    downside_std = np.std(downside_returns) if downside_returns else 1e-8 # Avoid division by zero
    sortino = np.mean(df["strategy_return"]) / downside_std
    
    max_dd = calculate_drawdown(df["cumulative_strategy"])
    win_rate = np.mean(df["strategy_return"] > df["benchmark_return"])

    # --- Save Results ---
    os.makedirs(OUTPUT_FOLDER, exist_ok=True)
    df.to_csv(os.path.join(OUTPUT_FOLDER, OUTPUT_CSV_FILENAME), index=False)
    with open(os.path.join(OUTPUT_FOLDER, OUTPUT_PORTFOLIO_FILENAME), "w") as f:
        json.dump(weekly_portfolios, f, indent=2)

    # --- Print Summary ---
    print("\n--- MS-TopN-Cap-GPT Weekly Backtest Complete ---")
    print("\nWeekly Returns Data (last 5 rows):")
    print(df.tail())
    print(f"\n Final Strategy Return: {final_return:.2%}")
    print(f" Final Benchmark Return: {benchmark_final:.2%}")
    print(f" Strategy Volatility (Std Dev of Weekly Returns): {volatility:.2%}")
    print(f" Sharpe Ratio: {sharpe:.2f}")
    print(f" Sortino Ratio: {sortino:.2f}")
    print(f" Max Drawdown: {max_dd:.2%}")
    print(f" Win Rate (Strategy Outperforms Benchmark): {win_rate:.2%}")
    print(f"\nDetailed weekly returns saved to: {os.path.join(OUTPUT_FOLDER, OUTPUT_CSV_FILENAME)}")
    print(f"Weekly portfolio selections saved to: {os.path.join(OUTPUT_FOLDER, OUTPUT_PORTFOLIO_FILENAME)}")

if __name__ == "__main__":
    backtest_topn_cap_gpt_weekly()