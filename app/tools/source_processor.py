from typing import List
from app.state import Source

def deduplicate_sources(sources: List[Source]) -> List[Source]:
    """
    Remove duplicate sources by URL.
    """
    unique_sources = []
    seen_urls = set()
    
    for source in sources:
        if source.url not in seen_urls:
            unique_sources.append(source)
            seen_urls.add(source.url)
            
    return unique_sources
