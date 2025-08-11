import os
import json
from pathlib import Path
from tqdm import tqdm
from groq_manager import GroqAPIManager
import time
import re

# === PATHS ===
price_dir = Path("results/summaries_price/weekly")
fund_dir = Path("results/summaries_fundamentals/weekly")
news_dir = Path("results/summaries_news/weekly")
macro_dir = Path("results/summaries_macro/weekly")
output_dir = Path("results/signals/weekly")
output_dir.mkdir(parents=True, exist_ok=True)

# === GROQ LLM WRAPPER ===
groq = GroqAPIManager()

# === Extract volatility and sharpe ratio from price summary ===
def extract_volatility_sharpe(text: str):
    try:
        vol_match = re.search(r"Volatility\s*[:=]\s*([\d.]+)", text)
        sharpe_match = re.search(r"Sharpe\s*Ratio\s*[:=]\s*([-]?\d*\.?\d+)", text)

        volatility = float(vol_match.group(1)) if vol_match else None
        sharpe = float(sharpe_match.group(1)) if sharpe_match else None

        return volatility, sharpe
    except Exception as e:
        print(f"[WARN] Could not extract metrics: {e}")
        return None, None

# === Prompt Builder ===
def build_prompt(ticker, week):
    try:
        price_path = price_dir/week/f"{ticker}.txt"
        fund_path = fund_dir/week/f"{ticker}_fundamentals.txt"
        news_path = news_dir/week/f"{ticker}_news.txt" 
        macro_path = macro_dir/week/"summary.txt"

        price_summary = open(price_path, encoding='utf-8').read()
        fund_summary = open(fund_path, encoding='utf-8').read()
        
        # Correctly handle missing news file
        if news_path.exists() and news_path.is_file():
           news_summary = open(news_path, encoding='utf-8').read()
        else:
            news_summary = "No specific news available for this company during this week."

        macro_summary = open(macro_path, encoding='utf-8').read()

        # volatility, sharpe = extract_volatility_sharpe(price_summary)
        # if volatility is None or sharpe is None:
        #     raise ValueError("Missing volatility or sharpe ratio")

    except Exception as e:
        raise RuntimeError(f"[ERROR] Missing file or extraction issue for {ticker} - {week}: {e}")

    prompt = f"""
### Price Trend:
{price_summary}

### Fundamentals:
{fund_summary}

### News Sentiment:
{news_summary}

### Macroeconomic Environment:
{macro_summary}

You are a financial analyst.

Use chain-of-thought reasoning to evaluate the stock.
Output only in the below format ,reasoning should be in 3-4 lines:

{{
  "decision": "<BUY/SELL/HOLD>",
  "confidence": <integer 1 to 10>,
  "volatility": value of volatility,
  "sharpe_ratio": value of sharpe ratio ,
  "reasoning": "<step-by-step explanation>"
}}
"""
    return prompt.strip()

# === Main Loop ===
def generate_signals_all(start_week: str = None, specific_tickers: list = None):
    all_weeks = sorted(os.listdir(price_dir))
    
    if start_week:
        try:
            start_index = all_weeks.index(start_week)
            weeks_to_process = all_weeks[start_index:]
            print(f"Starting signal generation from week: {start_week}")
        except ValueError:
            print(f"[ERROR] Specified start_week '{start_week}' not found in available weeks.")
            print(f"Available weeks are: {', '.join(all_weeks)}")
            return
    else:
        weeks_to_process = all_weeks
        print("Starting signal generation from the beginning of available weeks.")

    for week in weeks_to_process:
        print(f"\n[PROCESSING WEEK] {week}")
        week_price_folder = price_dir / week
        
        if not week_price_folder.exists() or not os.listdir(week_price_folder):
            print(f"[WARN] No price data found for week {week}. Skipping.")
            continue

        all_tickers_in_week = [f.replace(".txt", "") for f in os.listdir(week_price_folder) if f.endswith(".txt")]
        
        if specific_tickers:
            # Filter tickers based on the provided list
            tickers_to_process = [t for t in all_tickers_in_week if t in specific_tickers]
            if not tickers_to_process:
                print(f"[WARN] No specified tickers found in week {week}. Skipping.")
                continue
            else:
                print(f"Processing specific tickers: {', '.join(tickers_to_process)}")
        else:
            tickers_to_process = all_tickers_in_week

        for ticker in tqdm(tickers_to_process, desc=f"Generating signals for {week}"):
            try:
                prompt = build_prompt(ticker, week)
                # time.sleep(5)
                response = groq.generate(prompt)

                out_path = output_dir / week / f"{ticker}.json"
                out_path.parent.mkdir(parents=True, exist_ok=True)

                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(response)

                print(f"[OK] {ticker} - {week}")
            except Exception as e:
                print(f"[ERROR] {ticker} - {week}: {e}")

if __name__ == "__main__":
    # Example usage:

    # 1. To process all weeks for all companies:
    # generate_signals_all() 

    # 2. To start from a specific week for all companies:
    # generate_signals_all(start_week="2025-03-09") 
    
    # 3. To process specific companies for all available weeks:
    # generate_signals_all(specific_tickers=["AAPL", "MSFT"])

    # 4. To process specific companies starting from a specific week:
    generate_signals_all(start_week="2025-06-01", specific_tickers=["ASIANPAINT","DIVISLAB","DRREDDY"])