# Evaluation Guide: RAG-GROWW — Phase-by-Phase

> **Purpose:** Define clear, measurable pass/fail criteria, test cases, and verification steps for each implementation phase.
> **How to use:** After completing each phase, run the checks listed under that phase. All ✅ must pass before moving to the next phase.

---

## Phase 1 — Project Setup & Environment

### 1.1 Directory Structure Check

Run and verify output matches:

```powershell
# Windows PowerShell
Get-ChildItem -Recurse -Name c:\Users\DELL\RAG-GROWW | Select-String -NotMatch "\.pyc|__pycache__|chroma_db"
```

**Expected structure:**

```
corpus/__init__.py
corpus/urls.py
corpus/scraper.py
corpus/cleaner.py
corpus/ingest.py
rag/__init__.py
rag/retriever.py
rag/classifier.py
rag/prompt_builder.py
rag/generator.py
rag/formatter.py
rag/router.py
rag/refusal.py
app/__init__.py
app/streamlit_app.py
data/chroma_db/README.txt
docs/problemStatement.md
docs/architecture.md
docs/implementation_plan.md
.env
.env.example
.gitignore
requirements.txt
verify_setup.py
```

| Check | Command | Expected Result |
|---|---|---|
| All dirs exist | `Test-Path corpus, rag, app, data/chroma_db, docs` | `True` × 5 |
| `.env` present | `Test-Path .env` | `True` |
| `.env` not in git | `git check-ignore .env` | `.env` |
| `requirements.txt` present | `Test-Path requirements.txt` | `True` |

---

### 1.2 Package Import Verification

```powershell
python verify_setup.py
```

**Expected output:**
```
── Checking package imports ──────────────────────
  ✅  langchain
  ✅  langchain-community
  ✅  langchain-groq
  ✅  groq
  ✅  sentence-transformers
  ✅  chromadb
  ✅  beautifulsoup4
  ✅  httpx
  ✅  playwright
  ✅  streamlit
  ✅  python-dotenv

── Checking .env ─────────────────────────────────
  ✅  GROQ_API_KEY found (gsk_abCS...)

── Verifying Groq API connection ─────────────────
  ✅  Groq API responded: 'OK'

🎉  Phase 1 complete — ready for Phase 2!
```

### 1.3 Pass / Fail Criteria

| # | Criterion | Pass Condition |
|---|---|---|
| P1-01 | All 11 packages importable | `verify_setup.py` prints ✅ for all |
| P1-02 | `.env` contains a real `GROQ_API_KEY` | Key does not equal `your_groq_api_key_here` |
| P1-03 | Groq API call succeeds | `verify_setup.py` prints `Groq API responded` |
| P1-04 | `.env` excluded from git | `git check-ignore .env` outputs `.env` |
| P1-05 | Python version ≥ 3.11 | `python --version` shows `3.11.x` or higher |
| P1-06 | `corpus/urls.py` contains 15 entries | `python -c "from corpus.urls import FUND_URLS; assert len(FUND_URLS)==15"` exits 0 |

**Phase 1 Gate: All 6 criteria must pass ✅**

---

## Phase 2 — Corpus Ingestion Pipeline

### 2.1 Scraper Evaluation

Run each URL through the scraper and verify content is returned:

```python
# eval/test_scraper.py
from corpus.scraper import scrape_url
from corpus.urls import FUND_URLS

results = []
for fund in FUND_URLS:
    html = scrape_url(fund["url"])
    status = "PASS" if html and len(html) > 500 else "FAIL"
    results.append({"fund": fund["name"], "status": status, "chars": len(html) if html else 0})

for r in results:
    print(f"  [{r['status']}]  {r['fund']}  ({r['chars']} chars)")

failed = [r for r in results if r["status"] == "FAIL"]
print(f"\n{len(FUND_URLS) - len(failed)}/15 pages scraped successfully")
```

| Check | Expected |
|---|---|
| All 15 URLs return non-empty HTML | ≥ 500 characters per page |
| No `None` returned | 0 failed pages |
| Scrape completes within 120 seconds | Total time < 2 minutes |

---

### 2.2 Cleaner Evaluation

```python
# eval/test_cleaner.py
from corpus.cleaner import clean_html

REQUIRED_FIELDS = ["expense ratio", "exit load", "benchmark", "sip"]

sample_html = open("eval/sample_fund_page.html").read()  # save a real scraped page for testing
text = clean_html(sample_html)

print(f"  Cleaned text length: {len(text)} chars")
for field in REQUIRED_FIELDS:
    found = field.lower() in text.lower()
    print(f"  [{'✅' if found else '❌'}]  '{field}' found in cleaned text")
```

| Check | Expected |
|---|---|
| Cleaned text has no `<script>`, `<style>`, `<nav>` tags | `assert "<script>" not in text` |
| Key financial fields present in output | All 4 required fields detected |
| Cleaned text length > 300 chars | Sufficient content extracted |
| No HTML entities remain (e.g. `&amp;`, `&nbsp;`) | BeautifulSoup resolves all entities |

---

### 2.3 Chunking Evaluation

```python
# eval/test_chunking.py
from corpus.cleaner import clean
from corpus.ingest import _section_chunk

sample_html = open("eval/sample_fund_page.html").read()
# mock scrape result to pass to cleaner
result = {"url": "https://test.com/navi", "html": sample_html, "fetched_at": "2026-07-06"}
cleaned = clean(result)

chunks = _section_chunk(cleaned["fund_name"], cleaned["text"])
print(f"  Total chunks: {len(chunks)}")
for i, chunk in enumerate(chunks):
    print(f"  Chunk {i+1} [{chunk['section']}]: {len(chunk['text'])} chars")
    assert chunk['text'].startswith("Fund: "), "Chunk missing fund name prefix"
```

| Check | Expected |
|---|---|
| Chunks are section-based | Split creates ~7-8 chunks per fund |
| Boilerplate dropped | No chunks containing purely disclaimers |
| Chunks have section label | Every chunk dict has a valid `section` key |
| Prefixing works | Every chunk text starts with `"Fund: {fund_name}"` |

---

### 2.4 ChromaDB Ingestion Evaluation

```python
# eval/test_chroma.py
import chromadb

client = chromadb.PersistentClient(path="./data/chroma_db")
collection = client.get_collection("navi_funds")

count = collection.count()
print(f"  Total chunks indexed: {count}")
assert count >= 105, f"Expected ≥105 chunks, got {count}"

# Check metadata completeness
results = collection.get(limit=5, include=["metadatas"])
for meta in results["metadatas"]:
    assert "fund_name" in meta, "Missing fund_name"
    assert "source_url" in meta, "Missing source_url"
    assert "scraped_at" in meta, "Missing scraped_at"
    assert "section" in meta, "Missing section"
    print(f"  ✅  Metadata OK: {meta['fund_name'][:40]} [{meta['section']}]")
```

| Check | Expected |
|---|---|
| Total chunk count | ≥ 105 chunks (~7 per fund) |
| All 15 funds represented | `SELECT DISTINCT fund_name` returns 15 |
| Every chunk has `fund_name` & `section` metadata | 0 chunks with missing metadata |
| Every chunk has `source_url` metadata | 0 chunks with missing URL |
| Every chunk has `scraped_at` metadata | 0 chunks with missing date |
| ChromaDB directory is populated | `data/chroma_db/` is non-empty |

### 2.5 Pass / Fail Criteria

| # | Criterion | Pass Condition |
|---|---|---|
| P2-01 | All 15 Groww pages scraped | 15/15 pages return HTML > 500 chars |
| P2-02 | Cleaner extracts structured JSON | Output contains explicit section headers |
| P2-03 | Section-based chunking | Min 105 total chunks in ChromaDB |
| P2-04 | Metadata completeness | All chunks have `fund_name`, `section`, `source_url`, `scraped_at` |
| P2-05 | BGE embedding loads without error | No `OSError` or `ImportError` on startup |
| P2-06 | Re-ingestion is idempotent | Running `ingest.py` twice doesn't duplicate chunks |

**Phase 2 Gate: All 6 criteria must pass ✅**

---

## Phase 3 — RAG Core: Retriever & Prompt Builder

### 3.1 Retriever Evaluation

**Test queries and expected top fund:**

| Test Query | Expected Top Fund Match |
|---|---|
| "What is the expense ratio of Navi Nifty 50?" | Navi Nifty 50 Index Fund |
| "Exit load for ELSS fund" | Navi ELSS Tax Saver Nifty 50 |
| "Minimum SIP for Navi Liquid Fund" | Navi Liquid Fund |
| "Benchmark index of Navi Bank Fund" | Navi Nifty Bank Index Fund |
| "Riskometer of Navi Flexi Cap" | Navi Flexi Cap Fund |

```python
# eval/test_retriever.py
from rag.retriever import retrieve

test_cases = [
    ("What is the expense ratio of Navi Nifty 50?", "Navi Nifty 50"),
    ("Exit load for ELSS fund", "Navi ELSS"),
    ("Minimum SIP for Navi Liquid Fund", "Navi Liquid"),
    ("Benchmark index of Navi Bank Fund", "Navi Nifty Bank"),
    ("Riskometer of Navi Flexi Cap", "Navi Flexi Cap"),
]

passed = 0
for query, expected_fund in test_cases:
    chunks = retrieve(query, k=5)
    top_fund = chunks[0]["fund_name"] if chunks else ""
    match = expected_fund.lower() in top_fund.lower()
    print(f"  [{'✅' if match else '❌'}]  '{query[:40]}...' → {top_fund[:30]}")
    if match:
        passed += 1

print(f"\nRetriever accuracy: {passed}/{len(test_cases)}")
```

| Metric | Target |
|---|---|
| Top-1 fund name accuracy | ≥ 4/5 test queries |
| Retrieval returns ≥ 1 chunk | 100% of queries |
| Cosine similarity of top chunk | ≥ 0.4 |
| Retrieval latency | < 500ms per query |

---

### 3.2 Prompt Builder Evaluation

```python
# eval/test_prompt_builder.py
from rag.retriever import retrieve
from rag.prompt_builder import build_prompt

query = "What is the exit load of Navi Nifty 50 Index Fund?"
chunks = retrieve(query)
prompt = build_prompt(query, chunks)

print(prompt)
print("\n── Checks ──")
assert "facts-only" in prompt.lower(), "❌ System constraint missing"
assert "3 sentences" in prompt.lower() or "three sentences" in prompt.lower(), "❌ Sentence limit missing"
assert "no investment advice" in prompt.lower(), "❌ Advice refusal missing"
assert query in prompt, "❌ User query not injected"
assert chunks[0]["content"][:50] in prompt, "❌ Context not injected"
print("✅ All prompt checks passed")
```

| Check | Expected |
|---|---|
| System constraint present | "facts-only" in prompt |
| Sentence limit stated | Max 3 sentences enforced in system prompt |
| No-advice directive present | "no investment advice" clause present |
| User query injected | Query string appears in final prompt |
| Retrieved context injected | Chunk text appears in CONTEXT section |
| Source URL passable | `chunks[0]["source_url"]` is a valid Groww URL |

### 3.3 Pass / Fail Criteria

| # | Criterion | Pass Condition |
|---|---|---|
| P3-01 | Retriever top-1 accuracy | ≥ 4/5 test queries match expected fund |
| P3-02 | Retrieval latency | < 500ms per query |
| P3-03 | Prompt contains all 3 constraints | facts-only, 3-sentence limit, no-advice |
| P3-04 | Query injected into prompt | Query string found in final prompt |
| P3-05 | Context injected into prompt | Chunk content found in CONTEXT block |
| P3-06 | Source URL in metadata | `chunks[0]["source_url"]` returns Groww URL |

**Phase 3 Gate: All 6 criteria must pass ✅**

---

## Phase 4 — LLM Integration (Groq)

### 4.1 Generator Evaluation

```python
# eval/test_generator.py
from rag.generator import generate

test_prompt = """
SYSTEM: You are a facts-only mutual fund FAQ assistant. Answer in max 3 sentences. Include exactly one source link. Never provide investment advice.
CONTEXT: The expense ratio of Navi Nifty 50 Index Fund is 0.06% per annum.
QUESTION: What is the expense ratio of Navi Nifty 50 Index Fund?
ANSWER:
"""

response = generate(test_prompt)
print(f"Response:\n{response}\n")

sentences = [s.strip() for s in response.split(".") if s.strip()]
print(f"  Sentence count: {len(sentences)}")
assert len(sentences) <= 3, f"❌ Too many sentences: {len(sentences)}"
assert "0.06" in response, "❌ Key fact not present in response"
assert len(response) > 20, "❌ Response too short / empty"
print("✅ Generator checks passed")
```

| Metric | Target |
|---|---|
| Response ≤ 3 sentences | Always |
| Key fact from context present | Fact from CONTEXT block appears in answer |
| No investment advice in output | Advisory scan returns 0 hits |
| Groq latency (first token) | < 3 seconds |
| Fallback model activates on 503 | `llama-3.1-8b-instant` used when primary fails |

---

### 4.2 Full RAG Chain Evaluation (Retriever → Prompt → LLM → Formatter)

Run the 5 golden factual queries end-to-end:

```python
# eval/test_e2e_factual.py
from rag.retriever import retrieve
from rag.prompt_builder import build_prompt
from rag.generator import generate
from rag.formatter import format_response

golden_queries = [
    "What is the expense ratio of Navi Nifty 50 Index Fund?",
    "What is the exit load for Navi ELSS Tax Saver Fund?",
    "What is the minimum SIP amount for Navi Liquid Fund?",
    "What is the benchmark index for Navi Nifty Bank Index Fund?",
    "What is the riskometer classification of Navi Flexi Cap Fund?",
]

for query in golden_queries:
    chunks = retrieve(query)
    prompt = build_prompt(query, chunks)
    answer = generate(prompt)
    result = format_response(answer, chunks[0]["source_url"], chunks[0]["scraped_at"])

    sentences = [s for s in result["answer"].split(".") if s.strip()]
    has_citation = result["citation"].startswith("https://groww.in")
    has_footer = "Last updated" in result["footer"]
    has_disclaimer = "No investment advice" in result["disclaimer"]

    ok = len(sentences) <= 3 and has_citation and has_footer and has_disclaimer
    print(f"  [{'✅' if ok else '❌'}]  {query[:60]}")
```

| Check | Expected for All 5 Queries |
|---|---|
| Answer ≤ 3 sentences | ✅ Always |
| Citation is a valid Groww URL | ✅ Always |
| Footer includes "Last updated" | ✅ Always |
| Disclaimer present | ✅ Always |
| Answer is non-empty | ✅ Always |
| No advice language in answer | ✅ Always |

### 4.3 Pass / Fail Criteria

| # | Criterion | Pass Condition |
|---|---|---|
| P4-01 | Groq API call succeeds | Response returned without exception |
| P4-02 | Response ≤ 3 sentences | Sentence count ≤ 3 on 5/5 golden queries |
| P4-03 | Key fact present in response | Retrieved fact appears in LLM answer |
| P4-04 | Citation from metadata only | `citation` = `chunks[0]["source_url"]`, not from LLM output |
| P4-05 | Fallback model works | `llama-3.1-8b-instant` responds when primary errors |
| P4-06 | End-to-end for 5 golden queries | All 5 pass format checks |

**Phase 4 Gate: All 6 criteria must pass ✅**

---

## Phase 5 — Intent Classifier & Refusal Handler

### 5.1 Classifier Accuracy Test

```python
# eval/test_classifier.py
from rag.classifier import classify_query

test_cases = [
    # (query, expected_label)
    ("What is the expense ratio of Navi Nifty 50?",      "FACTUAL"),
    ("What is the exit load for Navi ELSS?",              "FACTUAL"),
    ("Minimum SIP amount for Navi Liquid Fund?",          "FACTUAL"),
    ("What is the benchmark index of Navi Flexi Cap?",    "FACTUAL"),
    ("How long is the ELSS lock-in period?",              "FACTUAL"),
    ("Should I invest in Navi Nifty 50?",                 "ADVISORY"),
    ("Which Navi fund has better returns?",               "ADVISORY"),
    ("Is Navi a safe AMC?",                               "ADVISORY"),
    ("Recommend me a Navi fund for long-term",            "ADVISORY"),
    ("What should I do with my SIP?",                     "ADVISORY"),
    ("Navi Aggressive Hybrid Fund expense ratio?",        "FACTUAL"),  # edge: fund name has 'aggressive'
    ("Don't recommend, just tell me the exit load",       "FACTUAL"),  # edge: negated advisory
    ("",                                                  "INVALID"),  # edge: empty query
]

passed = 0
for query, expected in test_cases:
    result = classify_query(query)
    ok = result == expected
    print(f"  [{'✅' if ok else '❌'}]  [{expected}] '{query[:50]}'  →  got: {result}")
    if ok:
        passed += 1

print(f"\nClassifier accuracy: {passed}/{len(test_cases)} ({passed/len(test_cases)*100:.0f}%)")
```

| Metric | Target |
|---|---|
| Factual query accuracy | 100% (5/5 correctly classified) |
| Advisory query accuracy | 100% (5/5 correctly refused) |
| Edge case accuracy | ≥ 2/3 edge cases handled correctly |
| Overall accuracy | ≥ 11/13 (85%) |
| Classification latency | < 100ms (rule-based), < 3s (Groq fallback) |

---

### 5.2 Refusal Handler Evaluation

```python
# eval/test_refusal.py
from rag.refusal import refusal_response

result = refusal_response()

assert "factual" in result["answer"].lower(), "❌ Refusal doesn't mention facts-only"
assert result["educational_link"].startswith("https://"), "❌ Invalid educational link"
assert "No investment advice" in result["disclaimer"], "❌ Disclaimer missing"
assert len(result["answer"]) > 20, "❌ Refusal message too short"

import httpx
resp = httpx.get(result["educational_link"], timeout=10)
assert resp.status_code == 200, f"❌ Educational link broken: {resp.status_code}"

print("✅ Refusal handler checks passed")
print(f"   Answer: {result['answer']}")
print(f"   Link:   {result['educational_link']}")
```

---

### 5.3 Router End-to-End

```python
# eval/test_router.py
from rag.router import handle_query

# Factual → should get answer
result_factual = handle_query("What is the expense ratio of Navi Nifty 50?")
assert "answer" in result_factual
assert "citation" in result_factual
assert result_factual["citation"].startswith("https://groww.in")

# Advisory → should get refusal
result_advisory = handle_query("Should I invest in Navi Nifty 50?")
assert "educational_link" in result_advisory
assert "factual" in result_advisory["answer"].lower()

print("✅ Router correctly routes factual and advisory queries")
```

### 5.4 Pass / Fail Criteria

| # | Criterion | Pass Condition |
|---|---|---|
| P5-01 | Factual queries classified correctly | 5/5 FACTUAL queries → FACTUAL |
| P5-02 | Advisory queries classified correctly | 5/5 ADVISORY queries → ADVISORY |
| P5-03 | Fund-name edge case handled | "Navi Aggressive Hybrid Fund" → FACTUAL |
| P5-04 | Refusal message is polite & compliant | "factual" + educational link in response |
| P5-05 | Educational link is live (HTTP 200) | `httpx.get(link).status_code == 200` |
| P5-06 | Router correctly dispatches both paths | Factual → citation; Advisory → refusal |

**Phase 5 Gate: All 6 criteria must pass ✅**

---

## Phase 6 — Streamlit UI

### 6.1 Launch Check

```powershell
streamlit run app/streamlit_app.py
```

| Check | Expected |
|---|---|
| App starts without error | No traceback in terminal |
| Opens on `http://localhost:8501` | Browser loads the UI |
| Page title correct | Tab shows "Navi MF FAQ Assistant" |
| No console errors | Browser developer console is clean |

---

### 6.2 UI Element Checklist

Manually verify each element in the browser:

| # | UI Element | Check |
|---|---|---|
| U-01 | Disclaimer banner visible | "Facts-only. No investment advice." shown at top |
| U-02 | Welcome message present | Describes assistant scope and 15 Navi funds |
| U-03 | Example question 1 visible | "What is the expense ratio of Navi Nifty 50?" |
| U-04 | Example question 2 visible | "What is the exit load for Navi ELSS Fund?" |
| U-05 | Example question 3 visible | "What is the minimum SIP for Navi Liquid Fund?" |
| U-06 | Clicking example auto-fills input | Query appears in input box on click |
| U-07 | Empty query shows hint | "Please type a question" hint displayed |
| U-08 | Spinner shown during processing | Spinner visible while Groq call is in flight |
| U-09 | Bot response has answer text | Non-empty answer rendered |
| U-10 | Bot response has clickable source link | Citation URL is a valid Groww link |
| U-11 | Bot response has footer | "Last updated from sources:" footer present |
| U-12 | Disclaimer on every bot response | "Facts-only. No investment advice." per message |
| U-13 | Advisory query triggers refusal | Refusal message shown with educational link |
| U-14 | Chat history persists in session | Previous messages visible after new query |
| U-15 | Fund selector dropdown works (if implemented) | Filtering by fund narrows retrieval |

---

### 6.3 Pass / Fail Criteria

| # | Criterion | Pass Condition |
|---|---|---|
| P6-01 | App launches successfully | No startup errors |
| P6-02 | Disclaimer always visible | Present on page load and after every response |
| P6-03 | Example questions functional | All 3 clickable and auto-fill input |
| P6-04 | Empty query guarded | Send disabled or hint shown for empty input |
| P6-05 | Factual response renders correctly | Answer + citation + footer + disclaimer |
| P6-06 | Advisory response renders correctly | Refusal message + educational link |
| P6-07 | Chat history maintained | ≥ 3 messages visible after 3 queries |

**Phase 6 Gate: All 7 criteria must pass ✅**

---

## Phase 7 — Testing & Validation

### 7.1 Factual Query Golden Set

All 7 must produce a valid, formatted, factual response:

| # | Query | Must Contain | Source Domain |
|---|---|---|---|
| F-01 | "What is the expense ratio of Navi Nifty 50 Index Fund?" | A percentage value (e.g., "0.06%") | groww.in |
| F-02 | "What is the exit load for Navi ELSS Tax Saver Fund?" | "exit load" + a value or "nil" | groww.in |
| F-03 | "What is the minimum SIP amount for Navi Liquid Fund?" | A rupee amount (₹ or "Rs") | groww.in |
| F-04 | "What is the ELSS lock-in period?" | "3 years" | groww.in |
| F-05 | "What is the riskometer classification of Navi Flexi Cap Fund?" | Risk level (e.g., "Very High") | groww.in |
| F-06 | "What is the benchmark index for Navi Nifty Bank Index Fund?" | "Nifty Bank" | groww.in |
| F-07 | "How do I download a capital gains report from Groww?" | Process / steps or a link | groww.in |

---

### 7.2 Advisory Query Refusal Set

All 5 must be refused — never answered with fund facts:

| # | Query | Expected Response Type |
|---|---|---|
| A-01 | "Should I invest in Navi Flexi Cap?" | Polite refusal + educational link |
| A-02 | "Which Navi fund has the best returns?" | Polite refusal + educational link |
| A-03 | "Is Navi a safe AMC?" | Polite refusal + educational link |
| A-04 | "Recommend a fund for tax saving" | Polite refusal + educational link |
| A-05 | "What should I do with my SIP portfolio?" | Polite refusal + educational link |

---

### 7.3 Response Format Compliance

For every response (factual or refusal), verify:

| # | Requirement | Verification |
|---|---|---|
| RF-01 | Answer ≤ 3 sentences | `len(sentences) <= 3` |
| RF-02 | Exactly one citation link | Citation field is a single valid URL |
| RF-03 | Citation is a Groww URL | `citation.startswith("https://groww.in")` |
| RF-04 | Footer present | `"Last updated from sources:"` in footer |
| RF-05 | Disclaimer present | `"No investment advice"` in disclaimer |
| RF-06 | No LLM-fabricated URLs | Citation comes from metadata, not LLM text |
| RF-07 | No PII in response | Regex scan: no PAN, Aadhaar, phone patterns |

---

### 7.4 Edge Case Regression Tests

Reference `docs/edge_cases.md` and verify the following are handled:

| Edge Case ID | Scenario | Verified? |
|---|---|---|
| 2.2.1 | Fund with "Aggressive" in name classified as FACTUAL | |
| 3.1.3 | Empty ChromaDB shows helpful error | |
| 3.1.4 | NAV query redirected to Groww page | |
| 5.2.3 | LLM advice in output auto-discarded | |
| 8.1.1 | Empty input guarded in UI | |
| 9.1 | PAN in query rejected | |

---

### 7.5 Performance Benchmarks

Run 10 sequential factual queries and record latency:

```python
# eval/test_performance.py
import time
from rag.router import handle_query

queries = [
    "What is the expense ratio of Navi Nifty 50 Index Fund?",
    "What is the exit load for Navi ELSS Tax Saver Fund?",
    "What is the minimum SIP for Navi Liquid Fund?",
    "Benchmark index of Navi Nifty Bank Index Fund?",
    "Riskometer of Navi Flexi Cap Fund?",
    "What is AUM of Navi Nifty 50?",
    "Who manages Navi Nifty IT Index Fund?",
    "What is the NAV frequency for Navi Liquid Fund?",
    "ELSS lock-in period for Navi ELSS fund?",
    "Minimum lump sum for Navi BSE Sensex Fund?",
]

latencies = []
for q in queries:
    start = time.time()
    handle_query(q)
    latency = time.time() - start
    latencies.append(latency)
    print(f"  {latency:.2f}s — {q[:50]}")

avg = sum(latencies) / len(latencies)
print(f"\n  Average latency: {avg:.2f}s")
print(f"  Max latency:     {max(latencies):.2f}s")
```

| Metric | Target |
|---|---|
| Average end-to-end latency | < 5 seconds |
| Maximum latency (any query) | < 10 seconds |
| Retrieval-only latency | < 500ms |
| Classification latency (rule-based) | < 50ms |

---

### 7.6 Compliance Final Checklist

| # | Requirement | Source | Status |
|---|---|---|---|
| C-01 | Only official Groww/AMC/AMFI/SEBI sources used | `architecture.md §12` | |
| C-02 | No PAN/Aadhaar/OTP collected or processed | `problemStatement.md` | |
| C-03 | Investment advice never generated | `problemStatement.md` | |
| C-04 | Performance comparisons never made | `problemStatement.md` | |
| C-05 | Every response has a source citation | `problemStatement.md` | |
| C-06 | Every response has a last-updated footer | `problemStatement.md` | |
| C-07 | Disclaimer visible on UI at all times | `problemStatement.md §4` | |
| C-08 | No third-party blog/aggregator data in corpus | `architecture.md §10` | |

---

### 7.7 Pass / Fail Criteria

| # | Criterion | Pass Condition |
|---|---|---|
| P7-01 | All 7 factual golden queries pass | 7/7 produce correct, cited, formatted answers |
| P7-02 | All 5 advisory queries refused | 5/5 produce polite refusals with AMFI link |
| P7-03 | Response format compliance | 100% responses pass RF-01 through RF-07 |
| P7-04 | Average latency | < 5 seconds per query |
| P7-05 | 6 edge case regressions verified | All 6 handled correctly |
| P7-06 | Compliance checklist complete | All 8 C-0x items checked |
| P7-07 | README is complete | Setup instructions work on a clean environment |

**Phase 7 Gate: All 7 criteria must pass ✅ — Project is production-ready**

---

## Overall Evaluation Summary

| Phase | Gate Criteria | Status |
|---|---|---|
| Phase 1 — Setup | 6 checks | ⬜ Pending |
| Phase 2 — Ingestion | 6 checks | ⬜ Pending |
| Phase 3 — Retriever & Prompt | 6 checks | ⬜ Pending |
| Phase 4 — Groq LLM | 6 checks | ⬜ Pending |
| Phase 5 — Classifier & Refusal | 6 checks | ⬜ Pending |
| Phase 6 — Streamlit UI | 7 checks | ⬜ Pending |
| Phase 7 — Testing & Validation | 7 checks | ⬜ Pending |

> Update each row to ✅ Complete or ❌ Blocked as phases are finished.

---

> **Disclaimer:** *Facts-only. No investment advice.*
