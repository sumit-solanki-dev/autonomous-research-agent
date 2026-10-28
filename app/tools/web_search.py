import os
import json
import sqlite3
from typing import List, Dict, Any
from tavily import TavilyClient
from urllib.parse import urlparse
from app.utils.logging import setup_logger

logger = setup_logger(__name__)

# Initialize SQLite Cache for web searches
CACHE_DB = ".search_cache.db"
def init_cache():
    with sqlite3.connect(CACHE_DB) as conn:
        conn.execute('''CREATE TABLE IF NOT EXISTS search_cache
                        (query TEXT PRIMARY KEY, result TEXT)''')
init_cache()

def perform_search(query: str, max_results: int = 5) -> List[Dict[str, Any]]:
    """
    Search using Tavily API. Falls back to DuckDuckGo if Tavily fails.
    Uses SQLite to cache results and prevent duplicate API calls.
    """
    # 1. Check local cache first
    with sqlite3.connect(CACHE_DB) as conn:
        cursor = conn.cursor()
        cursor.execute("SELECT result FROM search_cache WHERE query=?", (query,))
        row = cursor.fetchone()
        if row:
            logger.info(f"Cache hit for query: {query}")
            return json.loads(row[0])

    api_key = os.environ.get("TAVILY_API_KEY")
    results = []
    
    # 2. Attempt Tavily Search
    try:
        if not api_key:
            raise ValueError("TAVILY_API_KEY is not set.")
        client = TavilyClient(api_key=api_key)
        response = client.search(
            query=query,
            search_depth="advanced",
            max_results=max_results,
            include_answer=False,
            include_raw_content=False
        )
        
        for result in response.get("results", []):
            url = result.get("url", "")
            domain = urlparse(url).netloc
            results.append({
                "title": result.get("title", "No Title"),
                "url": url,
                "content": result.get("content", ""),
                "domain": domain,
                "query_used": query,
                "published_date": result.get("published_date")
            })
    except Exception as e:
        logger.warning(f"Tavily search failed for '{query}': {e}. Falling back to DuckDuckGo...")
        # 3. Fallback to DuckDuckGo (100% Free)
        try:
            from langchain_community.utilities import DuckDuckGoSearchAPIWrapper
            wrapper = DuckDuckGoSearchAPIWrapper(max_results=max_results)
            ddg_results = wrapper.results(query, max_results)
            
            for res in ddg_results:
                url = res.get("link", "")
                domain = urlparse(url).netloc
                results.append({
                    "title": res.get("title", "No Title"),
                    "url": url,
                    "content": res.get("snippet", ""),
                    "domain": domain,
                    "query_used": query,
                    "published_date": None
                })
        except Exception as ddg_e:
            logger.error(f"Error during DuckDuckGo fallback search: {ddg_e}")

    # 4. Save successful results to cache
    if results:
        with sqlite3.connect(CACHE_DB) as conn:
            conn.execute("INSERT OR REPLACE INTO search_cache (query, result) VALUES (?, ?)", 
                         (query, json.dumps(results)))
                         
    return results
