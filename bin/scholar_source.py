"""Google Scholar publication fetching shared by the maintenance scripts.

Google Scholar blocks requests from datacenter IPs (including GitHub Actions
runners) with HTTP 403 / CAPTCHA pages, so direct scraping is unreliable in CI.
The backend is chosen from environment variables, in order:

- SERPAPI_API_KEY: fetch the author profile through SerpAPI's
  ``google_scholar_author`` engine (recommended, works from CI).
- SCRAPER_API_KEY: scrape with scholarly through ScraperAPI.
- SCHOLAR_PROXY: scrape with scholarly through this HTTP(S) proxy URL.
- otherwise: scrape with scholarly directly (usually works only from a
  residential IP, e.g. when running locally).

Every backend returns a list of dicts with the keys ``pub_id``, ``title``,
``year``, ``citations``, ``authors`` and ``venue``.
"""

import os

import requests

REQUEST_TIMEOUT_SECONDS = 15
MAX_REQUEST_RETRIES = 1
SERPAPI_URL = "https://serpapi.com/search.json"
SERPAPI_PAGE_SIZE = 100
SERPAPI_MAX_PAGES = 10


def fetch_publications(scholar_user_id: str) -> list:
    """Fetch all publications of a Google Scholar profile."""
    serpapi_key = os.environ.get("SERPAPI_API_KEY")
    if serpapi_key:
        print("Using SerpAPI to fetch Google Scholar data.")
        return _fetch_with_serpapi(scholar_user_id, serpapi_key)
    print(
        "SERPAPI_API_KEY is not set; scraping Google Scholar with scholarly. "
        "This is usually blocked from CI runners."
    )
    return _fetch_with_scholarly(scholar_user_id)


def _fetch_with_serpapi(scholar_user_id: str, api_key: str) -> list:
    publications = []
    for page in range(SERPAPI_MAX_PAGES):
        params = {
            "engine": "google_scholar_author",
            "author_id": scholar_user_id,
            "hl": "en",
            "num": SERPAPI_PAGE_SIZE,
            "start": page * SERPAPI_PAGE_SIZE,
            "api_key": api_key,
        }
        response = requests.get(SERPAPI_URL, params=params, timeout=60)
        data = response.json() if response.content else {}
        if response.status_code != 200 or "error" in data:
            raise RuntimeError(
                f"SerpAPI request failed (HTTP {response.status_code}): "
                f"{data.get('error', response.text[:200])}"
            )

        articles = data.get("articles", [])
        for article in articles:
            publications.append(
                {
                    "pub_id": article.get("citation_id"),
                    "title": article.get("title", "Unknown Title"),
                    "year": article.get("year") or "Unknown Year",
                    "citations": (article.get("cited_by") or {}).get("value") or 0,
                    "authors": article.get("authors", ""),
                    "venue": article.get("publication", ""),
                }
            )

        if len(articles) < SERPAPI_PAGE_SIZE:
            break
    return publications


def _fetch_with_scholarly(scholar_user_id: str) -> list:
    from scholarly import ProxyGenerator, scholarly

    scholarly.set_timeout(REQUEST_TIMEOUT_SECONDS)
    scholarly.set_retries(MAX_REQUEST_RETRIES)

    scraper_api_key = os.environ.get("SCRAPER_API_KEY")
    proxy_url = os.environ.get("SCHOLAR_PROXY")
    if scraper_api_key or proxy_url:
        proxy_generator = ProxyGenerator()
        if scraper_api_key:
            configured = proxy_generator.ScraperAPI(scraper_api_key)
        else:
            configured = proxy_generator.SingleProxy(http=proxy_url, https=proxy_url)
        if not configured:
            raise RuntimeError("Could not configure the Google Scholar proxy.")
        scholarly.use_proxy(proxy_generator)

    author = scholarly.search_author_id(scholar_user_id)
    author_data = scholarly.fill(author, sections=["publications"])
    if not author_data or "publications" not in author_data:
        raise RuntimeError(f"No publications found for user ID '{scholar_user_id}'.")

    publications = []
    for pub in author_data["publications"]:
        bib = pub.get("bib", {})
        publications.append(
            {
                "pub_id": pub.get("author_pub_id") or pub.get("pub_id"),
                "title": bib.get("title", "Unknown Title"),
                "year": bib.get("pub_year", "Unknown Year"),
                "citations": pub.get("num_citations", 0),
                "authors": bib.get("author", ""),
                "venue": bib.get("citation", ""),
            }
        )
    return publications
