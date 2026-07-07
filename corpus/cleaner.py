"""
corpus/cleaner.py
HTML parser and structured text extractor for Groww mutual fund pages.

Strategy:
  Groww is a Next.js app. Every fund page embeds all structured data inside
  a <script id="__NEXT_DATA__"> JSON tag on the server side.
  We extract directly from this JSON for clean, structured output —
  avoiding the noise of HTML class selectors that can change anytime.

  If __NEXT_DATA__ is unavailable (edge case), we fall back to a
  BeautifulSoup visible-text extraction with noise removal.

Output per fund:
  A plain-text document structured as labelled sections, e.g.:
    Fund Name: ...
    Category: ...
    Expense Ratio: ...
    ...
  Plus source metadata dict attached alongside.
"""

import json
import re
import logging
from bs4 import BeautifulSoup

logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _safe(value, default="N/A") -> str:
    """Convert a value to a non-empty string, or return default."""
    if value is None or value == "" or value == []:
        return default
    return str(value).strip()


def _format_inr(value) -> str:
    """Format a numeric AUM value (in crores) to a readable string."""
    try:
        crores = float(value)
        if crores >= 1000:
            return f"Rs {crores / 1000:.2f} thousand crore (Rs {crores:.2f} crore)"
        return f"Rs {crores:.2f} crore"
    except (TypeError, ValueError):
        return _safe(value)


def _lock_in_text(lock_in: dict) -> str:
    """Format lock-in dict {'years':3,'months':0,'days':0} to readable string."""
    if not lock_in:
        return "None"
    parts = []
    y = lock_in.get("years", 0) or 0
    m = lock_in.get("months", 0) or 0
    d = lock_in.get("days", 0) or 0
    if y:
        parts.append(f"{y} year{'s' if y != 1 else ''}")
    if m:
        parts.append(f"{m} month{'s' if m != 1 else ''}")
    if d:
        parts.append(f"{d} day{'s' if d != 1 else ''}")
    return ", ".join(parts) if parts else "None"


def _fund_manager_names(details: list) -> str:
    """Extract fund manager names from fund_manager_details list."""
    if not details:
        return "N/A"
    names = []
    for fm in details:
        name = fm.get("name") or fm.get("fund_manager_name") or ""
        if name:
            names.append(name.strip())
    return ", ".join(names) if names else "N/A"


def _analysis_bullets(analysis: list) -> str:
    """
    Convert analysis list (PROS/CONS/NEUTRAL items) to labelled bullet points.
    Skips performance-comparison items to stay compliant.
    """
    if not analysis:
        return ""
    lines = []
    for item in analysis:
        atype = item.get("analysis_type", "").upper()
        subject = item.get("analysis_subject", "")
        text = item.get("analysis_text") or item.get("text") or ""
        # Skip return/performance comparisons (compliance)
        if any(kw in subject.lower() for kw in ["return", "performance", "alpha", "beta"]):
            continue
        label = {"PROS": "Positive", "CONS": "Consideration", "NEUTRAL": "Note"}.get(atype, atype)
        if text:
            lines.append(f"  {label}: {text.strip()}")
    return "\n".join(lines)


# ---------------------------------------------------------------------------
# Primary extractor — from __NEXT_DATA__ JSON
# ---------------------------------------------------------------------------

def _extract_from_next_data(html: str) -> dict | None:
    """
    Parse __NEXT_DATA__ JSON and return a structured dict with all fund fields.
    Returns None if the tag is missing or malformed.
    """
    soup = BeautifulSoup(html, "html.parser")
    tag = soup.find("script", id="__NEXT_DATA__")
    if not tag or not tag.string:
        logger.warning("__NEXT_DATA__ script tag not found")
        return None

    try:
        data = json.loads(tag.string)
    except json.JSONDecodeError as e:
        logger.warning("Failed to parse __NEXT_DATA__ JSON: %s", e)
        return None

    mf = (
        data.get("props", {})
            .get("pageProps", {})
            .get("mfServerSideData", {})
    )
    if not mf:
        logger.warning("mfServerSideData not found in __NEXT_DATA__")
        return None

    # -- Fund manager details (prefer structured list over flat string) --
    fm_text = _fund_manager_names(mf.get("fund_manager_details") or [])
    if fm_text == "N/A":
        fm_text = _safe(mf.get("fund_manager"))

    # -- Lock-in --
    lock_in = _lock_in_text(mf.get("lock_in") or {})
    lock_in_yrs = (mf.get("additional_details") or {}).get("lock_in_yrs")
    if lock_in == "None" and lock_in_yrs:
        lock_in = f"{lock_in_yrs} year(s)"

    # -- Category info description (educational, non-performance) --
    cat_info = mf.get("category_info") or {}
    category_description = _safe(cat_info.get("definition") or cat_info.get("description"))

    # -- AMC info --
    amc_info = mf.get("amc_info") or {}
    amc_description = _safe(amc_info.get("description"))

    # -- Analysis bullets (PROS/CONS, non-performance only) --
    analysis_text = _analysis_bullets(mf.get("analysis") or [])

    return {
        # --- Identity ---
        "fund_name":          _safe(mf.get("scheme_name") or mf.get("fund_name")),
        "fund_house":         _safe(mf.get("fund_house")),
        "isin":               _safe(mf.get("isin")),
        "plan_type":          _safe(mf.get("plan_type")),
        "scheme_type":        _safe(mf.get("scheme_type")),
        "launch_date":        _safe(mf.get("launch_date")),
        # --- Category ---
        "category":           _safe(mf.get("category")),
        "sub_category":       _safe(mf.get("sub_category")),
        "super_category":     _safe(mf.get("super_category")),
        "category_description": category_description,
        # --- Key metrics ---
        "nav":                _safe(mf.get("nav")),
        "nav_date":           _safe(mf.get("nav_date")),
        "aum":                _format_inr(mf.get("aum")),
        "expense_ratio":      _safe(mf.get("expense_ratio")),
        "exit_load":          _safe(mf.get("exit_load")),
        "benchmark":          _safe(mf.get("benchmark") or mf.get("benchmark_name")),
        "lock_in":            lock_in,
        "riskometer":         _safe(mf.get("nfo_risk")),
        "portfolio_turnover": _safe(mf.get("portfolio_turnover")),
        # --- Investment limits ---
        "min_lumpsum":        _safe(mf.get("min_investment_amount")),
        "min_sip":            _safe(mf.get("min_sip_investment")),
        "min_additional":     _safe(mf.get("mini_additional_investment")),
        "min_withdrawal":     _safe(mf.get("min_withdrawal")),
        # --- Fund manager ---
        "fund_manager":       fm_text,
        # --- Description ---
        "description":        _safe(mf.get("description")),
        # --- AMC ---
        "amc_description":    amc_description,
        # --- Stamp duty ---
        "stamp_duty":         _safe(mf.get("stamp_duty")),
        # --- Registrar ---
        "registrar":          _safe(mf.get("registrar_agent")),
        # --- SID link ---
        "sid_url":            _safe(mf.get("sid_url")),
        # --- Analysis bullets ---
        "analysis":           analysis_text,
        # --- Ratings ---
        "groww_rating":       _safe(mf.get("groww_rating")),
        "crisil_rating":      _safe(mf.get("crisil_rating")),
        # --- Meta ---
        "meta_description":   _safe(mf.get("meta_desc")),
    }


# ---------------------------------------------------------------------------
# Fallback extractor — plain BeautifulSoup visible-text
# ---------------------------------------------------------------------------

def _extract_from_html(html: str) -> dict | None:
    """
    Fallback: extract visible text from HTML after stripping noise tags.
    Returns a minimal dict with just a 'raw_text' key.
    """
    soup = BeautifulSoup(html, "html.parser")

    # Remove noise tags
    for tag in soup(["script", "style", "nav", "footer", "header",
                     "noscript", "iframe", "svg", "button", "form"]):
        tag.decompose()

    # Remove elements likely to be ads or cookie banners
    for cls in ["cookie", "banner", "ad-", "popup", "modal", "overlay", "sidebar"]:
        for el in soup.find_all(class_=re.compile(cls, re.I)):
            el.decompose()

    text = soup.get_text(separator="\n", strip=True)

    # Collapse multiple blank lines
    text = re.sub(r"\n{3,}", "\n\n", text)
    # Collapse excessive spaces
    text = re.sub(r"[ \t]{2,}", " ", text)

    logger.info("Fallback HTML extraction: %d chars", len(text))
    return {"raw_text": text} if text else None


# ---------------------------------------------------------------------------
# Text document builder
# ---------------------------------------------------------------------------

SECTION_TEMPLATE = """\
=== {fund_name} ===

Fund House       : {fund_house}
ISIN             : {isin}
Plan Type        : {plan_type} | Scheme Type: {scheme_type}
Launch Date      : {launch_date}

--- Category ---
Category         : {category} > {sub_category}
Benchmark        : {benchmark}
Riskometer       : {riskometer}

--- Key Details ---
NAV              : Rs {nav} (as of {nav_date})
AUM              : {aum}
Expense Ratio    : {expense_ratio}%
Exit Load        : {exit_load}
Lock-in Period   : {lock_in}
Portfolio Turnover: {portfolio_turnover}%
Stamp Duty       : {stamp_duty}

--- Investment Details ---
Minimum Lumpsum  : Rs {min_lumpsum}
Minimum SIP      : Rs {min_sip} per month
Minimum Additional: Rs {min_additional}
Minimum Withdrawal: Rs {min_withdrawal}

--- Fund Manager ---
Manager(s)       : {fund_manager}
Registrar        : {registrar}

--- Description ---
{description}

--- About the Category ---
{category_description}

--- Fund Analysis ---
{analysis}

--- Ratings ---
Groww Rating     : {groww_rating} / 5
CRISIL Rating    : {crisil_rating}

--- Documents ---
Scheme Information Document (SID): {sid_url}

--- Disclaimer ---
Facts-only. No investment advice. Source: Groww official fund page.
"""


def build_text_document(fields: dict) -> str:
    """
    Render the structured fields dict into a formatted plain-text document
    suitable for chunking and embedding.
    """
    try:
        return SECTION_TEMPLATE.format(**fields)
    except KeyError as e:
        logger.warning("Missing field in template: %s", e)
        return "\n".join(f"{k}: {v}" for k, v in fields.items() if v and v != "N/A")


# ---------------------------------------------------------------------------
# Main public API
# ---------------------------------------------------------------------------

def clean(scrape_result: dict) -> dict | None:
    """
    Clean a single scrape result dict (output of scraper.scrape_url).

    Returns:
        {
            "fund_name":  str,
            "category":   str,
            "source_url": str,
            "fetched_at": str,
            "text":       str   — clean plain-text document ready for chunking
        }
        Or None if extraction fails completely.
    """
    html = scrape_result.get("html", "")
    url  = scrape_result.get("url", "")
    fetched_at = scrape_result.get("fetched_at", "")

    # --- Try structured JSON extraction first ---
    fields = _extract_from_next_data(html)

    if fields:
        text = build_text_document(fields)
        logger.info(
            "Cleaned [JSON] '%s': %d chars",
            fields.get("fund_name", url), len(text)
        )
        return {
            "fund_name":  fields["fund_name"],
            "category":   fields.get("sub_category") or fields.get("category", ""),
            "source_url": url,
            "fetched_at": fetched_at,
            "text":       text,
        }

    # --- Fallback: raw HTML text ---
    logger.warning("Falling back to HTML extraction for %s", url)
    fallback = _extract_from_html(html)
    if fallback:
        return {
            "fund_name":  url.split("/")[-1].replace("-", " ").title(),
            "category":   "Unknown",
            "source_url": url,
            "fetched_at": fetched_at,
            "text":       fallback["raw_text"],
        }

    logger.error("Both extraction methods failed for %s", url)
    return None


def clean_all(scrape_results: list[dict]) -> list[dict]:
    """
    Clean a list of scrape results (output of scraper.scrape_all).

    Returns only successfully cleaned docs — failed ones are logged and skipped.
    """
    cleaned = []
    for result in scrape_results:
        doc = clean(result)
        if doc:
            cleaned.append(doc)
        else:
            logger.error("Skipping failed clean for: %s", result.get("url"))
    logger.info("Cleaning complete: %d/%d docs cleaned", len(cleaned), len(scrape_results))
    return cleaned


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------

if __name__ == "__main__":
    from corpus.scraper import scrape_url

    test_url = "https://groww.in/mutual-funds/navi-nifty-50-index-fund-direct-growth"
    print(f"\n=== Cleaner Test: {test_url} ===\n")

    result = scrape_url(test_url)
    doc = clean(result)

    if doc:
        print(f"Fund Name   : {doc['fund_name']}")
        print(f"Category    : {doc['category']}")
        print(f"Source URL  : {doc['source_url']}")
        print(f"Fetched At  : {doc['fetched_at']}")
        print(f"Text Length : {len(doc['text'])} chars")
        print("\n--- Text Preview (first 800 chars) ---\n")
        print(doc["text"][:800])
    else:
        print("FAILED: clean() returned None")
