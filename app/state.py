import operator
from typing import Annotated, TypedDict, Any, List, Dict, Optional
from pydantic import BaseModel, Field

class ResearchTask(BaseModel):
    topic: str
    questions: List[str]
    priority: str

class ResearchPlan(BaseModel):
    objective: str
    research_tasks: List[ResearchTask]

class Source(BaseModel):
    title: str
    url: str
    content: str
    domain: str
    published_date: Optional[str] = None
    query_used: str

class Finding(BaseModel):
    claim: str
    source_urls: List[str]
    confidence: str

class TaskSummary(BaseModel):
    topic: str
    key_findings: List[Finding]

class FactCheckResult(BaseModel):
    claim: str
    status: str # SUPPORTED, PARTIALLY_SUPPORTED, CONTRADICTED, INSUFFICIENT_EVIDENCE
    explanation: str
    source_urls: List[str]

class Conflict(BaseModel):
    topic: str
    description: str
    source_urls: List[str]

def merge_lists(a: list, b: list) -> list:
    return a + b

class AgentState(TypedDict):
    research_question: str
    research_plan: Optional[ResearchPlan]
    research_tasks: List[ResearchTask]
    
    # State accumulated across parallel tasks
    search_queries: Annotated[List[str], merge_lists]
    sources: Annotated[List[Source], merge_lists]
    summaries: Annotated[List[TaskSummary], merge_lists]
    fact_checks: Annotated[List[FactCheckResult], merge_lists]
    conflicts: Annotated[List[Conflict], merge_lists]
    
    final_report: str
    markdown_report: str
    pdf_path: str
    
    errors: Annotated[List[str], merge_lists]
    execution_status: str
