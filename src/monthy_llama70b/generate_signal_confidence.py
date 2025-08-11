import os
import time
import json
import re
from tqdm import tqdm
from groq_manager_2 import GroqAPIManager
from openrouter_manager import OpenRouterAPIManager  # make sure this path is correct

# === Configuration ===
PRICE_FOLDER = "results/summaries_price"
FUNDAMENTAL_FOLDER = "results/summaries_fundamentals"
NEWS_FOLDER = "results/summaries_news"
MACRO_FOLDER = "results/summaries_macro"  # monthly macro summary is saved in data/{month}/summary.txt
SIGNAL_OUTPUT_FOLDER = "results/signals"

# === Set your desired month and tickers here ===
# Set to None to process all available months
MONTH_TO_PROCESS = "2025-05" 

# Set to an empty list [] or None to process all tickers in the selected month(s)
# Example: ["RELIANCE", "TCS", "INFY"]
TICKERS_TO_PROCESS = ["MARUTI","TCS","KOTAKBANK","WIPRO","TITAN"]
# ===============================================

groq = GroqAPIManager()
# If you want to use OpenRouter, uncomment the line below and comment out the GroqAPIManager line
# openrouter = OpenRouterAPIManager()

# === Prompt Template ===
def build_prompt(price, fundamentals, news, macro):
    return f"""You are a financial analyst AI. Based on the information provided, give a recommendation to BUY, SELL, or HOLD the stock, along with a confidence score between 1 (lowest) and 10 (highest). First reason through your decision, and then clearly state the final decision and confidence.

# Price Trends:
{price}

# Fundamentals:
{fundamentals}

# News Sentiment:
{news}

# Macroeconomic Environment:
{macro}

Use chain-of-thought reasoning to evaluate the stock.
Output only in the below format. Reasoning should be in 3–4 lines:

{{
  "decision": "<BUY/SELL/HOLD>",
  "confidence": <integer 1 to 10>,
  "reasoning": "<step-by-step explanation>"
}}
"""

# === Main Execution ===
def generate_monthly_signals(target_month=None, target_tickers=None):
    # Determine which months to process
    if target_month:
        months_to_process = [target_month]
    else:
        months_to_process = sorted(os.listdir(PRICE_FOLDER))

    for month in months_to_process:
        print(f"[PROCESSING MONTH] {month}")
        output_dir = os.path.join(SIGNAL_OUTPUT_FOLDER, month)
        os.makedirs(output_dir, exist_ok=True)

        available_tickers_in_month = [
            f.replace("_price.txt", "") for f in os.listdir(os.path.join(PRICE_FOLDER, month))
            if f.endswith("_price.txt")
        ]

        # Determine which tickers to process within the current month
        if target_tickers:
            # Convert target_tickers to uppercase for case-insensitive matching
            target_tickers_upper = [t.strip().upper() for t in target_tickers]
            tickers_to_process = [t for t in available_tickers_in_month if t.upper() in target_tickers_upper]
            if not tickers_to_process:
                print(f"[SKIP] No matching tickers found for month {month} from the provided list.")
                continue
        else:
            tickers_to_process = available_tickers_in_month


        macro_path = os.path.join(MACRO_FOLDER, month, "summary.txt")
        if not os.path.exists(macro_path):
            print(f"[SKIP] Missing macro summary for month {month}: {macro_path}")
            continue

        with open(macro_path) as f:
            macro = f.read()

        for ticker in tqdm(tickers_to_process, desc=f"Generating signals for {month}"):
            try:
                price_path = os.path.join(PRICE_FOLDER, month, f"{ticker}_price.txt")
                fund_path = os.path.join(FUNDAMENTAL_FOLDER, month, f"{ticker}.NS_fundamentals.txt")
                news_path = os.path.join(NEWS_FOLDER, month, f"{ticker}_news.txt")

                # Check if all necessary files exist for the current ticker
                if not all(os.path.exists(p) for p in [price_path, fund_path, news_path]):
                    print(f"[SKIP] Missing data for {ticker} in {month}. Skipping.")
                    continue

                with open(price_path) as f1, open(fund_path) as f2, open(news_path) as f3:
                    price = f1.read()
                    fundamentals = f2.read()
                    news = f3.read()

                prompt = build_prompt(price, fundamentals, news, macro)
                
                # Choose which API manager to use (Groq or OpenRouter)
                # For Groq:
                response_text = groq.generate(prompt)
                
                # For OpenRouter (uncomment the line below and comment out the groq.generate line above if you want to use OpenRouter):
                # response_text = openrouter.generate(prompt)

                time.sleep(5) # Add a small delay between API calls

                # Try to parse the response as JSON
                try:
                    parsed_response = json.loads(response_text)
                    decision = parsed_response.get("decision", "HOLD").strip().upper()
                    confidence = int(parsed_response.get("confidence", 5))
                    reasoning = parsed_response.get("reasoning", "").strip()
                except json.JSONDecodeError as e:
                    print(f"[PARSE ERROR] Invalid JSON for {ticker} in {month}: {e}\nResponse: {response_text}")
                    continue
                except Exception as e:
                    print(f"[PARSE ERROR] Unexpected error parsing response for {ticker} in {month}: {e}\nResponse: {response_text}")
                    continue

                result = {
                    "decision": decision,
                    "confidence": confidence,
                    "reasoning": reasoning
                }

                with open(os.path.join(output_dir, f"{ticker}.json"), "w") as fout:
                    json.dump(result, fout, indent=2)
                print(f"[SAVED] {ticker} in {month}")

            except Exception as e:
                print(f"[ERROR] Processing {ticker} in {month}: {e}")

if __name__ == "__main__":
    print("Starting Monthly Stock Signal Generation...")
    # Call the main function with the predefined variables
    generate_monthly_signals(target_month=MONTH_TO_PROCESS, target_tickers=TICKERS_TO_PROCESS)
    print("Signal generation complete.")