"""
Runs Phase 3 evaluations (Retriever and Prompt Builder)
"""
from rag.retriever import retrieve
from rag.prompt_builder import build_prompt

def test_retriever():
    print("--- 3.1 Retriever Evaluation ---")
    
    test_cases = [
        ("What is the expense ratio of Navi Nifty 50?", "Navi Nifty 50 Index Fund Direct Growth"),
        ("Exit load for ELSS fund", "Navi ELSS Tax Saver Nifty 50 Index Fund Direct Growth"),
        ("Minimum SIP for Navi Liquid Fund", "Navi Liquid Fund Direct Growth")
    ]
    
    for query, expected_fund in test_cases:
        chunks = retrieve(query, k=3)
        assert chunks, f"No chunks returned for '{query}'"
        
        top_fund = chunks[0]["metadata"]["fund_name"]
        print(f"Query: '{query}'")
        print(f"  Top Match: {top_fund}")
        
        # Verify the top match belongs to the expected fund
        assert top_fund == expected_fund, f"Expected {expected_fund}, got {top_fund}"
        
    print("  [OK] Retriever correctly fetches relevant fund chunks.")


def test_prompt_builder():
    print("\n--- 3.2 Prompt Builder Evaluation ---")
    
    query = "What is the exit load for Navi ELSS?"
    chunks = retrieve(query, k=2)
    prompt = build_prompt(query, chunks)
    
    print(f"Generated prompt length: {len(prompt)} chars")
    
    assert "facts-only mutual fund FAQ assistant" in prompt
    assert "max 3 sentences" in prompt
    assert "Never provide investment advice" in prompt
    assert chunks[0]["text"] in prompt
    assert query in prompt
    
    print("  [OK] Prompt successfully assembled with all constraints and context.")


if __name__ == "__main__":
    print("=== Running Phase 3 Evaluations ===")
    test_retriever()
    test_prompt_builder()
    print("\n[OK] All Phase 3 Evaluations Passed! Ready for Phase 4.")
