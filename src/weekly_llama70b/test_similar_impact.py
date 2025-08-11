from utils.similarity_with_impact import get_similar_news_with_impact

query = "Adani plans big investment next quarter"
ticker = "ADANIENT"
week_str = "2024-03-03"

similar = get_similar_news_with_impact(query, ticker, week_str)
print(similar)
