"""
Query ChromaDB and view the matching chunks and their distances.
"""
import chromadb
from sentence_transformers import SentenceTransformer
import logging

# Silence telemetry logs
logging.getLogger("chromadb").setLevel(logging.ERROR)

import sys

BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "

def query_db(query_text: str, top_k: int = 10):
    print(f"Loading embedding model to encode the query: '{query_text}'...")
    model = SentenceTransformer("BAAI/bge-base-en-v1.5", device="cpu")
    
    # 1. Embed the query (with the required BGE prefix)
    full_query = BGE_QUERY_PREFIX + query_text
    query_embedding = model.encode(
        [full_query], 
        normalize_embeddings=True
    ).tolist()

    # 2. Connect to Chroma
    client = chromadb.PersistentClient(path="./data/chroma_db")
    collection = client.get_collection("navi_funds")

    print(f"\nSearching database for the top {top_k} closest vectors...\n")
    
    # 3. Query the database
    results = collection.query(
        query_embeddings=query_embedding,
        n_results=top_k,
        include=["documents", "metadatas", "distances"]
    )

    if not results["documents"] or not results["documents"][0]:
        print("No results found.")
        return

    # 4. Display results
    for i in range(len(results["documents"][0])):
        doc = results["documents"][0][i]
        meta = results["metadatas"][0][i]
        
        distance = results["distances"][0][i]
        similarity = 1.0 - distance
        
        print(f"--- Rank {i+1} (Similarity: {similarity:.4f}) ---")
        print(f"Fund   : {meta['fund_name']}")
        print(f"Section: {meta['section']}")
        print(f"Text   :\n{doc.strip()}")
        print("-" * 50 + "\n")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        user_query = " ".join(sys.argv[1:])
    else:
        print("Usage: python view_embeddings.py \"your query here\"")
        print("Example: python view_embeddings.py \"nav of large cap\"")
        sys.exit(1)
        
    query_db(user_query, top_k=10)
