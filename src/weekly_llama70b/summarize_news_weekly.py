# src/weekly_llama70b/summarize_news_weekly.py
import time
import os
import json
import pandas as pd
from tqdm import tqdm
from pathlib import Path
from groq_manager import GroqAPIManager

# Paths
weekly_news_dir = Path("data/news/weekly")
impact_dir = Path("results/similar_news_impact")
output_dir = Path("results/summaries_news/weekly")
output_dir.mkdir(parents=True, exist_ok=True)

# Load GROQ Manager
groq = GroqAPIManager()

def load_historical_impact(week, ticker):
    """Loads the saved similar news with price impact for a company-week."""
    impact_path = impact_dir / week / f"{ticker}.json"
    if not impact_path.exists():
        return ""
    
    lines = []
    with open(impact_path, "r", encoding="utf-8") as f:
        for line in f:
            obj = json.loads(line)
            lines.append(f"\nQuery: {obj['query']}")
            for s in obj['similar']:
                lines.append(f"- {s['date']} | {s['title']} | Impact: {s['impact']}")
    
    return "\n".join(lines)

def build_prompt(news_items, historical_impact):
    """Constructs the full summarization prompt."""
    prompt = "Weekly News:\n"
    for i, row in enumerate(news_items.itertuples(), 1):
        prompt += f"{i}. {row.Heading}\n"

    # if historical_impact.strip():
    prompt += "Historical Similar News and Price Impact:\n"
    prompt += historical_impact

    prompt += "\nSummarize the current week's news sentiment, mention notable events, and whether the news tone is positive, neutral, or negative for the stock."
    return prompt

def summarize_all():
    weeks = sorted(os.listdir(weekly_news_dir))
    for week in weeks:
        print(f"\n[PROCESSING WEEK] {week}")
        week_folder = weekly_news_dir / week
        tickers = [f.replace(".csv", "") for f in os.listdir(week_folder)]

        for ticker in tqdm(tickers, desc=f"Summarizing {week}"):
            try:
                df = pd.read_csv(week_folder / f"{ticker}.csv")
                if df.empty:
                    continue

                historical_impact = load_historical_impact(week, ticker)
                prompt = build_prompt(df, historical_impact)
                # print(prompt)
                response = groq.generate(prompt)
                time.sleep(5)
                out_path = output_dir / week / f"{ticker}_news.txt"
                out_path.parent.mkdir(parents=True, exist_ok=True)
                with open(out_path, "w", encoding="utf-8") as f:
                    f.write(response)

                print(f"[OK] {ticker} - {week}")

            except Exception as e:
                print(f"[ERROR] {ticker} - {week}: {e}")
            
if __name__ == "__main__":
    summarize_all()
