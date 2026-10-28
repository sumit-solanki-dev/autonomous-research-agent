from typing import List, Dict, Any
import concurrent.futures
from pydantic import BaseModel
from langchain_core.messages import HumanMessage
from langgraph.constants import Send
from app.state import AgentState, ResearchTask, Source
from app.utils.llm import get_llm, invoke_with_retry
from app.prompts.researcher import RESEARCHER_PROMPT
from app.tools.web_search import perform_search
from app.utils.logging import setup_logger

logger = setup_logger(__name__)

class QueriesList(BaseModel):
    queries: List[str]

def generate_research_tasks(state: AgentState):
    """
    Map research tasks into parallel node executions.
    """
    tasks = state.get("research_tasks", [])
    logger.info(f"Generating parallel research executions for {len(tasks)} tasks.")
    
    # We will use Send to route to the 'research_task' node
    return [Send("execute_research_task", task) for task in tasks]

def execute_research_task(task: ResearchTask) -> dict:
    """
    Execute a single research task.
    1. Generate queries
    2. Search Tavily
    3. Return sources
    """
    logger.info(f"Research task started for topic: {task.topic}")
    llm = get_llm(temperature=0.0)
    structured_llm = llm.with_structured_output(QueriesList)
    
    questions_text = "\n".join([f"- {q}" for q in task.questions])
    prompt_text = RESEARCHER_PROMPT.format(topic=task.topic, questions=questions_text)
    
    queries = []
    try:
        result: QueriesList = invoke_with_retry(structured_llm, prompt_text)
        queries = result.queries
    except Exception as e:
        logger.error(f"Error generating queries for topic '{task.topic}': {e}")
        # fallback query
        queries = [task.topic]
        
    all_sources = []
    
    # Execute search queries in parallel
    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        future_to_query = {executor.submit(perform_search, q): q for q in queries}
        for future in concurrent.futures.as_completed(future_to_query):
            query = future_to_query[future]
            try:
                results = future.result()
                logger.info(f"Search results received for query: {query} (count: {len(results)})")
                for res in results:
                    all_sources.append(Source(**res))
            except Exception as e:
                logger.error(f"Error executing search for query '{query}': {e}")
            
    return {
        "search_queries": queries,
        "sources": all_sources
    }
