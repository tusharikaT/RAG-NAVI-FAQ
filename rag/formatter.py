"""
rag/formatter.py
Post-processes the LLM output into a standard structured format.
"""

import re

def format_response(llm_output: str, source_url: str, scraped_date: str) -> dict:
    """
    Format the raw string output from the LLM into a dictionary
    matching the response format specification in the architecture document.
    """
    if not llm_output:
        llm_output = "I don't have that information."
        
    # Strip hallucinated URLs from the answer text
    llm_output = re.sub(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+', '', llm_output)
    # Clean up trailing spaces or "visit" phrases left behind
    llm_output = re.sub(r'(?i)For more (?:details|information)(?:,|) (?:you can )?visit\s*\.?', '', llm_output)
    llm_output = llm_output.replace(' .', '.').strip()
        
    return {
        "answer": llm_output,
        "citation": source_url or "URL unavailable",
        "footer": f"Last updated from sources: {scraped_date or 'date unavailable'}",
        "disclaimer": "Facts-only. No investment advice."
    }
