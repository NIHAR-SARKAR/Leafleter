"""Slug generation utilities."""

import re
import unicodedata


def _simple_slugify(text: str) -> str:
    """Normalize text to a URL-safe slug without external dependencies."""
    text = unicodedata.normalize("NFKD", text)
    text = text.encode("ascii", "ignore").decode("ascii")
    text = re.sub(r"[^\w\s-]", "", text).strip().lower()
    return re.sub(r"[-\s]+", "-", text)


def generate_slug(text: str) -> str:
    """Generate a URL-safe slug from arbitrary text."""
    base = _simple_slugify(text)[:100]
    base = re.sub(r"[^a-z0-9-]", "", base).strip("-")
    return base or "org"
