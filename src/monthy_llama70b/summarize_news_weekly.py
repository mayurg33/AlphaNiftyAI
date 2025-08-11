import os
import json
import pandas as pd
from tqdm import tqdm
from pathlib import Path
from dotenv import load_dotenv
from weekly_llama70b.groq_manager import GroqAPIManager

from utils.similarity_with_impact import get_similar_news_with_impact

# Load environment variables
load_dotenv()

# Initialize GROQ API Manager
groq = GroqAPIManager()

# Paths
news_base = Path("data/news/weekly")
impact_base = Path("results/similar_news_impact")
summary_base = Path("results/summaries_news/weekly")
summary_base.mkdir(parents=True, exist_ok=True)

# Get all weekly folders
weeks = sorted([p.name for p in news_base.iterdir() if p.is_dir()])

def build_prompt(current_articles, historical_news):
    prompt = "You are a financial assistant. Summarize the news sentiment for the company based on the following information.\n\n"

    prompt += "### This Week's News Articles:\n"
    for i, row in current_articles.iterrows():
        prompt += f"- [{row['Date']}] {row['Heading']} ({row['Source']})\n"

    prompt += "\n### Similar Historical News with Stock Price Impact:\n"
    if historical_news:
        for item in historical_news:
            prompt += f"- [{item['date']}] {item['title']} | Impact: {item['impact']}\n"
    else:
        prompt += "No similar past news found.\n"

    prompt += "\n### Task:\nSummarize the overall news sentiment and any insights. Be concise and use clear language.End with an overall sentiment: Positive / Neutral / Negative.\n"

    return prompt

def summarize_weekly_news():
    for week in tqdm(weeks, desc="Processing Weeks"):
        week_path = news_base / week
        for file in os.listdir(week_path):
            if not file.endswith(".csv"):
                continue
            ticker = file.replace(".csv", "")
            try:
                df = pd.read_csv(week_path / file)
                if df.empty:
                    continue

                # Use first article as representative
                representative_query = df["Heading"].iloc[0]

                # Load past similar news
                impact_path = impact_base / week / f"{ticker}.jsonl"
                if impact_path.exists():
                    with open(impact_path, "r", encoding="utf-8") as f:
                        entries = [json.loads(line) for line in f]
                        past_news = entries[0]["similar"] if entries else []
                else:
                    past_news = get_similar_news_with_impact(representative_query, ticker, week)

                # Prompt + response
                prompt = build_prompt(df, past_news)
                response = groq.generate(prompt)

                # Save summary
                out_dir = summary_base / week
                out_dir.mkdir(parents=True, exist_ok=True)
                with open(out_dir / f"{ticker}_news.txt", "w", encoding="utf-8") as f:
                    f.write(response)

                print(f"[ok] {ticker} - {week}")
            except Exception as e:
                print(f"[ERROR] {ticker} - {week}: {e}")

if __name__ == "__main__":
    summarize_weekly_news()
