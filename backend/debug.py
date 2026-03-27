import asyncio
import httpx
import sys
sys.path.insert(0, '.')
from app.core.config import settings

async def debug():
    queries = [
    'quantum computing',
    'open source', 
    'cybersecurity',
    'artificial intelligence',
    'machine learning',
]
    async with httpx.AsyncClient(timeout=15.0) as client:
        for q in queries:
            r = await client.get('https://newsapi.org/v2/everything', params={
                'q': q,
                'searchIn': 'title',
                'language': 'en',
                'sortBy': 'publishedAt',
                'pageSize': 5,
                'apiKey': settings.NEWSAPI_KEY
            })
            data = r.json()
            print(f"Query: {q}")
            print(f"  status: {data.get('status')}")
            print(f"  totalResults: {data.get('totalResults')}")
            print(f"  articles: {len(data.get('articles', []))}")
            print(f"  message: {data.get('message', 'none')}")
            # Print first article title if any
            articles = data.get('articles', [])
            if articles:
                print(f"  first title: {articles[0].get('title')}")
            print()

asyncio.run(debug())