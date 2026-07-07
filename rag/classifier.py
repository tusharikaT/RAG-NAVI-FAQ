"""
rag/classifier.py
Intent classifier – distinguishes factual from advisory queries.
"""
from rag.generator import generate

ADVISORY_KEYWORDS = [
    "should I", "should i", "better fund", "recommend", "invest in",
    "which is best", "compare", "buy", "sell", "worth it",
    "safe", "good fund", "advice", "opinion", "better return"
]

def classify_query(query: str) -> str:
    """Classifies a query as 'FACTUAL' or 'ADVISORY'."""
    query_lower = query.lower()
    
    # 1. Rule-based keyword scan
    for keyword in ADVISORY_KEYWORDS:
        if keyword.lower() in query_lower:
            return "ADVISORY"
            
    # 2. Fallback: LLM Call for ambiguous queries
    prompt = f"""You are an intent classifier for a mutual fund assistant. 
Determine if the following user query is "FACTUAL" (asking for objective information, facts, data about funds) or "ADVISORY" (asking for opinions, recommendations, advice on investing, comparing which fund is better to invest in).
Respond with exactly one word: FACTUAL or ADVISORY.

Query: "{query}"
Intent:"""
    
    try:
        response = generate(prompt).strip().upper()
        if "ADVISORY" in response:
            return "ADVISORY"
    except Exception:
        pass
        
    return "FACTUAL"
