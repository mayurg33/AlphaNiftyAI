# src/utils/similarity_with_impact.py

import json
from pathlib import Path
from .similarity_search import search_similar
from price_impact import get_next_week_stock_return

def get_similar_news_with_impact(query, ticker, week_str, top_k=3):
    results = search_similar(query, top_k=top_k)
    enriched = []

    for r in results:
        article_title = r.get("article_title", "")
        article_date = r.get("article_date", "")
        impact = get_next_week_stock_return(ticker, article_date)

        enriched.append({
            "title": article_title,
            "date": article_date,
            "impact": f"{impact:+.2f}%" if impact is not None else "N/A"
        })

    # Save to file
    out_dir = Path(f"results/similar_news_impact/{week_str}")
    out_dir.mkdir(parents=True, exist_ok=True)
    out_path = out_dir / f"{ticker}.json"

    with open(out_path, "a", encoding="utf-8") as f:
        json.dump({"query": query, "similar": enriched}, f, ensure_ascii=False)
        f.write("\n")  # JSONL format

    return enriched
query = "Adani Enterprises facing SEBI probe over accounting irregularities"
ticker = "ADANIENT"
week_str = "2024-03-10"

similar = get_similar_news_with_impact(query, ticker, week_str)
print(similar)