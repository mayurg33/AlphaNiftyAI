import os
import json
import pandas as pd
import numpy as np
from datetime import datetime
from dateutil.relativedelta import relativedelta

# --- Configuration ---
SIGNAL_DIR = "results/signals"
PRICE_DIR = "data/prices"
BENCHMARK = "^NSEI" # Assumes benchmark file is named ^NSEI.csv (e.g., ^NSEI.csv)
OUTPUT_CSV = "results/backtests/ms_l_monthly.csv"

# --- Helper Functions ---

def get_next_month(month_str):
    """Calculates the string representation of the month following the given month."""
    dt = datetime.strptime(month_str, "%Y-%m")
    next_month = dt + relativedelta(months=1)
    return next_month.strftime("%Y-%m")

def get_return(price_path):
    """
    Calculates the monthly return from a price CSV file.
    Assumes CSV has 'Date' and 'Close' columns.
    Returns the return as a decimal (e.g., 0.05 for 5%).
    Returns None if data is insufficient or file cannot be processed.
    """
    try:
        # Read CSV, set 'Date' as index, and parse dates
        df = pd.read_csv(price_path, index_col="Date", parse_dates=True)
        # Ensure data is sorted by date for correct start/end prices
        df = df.sort_index()

        # Check for sufficient data
        if df.empty or len(df) < 2:
            # print(f"Warning: Insufficient data in {price_path} for return calculation.") # Optional: for debugging
            return None
        
        start_price = df['Close'].iloc[0]
        end_price = df['Close'].iloc[-1]
        
        # Calculate return as a decimal
        return (end_price - start_price) / start_price
    except FileNotFoundError:
        # print(f"Warning: Price file not found: {price_path}") # Optional: for debugging
        return None
    except KeyError:
        # print(f"Warning: 'Close' or 'Date' column missing in {price_path}.") # Optional: for debugging
        return None
    except Exception as e:
        # print(f"An unexpected error occurred while processing {price_path}: {e}") # Optional: for debugging
        return None

def calculate_drawdown(cum_returns):
    """Calculates the maximum drawdown given cumulative returns (decimal)."""
    peak = cum_returns.cummax()
    dd = (cum_returns - peak) / peak # Drawdown as a decimal
    return dd.min()

# --- Main Backtesting Function ---

def backtest_ms_l():
    # Get all months for which signals are available and sort them
    # The original code had a fixed range, adapting to list available signal months
    # Ensure your signal directories (e.g., results/signals/2024-03) exist
    all_signal_months = sorted([m for m in os.listdir(SIGNAL_DIR) if os.path.isdir(os.path.join(SIGNAL_DIR, m))])
    
    # Filter months if a specific range is desired, or use all_signal_months
    # Example: months = [m for m in all_signal_months if "2024-03" <= m <= "2025-05"]
    months_to_process = all_signal_months 
    
    strategy_returns = [] # Stores monthly strategy returns (decimal)
    benchmark_returns = [] # Stores monthly benchmark returns (decimal)
    valid_months = [] # Stores months that were successfully processed
    portfolios = {} # To store the list of tickers that were 'BUY' for each month

    print("Starting MS-L (Monthly Buy-Only) Backtest...\n")

    for month in months_to_process:
        signal_path = os.path.join(SIGNAL_DIR, month)
        
        # Determine the price data month (signals from month N predict returns for month N+1)
        next_month = get_next_month(month)
        price_data_path_for_returns = os.path.join(PRICE_DIR, next_month)
        
        # Skip if price data for the next month is missing
        if not os.path.exists(price_data_path_for_returns):
            print(f"[SKIP] No price data directory for {next_month} (needed for returns from {month}'s signals).")
            continue

        buy_tickers_in_month = []
        monthly_picked_stock_returns = [] # Returns of individual stocks selected by strategy for this month

        # Iterate through all signal files for the current month
        for file in os.listdir(signal_path):
            if not file.endswith(".json"):
                continue
            
            ticker = file.replace(".json", "")
            signal_file_full_path = os.path.join(signal_path, file)
            
            try:
                with open(signal_file_full_path, 'r') as f:
                    signal_data = json.load(f)
                    
                # Check if the decision is 'BUY'
                decision = signal_data.get("decision", "").strip().upper()
                if decision == "BUY":
                    stock_price_file = os.path.join(price_data_path_for_returns, f"{ticker}.csv")
                    
                    # Get the return for the picked stock
                    stock_return = get_return(stock_price_file)
                    if stock_return is not None:
                        monthly_picked_stock_returns.append(stock_return)
                        buy_tickers_in_month.append(ticker)
                    # else:
                        # print(f"   [INFO] No return calculated for {ticker} from {stock_price_file}") # Uncomment for verbose info
            except json.JSONDecodeError:
                print(f"[ERROR] Could not decode JSON from {signal_file_full_path}. Skipping this signal.")
                continue
            except Exception as e:
                print(f"[ERROR] Problem processing signal file {signal_file_full_path}: {e}")
                continue

        # Calculate average strategy return for this month (equal-weighted portfolio of BUY signals)
        avg_strategy_return = np.mean(monthly_picked_stock_returns) if monthly_picked_stock_returns else 0

        # Calculate benchmark return for this month
        benchmark_price_file = os.path.join(price_data_path_for_returns, f"{BENCHMARK}.csv")
        benchmark_return = get_return(benchmark_price_file) or 0 # Use 0 if benchmark return couldn't be calculated

        # Store results for this month
        strategy_returns.append(avg_strategy_return)
        benchmark_returns.append(benchmark_return)
        valid_months.append(month)
        portfolios[month] = buy_tickers_in_month

        print(f"[{month}] Strategy Return: {avg_strategy_return:.2%} | Benchmark Return: {benchmark_return:.2%} | Buys: {buy_tickers_in_month}")

    # Create DataFrame from collected monthly returns
    df = pd.DataFrame({
        "month": valid_months,
        "strategy_return": strategy_returns,
        "benchmark_return": benchmark_returns
    })

    # Calculate additional performance metrics
    df["excess_return"] = df["strategy_return"] - df["benchmark_return"]
    # Cumulative returns: (1 + decimal return) multiplied across months
    df["cumulative_strategy"] = (1 + df["strategy_return"]).cumprod()
    df["cumulative_benchmark"] = (1 + df["benchmark_return"]).cumprod()

    # --- Performance Statistics Calculation ---
    final_ret = df["cumulative_strategy"].iloc[-1] - 1
    bench_final = df["cumulative_benchmark"].iloc[-1] - 1
    
    # Volatility (Standard Deviation of Monthly Returns)
    volatility = np.std(df["strategy_return"])* np.sqrt(15)
    sharpe = (final_ret-0.06)/volatility
    sortino = (final_ret-0.06) / ((np.std([r for r in df["strategy_return"] if r < 0]))*np.sqrt(15))

    max_dd = calculate_drawdown(df["cumulative_strategy"])
    
    # Win Rate: Percentage of months where strategy outperformed benchmark
    winrate = np.mean(df["strategy_return"] > df["benchmark_return"])

    # --- Save Results and Print Summary ---
    os.makedirs(os.path.dirname(OUTPUT_CSV), exist_ok=True)
    df.to_csv(OUTPUT_CSV, index=False)

    print("\n--- MS-L (Monthly Buy-Only) Backtest Summary ---")
    print(df.tail()) # Show last few rows of the detailed monthly returns
    print(f"\n Final Strategy Return: {final_ret:.2%}")
    print(f" Benchmark Return: {bench_final:.2%}")
    print(f" Volatility (Std Dev of Monthly Returns): {volatility:.2%}")
    print(f" Sharpe Ratio: {sharpe:.2f}")
    print(f" Sortino Ratio: {sortino:.2f}")
    print(f" Max Drawdown: {max_dd:.2%}")
    print(f" Win Rate (Strategy > Benchmark): {winrate:.2%}")
    print(f"\n Detailed monthly returns saved to: {OUTPUT_CSV}")

if __name__ == "__main__":
    backtest_ms_l()