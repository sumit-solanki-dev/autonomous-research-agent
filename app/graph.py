from langgraph.graph import StateGraph, START, END
from app.state import AgentState
from app.agents.planner import plan_research
from app.agents.researcher import generate_research_tasks, execute_research_task
from app.agents.summarizer import summarize_research
from app.agents.fact_checker import fact_check
from app.agents.report_writer import write_report
from app.utils.logging import setup_logger

logger = setup_logger(__name__)

def should_continue_from_planner(state: AgentState):
    if state.get("errors"):
        logger.error("Stopping at planner due to errors.")
        return "end"
    return "generate_research_tasks"

def create_research_graph():
    workflow = StateGraph(AgentState)
    
    # Add nodes
    workflow.add_node("planner", plan_research)
    workflow.add_node("execute_research_task", execute_research_task)
    workflow.add_node("summarizer", summarize_research)
    workflow.add_node("fact_checker", fact_check)
    workflow.add_node("report_writer", write_report)
    
    # Edges
    workflow.add_edge(START, "planner")
    
    # Map-reduce: Conditional edges from planner for parallel tasks
    workflow.add_conditional_edges(
        "planner",
        generate_research_tasks,
        ["execute_research_task"]
    )
    
    # After all parallel tasks finish, move to summarizer
    workflow.add_edge("execute_research_task", "summarizer")
    
    workflow.add_edge("summarizer", "fact_checker")
    workflow.add_edge("fact_checker", "report_writer")
    workflow.add_edge("report_writer", END)
    
    return workflow.compile()
