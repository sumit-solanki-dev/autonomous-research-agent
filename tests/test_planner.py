import pytest
from app.agents.planner import plan_research
from app.state import ResearchPlan, ResearchTask

def test_plan_research_success(mocker):
    mock_llm = mocker.patch("app.agents.planner.get_llm")
    mock_structured = mock_llm.return_value.with_structured_output.return_value
    mock_structured.invoke.return_value = ResearchPlan(
        objective="Test Objective",
        research_tasks=[
            ResearchTask(topic="Test Topic", questions=["Q1?"], priority="high")
        ]
    )
    
    state = {"research_question": "Test question"}
    result = plan_research(state)
    
    assert "research_plan" in result
    assert "research_tasks" in result
    assert len(result["research_tasks"]) == 1
    assert result["research_tasks"][0].topic == "Test Topic"

def test_plan_research_exception(mocker):
    mock_llm = mocker.patch("app.agents.planner.get_llm")
    mock_structured = mock_llm.return_value.with_structured_output.return_value
    mock_structured.invoke.side_effect = Exception("API Error")
    
    state = {"research_question": "Test question"}
    result = plan_research(state)
    
    assert "errors" in result
    assert result["execution_status"] == "failed_at_planner"
