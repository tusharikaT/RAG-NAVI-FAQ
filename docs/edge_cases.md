# Edge Cases: RAG-GROWW Mutual Fund FAQ Assistant

> **Coverage:** All components across all 7 phases — Ingestion, Retrieval, Classification, Generation, Formatting, UI, and System-level.

---

## Table of Contents

1. [Corpus Ingestion Edge Cases](#1-corpus-ingestion-edge-cases)
2. [Query Intent Classification Edge Cases](#2-query-intent-classification-edge-cases)
3. [Retrieval Edge Cases](#3-retrieval-edge-cases)
4. [Prompt Builder Edge Cases](#4-prompt-builder-edge-cases)
5. [LLM Generation Edge Cases (Groq)](#5-llm-generation-edge-cases-groq)
6. [Response Formatter Edge Cases](#6-response-formatter-edge-cases)
7. [Refusal Handler Edge Cases](#7-refusal-handler-edge-cases)
8. [Streamlit UI Edge Cases](#8-streamlit-ui-edge-cases)
9. [Privacy & Security Edge Cases](#9-privacy--security-edge-cases)
10. [System & Infrastructure Edge Cases](#10-system--infrastructure-edge-cases)

---

## 1. Corpus Ingestion Edge Cases

### 1.1 Scraping Failures

| # | Scenario | Risk | Handling Strategy |
|---|---|---|---|
| 1.1.1 | Groww returns HTTP 429 (rate limit) | Ingestion halts mid-corpus | Implement exponential backoff with max 3 retries; log failed URLs and skip gracefully |
| 1.1.2 | Groww returns HTTP 403 (blocked bot) | Page not fetched | Add User-Agent spoofing; fall back to Playwright with realistic browser fingerprint |
| 1.1.3 | Groww returns HTTP 503 (server error) | Page not fetched | Retry after 30s delay; log as failed if persists |
| 1.1.4 | Network timeout (DNS failure, no internet) | Ingestion crashes | Wrap all requests in try/except with a timeout of 15s; skip and log |
| 1.1.5 | URL structure changes (Groww redesigns routing) | 404 returned | Validate URL list against confirmed slugs on startup; alert if any 404s |

### 1.2 HTML Parsing Edge Cases

| # | Scenario | Risk | Handling Strategy |
|---|---|---|---|
| 1.2.1 | Page is fully JS-rendered — `httpx` returns empty body | Zero content extracted | Detect empty `<body>` and automatically fall back to Playwright |
| 1.2.2 | BeautifulSoup parses partial HTML (truncated response) | Incomplete fund data | Check for key sections; if missing, re-fetch and flag |
| 1.2.3 | Fund page shows "Data Temporarily Unavailable" | Stale or placeholder content gets embedded | Detect known error strings and skip the page; alert operator |
| 1.2.4 | Groww adds a CAPTCHA challenge on bot detection | Page returns CAPTCHA HTML | Playwright with human-like delays; if CAPTCHA persists, skip and log |
| 1.2.5 | Key data sections (expense ratio, exit load) are missing from the page | Chunks don't contain answerable data | Tag chunk metadata with `sections_found: []`; log missing sections per fund |

### 1.3 Chunking Edge Cases

| # | Scenario | Risk | Handling Strategy |
|---|---|---|---|
| 1.3.1 | Cleaned text has missing section headers | Entire text grouped into a single 'identity' chunk | `_section_chunk` safely falls back to chunking the whole text; sub-splitter handles sizing > 512 chars |
| 1.3.2 | Section content (e.g. Description) is very long | BGE embedding loses context focus | Sections > 512 chars are sub-split using `RecursiveCharacterTextSplitter` with 30-char overlap |
| 1.3.3 | Two funds produce near-identical sections (e.g., benchmark description) | Retrieval ambiguity | Every chunk is explicitly prefixed with `"Fund: {fund_name}\n"` to anchor cosine similarity to the fund |
| 1.3.4 | Chunk contains only boilerplate disclaimer text | Low-quality vector pollutes the index | `_section_chunk` explicitly drops `--- Documents ---` and `--- Disclaimer ---` sections |
| 1.3.5 | Section contains only 'N/A' or '-' | Pointless vectors embedded | `_section_chunk` drops sections that are empty after stripping 'N/A' |

### 1.4 Embedding & Indexing Edge Cases

| # | Scenario | Risk | Handling Strategy |
|---|---|---|---|
| 1.4.1 | BGE model fails to download (no internet at model init) | Ingestion crashes on first run | Catch `OSError` on `HuggingFaceEmbeddings` init; print clear error with fix instructions |
| 1.4.2 | ChromaDB collection already exists from a previous run | Duplicate chunks indexed | Check if collection exists; use `get_or_create_collection` and upsert by `chunk_id` |
| 1.4.3 | Disk full while writing ChromaDB | Partial index written | Wrap Chroma writes in try/except; on error, delete partial collection and re-run |
| 1.4.4 | Ingestion interrupted mid-way (Ctrl+C) | Only some funds indexed | Track ingested fund IDs in a `data/ingestion_state.json`; support resume mode |
| 1.4.5 | Re-ingestion overwrites fresh data with stale scraped content | ChromaDB has stale data | Stamp each chunk with `scraped_at` date; only re-ingest a fund if its date is older than 30 days |

---

## 2. Query Intent Classification Edge Cases

### 2.1 Ambiguous Queries

| # | Query Example | Ambiguity | Expected Behaviour |
|---|---|---|---|
| 2.1.1 | *"Is Navi Nifty 50 good?"* | "Good" implies opinion, but user may mean factual attributes | Classify as ADVISORY; refuse with educational link |
| 2.1.2 | *"Tell me about Navi ELSS"* | Vague — could be factual or advisory | Classify as FACTUAL; retrieve overview chunks |
| 2.1.3 | *"Should I do SIP in Navi Liquid Fund?"* | "Should I" is advisory despite factual subject | Classify as ADVISORY; refuse |
| 2.1.4 | *"What is the difference between Navi Nifty 50 and Navi Next 50?"* | Comparison — could lead to implicit recommendation | Classify as ADVISORY (performance comparison); refuse; link to individual factsheets |
| 2.1.5 | *"Is 0.06% expense ratio low?"* | Asks for evaluation — subjective | Classify as ADVISORY; refuse; provide factsheet link |
| 2.1.6 | *"What is the expense ratio and is it good?"* | Mixed factual + advisory in one query | Split not possible; classify as ADVISORY; refuse entire query |

### 2.2 Keyword Classifier Edge Cases

| # | Scenario | Risk | Handling Strategy |
|---|---|---|---|
| 2.2.1 | Advisory keyword appears in a fund name: *"Navi Aggressive Hybrid Fund expense ratio?"* | "Aggressive" may trigger advisory filter | Keyword matching must operate on query intent, not fund name tokens; exclude fund names from scan |
| 2.2.2 | Query uses synonyms: *"Advise me on exit load"* | "Advise" not in keyword list | Add synonym expansion to keyword list; cover `advise`, `suggest`, `guide`, `recommend` |
| 2.2.3 | Query in informal language: *"bhai konsa fund better hai?"* | Hindi/mixed language bypasses English keyword filter | Groq fallback classifier handles ambiguous/non-English inputs |
| 2.2.4 | Negated advisory: *"Don't recommend, just tell me the exit load"* | "recommend" triggers advisory flag | Rule-based classifier incorrectly refuses; Groq fallback should re-classify as FACTUAL |
| 2.2.5 | Empty query submitted | Classifier receives empty string | Return a prompt asking the user to type a question; do not call Groq |

### 2.3 Groq Fallback Classifier Edge Cases

| # | Scenario | Risk | Handling Strategy |
|---|---|---|---|
| 2.3.1 | Groq rate limit hit during classification | Fallback fails | Default to ADVISORY (safe) if fallback cannot classify; show generic refusal |
| 2.3.2 | Groq returns unexpected classification output | Neither FACTUAL nor ADVISORY returned | Validate output; if invalid, default to ADVISORY |
| 2.3.3 | Groq classifier latency > 3s | Poor UX | Set `timeout=3s` on classification call; on timeout, default to rule-based result |

---

## 3. Retrieval Edge Cases

### 3.1 No Results / Low Similarity

| # | Scenario | Risk | Handling Strategy |
|---|---|---|---|
| 3.1.1 | Query is factual but about a fund not in the corpus | Retriever returns irrelevant chunks | Set a minimum similarity threshold (e.g., 0.4); if all scores below threshold, respond: *"I only have information about the 15 Navi funds listed. Please specify one of those."* |
| 3.1.2 | Query is too vague: *"tell me something"* | Retriever returns random high-scoring chunks | Low cosine similarity + no clear fund mention → trigger a "please be more specific" response |
| 3.1.3 | ChromaDB collection is empty (ingestion never ran) | Retriever crashes or returns nothing | Catch empty collection error; display: *"Knowledge base not loaded. Run corpus/ingest.py first."* |
| 3.1.4 | Query about a real-time value: *"What is today's NAV?"* | No real-time data in corpus | Detect NAV/live-price queries via keywords; redirect to the official Groww fund page URL |
| 3.1.5 | Top-K chunks are from different funds | Prompt context becomes mixed / contradictory | Filter retrieved chunks by the most mentioned `fund_name`; only pass consistent chunks to LLM |

### 3.2 Metadata Filter Edge Cases

| # | Scenario | Risk | Handling Strategy |
|---|---|---|---|
| 3.2.1 | User mentions fund by partial name: *"Navi 50"* | Metadata filter fails to match exact `fund_name` | Implement fuzzy matching on fund names in the metadata filter |
| 3.2.2 | User misspells fund name: *"Navi Nifty Fifty"* | No filter match | Fuzzy match against known fund names list from `corpus/urls.py` |
| 3.2.3 | Fund selector dropdown set to "All Funds" but user asks about one specific fund | Too many chunks returned from unrelated funds | Score-rank results; fund-name mention in query boosts cosine similarity naturally |

---

## 4. Prompt Builder Edge Cases

| # | Scenario | Risk | Handling Strategy |
|---|---|---|---|
| 4.1 | Retrieved chunks are very long and exceed context window | LLM truncates or errors | Cap total context at 2,000 tokens; truncate chunks proportionally if needed |
| 4.2 | Retrieved chunks contain conflicting data (two chunks disagree on expense ratio) | LLM generates inconsistent answer | Pass chunks in recency order (`scraped_at` descending); instruct LLM to prefer the most recent chunk |
| 4.3 | Retrieved chunks contain only boilerplate disclaimers, no factual data | LLM generates vague or hallucinated answer | Detect disclaimer-only chunks; trigger "cannot find information" response instead of LLM call |
| 4.4 | Prompt template variable `{retrieved_chunks}` is empty string | LLM receives empty context | Guard: if chunks list is empty, short-circuit to a "no data found" response without calling LLM |
| 4.5 | Prompt exceeds Groq model's max context length | API error 400 | Measure token count before sending; truncate oldest chunks until within limit |

---

## 5. LLM Generation Edge Cases (Groq)

### 5.1 API & Network

| # | Scenario | Risk | Handling Strategy |
|---|---|---|---|
| 5.1.1 | Groq API key invalid or expired | 401 Unauthorized | Catch `AuthenticationError`; display: *"API key error. Please check your .env file."* |
| 5.1.2 | Groq rate limit exceeded (429) | Request fails | Retry with 5s exponential backoff up to 3 times; fall back to `llama-3.1-8b-instant` |
| 5.1.3 | Groq primary model (`llama-3.3-70b-versatile`) unavailable | 503 Service Unavailable | Automatically retry with `llama-3.1-8b-instant` fallback model |
| 5.1.4 | Groq API times out after 10s | No response returned | Set `timeout=10s`; catch `TimeoutError`; show: *"Response timed out. Please try again."* |
| 5.1.5 | Groq API returns empty completion | No answer text | Detect `choices[0].message.content == ""`; respond with: *"Could not generate an answer. Please rephrase your query."* |

### 5.2 Response Quality

| # | Scenario | Risk | Handling Strategy |
|---|---|---|---|
| 5.2.1 | LLM hallucinates a fact not present in the retrieved chunks | Incorrect financial data served | Set `temperature=0.0`; use strict system prompt: *"Only use the provided context. If the answer is not in the context, say so."* |
| 5.2.2 | LLM generates more than 3 sentences | Violates response constraint | Post-process output: split by sentence, keep first 3, discard the rest |
| 5.2.3 | LLM includes investment advice despite system prompt | Compliance violation | Add a post-generation advisory keyword scan; if triggered, discard response and return the refusal message instead |
| 5.2.4 | LLM generates a response in a different language | Non-English output | Detect non-ASCII majority; fallback to: *"Please ask your question in English."* |
| 5.2.5 | LLM fabricates a source URL | Fake citation served | Never use URLs from LLM output; always append citation from retrieval metadata, not from LLM |

---

## 6. Response Formatter Edge Cases

| # | Scenario | Risk | Handling Strategy |
|---|---|---|---|
| 6.1 | `source_url` metadata is missing from top chunk | Response has no citation | Fall back to the fund's known Groww URL from `corpus/urls.py` using `fund_name` key |
| 6.2 | `scraped_at` date is missing from chunk metadata | Footer shows "Last updated from sources: None" | Fall back to: *"Last updated from sources: date unavailable"* |
| 6.3 | LLM output already contains a self-generated source link | Duplicate or fake link in response | Strip all URLs from raw LLM output using regex before rendering; attach only metadata-sourced citation |
| 6.4 | Response is exactly 3 sentences but the 3rd is a disclaimer inserted by the LLM | Disclaimer duplicated (formatter also adds one) | Detect if last sentence matches known disclaimer patterns; remove from LLM output before formatting |
| 6.5 | Formatter receives `None` as `llm_output` | `AttributeError` on `.strip()` | Guard with `if not llm_output: return error_response()` |

---

## 7. Refusal Handler Edge Cases

| # | Scenario | Risk | Handling Strategy |
|---|---|---|---|
| 7.1 | Refusal triggered for a legitimate factual query (false positive) | User frustrated; correct data not served | Log all refusals; allow user to rephrase with a suggestion: *"Try asking: 'What is the expense ratio of [Fund]?'"* |
| 7.2 | User rephrases advisory query to bypass classifier | *"As a hypothetical, which fund would perform better?"* | Groq fallback classifier catches semantic advisory intent regardless of phrasing |
| 7.3 | AMFI educational link in refusal response is broken/changed | Dead link served | Validate AMFI link periodically; maintain a fallback secondary link (SEBI investor education) |
| 7.4 | Refusal message itself sounds too harsh | Poor user experience | Use polite tone: *"I can only share factual information about these funds. For investment guidance, please consult a SEBI-registered advisor."* |
| 7.5 | Query is about a completely different topic (e.g., weather, cricket) | Off-topic query handled poorly | Classify as non-mutual-fund query; return a scoped refusal: *"I can only answer questions about the 15 Navi Mutual Fund schemes in my knowledge base."* |

---

## 8. Streamlit UI Edge Cases

### 8.1 Input Handling

| # | Scenario | Risk | Handling Strategy |
|---|---|---|---|
| 8.1.1 | User submits an empty query | `classify_query("")` called | Disable Send button and show inline hint: *"Please type a question."* |
| 8.1.2 | Query exceeds 500 characters | Very long prompt sent to Groq | Truncate input at 500 chars with a warning: *"Query too long. Please keep it under 500 characters."* |
| 8.1.3 | Query contains only whitespace or newlines | Treated as empty | Strip and check; treat as empty if blank after stripping |
| 8.1.4 | User pastes PII (PAN, Aadhaar, phone number) into the chat | Sensitive data in session state / logs | Add a client-side regex scan on input; if PII pattern detected, clear the input and warn: *"Please do not share personal information."* |
| 8.1.5 | Special characters in query: `<script>`, `--`, SQL injection | Potential injection or rendering issue | Escape all user input before rendering in chat history using `st.markdown(..., unsafe_allow_html=False)` |

### 8.2 Session & State

| # | Scenario | Risk | Handling Strategy |
|---|---|---|---|
| 8.2.1 | User refreshes the page mid-conversation | Session state lost, chat history cleared | This is expected Streamlit behaviour; inform users in the UI: *"Chat history is not persisted across page refreshes."* |
| 8.2.2 | Multiple browser tabs open the same Streamlit instance | Session state shared unexpectedly | Streamlit isolates sessions per browser tab by default; no action needed |
| 8.2.3 | Groq call hangs and spinner runs indefinitely | User stuck | Set a 15s timeout on the full `handle_query()` call; display: *"Request timed out. Please try again."* and re-enable input |
| 8.2.4 | Chat history grows very large in one session | UI becomes slow to render | Cap rendered history at the last 20 messages; earlier messages not displayed but preserved in `session_state` |

### 8.3 Example Questions

| # | Scenario | Risk | Handling Strategy |
|---|---|---|---|
| 8.3.1 | User clicks example question button but Chroma isn't loaded yet | Error on retrieval | Show a loading indicator on startup; disable example buttons until the RAG chain is initialized |
| 8.3.2 | Example question button clicked while another query is processing | Race condition | Disable all input controls while a request is in flight |

---

## 9. Privacy & Security Edge Cases

| # | Scenario | Risk | Handling Strategy |
|---|---|---|---|
| 9.1 | User includes their PAN number in a query: *"My PAN is ABCDE1234F, am I eligible for ELSS?"* | PII in query text | Detect PAN pattern `[A-Z]{5}[0-9]{4}[A-Z]{1}` with regex; clear input, refuse to process, warn user |
| 9.2 | User includes Aadhaar number in a query | PII in query text | Detect 12-digit numeric string; same treatment as PAN |
| 9.3 | User includes phone number or email | PII in query text | Regex detection; clear input and warn |
| 9.4 | `.env` file accidentally committed to Git | API key exposure | `.gitignore` includes `.env`; add `pre-commit` hook to block commits containing `GROQ_API_KEY=gsk_` |
| 9.5 | ChromaDB persisted data contains scraped content from outside the whitelist | Untrusted data indexed | Enforce URL whitelist check in `ingest.py`: only process URLs in `corpus/urls.py`; reject others |
| 9.6 | Session logging accidentally captures user queries | Privacy violation | Streamlit session state is in-memory only; no server-side query logging is implemented |
| 9.7 | Third-party CDN scripts injected via Groww HTML into clean text | Malicious content in vector store | `cleaner.py` strips all `<script>` and `<style>` tags before text extraction |

---

## 10. System & Infrastructure Edge Cases

| # | Scenario | Risk | Handling Strategy |
|---|---|---|---|
| 10.1 | ChromaDB is corrupted (partial write, disk error) | Vector store unreadable | Detect `chromadb.errors.InvalidCollectionException` on startup; prompt user to re-run `ingest.py` |
| 10.2 | ChromaDB directory deleted accidentally | All embeddings lost | Ingestion is idempotent; re-run `python corpus/ingest.py` to rebuild from scratch |
| 10.3 | BGE model files are deleted or corrupted | Embedding fails | `sentence-transformers` will re-download from HuggingFace Hub on next startup; requires internet |
| 10.4 | Groq free-tier daily token limit reached | All LLM calls fail for the rest of the day | Catch `RateLimitError`; display: *"Daily usage limit reached. Please try again tomorrow or upgrade your Groq plan."* |
| 10.5 | Python version mismatch (< 3.11) | Dependency incompatibilities | Add a version check at the top of `verify_setup.py`; exit with clear error if Python < 3.11 |
| 10.6 | `requirements.txt` installs incompatible versions | Runtime `ImportError` or `AttributeError` | Pins exact versions; use a virtual environment (`venv`) to isolate from system Python |
| 10.7 | Playwright browsers not installed (skipped `playwright install`) | Scraper crashes when falling back to Playwright | Catch `playwright._impl._errors.Error`; print: *"Run: playwright install chromium"* |
| 10.8 | Streamlit port 8501 already in use | App fails to start | Instruct user to run `streamlit run app/streamlit_app.py --server.port 8502` |
| 10.9 | Ingestion runs with no internet access | Scraper fails for all 15 URLs | Detect `httpx.ConnectError`; abort with: *"No internet connection. Ingestion requires live access to Groww URLs."* |
| 10.10 | Groww fund URL returns a redirect (fund renamed/merged) | Scraper follows redirect to unrelated page | Detect URL mismatch between requested and final URL after redirect; log warning and skip |

---

## Summary: Priority Matrix

| Severity | Edge Cases |
|---|---|
| 🔴 **Critical** | 5.2.3 (LLM generates advice), 9.1–9.3 (PII in query), 5.1.1 (invalid API key), 3.1.3 (empty ChromaDB), 6.5 (None LLM output) |
| 🟠 **High** | 1.2.1 (JS rendering fallback), 1.4.2 (duplicate chunks on re-ingest), 5.1.2–5.1.3 (Groq rate limit/fallback), 5.2.1 (hallucination), 5.2.5 (fake citation from LLM) |
| 🟡 **Medium** | 2.2.1 (fund name in keyword), 3.1.1 (fund not in corpus), 3.1.4 (real-time NAV query), 4.4 (empty chunks), 7.5 (off-topic query) |
| 🟢 **Low** | 8.2.1 (session lost on refresh), 8.2.4 (long chat history), 10.8 (port in use) |

---

> **Disclaimer:** *Facts-only. No investment advice.*
