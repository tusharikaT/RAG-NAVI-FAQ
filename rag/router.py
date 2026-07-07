"""
rag/router.py
Central query router – classifies intent and dispatches to retriever or refusal handler.
"""
from rag.classifier import classify_query
from rag.refusal import refusal_response
from rag.retriever import retrieve
from rag.prompt_builder import build_prompt
from rag.generator import generate
from rag.formatter import format_response

def handle_query(query: str) -> dict:
    """
    Main entry point for the RAG pipeline.
    Classifies the intent, retrieves context if factual, and generates an answer.
    """
    if classify_query(query) == "ADVISORY":
        return refusal_response()
        
    chunks = retrieve(query, k=10)
    
    prompt = build_prompt(query, chunks)
    answer = generate(prompt)
    
    if chunks:
        source_url = chunks[0]["metadata"].get("source_url", "")
        scraped_at = chunks[0]["metadata"].get("scraped_at", "")
    else:
        source_url = ""
        scraped_at = ""
        
    return format_response(answer, source_url, scraped_at)
