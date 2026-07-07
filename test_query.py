"""
Simple script to test a single query through the complete RAG pipeline.
"""
import sys
import logging
from rag.retriever import retrieve
from rag.prompt_builder import build_prompt
from rag.generator import generate
from rag.formatter import format_response

# Silence some noisy logs
logging.getLogger("httpx").setLevel(logging.WARNING)

def test_query(query: str):
    print(f"\n--- Processing Query: '{query}' ---\n")
    
    print("1. Retrieving context...")
    chunks = retrieve(query, k=5)
    
    if not chunks:
        print("No chunks found!")
        return
        
    best_chunk = chunks[0]["metadata"]
    source_url = best_chunk.get("source_url", "URL not found")
    scraped_at = best_chunk.get("scraped_at", "Date not found")
    
    print("2. Building prompt...")
    prompt = build_prompt(query, chunks)
    
    print("3. Generating response via Groq...")
    llm_output = generate(prompt)
    
    print("4. Formatting...")
    final_response = format_response(llm_output, source_url, scraped_at)
    
    print("\n--- FINAL OUTPUT ---\n")
    print(final_response["answer"])
    print("\nSource:", final_response["citation"])
    print(final_response["footer"])
    print(final_response["disclaimer"])
    print("\n--------------------\n")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        query = " ".join(sys.argv[1:])
    else:
        query = "expense ratio of nifty it index"
        
    test_query(query)
