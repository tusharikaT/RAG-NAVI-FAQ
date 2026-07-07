"""
Runs Phase 4 evaluations (End-to-End RAG Chain with Groq LLM)
"""
from rag.retriever import retrieve
from rag.prompt_builder import build_prompt
from rag.generator import generate
from rag.formatter import format_response
import logging

logging.getLogger("httpx").setLevel(logging.WARNING)

def run_e2e_rag():
    print("--- 4.3 End-to-End RAG Chain Evaluation ---")
    
    test_queries = [
        "What is the expense ratio of Navi Nifty 50?",
        "What is the exit load for Navi ELSS?",
        "Minimum SIP for Navi Liquid Fund"
    ]
    
    for i, query in enumerate(test_queries):
        print(f"\n[{i+1}/3] Query: '{query}'")
        
        # 1. Retrieve
        print("  Retrieving context...")
        chunks = retrieve(query, k=5)
        
        # Get source metadata from the best matching chunk
        best_chunk = chunks[0]["metadata"]
        source_url = best_chunk.get("source_url", "URL not found")
        scraped_at = best_chunk.get("scraped_at", "Date not found")
        
        # 2. Build Prompt
        print("  Building prompt...")
        prompt = build_prompt(query, chunks)
        
        # 3. Generate
        print("  Calling Groq LLM...")
        llm_output = generate(prompt)
        
        # 4. Format
        print("  Formatting response...")
        final_response = format_response(llm_output, source_url, scraped_at)
        
        # Print final
        print("\n--- RAG Response ---")
        print(final_response["answer"])
        print()
        print(f"Source: {final_response['citation']}")
        print(final_response["footer"])
        print(final_response["disclaimer"])
        print("--------------------\n")
        
        # Simple assertions
        assert len(final_response["answer"]) > 10, "Answer too short"
        assert "navi" in final_response["citation"].lower(), "Invalid citation link"
        assert "Facts-only" in final_response["disclaimer"], "Disclaimer missing"

if __name__ == "__main__":
    print("=== Running Phase 4 Evaluations ===")
    run_e2e_rag()
    print("[OK] All Phase 4 Evaluations Passed! The End-to-End RAG Chain works.")
