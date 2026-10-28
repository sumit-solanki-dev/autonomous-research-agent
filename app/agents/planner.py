from app.state import AgentState, ResearchPlan
from app.utils.llm import get_llm, invoke_with_retry
from app.prompts.planner import PLANNER_PROMPT
from app.utils.logging import setup_logger

logger = setup_logger(__name__)

def plan_research(state: AgentState) -> dict:
    logger.info("Planner started")
    llm = get_llm(temperature=0.0)
    structured_llm = llm.with_structured_output(ResearchPlan)
    
    prompt_text = PLANNER_PROMPT.format(research_question=state.get("research_question"))
    
    try:
        plan = invoke_with_retry(structured_llm, prompt_text)
        logger.info("Planner completed")
        return {
            "research_plan": plan,
            "research_tasks": plan.research_tasks
        }
    except Exception as e:
        logger.error(f"Error in planner: {e}")
        return {
            "errors": [f"Planner failed: {str(e)}"],
            "execution_status": "failed_at_planner"
        }
