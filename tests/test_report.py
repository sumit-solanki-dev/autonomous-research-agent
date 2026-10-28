import pytest
import os
from app.agents.report_writer import write_report
from app.state import ResearchPlan, TaskSummary, Finding, Conflict, Source

def test_write_report_success(mocker, tmp_path):
    mock_llm = mocker.patch("app.agents.report_writer.get_llm")
    
    class MockResponse:
        content = "# Test Report\n\nThis is a test report."
        
    mock_llm.return_value.invoke.return_value = MockResponse()
    
    # Mock PDF generation to not actually write PDF or if it does, it's fine.
    # We can just let it write to the reports folder or mock it.
    mocker.patch("app.agents.report_writer.generate_pdf_from_md", return_value=True)
    mocker.patch("builtins.open", mocker.mock_open())
    
    state = {
        "research_question": "Test",
        "research_plan": ResearchPlan(objective="Test Obj", research_tasks=[]),
        "summaries": [
            TaskSummary(topic="T1", key_findings=[Finding(claim="C1", source_urls=["http://example.com"], confidence="high")])
        ],
        "conflicts": [],
        "sources": [Source(title="S1", url="http://example.com", content="C", domain="example.com", query_used="Q")]
    }
    
    result = write_report(state)
    
    assert "final_report" in result
    assert result["execution_status"] == "completed"
    assert "markdown_report" in result
    assert "pdf_path" in result
