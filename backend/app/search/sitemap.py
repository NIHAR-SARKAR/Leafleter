"""Sitemap parser using httpx and ElementTree."""

import xml.etree.ElementTree as ET
from urllib.parse import urljoin

import httpx

from app.core.exceptions import AppException
from app.core.logging import get_logger

logger = get_logger(__name__)

DEFAULT_USER_AGENT = (
    "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
    "AppleWebKit/537.36 (KHTML, like Gecko) "
    "Chrome/120.0.0.0 Safari/537.36"
)
MAX_SITEMAP_DEPTH = 2
MAX_URLS = 10_000
NAMESPACE = "{http://www.sitemaps.org/schemas/sitemap/0.9}"


async def _fetch_sitemap(url: str) -> str:
    """Fetch raw sitemap XML from a URL."""
    headers = {"User-Agent": DEFAULT_USER_AGENT}
    async with httpx.AsyncClient(timeout=30.0, follow_redirects=True, headers=headers) as client:
        try:
            response = await client.get(url)
            response.raise_for_status()
        except httpx.HTTPStatusError as exc:
            logger.error(
                "sitemap_http_error",
                url=url,
                status_code=exc.response.status_code,
            )
            raise AppException(
                f"HTTP error {exc.response.status_code} while fetching sitemap {url}",
                status_code=exc.response.status_code,
            ) from exc
        except httpx.RequestError as exc:
            logger.error("sitemap_request_error", url=url, error=str(exc))
            raise AppException(f"Failed to fetch sitemap {url}") from exc

    return response.text


def _extract_urls(xml_text: str) -> tuple[list[str], list[str]]:
    """Extract page URLs and nested sitemap URLs from sitemap XML.

    Returns:
        A tuple of (page_urls, nested_sitemap_urls).
    """
    try:
        root = ET.fromstring(xml_text)
    except ET.ParseError as exc:
        raise AppException("Invalid sitemap XML") from exc

    tag = root.tag
    is_index = tag == f"{NAMESPACE}sitemapindex" or tag.endswith("sitemapindex")

    page_urls: list[str] = []
    nested_urls: list[str] = []

    child_tag = "sitemap" if is_index else "url"
    for child in root.findall(f"{NAMESPACE}{child_tag}"):
        loc = child.find(f"{NAMESPACE}loc")
        if loc is None or not loc.text:
            continue
        url = loc.text.strip()
        if is_index:
            nested_urls.append(url)
        else:
            page_urls.append(url)

    return page_urls, nested_urls


async def parse_sitemap(url: str) -> list[str]:
    """Parse a sitemap (or sitemap index) and return a list of page URLs.

    Args:
        url: The sitemap URL to parse.

    Returns:
        A deduplicated list of page URLs up to ``MAX_URLS``.

    Raises:
        AppException: If the sitemap cannot be fetched or parsed.
    """
    logger.info("parse_sitemap_request", url=url)

    urls: list[str] = []
    sitemaps_to_process: list[tuple[str, int]] = [(url, 0)]
    seen_sitemaps: set[str] = set()

    while sitemaps_to_process and len(urls) < MAX_URLS:
        current_url, depth = sitemaps_to_process.pop(0)
        if current_url in seen_sitemaps or depth > MAX_SITEMAP_DEPTH:
            continue
        seen_sitemaps.add(current_url)

        xml_text = await _fetch_sitemap(current_url)
        page_urls, nested_urls = _extract_urls(xml_text)

        for page_url in page_urls:
            if len(urls) >= MAX_URLS:
                break
            urls.append(page_url)

        if depth < MAX_SITEMAP_DEPTH:
            for nested in nested_urls:
                resolved = urljoin(current_url, nested)
                sitemaps_to_process.append((resolved, depth + 1))

    unique_urls = list(dict.fromkeys(urls))
    logger.info(
        "parse_sitemap_complete",
        url=url,
        urls_found=len(unique_urls),
    )
    return unique_urls
