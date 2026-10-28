import argparse
from dotenv import load_dotenv
from app.graph import create_research_graph
import os

def main():
    load_dotenv(override=True)
    
    if not os.environ.get("GEMINI_API_KEY") or not os.environ.get("TAVILY_API_KEY"):
        print("ERROR: Missing API Keys. Please configure GEMINI_API_KEY and TAVILY_API_KEY in the .env file.")
        return
        
    parser = argparse.ArgumentParser(description="Autonomous Research AI")
    parser.add_argument("query", type=str, help="Research question")
    args = parser.parse_args()
    
    graph = create_research_graph()
    
    initial_state = {
        "research_question": args.query,
        "research_tasks": [],
        "search_queries": [],
        "sources": [],
        "summaries": [],
        "fact_checks": [],
        "conflicts": [],
        "errors": []
    }
    
    print(f"Starting research for: {args.query}")
    events = graph.stream(initial_state)
    for event in events:
        for node_name, state in event.items():
            print(f"[{node_name}] Completed.")
            if node_name == "report_writer":
                print(f"\nFinal Report saved to: {state.get('markdown_report')}")
                print(f"PDF Report saved to: {state.get('pdf_path')}")
                
if __name__ == "__main__":
    main()
