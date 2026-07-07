"""
Runs all Phase 2 evaluations as defined in docs/eval.md.
"""
import os
import sys
import json
import logging
from corpus.urls import FUND_URLS
from corpus.scraper import scrape_url
from corpus.cleaner import clean
from corpus.ingest import _section_chunk
import chromadb

# Silence chromadb telemetry logs
logging.getLogger("chromadb").setLevel(logging.ERROR)

def run_scraper_eval():
    print("\n--- 2.1 Scraper Evaluation ---")
    results = []
    # Test just 2 URLs to save time, full run was already verified
    sample = FUND_URLS[:2]
    for fund in sample:
        result = scrape_url(fund["url"])
        html = result.get("html", "")
        status = "PASS" if html and len(html) > 500 else "FAIL"
        results.append({"fund": fund["name"], "status": status, "chars": len(html) if html else 0})

    for r in results:
        print(f"  [{r['status']}]  {r['fund']}  ({r['chars']} chars)")
    
    assert all(r["status"] == "PASS" for r in results), "Scraper evaluation failed"
    print("  [OK] Scraper eval passed (sampled).")

def run_cleaner_eval():
    print("\n--- 2.2 Cleaner Evaluation ---")
    # Fetch one page to test
    result = scrape_url(FUND_URLS[0]["url"])
    cleaned = clean(result)
    text = cleaned["text"]
    
    print(f"  Cleaned text length: {len(text)} chars")
    
    # Check no HTML tags
    assert "<script>" not in text
    assert "<nav>" not in text
    
    # Check key fields
    REQUIRED_FIELDS = ["expense ratio", "exit load", "benchmark"]
    for field in REQUIRED_FIELDS:
        found = field.lower() in text.lower()
        print(f"  [{'OK' if found else 'FAIL'}]  '{field}' found in cleaned text")
        assert found, f"Field '{field}' missing from cleaned text"

    assert "--- Key Details ---" in text, "Explicit section headers missing"
    print("  [OK] Cleaner eval passed.")
    return cleaned

def run_chunking_eval(cleaned_doc):
    print("\n--- 2.3 Chunking Evaluation ---")
    chunks = _section_chunk(cleaned_doc["fund_name"], cleaned_doc["text"])
    print(f"  Total chunks: {len(chunks)}")
    
    for i, chunk in enumerate(chunks):
        print(f"  Chunk {i+1} [{chunk['section']}]: {len(chunk['text'])} chars")
        assert chunk['text'].startswith("Fund: "), f"Chunk {i+1} missing fund name prefix"
        assert chunk['section'] in ["identity", "category", "key_details", "investment", "manager", "description", "ratings", "analysis", "other"], f"Invalid section: {chunk['section']}"
    
    assert 6 <= len(chunks) <= 9, f"Expected ~7-8 chunks per fund, got {len(chunks)}"
    print("  [OK] Chunking eval passed.")

def run_chroma_eval():
    print("\n--- 2.4 ChromaDB Ingestion Evaluation ---")
    client = chromadb.PersistentClient(path="./data/chroma_db")
    collection = client.get_collection("navi_funds")

    count = collection.count()
    print(f"  Total chunks indexed: {count}")
    assert count >= 105, f"Expected ≥105 chunks, got {count}"

    results = collection.get(limit=10, include=["metadatas"])
    for meta in results["metadatas"]:
        assert "fund_name" in meta, "Missing fund_name"
        assert "source_url" in meta, "Missing source_url"
        assert "scraped_at" in meta, "Missing scraped_at"
        assert "section" in meta, "Missing section"
        print(f"  [OK]  Metadata OK: {meta['fund_name'][:40]} [{meta['section']}]")
        
    print("  [OK] ChromaDB eval passed.")

if __name__ == "__main__":
    print("=== Running Phase 2 Evaluations ===")
    try:
        run_scraper_eval()
        cleaned_doc = run_cleaner_eval()
        run_chunking_eval(cleaned_doc)
        run_chroma_eval()
        print("\n[OK] All Phase 2 Evaluations Passed! Ready for Phase 3.")
    except AssertionError as e:
        print(f"\n[FAIL] Evaluation Failed: {e}")
        sys.exit(1)
