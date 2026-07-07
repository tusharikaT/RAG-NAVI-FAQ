import logging
import chromadb
from sentence_transformers import SentenceTransformer

# Silence chromadb telemetry logs
logging.getLogger("chromadb").setLevel(logging.ERROR)

BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "
_model = None
_collection = None

def _get_model():
    global _model
    if _model is None:
        _model = SentenceTransformer("BAAI/bge-base-en-v1.5", device="cpu")
    return _model

def _get_collection():
    global _collection
    if _collection is None:
        client = chromadb.PersistentClient(path="./data/chroma_db")
        _collection = client.get_collection("navi_funds")
    return _collection

def retrieve(query: str, k: int = 10) -> list[dict]:
    """
    Embed the query and retrieve the top K most similar chunks from ChromaDB.
    """
    model = _get_model()
    collection = _get_collection()

    full_query = BGE_QUERY_PREFIX + query
    query_embedding = model.encode([full_query], normalize_embeddings=True).tolist()

    results = collection.query(
        query_embeddings=query_embedding,
        n_results=k,
        include=["documents", "metadatas", "distances"]
    )

    chunks = []
    if not results["documents"] or not results["documents"][0]:
        return chunks

    for i in range(len(results["documents"][0])):
        chunks.append({
            "text": results["documents"][0][i],
            "metadata": results["metadatas"][0][i],
            "distance": results["distances"][0][i],
        })

    return chunks
