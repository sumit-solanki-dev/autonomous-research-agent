import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_community.cache import SQLiteCache
import langchain
from app.utils.logging import setup_logger

logger = setup_logger(__name__)

# Initialize global LLM cache to save time and API quota
langchain.llm_cache = SQLiteCache(database_path=".langchain.db")

def get_llm(temperature: float = 0.0) -> ChatGoogleGenerativeAI:
    api_key = os.environ.get("GEMINI_API_KEY")
    if not api_key:
        logger.error("GEMINI_API_KEY is not set.")
        raise ValueError("GEMINI_API_KEY is missing.")
    
    # Use gemini-3.5-flash-lite for speed, large context window, and generous free tier limits
    return ChatGoogleGenerativeAI(model="gemini-3.5-flash-lite", temperature=temperature, google_api_key=api_key, max_retries=10)

import time

def invoke_with_retry(llm_or_chain, prompt, max_retries=6):
    """Wraps invoke calls to gracefully handle 429 Rate Limits from Gemini free tier."""
    for attempt in range(max_retries):
        try:
            return llm_or_chain.invoke(prompt)
        except Exception as e:
            error_msg = str(e)
            if '429' in error_msg or 'RESOURCE_EXHAUSTED' in error_msg or 'quota' in error_msg.lower():
                sleep_time = 25  # Sleep for 25s since Gemini API asks to retry in ~22s
                logger.warning(f"Rate limit hit (429). Attempt {attempt+1}/{max_retries}. Sleeping for {sleep_time}s...")
                time.sleep(sleep_time)
            else:
                raise
    # Final attempt
    return llm_or_chain.invoke(prompt)
