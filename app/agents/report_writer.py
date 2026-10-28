from datetime import datetime
import os
from app.state import AgentState
from app.utils.llm import get_llm, invoke_with_retry
from app.prompts.report_writer import REPORT_WRITER_PROMPT
from app.tools.pdf_generator import generate_pdf_from_md
from app.utils.logging import setup_logger

logger = setup_logger(__name__)

def write_report(state: AgentState) -> dict:
    logger.info("Report generation started")
    llm = get_llm(temperature=0.2)
    
    plan = state.get("research_plan")
    objective = plan.objective if plan else state.get("research_question")
    
    summaries = state.get("summaries", [])
    summaries_text = ""
    for s in summaries:
        summaries_text += f"Topic: {s.topic}\n"
        for f in s.key_findings:
            summaries_text += f"- {f.claim} (Sources: {', '.join(f.source_urls)})\n"
        summaries_text += "\n"
        
    conflicts = state.get("conflicts", [])
    conflicts_text = ""
    for c in conflicts:
        conflicts_text += f"Topic: {c.topic}\nConflict: {c.description}\nSources: {', '.join(c.source_urls)}\n\n"
        
    all_sources = state.get("sources", [])
    sources_text = ""
    
    unique_urls = []
    unique_sources = []
    for s in all_sources:
        if s.url not in unique_urls:
            unique_urls.append(s.url)
            unique_sources.append(s)
            
    for i, s in enumerate(unique_sources):
        sources_text += f"[{i+1}] {s.title} - {s.url}\n"
        
    prompt_text = REPORT_WRITER_PROMPT.format(
        objective=objective,
        summaries=summaries_text,
        conflicts=conflicts_text if conflicts else "No conflicts detected.",
        sources=sources_text
    )
    
    try:
        response = invoke_with_retry(llm, prompt_text)
        markdown_content = response.content
        
        if isinstance(markdown_content, list):
            text_blocks = []
            for block in markdown_content:
                if isinstance(block, dict) and "text" in block:
                    text_blocks.append(block["text"])
                elif isinstance(block, str):
                    text_blocks.append(block)
            markdown_content = "".join(text_blocks)
            
        if markdown_content.startswith("```markdown"):
            markdown_content = markdown_content[11:]
        elif markdown_content.startswith("```"):
            markdown_content = markdown_content[3:]
        if markdown_content.endswith("```"):
            markdown_content = markdown_content[:-3]
            
        markdown_content = markdown_content.strip()
        
        timestamp = datetime.now().strftime("%Y_%m_%d_%H%M%S")
        reports_dir = "reports"
        os.makedirs(reports_dir, exist_ok=True)
        md_path = os.path.join(reports_dir, f"research_{timestamp}.md")
        pdf_path = os.path.join(reports_dir, f"research_{timestamp}.pdf")
        
        with open(md_path, "w", encoding="utf-8") as f:
            f.write(markdown_content)
            
        generate_pdf_from_md(markdown_content, pdf_path)
        
        logger.info("Report generation completed")
        return {
            "final_report": markdown_content,
            "markdown_report": md_path,
            "pdf_path": pdf_path,
            "execution_status": "completed"
        }
    except Exception as e:
        logger.error(f"Error generating report: {e}")
        return {
            "errors": [f"Report writer failed: {str(e)}"],
            "execution_status": "failed_at_report"
        }
