import os
import json
from pathlib import Path
from tqdm import tqdm
from groq_manager import GroqAPIManager
import time
# Paths
input_dir = Path("data/fundamentals/weekly")
output_dir = Path("results/summaries_fundamentals/weekly")
output_dir.mkdir(parents=True, exist_ok=True)

# GROQ Manager
groq = GroqAPIManager()

def build_prompt(fundamentals):
    metrics = fundamentals.get("metrics", {})
    
    prompt = "### Company Fundamentals Summary\n"
    prompt += f"Company Name: {metrics.get('companyName')}\n"
    prompt += f"Sector: {metrics.get('sector')} | Industry: {metrics.get('industry')}\n"
    prompt += f"Market Cap: {metrics.get('marketCap')}\n\n"

    prompt += "### Valuation & Profitability Metrics:\n"
    prompt += f"- Trailing P/E: {metrics.get('trailingPE')}\n"
    prompt += f"- Forward P/E: {metrics.get('forwardPE')}\n"
    prompt += f"- ROE: {metrics.get('returnOnEquity')}\n"
    prompt += f"- EBITDA Margins: {metrics.get('ebitdaMargins')}\n"
    prompt += f"- Gross Margins: {metrics.get('grossMargins')}\n"
    prompt += f"- Profit Margins: {metrics.get('profitMargins')}\n\n"

    prompt += "### Growth Metrics:\n"
    prompt += f"- Revenue Growth: {metrics.get('revenueGrowth')}\n"
    prompt += f"- Earnings Growth: {metrics.get('earningsGrowth')}\n"
    prompt += f"- Book Value: {metrics.get('bookValue')}\n"
    prompt += f"- Dividend Yield: {metrics.get('dividendYield')}\n"
    prompt += f"- Debt to Equity Ratio: {metrics.get('debtToEquity')}\n\n"

    prompt += "Summarize the overall financial health of the company based on the above metrics. Highlight strengths, weaknesses, valuation, and debt position in 4–6 lines."
    return prompt

def summarize_weekly_fundamentals():
    weeks = sorted(os.listdir(input_dir))
    for week in weeks:
        print(f"\n[WEEK] {week}")
        week_path = input_dir / week
        output_week_dir = output_dir / week
        output_week_dir.mkdir(parents=True, exist_ok=True)

        for file in tqdm(os.listdir(week_path), desc=f"Summarizing {week}"):
            if not file.endswith(".json"):
                continue
            ticker = file.replace(".json", "")
            try:
                with open(week_path / file, "r") as f:
                    fundamentals = json.load(f)
                prompt = build_prompt(fundamentals)
                summary = groq.generate(prompt)
                time.sleep(3)
                out_path = output_week_dir / f"{ticker}_fundamentals.txt"
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(summary)
                print(f"[OK] {ticker} - {week}")
            except Exception as e:
                print(f"[ERROR] {ticker} - {week}: {e}")

if __name__ == "__main__":
    summarize_weekly_fundamentals()
