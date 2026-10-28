import time
import asyncio
from app.graph import create_research_graph
import os
from dotenv import load_dotenv

def run_benchmark():
    load_dotenv(override=True)
    graph = create_research_graph()
    
    query = "What is LinkedIn?"
    print(f"Starting benchmark for query: '{query}'")
    
    start_time = time.time()
    
    # Run the graph
    inputs = {"research_question": query}
    for event in graph.stream(inputs, {"recursion_limit": 50}):
        for node_name, state in event.items():
            print(f"[{time.time() - start_time:.2f}s] Finished node: {node_name}")
            
    end_time = time.time()
    total_time = end_time - start_time
    print(f"\n--- BENCHMARK COMPLETE ---")
    print(f"Total Execution Time: {total_time:.2f} seconds")

if __name__ == "__main__":
    run_benchmark()
