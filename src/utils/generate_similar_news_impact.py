import os
import pandas as pd
from pathlib import Path
from similarity_with_impact import get_similar_news_with_impact
from tqdm import tqdm

news_base = Path("data/news/weekly")
tickers = [f.replace(".csv", "") for f in os.listdir(news_base / "2024-03-03")]

# All weeks from your weekly folder
weeks = sorted(os.listdir(news_base))

for week_str in tqdm(weeks, desc="Processing Weeks"):
    week_path = news_base / week_str
    if not week_path.is_dir():
        continue

    for ticker in os.listdir(week_path):
        if not ticker.endswith(".csv"):
            continue
        ticker_name = ticker.replace(".csv", "")
        try:
            df = pd.read_csv(week_path / ticker)
            for _, row in df.iterrows():
                query = row.get("Heading") or row.get("title") or row.get("headline")
                if isinstance(query, str) and query.strip():
                    get_similar_news_with_impact(query.strip(), ticker_name, week_str)
        except Exception as e:
            print(f"[ERROR] {ticker_name} - {week_str}: {e}")
