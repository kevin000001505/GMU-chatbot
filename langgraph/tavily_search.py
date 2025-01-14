import os
import asyncio
from dotenv import load_dotenv

load_dotenv()
from tavily import AsyncTavilyClient, TavilyClient
from langchain_openai import ChatOpenAI

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
TAVILY_API_KEY = os.getenv("TAVILY_API_KEY")

llm = ChatOpenAI(model="gpt-4o-mini")

tavily_client = AsyncTavilyClient(api_key=TAVILY_API_KEY)
simple_client = TavilyClient(api_key=TAVILY_API_KEY)

def simple_search(query):
    return simple_client.get_search_context(f"George Mason University - {query}", max_tokens=8000)

# Define a function to perform a single query
async def single_query(query):
    response = await tavily_client.get_search_context(f"George Mason University - {query}", max_tokens=8000)
    return response

# Define a function to run multiple queries concurrently
async def run_multiple_queries(queries):
    tasks = [single_query(query) for query in queries]  # Create a list of tasks
    results = await asyncio.gather(*tasks)  # Run tasks concurrently and gather results
    return results


# Run the queries concurrently using await
async def run_search(queries: list):
    results = await run_multiple_queries(queries)
    return results

def search(queries: list):
    return asyncio.run(run_search(queries))

if __name__ == "__main__":
    # Define your list of queries
    queries = [
        "How much tuition is it for George Mason University?",
        "What are the admission requirements for GMU?",
        "What is the student population at GMU?"
    ]
    results = search(queries)
