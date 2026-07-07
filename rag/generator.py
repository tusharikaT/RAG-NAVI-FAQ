"""
rag/generator.py
LLM integration with Groq via LangChain, including rate-limit handling and fallbacks.
"""
import os
import logging
from dotenv import load_dotenv
from langchain_groq import ChatGroq
from tenacity import retry, wait_random_exponential, stop_after_attempt, retry_if_exception_type
from groq import RateLimitError, InternalServerError

# Load GROQ_API_KEY from .env
load_dotenv()
api_key = os.getenv("GROQ_API_KEY")
if not api_key:
    raise ValueError("GROQ_API_KEY not found in environment variables.")

# Primary and Fallback Models
PRIMARY_MODEL = "llama-3.3-70b-versatile"
FALLBACK_MODEL = "llama-3.1-8b-instant"

def _get_llm(model_name: str) -> ChatGroq:
    """Initialize the ChatGroq client with the specified model."""
    return ChatGroq(
        model=model_name,
        temperature=0.0,
        max_tokens=256,
        api_key=api_key
    )

# Retry logic: Wait up to 10 seconds between retries, max 3 attempts.
# Only retry on rate limits or server errors.
@retry(
    wait=wait_random_exponential(multiplier=1, max=10),
    stop=stop_after_attempt(3),
    retry=retry_if_exception_type((RateLimitError, InternalServerError)),
    reraise=True
)
def _generate_with_retry(llm: ChatGroq, prompt: str) -> str:
    """Call the LLM with automatic retries on rate limits (429) or server errors (5xx)."""
    response = llm.invoke(prompt)
    return response.content

def generate(prompt: str) -> str:
    """
    Generate an answer using the primary model. 
    If rate limits completely block the primary model after 3 retries,
    it falls back to the secondary model.
    """
    primary_llm = _get_llm(PRIMARY_MODEL)
    
    try:
        logging.info(f"Attempting generation with {PRIMARY_MODEL}...")
        return _generate_with_retry(primary_llm, prompt)
    except Exception as e:
        logging.warning(f"Primary model ({PRIMARY_MODEL}) failed: {e}. Falling back to {FALLBACK_MODEL}...")
        
        fallback_llm = _get_llm(FALLBACK_MODEL)
        try:
            return _generate_with_retry(fallback_llm, prompt)
        except Exception as fallback_e:
            logging.error(f"Fallback model also failed: {fallback_e}")
            return "I am currently experiencing high traffic and cannot generate an answer at this moment. Please try again later."
