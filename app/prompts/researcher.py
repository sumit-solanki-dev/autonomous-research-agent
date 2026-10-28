RESEARCHER_PROMPT = """You are an expert AI Research Assistant.
Your task is to generate highly targeted web search queries based on a specific research topic and a set of questions.

TOPIC:
{topic}

QUESTIONS TO ANSWER:
{questions}

INSTRUCTIONS:
Generate 2-3 targeted search queries that will help find the most relevant information to answer these questions.
Keep the queries concise and optimized for a search engine. 
Do not use quotes unless strictly necessary.

Output strictly a JSON object with a single key "queries" containing a list of strings.
Example: {{"queries": ["query 1", "query 2"]}}
"""
