import pytest
from app.tools.web_search import perform_search

def test_perform_search_success(mocker):
    mocker.patch("os.environ.get", return_value="fake_api_key")
    mock_client = mocker.patch("app.tools.web_search.TavilyClient")
    mock_client.return_value.search.return_value = {
        "results": [
            {
                "title": "Test Title",
                "url": "https://example.com",
                "content": "Test content",
                "published_date": "2024-01-01"
            }
        ]
    }
    
    results = perform_search("test query")
    assert len(results) == 1
    assert results[0]["title"] == "Test Title"
    assert results[0]["domain"] == "example.com"

def test_perform_search_no_api_key(mocker):
    mocker.patch("os.environ.get", return_value=None)
    results = perform_search("test query")
    assert results == []

def test_perform_search_exception(mocker):
    mocker.patch("os.environ.get", return_value="fake_api_key")
    mock_client = mocker.patch("app.tools.web_search.TavilyClient")
    mock_client.return_value.search.side_effect = Exception("Timeout")
    
    results = perform_search("test query")
    assert results == []
