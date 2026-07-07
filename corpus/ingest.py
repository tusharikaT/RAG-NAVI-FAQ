"""
corpus/ingest.py
Full ingestion pipeline: Scrape → Clean → Chunk → Embed (BGE) → Index (ChromaDB).

Pipeline steps:
  1. Load all 15 fund URLs from corpus/urls.py
  2. Scrape each Groww page via corpus/scraper.py
  3. Clean and extract structured text via corpus/cleaner.py
  4. Chunk text using LangChain RecursiveCharacterTextSplitter (512 tokens / 50 overlap)
  5. Embed chunks using BAAI/bge-base-en-v1.5 (local, no API cost)
  6. Store in ChromaDB with full metadata per chunk

Features:
  - Idempotent: upserts by chunk_id — safe to re-run without duplicates
  - Resume mode: tracks ingested fund IDs in data/ingestion_state.json
  - Force re-ingest flag: --force bypasses resume state
  - Per-fund progress logging

Usage:
  python -m corpus.ingest           # ingest all unprocessed funds
  python -m corpus.ingest --force   # re-ingest all 15 funds from scratch
  python -m corpus.ingest --verify  # verify ChromaDB contents only
"""

import os
import sys
import json
import logging
import hashlib
import argparse
from pathlib import Path
from datetime import datetime, timezone

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(message)s"
)
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Paths
# ---------------------------------------------------------------------------
ROOT_DIR        = Path(__file__).resolve().parent.parent
CHROMA_PATH     = ROOT_DIR / "data" / "chroma_db"
STATE_FILE      = ROOT_DIR / "data" / "ingestion_state.json"
COLLECTION_NAME = "navi_funds"

# ---------------------------------------------------------------------------
# Chunking config
# ---------------------------------------------------------------------------
CHUNK_SIZE    = 512
CHUNK_OVERLAP = 50


# ---------------------------------------------------------------------------
# Ingestion state (resume support)
# ---------------------------------------------------------------------------

def _load_state() -> dict:
    """Load the ingestion state file. Returns empty dict if missing."""
    if STATE_FILE.exists():
        try:
            return json.loads(STATE_FILE.read_text(encoding="utf-8"))
        except json.JSONDecodeError:
            return {}
    return {}


def _save_state(state: dict) -> None:
    STATE_FILE.parent.mkdir(parents=True, exist_ok=True)
    STATE_FILE.write_text(json.dumps(state, indent=2), encoding="utf-8")


def _mark_ingested(fund_id: int, fund_name: str, chunk_count: int) -> None:
    state = _load_state()
    state[str(fund_id)] = {
        "fund_name":   fund_name,
        "chunk_count": chunk_count,
        "ingested_at": datetime.now(timezone.utc).isoformat(),
    }
    _save_state(state)


def _already_ingested(fund_id: int, force: bool) -> bool:
    if force:
        return False
    state = _load_state()
    return str(fund_id) in state


# ---------------------------------------------------------------------------
# ChromaDB collection
# ---------------------------------------------------------------------------

def _get_collection():
    """
    Get or create the ChromaDB persistent collection.
    Uses cosine similarity for embedding distance.
    """
    import chromadb
    from chromadb.config import Settings

    CHROMA_PATH.mkdir(parents=True, exist_ok=True)
    client = chromadb.PersistentClient(path=str(CHROMA_PATH))
    collection = client.get_or_create_collection(
        name=COLLECTION_NAME,
        metadata={"hnsw:space": "cosine"},
    )
    logger.info(
        "ChromaDB collection '%s' ready — %d chunks already indexed",
        COLLECTION_NAME, collection.count()
    )
    return collection


# ---------------------------------------------------------------------------
# BGE Embedding model
# ---------------------------------------------------------------------------

def _get_embedding_model():
    """
    Load BAAI/bge-base-en-v1.5 via sentence-transformers.
    Model is cached locally after first download (~400 MB).
    """
    from sentence_transformers import SentenceTransformer

    model_name = "BAAI/bge-base-en-v1.5"
    logger.info("Loading embedding model: %s", model_name)
    model = SentenceTransformer(model_name)
    logger.info("Embedding model loaded — dimension: %d", model.get_sentence_embedding_dimension())
    return model


BGE_QUERY_PREFIX = "Represent this sentence for searching relevant passages: "


def _embed(model, texts: list[str], is_query: bool = False) -> list[list[float]]:
    """
    Embed a list of text strings using BGE.

    BGE is an asymmetric retrieval model:
      - Documents (chunks): embed as raw text — no prefix.
      - Queries: prepend BGE instruction prefix for best cosine similarity.

    Args:
        texts:    List of strings to embed.
        is_query: If True, prepends BGE_QUERY_PREFIX to each text before encoding.
    """
    if is_query:
        texts = [BGE_QUERY_PREFIX + t for t in texts]

    embeddings = model.encode(
        texts,
        batch_size=32,
        show_progress_bar=False,
        normalize_embeddings=True,   # required for cosine similarity in ChromaDB
    )
    return embeddings.tolist()


# ---------------------------------------------------------------------------
# Section-based chunker (revised strategy)
# ---------------------------------------------------------------------------

# Sections to skip entirely — pure boilerplate, not useful for retrieval
SKIP_SECTIONS = {"--- Documents ---", "--- Disclaimer ---", "--- Fund Analysis ---"}

# Map section header text → short label stored in metadata
SECTION_LABELS = {
    "=== HEADER ===":              "identity",   # document title block
    "--- Category ---":            "category",
    "--- Key Details ---":         "key_details",
    "--- Investment Details ---":  "investment",
    "--- Fund Manager ---":        "manager",
    "--- Description ---":         "description",
    "--- About the Category ---":  "description",
    "--- Ratings ---":             "ratings",
    "--- Fund Analysis ---":       "analysis",
}


def _section_chunk(fund_name: str, text: str) -> list[dict]:
    """
    Split a cleaned fund document into per-section chunks.

    Strategy:
      1. Identify section boundaries using '--- Section ---' markers.
      2. Drop boilerplate sections (Disclaimer, Documents).
      3. Skip sections that are entirely empty or all-N/A.
      4. Prefix every chunk with 'Fund: {fund_name}' for retrieval anchoring.
      5. Sub-split any section exceeding 512 chars to keep embeddings tight.

    Returns:
        list of { "text": str, "section": str } dicts
    """
    from langchain.text_splitter import RecursiveCharacterTextSplitter

    sub_splitter = RecursiveCharacterTextSplitter(
        chunk_size=512,
        chunk_overlap=30,
        length_function=len,
        separators=["\n\n", "\n", ". ", " ", ""],
    )

    lines = text.splitlines()
    chunks_out = []

    current_section_label = "identity"
    current_lines: list[str] = []

    def _flush(label: str, section_lines: list[str]) -> None:
        """Finalize the current section, apply prefix, store."""
        section_text = "\n".join(section_lines).strip()

        # Skip empty or all-N/A sections
        meaningful = section_text.replace("N/A", "").replace("-", "").strip()
        if not meaningful:
            return

        prefixed = f"Fund: {fund_name}\n{section_text}"

        # Sub-split if too long
        if len(prefixed) > 512:
            sub_chunks = sub_splitter.split_text(prefixed)
            for sc in sub_chunks:
                if sc.strip():
                    chunks_out.append({"text": sc.strip(), "section": label})
        else:
            chunks_out.append({"text": prefixed, "section": label})

    for line in lines:
        stripped = line.strip()

        # Detect section boundary markers
        matched_skip    = any(stripped == s for s in SKIP_SECTIONS)
        matched_section = next(
            (label for header, label in SECTION_LABELS.items() if stripped == header),
            None
        )

        if matched_skip:
            # Flush current section, then skip this boilerplate section
            _flush(current_section_label, current_lines)
            current_lines = []
            current_section_label = "__skip__"
            continue

        if matched_section:
            # Flush current, start new section
            _flush(current_section_label, current_lines)
            current_lines = [line]
            current_section_label = matched_section
            continue

        # Check generic --- Header --- pattern (any unrecognised header)
        if stripped.startswith("---") and stripped.endswith("---") and len(stripped) > 6:
            _flush(current_section_label, current_lines)
            current_lines = [line]
            current_section_label = "other"
            continue

        if current_section_label != "__skip__":
            current_lines.append(line)

    # Flush remaining content
    _flush(current_section_label, current_lines)
    return chunks_out


def _make_chunk_id(fund_id: int, chunk_index: int) -> str:
    """Generate a deterministic, unique chunk ID."""
    raw = f"fund-{fund_id:02d}-chunk-{chunk_index:04d}"
    return hashlib.md5(raw.encode()).hexdigest()[:16]


# ---------------------------------------------------------------------------
# Per-fund ingest
# ---------------------------------------------------------------------------

def ingest_fund(
    fund: dict,
    scrape_result: dict,
    clean_result: dict,
    model,
    collection,
) -> int:
    """
    Ingest a single fund document into ChromaDB.

    Returns the number of chunks successfully indexed.
    """
    fund_id   = fund["id"]
    fund_name = clean_result["fund_name"]
    category  = clean_result["category"]
    source_url = clean_result["source_url"]
    fetched_at = clean_result["fetched_at"]
    text       = clean_result["text"]

    # 1. Section-based chunking (revised strategy)
    section_chunks = _section_chunk(fund_name, text)
    if not section_chunks:
        logger.warning("No chunks generated for '%s' — skipping", fund_name)
        return 0

    logger.info(
        "  Chunking '%s': %d chars -> %d section chunks",
        fund_name, len(text), len(section_chunks)
    )

    # 2. Embed documents (no query prefix for document chunks)
    chunk_texts = [sc["text"] for sc in section_chunks]
    embeddings  = _embed(model, chunk_texts, is_query=False)

    # 3. Build Chroma upsert payload
    ids       = [_make_chunk_id(fund_id, i) for i in range(len(section_chunks))]
    documents = chunk_texts
    metadatas = [
        {
            "fund_id":     str(fund_id),
            "fund_name":   fund_name,
            "category":    category,
            "section":     section_chunks[i]["section"],   # NEW: section label
            "source_url":  source_url,
            "scraped_at":  fetched_at,
            "chunk_index": str(i),
            "chunk_total": str(len(section_chunks)),
        }
        for i in range(len(section_chunks))
    ]

    # 4. Upsert into ChromaDB (idempotent)
    collection.upsert(
        ids=ids,
        embeddings=embeddings,
        documents=documents,
        metadatas=metadatas,
    )

    logger.info(
        "  Indexed %d chunks for '%s' [method: %s]",
        len(section_chunks), fund_name, scrape_result.get("method", "unknown")
    )
    return len(section_chunks)


# ---------------------------------------------------------------------------
# Full pipeline
# ---------------------------------------------------------------------------

def run_ingestion(force: bool = False) -> None:
    """
    Run the full ingestion pipeline for all 15 Navi fund URLs.

    Args:
        force: If True, re-ingest all funds even if already in state file.
    """
    from corpus.urls import FUND_URLS
    from corpus.scraper import scrape_url
    from corpus.cleaner import clean

    print("\n=== RAG-GROWW Corpus Ingestion ===")
    print(f"  Funds     : {len(FUND_URLS)}")
    print(f"  ChromaDB  : {CHROMA_PATH}")
    print(f"  Force     : {force}")
    print()

    # Init shared resources
    model      = _get_embedding_model()
    collection = _get_collection()

    total_chunks = 0
    success      = 0
    skipped      = 0
    failed       = []

    for fund in FUND_URLS:
        fund_id   = fund["id"]
        fund_name = fund["name"]

        print(f"[{fund_id:02d}/15] {fund_name}")

        # Resume check
        if _already_ingested(fund_id, force):
            state = _load_state()
            prev  = state[str(fund_id)]
            print(f"  SKIPPED (already ingested on {prev['ingested_at'][:10]},"
                  f" {prev['chunk_count']} chunks). Use --force to re-ingest.")
            skipped += 1
            continue

        # Step 1: Scrape
        scrape_result = scrape_url(fund["url"])
        if not scrape_result:
            logger.error("  Scrape FAILED for '%s'", fund_name)
            failed.append(fund_name)
            continue

        # Step 2: Clean
        clean_result = clean(scrape_result)
        if not clean_result:
            logger.error("  Clean FAILED for '%s'", fund_name)
            failed.append(fund_name)
            continue

        # Step 3: Chunk + Embed + Index
        try:
            chunk_count = ingest_fund(fund, scrape_result, clean_result, model, collection)
        except Exception as e:
            logger.error("  Ingest FAILED for '%s': %s", fund_name, e)
            failed.append(fund_name)
            continue

        if chunk_count > 0:
            _mark_ingested(fund_id, fund_name, chunk_count)
            total_chunks += chunk_count
            success += 1
            print(f"  OK — {chunk_count} chunks indexed")
        else:
            failed.append(fund_name)

    # Summary
    print("\n=== Ingestion Summary ===")
    print(f"  Successful : {success}")
    print(f"  Skipped    : {skipped}")
    print(f"  Failed     : {len(failed)}")
    print(f"  New chunks : {total_chunks}")
    print(f"  Total in DB: {collection.count()}")

    if failed:
        print("\n  Failed funds:")
        for f in failed:
            print(f"    - {f}")

    print()


# ---------------------------------------------------------------------------
# Verify
# ---------------------------------------------------------------------------

def verify_ingestion() -> None:
    """
    Verify ChromaDB contents — count chunks, check metadata, list funds indexed.
    """
    import chromadb

    if not CHROMA_PATH.exists():
        print("ChromaDB not found. Run ingestion first.")
        return

    client     = chromadb.PersistentClient(path=str(CHROMA_PATH))
    collection = client.get_or_create_collection(COLLECTION_NAME)
    total      = collection.count()

    print(f"\n=== ChromaDB Verification ===")
    print(f"  Collection : {COLLECTION_NAME}")
    print(f"  Total chunks: {total}")

    if total == 0:
        print("  WARNING: No chunks found. Run ingestion first.")
        return

    # Sample 20 chunks and check metadata
    sample = collection.get(limit=20, include=["metadatas"])
    fund_names = set()
    missing_meta = 0

    for meta in sample["metadatas"]:
        for required_key in ["fund_name", "source_url", "scraped_at", "category"]:
            if required_key not in meta or not meta[required_key]:
                missing_meta += 1
        fund_names.add(meta.get("fund_name", "UNKNOWN"))

    print(f"  Sample size     : {len(sample['metadatas'])}")
    print(f"  Missing metadata: {missing_meta} field(s) in sample")
    print(f"  Funds in sample : {len(fund_names)}")

    # Per-fund chunk counts
    state = _load_state()
    print("\n  Per-fund ingestion state:")
    for fid, info in sorted(state.items(), key=lambda x: int(x[0])):
        print(f"    [{fid:>2}] {info['fund_name'][:50]:<50} {info['chunk_count']:>3} chunks")

    # Pass/fail
    print()
    expected_min_chunks = len(state) * 3  # at least 3 chunks per fund
    checks = [
        (f"Total chunks >= {expected_min_chunks} (15 funds x 3 min)", total >= expected_min_chunks),
        ("Missing metadata = 0", missing_meta == 0),
        ("All 15 funds in state file", len(state) == 15),
    ]
    for label, ok in checks:
        print(f"  [{'OK' if ok else 'FAIL'}] {label}")

    print()


# ---------------------------------------------------------------------------
# CLI entry point
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="RAG-GROWW Corpus Ingestion Pipeline")
    parser.add_argument("--force",  action="store_true", help="Re-ingest all funds, ignoring state file")
    parser.add_argument("--verify", action="store_true", help="Verify ChromaDB contents without ingesting")
    args = parser.parse_args()

    if args.verify:
        verify_ingestion()
    else:
        run_ingestion(force=args.force)
        verify_ingestion()
