from typing import List
import concurrent.futures
from pydantic import BaseModel
from app.state import AgentState, FactCheckResult, Conflict, Source
from app.utils.llm import get_llm, invoke_with_retry
from app.prompts.fact_checker import FACT_CHECKER_PROMPT
from app.utils.logging import setup_logger

logger = setup_logger(__name__)

class FactCheckItem(BaseModel):
    claim: str
    status: str
    explanation: str
    source_urls: List[str]

class FactCheckResponse(BaseModel):
    results: List[FactCheckItem]

def fact_check(state: AgentState) -> dict:
    logger.info("Fact checking started")
    llm = get_llm(temperature=0.0)
    structured_llm = llm.with_structured_output(FactCheckResponse)
    
    all_sources: List[Source] = state.get("sources", [])
    summaries = state.get("summaries", [])
    
    sources_text = ""
    for i, s in enumerate(all_sources):
        sources_text += f"[{i+1}] URL: {s.url}\nContent: {s.content[:1000]}...\n\n"
        
    fact_checks = []
    conflicts = []
    
    # Collect all claims and build a mapping to their topics
    claims_list = []
    claim_to_topic = {}
    
    for summary in summaries:
        for finding in summary.key_findings:
            if finding.confidence != 'low':
                claims_list.append(finding.claim)
                claim_to_topic[finding.claim] = summary.topic
                
    if not claims_list:
        return {"fact_checks": [], "conflicts": []}
        
    claims_text = "\n".join([f"- {claim}" for claim in claims_list])
    
    prompt_text = FACT_CHECKER_PROMPT.format(
        claims=claims_text,
        sources=sources_text
    )
    
    try:
        # Perform 1 single batch LLM call to save API rate limits!
        response = invoke_with_retry(structured_llm, prompt_text)
        
        for item in response.results:
            fact_check_result = FactCheckResult(
                claim=item.claim,
                status=item.status,
                explanation=item.explanation,
                source_urls=item.source_urls
            )
            fact_checks.append(fact_check_result)
            
            if item.status == "CONTRADICTED":
                # Find the topic for this claim
                # Use a partial match in case the LLM slightly rephrased the claim string
                topic = "General"
                for original_claim, t in claim_to_topic.items():
                    if original_claim[:30] in item.claim or item.claim[:30] in original_claim:
                        topic = t
                        break
                        
                conflicts.append(Conflict(
                    topic=topic,
                    description=f"Claim: {item.claim}\nExplanation: {item.explanation}",
                    source_urls=item.source_urls
                ))
    except Exception as e:
        logger.error(f"Error during batch fact checking: {e}")
                
    return {
        "fact_checks": fact_checks,
        "conflicts": conflicts
    }
