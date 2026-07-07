# Navi Mutual Fund FAQ Assistant

A highly accurate, "Facts-Only" RAG (Retrieval-Augmented Generation) assistant dedicated to answering factual questions about **Navi Mutual Funds**. It utilizes semantic vector search (ChromaDB + BGE) combined with LLM generation (Groq Llama-3 70b) to answer user queries with precise source citations.

## Project Overview

The project provides an end-to-end question-answering system that strictly limits hallucination and advisory content. If a user asks for investment advice (e.g. "Should I invest in Navi Flexi Cap?"), the query intent classifier politely refuses to answer. All factual responses are restricted to a maximum of 3 sentences and include exactly one source citation URL.

## Architecture

The system is composed of several components:
1. **Data Ingestion Pipeline**: Scrapes and indexes official fund URLs into a ChromaDB vector store.
2. **Query Intent Classifier**: Pre-filters queries to ensure only factual requests hit the retrieval engine.
3. **Retrieval-Augmented Generation (RAG)**: Retrieves top vector matches (`k=10`) and generates an answer via Groq.
4. **FastAPI Backend**: Provides a standard HTTP `POST` endpoint for querying.
5. **Next.js UI**: A modern, glassmorphic frontend built with React and TailwindCSS.

For deeper details, see our full [Architecture Document](docs/architecture.md) and [Implementation Plan](docs/implementation_plan.md).

## Setup & Run Instructions

### 1. Prerequisites
- Python 3.11+
- Node.js (for Next.js frontend)
- A valid [Groq API Key](https://console.groq.com/keys)

### 2. Backend Setup
```bash
# Install Python dependencies
pip install -r requirements.txt

# Create .env and set your Groq key
echo "GROQ_API_KEY=your_key_here" > .env
```

### 3. Data Ingestion
You must populate the vector database first:
```bash
python main.py --ingest-only
```
*Note: We have also configured a GitHub Action scheduler to run this daily at 10:00 AM IST.*

### 4. Running the App
**Start Backend (Terminal 1):**
```bash
python -m uvicorn app.api:app --host 127.0.0.1 --port 8000
```
**Start Frontend (Terminal 2):**
```bash
cd frontend
npm run dev
```

Visit `http://localhost:3000` to interact with the assistant!

## Selected AMC & Schemes
The corpus currently tracks the following Navi funds:
- Navi Nifty 50 Index Fund
- Navi Nifty Next 50 Index Fund
- Navi Nifty Bank Index Fund
- Navi Nifty Midcap 150 Index Fund
- Navi Nifty India Defence Index Fund
- Navi US Total Stock Market Fund of Fund
- Navi Nasdaq 100 Fund of Fund
- Navi Flexi Cap Fund
- Navi ELSS Tax Saver Nifty 50 Index Fund
- Navi Large & Midcap Fund
- Navi Liquid Fund
- Navi Aggressive Hybrid Fund
- Navi Arbitrage Fund
- Navi Nifty IT Index Fund
- Navi BSE Sensex Index Fund

## Known Limitations
- The system uses HTML string scraping which is susceptible to layout changes on Groww.in.
- The `sentence-transformers` embeddings (BGE) run locally on CPU; ingestion can be slow on low-end machines.
- Responses are tightly constrained to 3 sentences, which may sometimes cut off highly detailed process questions.

## Disclaimer
⚠️ **Facts-only. No investment advice.** All generated text should be verified against the official Scheme Information Documents (SID). This system does not recommend funds or guarantee returns.
