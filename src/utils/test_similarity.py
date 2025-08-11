# src/utils/test_similarity.py

from similarity_search import search_similar

query = "Adani Group faces allegations of financial misconduct"
results = search_similar(query, top_k=3)

for i, r in enumerate(results, 1):
    print(f"Result {i}:")
    print("Title:", r.get("article_title", "N/A"))
    print("Date:", r.get("article_date", "N/A"))
    print("Text:", r.get("chunk", "")[:200], "...\n")
