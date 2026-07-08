from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional
import sys
import os

# Ensure the root directory is in sys.path so we can import from rag
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from rag.router import handle_query

app = FastAPI(title="Navi MF FAQ Assistant API")

# Add CORS middleware to allow requests from the Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # For local dev, allow all origins
    allow_credentials=False,  # Browsers reject credentials with wildcard origins
    allow_methods=["*"],
    allow_headers=["*"],
)

class QueryRequest(BaseModel):
    query: str

@app.post("/api/v1/query")
def query_assistant(req: QueryRequest):
    """
    Accepts a user query, routes it through the RAG pipeline using semantic search, 
    and returns a structured factual answer or a polite refusal.
    """
    response_dict = handle_query(req.query)
    return response_dict
