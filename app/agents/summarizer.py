from typing import List, Dict, Any
from pydantic import BaseModel
from app.state import AgentState, TaskSummary, Finding, Source
from app.utils.llm import get_llm, invoke_with_retry
from app.prompts.summarizer import SUMMARIZER_PROMPT
from app.utils.logging import setup_logger

logger = setup_logger(__name__)

class BatchSummarizerOutput(BaseModel):
    summaries: List[TaskSummary]

def summarize_research(state: AgentState) -> dict:
    logger.info("Summarization started")
    llm = get_llm(temperature=0.0)
    structured_llm = llm.with_structured_output(BatchSummarizerOutput)
    
    tasks = state.get("research_tasks", [])
    all_sources: List[Source] = state.get("sources", [])
    
    # Format sources for prompt
    sources_text = ""
    for i, s in enumerate(all_sources):
        sources_text += f"[{i+1}] Title: {s.title}\nURL: {s.url}\nContent: {s.content}\n\n"
        
    tasks_text = ""
    for task in tasks:
        questions_text = "\n".join([f"  - {q}" for q in task.questions])
        tasks_text += f"Topic: {task.topic}\nQuestions:\n{questions_text}\n\n"
        
    prompt_text = SUMMARIZER_PROMPT.format(
        tasks=tasks_text,
        sources=sources_text
    )
    
    summaries = []
    try:
        # Perform 1 single batch LLM call to save API rate limits!
        result = invoke_with_retry(structured_llm, prompt_text)
        summaries = result.summaries
        logger.info("Summarized all tasks in a single batch.")
    except Exception as e:
        logger.error(f"Error during batch summarization: {e}")
            
    return {
        "summaries": summaries
    }
