"""
app/ingestion/news_fetcher.py

Three functions:
  1. fetch_news_by_interests()  — personalized daily news feed with images (home page banner)
  2. search_news()              — search bar, free-text search across all news
  3. fetch_news_for_project()   — relevant news for a project detail page

HOW THE PERSONALIZED FEED WORKS:
  - Called daily with user.interests pulled from DB
  - Groq generates one focused 3-4 word query per interest
  - Each query fires separately at NewsAPI /top-headlines
  - Results merged, deduplicated, filtered for images, sorted newest first
  - Each interest gets equal representation in the feed
  - Fresh results every day as top headlines refresh

WHY /top-headlines NOT /everything:
  - Top headlines are already curated, high quality, image-rich
  - Short focused queries work reliably on it
  - No noise from obscure or irrelevant global articles

Person A (Satvick) — Phase 9
"""

import httpx
import json
from datetime import datetime
import logging

from app.core.config import settings

logger = logging.getLogger(__name__)

NEWSAPI_BASE = "https://newsapi.org/v2"
GROQ_API_URL = "https://api.groq.com/openai/v1/chat/completions"
GROQ_MODEL   = "llama-3.3-70b-versatile"


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _format_article(article: dict) -> dict | None:
    """
    Convert a raw NewsAPI article into a clean standard dict.
    Returns None if article is missing title or marked as removed.
    """
    title = article.get("title", "") or ""
    if not title or title == "[Removed]":
        return None

    description = article.get("description") or ""
    if description == "[Removed]":
        description = ""

    source = article.get("source", {})
    publisher = source.get("name", "") or ""

    # Filter out non-news sources — package repos, ebook sites, changelogs etc.
    blacklisted = {
        "pypi.org", "wowebook.org", "github.com", "npmjs.com",
        "rubygems.org", "packagist.org", "crates.io", "hub.docker.com",
    }
    if publisher.lower() in blacklisted:
        return None

    return {
        "source"      : "news",
        "type"        : "article",
        "title"       : title.strip(),
        "url"         : article.get("url", ""),
        "image_url"   : article.get("urlToImage"),
        "description" : description.strip(),
        "author"      : article.get("author") or publisher,
        "publisher"   : publisher,
        "published_at": article.get("publishedAt", ""),
        "fetched_at"  : datetime.utcnow().isoformat(),
    }


async def _interest_to_query(interest: str, skill_level: str = "intermediate") -> str:
    """
    Use Groq to convert a single user interest into one focused 3-4 word
    NewsAPI search query. Adjusted by skill_level so query depth matches
    the user's level.

    skill_level:
      beginner     → explainer/intro angle  e.g. "AI explained beginners"
      intermediate → product/trend angle    e.g. "AI technology startups"
      advanced     → research/deep angle    e.g. "AI research breakthroughs"

    Falls back to the raw interest string if Groq fails.
    """
    skill_guidance = {
        "beginner"    : "introductory, explainer-style, beginner-friendly articles",
        "intermediate": "product launches, industry trends, practical applications",
        "advanced"    : "research breakthroughs, technical deep dives, cutting-edge developments",
    }
    guidance = skill_guidance.get(skill_level.lower(), skill_guidance["intermediate"])

    prompt = f"""You are a news search keyword generator.

Convert this user interest into ONE search keyword or short phrase (1-2 words max)
that will find relevant news articles when searched in article titles.

Interest: "{interest}"
User level: {skill_level} — target {guidance}

RULES:
- Return 1-2 words ONLY — no more
- Must be a real recognizable tech term that appears in news headlines
- No generic words like "trends", "basics", "explained", "overview"
- Return ONLY the keyword, nothing else, no quotes, no punctuation

Examples:
  "AI" + beginner      → artificial intelligence
  "AI" + intermediate  → AI startups
  "AI" + advanced      → AI research
  "mental health"      → mental health
  "blockchain"         → blockchain
  "open source"        → open source
  "cybersecurity"      → cybersecurity
  "quantum computing"  → quantum computing
  "NLP"                → natural language"""

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                GROQ_API_URL,
                headers={
                    "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model"      : GROQ_MODEL,
                    "max_tokens" : 20,
                    "temperature": 0.2,
                    "messages"   : [{"role": "user", "content": prompt}],
                },
            )
            resp.raise_for_status()
            query = resp.json()["choices"][0]["message"]["content"].strip()
            query = query.strip('"').strip("'").strip()
            # Fix camelCase or run-together words Groq sometimes returns
            # e.g. "OpenSource" → "open source", "CyberSecurity" → "cyber security"
            import re
            query = re.sub(r'([a-z])([A-Z])', r'\1 \2', query).lower().strip()
            logger.info(f"Groq query for '{interest}' ({skill_level}): '{query}'")
            return query

    except Exception as e:
        logger.warning(f"Groq query generation failed for '{interest}': {e}")
        return interest  # fallback to raw interest


async def _project_to_query(project_description: str) -> str:
    """
    Use Groq to convert a project description into one focused news search query.
    Purpose/domain focused — not raw tech stack.
    Falls back to first 4 words of description if Groq fails.
    """
    prompt = f"""You are a news search keyword generator.

Convert this project description into ONE 1-2 word search keyword
that finds relevant NEWS articles when searched in article titles.

Project: "{project_description}"

RULES:
- Return 1-2 words ONLY
- Focus on the project's DOMAIN or WHO IT HELPS — never the tech stack
- Never return raw library/framework names like "NLP", "ML", "PyTorch", "BERT", "LLM"
- Must be a term that appears in mainstream tech news headlines
- Return ONLY the keyword, nothing else, no quotes

Examples:
  "mental health chatbot using NLP"  → mental health
  "stock price predictor using ML"   → stock market
  "code review assistant using LLMs" → code review
  "drone delivery system"            → drone delivery
  "NLP text summarizer tool"         → text summarization"""

    try:
        async with httpx.AsyncClient(timeout=15.0) as client:
            resp = await client.post(
                GROQ_API_URL,
                headers={
                    "Authorization": f"Bearer {settings.GROQ_API_KEY}",
                    "Content-Type": "application/json",
                },
                json={
                    "model"      : GROQ_MODEL,
                    "max_tokens" : 20,
                    "temperature": 0.2,
                    "messages"   : [{"role": "user", "content": prompt}],
                },
            )
            resp.raise_for_status()
            query = resp.json()["choices"][0]["message"]["content"].strip()
            query = query.strip('"').strip("'").strip()
            logger.info(f"Groq project query: '{query}'")
            return query

    except Exception as e:
        logger.warning(f"Groq project query failed: {e}")
        return " ".join(project_description.split()[:4])


# ---------------------------------------------------------------------------
# Function 1 — Personalized daily news feed (home page banner)
# ---------------------------------------------------------------------------

async def fetch_news_by_interests(
    interests: list[str],
    skill_level: str = "intermediate",
    articles_per_interest: int = 34,  # ~100 total for 3 interests, good for scrolling
) -> list[dict]:
    """
    Fetch personalized tech news articles with images for the home page banner.
    Called daily with user.interests and user.skill_level from the DB.

    For each interest:
      1. Groq generates one focused query tuned to the user's skill_level
      2. Query fires at NewsAPI /top-headlines
      3. Only articles with images are kept
    All results merged, deduplicated, sorted newest first.

    Args:
        interests:             User interest list from DB e.g. ["AI", "NLP", "mental health"]
        skill_level:           User skill level from DB: "beginner" | "intermediate" | "advanced"
        articles_per_interest: How many articles to fetch per interest (default 5)

    Returns:
        List of article dicts with image_url guaranteed, sorted by published_at descending.
        Each interest contributes equally to the feed.
    """
    seen_urls: set[str] = set()
    all_articles: list[dict] = []

    async with httpx.AsyncClient(timeout=15.0) as client:
        for interest in interests:
            try:
                # Groq generates a focused query per interest + skill level
                query = await _interest_to_query(interest, skill_level)

                params = {
                    "q"        : query,
                    "searchIn" : "title",
                    "language" : "en",
                    "sortBy"   : "publishedAt",
                    "pageSize" : 100,              # NewsAPI free tier max per request
                    "apiKey"   : settings.NEWSAPI_KEY,
                }

                resp = await client.get(f"{NEWSAPI_BASE}/everything", params=params)
                resp.raise_for_status()
                raw_articles = resp.json().get("articles", [])

                count = 0
                for raw in raw_articles:
                    article = _format_article(raw)
                    if not article:
                        continue
                    if not article["image_url"]:
                        continue
                    if article["url"] in seen_urls:
                        continue
                    seen_urls.add(article["url"])
                    all_articles.append(article)
                    count += 1

                logger.info(f"Fetched {count} articles for interest '{interest}' (query: '{query}')")

            except Exception as e:
                logger.warning(f"News fetch failed for interest '{interest}': {e}")
                continue

    # Sort by published date — most recent first
    all_articles.sort(key=lambda a: a["published_at"], reverse=True)
    logger.info(f"Total: {len(all_articles)} personalized news articles for {interests}")
    return all_articles


# ---------------------------------------------------------------------------
# Function 2 — Search bar
# ---------------------------------------------------------------------------

async def search_news(
    query: str,
    limit: int = 20,
    with_images_only: bool = False,
) -> list[dict]:
    """
    Search news articles by a user-typed query. Powers the search bar.
    Uses /everything endpoint for broad search coverage.
    Sorted by relevance — most matching articles first.

    Args:
        query:            Search string from the user e.g. "GPT-4 fine tuning"
        limit:            Number of results to return
        with_images_only: If True, only return articles with an image

    Returns:
        List of article dicts sorted by relevance.
    """
    logger.info(f"Searching news for: '{query}'")

    params = {
        "q"        : query,
        "language" : "en",
        "sortBy"   : "relevancy",
        "pageSize" : limit,
        "apiKey"   : settings.NEWSAPI_KEY,
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(f"{NEWSAPI_BASE}/everything", params=params)
        resp.raise_for_status()
        raw_articles = resp.json().get("articles", [])

    articles = []
    for raw in raw_articles:
        article = _format_article(raw)
        if not article:
            continue
        if with_images_only and not article["image_url"]:
            continue
        articles.append(article)

    logger.info(f"News search returned {len(articles)} results for '{query}'")
    return articles


# ---------------------------------------------------------------------------
# Function 3 — Project detail page
# ---------------------------------------------------------------------------

async def fetch_news_for_project(
    project_description: str,
    limit: int = 5,
) -> list[dict]:
    """
    Find news articles relevant to a specific project.
    Called when a user opens a project detail page.
    Mirrors fetch_repos_for_project() and fetch_stories_for_project().

    Groq converts the project description into one domain-focused query,
    fires it at /top-headlines, returns most relevant results.

    Args:
        project_description: Free-text project description
        limit:               Number of articles to return (default 5)

    Returns:
        List of article dicts sorted by published_at descending.
    """
    query = await _project_to_query(project_description)
    logger.info(f"Fetching project news with query: '{query}'")

    params = {
        "q"        : query,
        "searchIn" : "title",
        "language" : "en",
        "sortBy"   : "relevancy",
        "pageSize" : limit * 2,
        "apiKey"   : settings.NEWSAPI_KEY,
    }

    async with httpx.AsyncClient(timeout=15.0) as client:
        resp = await client.get(f"{NEWSAPI_BASE}/everything", params=params)
        resp.raise_for_status()
        raw_articles = resp.json().get("articles", [])

    articles = []
    for raw in raw_articles:
        article = _format_article(raw)
        if article:
            articles.append(article)
        if len(articles) >= limit:
            break

    articles.sort(key=lambda a: a["published_at"], reverse=True)
    logger.info(f"Found {len(articles)} news articles for project")
    return articles