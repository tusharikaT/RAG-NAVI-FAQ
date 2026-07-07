"""
rag/refusal.py
Refusal handler – returns polite refusals for advisory/non-factual queries.
"""

def refusal_response() -> dict:
    """Returns a standardized polite refusal response."""
    return {
        "answer": "This assistant provides factual information only and cannot offer investment advice or fund recommendations.",
        "educational_link": "https://www.amfiindia.com/investor-corner/knowledge-center",
        "disclaimer": "Facts-only. No investment advice."
    }
