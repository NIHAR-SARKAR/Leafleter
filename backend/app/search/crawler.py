"""Web page crawler using httpx and BeautifulSoup."""

from __future__ import annotations

import asyncio
from urllib.parse import urljoin, urlparse, urlunparse

import httpx
from bs4 import BeautifulSoup
from urllib.robotparser import RobotFileParser

from app.core.exceptions import AppException
from app.core.logging import get_logger

logger = get_logger(__name__)

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)

MAX_TEXT_LENGTH = 50_000
MAX_REDIRECTS = 10
TIMEOUT = 30.0
MAX_LINKS = 500


# ---------------------------------------------------------------------------
# Robots.txt cache (process-lifetime, best-effort)
# ---------------------------------------------------------------------------

class _RobotsCache:
    """Lightweight in-process cache for robots.txt parsers."""

    def __init__(self) -> None:
        self._cache: dict[str, RobotFileParser] = {}
        self._lock = asyncio.Lock()

    async def is_allowed(self, url: str, user_agent: str = DEFAULT_USER_AGENT) -> bool:
        """Return True if *user_agent* is allowed to fetch *url*."""
        parsed = urlparse(url)
        origin = f"{parsed.scheme}://{parsed.netloc}"

        async with self._lock:
            if origin not in self._cache:
                robots_url = f"{origin}/robots.txt"
                rp = RobotFileParser(robots_url)
                try:
                    # RobotFileParser is sync; run in a thread to avoid blocking.
                    await asyncio.to_thread(rp.read)
                except Exception:
                    # If we can't fetch robots.txt, assume allowed.
                    rp = RobotFileParser()
                self._cache[origin] = rp

        return self._cache[origin].can_fetch(user_agent, url)


_robots_cache = _RobotsCache()


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _normalise_link(href: str, base_url: str) -> str | None:
    """
    Resolve *href* against *base_url* and return a normalised absolute URL,
    or ``None`` if the link should be discarded.
    """
    href = href.strip()

    # Skip non-navigable schemes before joining.
    if not href or href.startswith(("#", "javascript:", "mailto:", "tel:", "data:")):
        return None

    absolute = urljoin(base_url, href)
    parsed = urlparse(absolute)

    if parsed.scheme not in {"http", "https"}:
        return None

    # Drop fragment, normalise trailing slash on bare paths.
    path = parsed.path or "/"
    normalised = urlunparse((parsed.scheme, parsed.netloc, path, parsed.params, parsed.query, ""))
    return normalised


def _decode_response(response: httpx.Response) -> str:
    """
    Return the response body as text.

    Falls back to UTF-8 with replacement characters if the declared encoding
    is wrong or absent, rather than raising a ``UnicodeDecodeError``.
    """
    try:
        return response.text
    except (UnicodeDecodeError, LookupError):
        return response.content.decode("utf-8", errors="replace")


# ---------------------------------------------------------------------------
# Public API
# ---------------------------------------------------------------------------

async def crawl_url(
    url: str,
    *,
    timeout: float = TIMEOUT,
    max_links: int = MAX_LINKS,
    respect_robots: bool = True,
) -> dict[str, object]:
    """Crawl a URL and extract title, visible text, and outbound links.

    Args:
        url: The URL to crawl.
        timeout: HTTP timeout in seconds.
        max_links: Maximum number of unique outbound links to return.
        respect_robots: When ``True`` (default), skip URLs disallowed by
            ``robots.txt``.

    Returns:
        A dictionary with ``url``, ``title``, ``text``, and ``links`` keys.

    Raises:
        AppException: If the request fails, the content type is unsupported,
            or the URL is disallowed by robots.txt.
    """
    if respect_robots and not await _robots_cache.is_allowed(url):
        logger.warning("crawl_robots_disallowed", url=url)
        raise AppException(f"Crawling disallowed by robots.txt: {url}", status_code=403)

    headers = {
        "User-Agent": DEFAULT_USER_AGENT,
        "Accept": "text/html,application/xhtml+xml",
    }

    logger.info("crawl_url_request", url=url)

    async with httpx.AsyncClient(
        timeout=timeout,
        follow_redirects=True,
        max_redirects=MAX_REDIRECTS,
        headers=headers,
    ) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error(
                "crawl_http_error",
                url=url,
                status_code=exc.response.status_code,
            )
            raise AppException(
                f"HTTP error {exc.response.status_code} while crawling {url}",
                status_code=exc.response.status_code,
            ) from exc
        except httpx.TooManyRedirects as exc:
            logger.error("crawl_too_many_redirects", url=url)
            raise AppException(f"Too many redirects while crawling {url}") from exc
        except httpx.RequestError as exc:
            logger.error("crawl_request_error", url=url, error=str(exc))
            raise AppException(f"Failed to crawl {url}") from exc

        # ----------------------------------------------------------------
        # All response processing is inside the `async with` block so that
        # the client (and its connection pool) is still alive when we read
        # `response.text`, `response.headers`, and `response.url`.
        # ----------------------------------------------------------------

        content_type = response.headers.get("content-type", "")
        if "text/html" not in content_type and "application/xhtml" not in content_type:
            logger.warning("crawl_unsupported_content_type", url=url, content_type=content_type)
            raise AppException(
                f"Unsupported content type: {content_type}",
                status_code=400,
            )

        html = _decode_response(response)
        base_url = str(response.url)

    # Parsing is CPU-bound; do it outside the HTTP client context.
    soup = BeautifulSoup(html, "html.parser")

    # --- Respect <meta name="robots" content="nofollow"> ------------------
    meta_robots = soup.find("meta", attrs={"name": lambda v: v and v.lower() == "robots"})
    meta_content = (meta_robots.get("content", "") if meta_robots else "").lower()
    follow_links = "nofollow" not in meta_content

    # --- Title (before destructive decompose calls) -----------------------
    title_tag = soup.find("title")
    title = title_tag.get_text(strip=True) if title_tag else ""

    # --- Visible text -----------------------------------------------------
    for tag in soup(["script", "style", "nav", "footer", "header"]):
        tag.decompose()

    text = soup.get_text(separator="\n", strip=True)
    lines = [line.strip() for line in text.splitlines() if line.strip()]
    text = "\n".join(lines)[:MAX_TEXT_LENGTH]

    # --- Outbound links ---------------------------------------------------
    links: list[str] = []
    if follow_links:
        seen: set[str] = set()
        for anchor in soup.find_all("a", href=True):
            if len(links) >= max_links:
                break
            normalised = _normalise_link(anchor["href"], base_url)
            if normalised and normalised not in seen:
                seen.add(normalised)
                links.append(normalised)

    logger.info(
        "crawl_url_complete",
        url=base_url,
        title=title,
        text_length=len(text),
        links_found=len(links),
    )

    return {
        "url": base_url,
        "title": title,
        "text": text,
        "links": links,
    }