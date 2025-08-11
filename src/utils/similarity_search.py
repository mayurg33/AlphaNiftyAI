import faiss
import pickle
import numpy as np
import pandas as pd
from sentence_transformers import SentenceTransformer

# Define file paths
INDEX_FILE = "src/utils/faiss_index.bin"
CHUNK_METADATA_FILE = "src/utils/chunk_metadata.pkl"
DATA_FILE = "src/utils/news_data.xlsx"

# Global variables (Lazy Loading)
_index = None
_all_chunks = None
_article_mapping = None
_df = None
_model = None

def load_resources():
    """Load the FAISS index, metadata, and model only once."""
    global _index, _all_chunks, _article_mapping, _df, _model
    if _index is None:
        print(" Loading FAISS index and metadata...")
        _index = faiss.read_index(INDEX_FILE)
        with open(CHUNK_METADATA_FILE, "rb") as f:
            _all_chunks, _article_mapping = pickle.load(f)
        _df = pd.read_excel(DATA_FILE)
        _model = SentenceTransformer("all-MiniLM-L6-v2")
        print(f" Loaded {_index.ntotal} chunks from FAISS index.")

def search_similar(query, top_k=3, chunk_threshold=3):
    """Search for similar articles based on chunk similarity."""
    if _index is None:
        load_resources()  # Ensure resources are loaded before search

    query_vector = _model.encode([query]).astype(np.float32)
    
    # Search for more chunks than top_k to ensure good article coverage
    k_chunks = min(top_k * chunk_threshold, _index.ntotal)
    distances, indices = _index.search(query_vector, k_chunks)
    
    # Track article scores
    article_scores = {}
    for idx, score in zip(indices[0], distances[0]):
        if idx != -1:
            chunk_text = _all_chunks[idx]
            chunk_info = _article_mapping[chunk_text]
            article_idx = chunk_info['article_idx']
            
            if article_idx not in article_scores:
                article_scores[article_idx] = {
                    'min_score': float('inf'),
                    'total_score': 0,
                    'chunk_count': 0,
                    'chunks': []
                }
            
            article_scores[article_idx]['min_score'] = min(article_scores[article_idx]['min_score'], score)
            article_scores[article_idx]['total_score'] += score
            article_scores[article_idx]['chunk_count'] += 1
            article_scores[article_idx]['chunks'].append({
                'text': chunk_text,
                'score': score,
                'position': chunk_info['chunk_position']
            })
    
    # Prepare results
    results = []
    for article_idx, scores in article_scores.items():
        avg_score = scores['total_score'] / scores['chunk_count']
        article_title = _df.iloc[article_idx]["title"]
        article_description = _df.iloc[article_idx]["description"]
        article_stocks = _df.iloc[article_idx]["stocks"]
        article_date = _df.iloc[article_idx]["date"]
        
        results.append({
            'article_idx': article_idx,
            'score': avg_score,
            'min_score': scores['min_score'],
            'chunk_count': scores['chunk_count'],
            'article_title': article_title,
            'article_description': article_description,
            'article_stocks': article_stocks,
            'article_date': article_date,
            'matched_chunks': sorted(scores['chunks'], key=lambda x: x['position'])
        })
    
    results.sort(key=lambda x: x['min_score'])
    return results[:top_k]

def display_results(results, show_chunks=False):
    """Pretty print search results"""
    print("\nTop Similar Articles:")
    for i, result in enumerate(results, 1):
        print(f"\n{'-'*80}")
        print(f"Article Index: {result['article_idx']}")  # Original dataset index
        print(f"Article {i}:")
        print(f"Score: {result['score']:.4f} (Best chunk: {result['min_score']:.4f})")
        print(f"Matching chunks: {result['chunk_count']}")
        print(f"\nArticle Preview:")
        print(f"{result['article_title'][:500]}...")
        
        if show_chunks:
            print("\nMatched Chunks:")
            for chunk in result['matched_chunks']:
                print(f"\nChunk {chunk['position']+1} (Score: {chunk['score']:.4f}):")
                print(chunk['text'])
results=search_similar("adani")
display_results(results)