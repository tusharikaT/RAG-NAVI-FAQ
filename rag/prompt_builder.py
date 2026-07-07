"""
rag/prompt_builder.py
Assembles the structured LLM prompt with retrieved context and constraints.
"""

SYSTEM_PROMPT_TEMPLATE = """You are a facts-only mutual fund FAQ assistant.
Answer in max 3 sentences.
NEVER include URLs, website links, or 'https://' anywhere in your response.
Never provide investment advice, comparisons, or return predictions.
Only use the provided context. If the answer is not in the context, say "I don't have that information."

CONTEXT:
{retrieved_chunks}

QUESTION:
{user_query}

ANSWER:"""

def build_prompt(query: str, chunks: list[dict]) -> str:
    """
    Build the final prompt string using the retrieved chunks and user query.
    Returns the formatted string ready to be sent to the LLM.
    """
    # Join chunk texts with double newlines
    context_text = "\n\n".join([chunk["text"] for chunk in chunks])
    
    return SYSTEM_PROMPT_TEMPLATE.format(
        retrieved_chunks=context_text,
        user_query=query
    )
