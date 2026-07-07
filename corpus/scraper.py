"""
corpus/scraper.py
Web scraper for Groww mutual fund pages.

Strategy:
  1. Try httpx (fast, lightweight) first.
  2. If the returned HTML body is too small or empty (JS-rendered page),
     fall back to Playwright (headless Chromium) to get the fully rendered DOM.
  3. Both paths use exponential backoff with up to MAX_RETRIES attempts.

Returns:
  A dict per fund: { "url", "html", "fetched_at" }
  Returns None for a fund if all retries are exhausted.
"""

import time
import logging
from datetime import datetime, timezone

import httpx

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(message)s")
logger = logging.getLogger(__name__)

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------
MAX_RETRIES = 3
RETRY_BASE_DELAY = 2          # seconds (doubles each retry)
HTTPX_TIMEOUT = 15            # seconds
MIN_HTML_LENGTH = 5_000       # bytes — below this we assume JS-rendering needed
PLAYWRIGHT_WAIT_MS = 3_000    # ms to wait for JS to settle after page load

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept-Language": "en-US,en;q=0.9",
    "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
}


# ---------------------------------------------------------------------------
# httpx fetch (fast path)
# ---------------------------------------------------------------------------
def _fetch_httpx(url: str) -> str | None:
    """
    Fetch a URL using httpx. Returns raw HTML string or None on failure.
    Follows redirects automatically and validates the final URL.
    """
    try:
        with httpx.Client(headers=HEADERS, timeout=HTTPX_TIMEOUT, follow_redirects=True) as client:
            response = client.get(url)
            response.raise_for_status()

            # Detect redirect to an unrelated page
            final_url = str(response.url)
            if final_url != url and "mutual-funds" not in final_url:
                logger.warning("Redirect to unrelated page: %s -> %s", url, final_url)
                return None

            html = response.text
            logger.info("httpx fetched %s (%d chars)", url, len(html))
            return html

    except httpx.HTTPStatusError as e:
        logger.warning("HTTP error %s for %s", e.response.status_code, url)
    except httpx.TimeoutException:
        logger.warning("Timeout on httpx fetch: %s", url)
    except httpx.RequestError as e:
        logger.warning("Request error for %s: %s", url, e)
    return None


# ---------------------------------------------------------------------------
# Playwright fetch (JS-rendered fallback)
# ---------------------------------------------------------------------------
def _fetch_playwright(url: str) -> str | None:
    """
    Fetch a URL using headless Playwright Chromium.
    Waits for the network to be idle so JS-rendered content is fully loaded.
    Returns rendered HTML string or None on failure.
    """
    try:
        from playwright.sync_api import sync_playwright, TimeoutError as PlaywrightTimeout

        with sync_playwright() as p:
            browser = p.chromium.launch(headless=True)
            context = browser.new_context(
                user_agent=HEADERS["User-Agent"],
                locale="en-US",
            )
            page = context.new_page()

            try:
                page.goto(url, wait_until="networkidle", timeout=30_000)
                page.wait_for_timeout(PLAYWRIGHT_WAIT_MS)   # extra settle time

                # Detect redirect
                final_url = page.url
                if final_url != url and "mutual-funds" not in final_url:
                    logger.warning("Playwright redirect to unrelated page: %s -> %s", url, final_url)
                    return None

                html = page.content()
                logger.info("Playwright fetched %s (%d chars)", url, len(html))
                return html

            except PlaywrightTimeout:
                logger.warning("Playwright timeout for %s", url)
                return None
            finally:
                context.close()
                browser.close()

    except Exception as e:
        logger.error("Playwright error for %s: %s", url, e)
        return None


# ---------------------------------------------------------------------------
# Core scrape function with retry + fallback
# ---------------------------------------------------------------------------
def scrape_url(url: str) -> dict | None:
    """
    Scrape a single Groww fund URL.

    Flow:
      - Attempt httpx up to MAX_RETRIES times with exponential backoff.
      - If resulting HTML is too short (JS rendering suspected), fall back to Playwright.
      - Returns a result dict or None if all attempts fail.

    Returns:
        {
            "url":        str  — the original requested URL,
            "html":       str  — raw HTML content,
            "fetched_at": str  — ISO 8601 UTC timestamp,
            "method":     str  — "httpx" or "playwright"
        }
    """
    html = None
    method = None

    # --- httpx attempts ---
    for attempt in range(1, MAX_RETRIES + 1):
        logger.info("[%d/%d] httpx -> %s", attempt, MAX_RETRIES, url)
        html = _fetch_httpx(url)

        if html and len(html) >= MIN_HTML_LENGTH:
            method = "httpx"
            break

        if html and len(html) < MIN_HTML_LENGTH:
            logger.info("HTML too short (%d chars) — will try Playwright", len(html))
            html = None
            break   # no point retrying httpx; escalate to Playwright

        # Exponential backoff before retry
        if attempt < MAX_RETRIES:
            delay = RETRY_BASE_DELAY * (2 ** (attempt - 1))
            logger.info("Retrying in %ds...", delay)
            time.sleep(delay)

    # --- Playwright fallback ---
    if not html:
        logger.info("Falling back to Playwright for %s", url)
        for attempt in range(1, MAX_RETRIES + 1):
            logger.info("[%d/%d] Playwright -> %s", attempt, MAX_RETRIES, url)
            html = _fetch_playwright(url)

            if html and len(html) >= MIN_HTML_LENGTH:
                method = "playwright"
                break

            if attempt < MAX_RETRIES:
                delay = RETRY_BASE_DELAY * (2 ** (attempt - 1))
                logger.info("Playwright retry in %ds...", delay)
                time.sleep(delay)

    if not html:
        logger.error("All attempts failed for %s", url)
        return None

    return {
        "url": url,
        "html": html,
        "fetched_at": datetime.now(timezone.utc).strftime("%Y-%m-%d"),
        "method": method,
    }


# ---------------------------------------------------------------------------
# Batch scraper — all 15 funds
# ---------------------------------------------------------------------------
def scrape_all(fund_urls: list[dict], delay_between: float = 1.5) -> list[dict]:
    """
    Scrape all funds from the FUND_URLS registry.

    Args:
        fund_urls:       List of fund dicts from corpus/urls.py
        delay_between:   Polite delay (seconds) between each request

    Returns:
        List of result dicts — each contains fund metadata merged with scrape result.
        Failed scrapes are logged and excluded from the output.
    """
    results = []
    total = len(fund_urls)

    for i, fund in enumerate(fund_urls, 1):
        logger.info("Scraping [%d/%d]: %s", i, total, fund["name"])
        result = scrape_url(fund["url"])

        if result:
            results.append({
                "id":         fund["id"],
                "name":       fund["name"],
                "category":   fund["category"],
                "url":        result["url"],
                "html":       result["html"],
                "fetched_at": result["fetched_at"],
                "method":     result["method"],
            })
            logger.info("  OK  [%s] %d chars", result["method"], len(result["html"]))
        else:
            logger.error("  FAILED  %s — skipped", fund["name"])

        # Polite delay to avoid rate-limiting
        if i < total:
            time.sleep(delay_between)

    logger.info("Scraping complete: %d/%d pages fetched", len(results), total)
    return results


# ---------------------------------------------------------------------------
# Standalone test
# ---------------------------------------------------------------------------
if __name__ == "__main__":
    from corpus.urls import FUND_URLS

    print("\n=== Scraper Test — first 2 funds ===\n")
    sample = FUND_URLS[:2]
    results = scrape_all(sample, delay_between=1.0)

    for r in results:
        print(f"  [{r['method'].upper():10s}]  {r['name'][:50]}  ({len(r['html'])} chars)  fetched_at={r['fetched_at']}")

    print(f"\nFetched {len(results)}/{len(sample)} pages")
