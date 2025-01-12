import os
import asyncio
from dotenv import load_dotenv

load_dotenv()
from tavily import AsyncTavilyClient, TavilyClient
from langchain.prompts import PromptTemplate
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
async def run_search(queries):
    results = await run_multiple_queries(queries)
    return results

def search(queries):
    return asyncio.run(run_search(queries))

if __name__ == "__main__":
    # Define your list of queries
    queries = [
        "How much tuition is it for George Mason University?",
        "What are the admission requirements for GMU?",
        "What is the student population at GMU?"
    ]
    results = search(queries)

decompose_prompt = PromptTemplate(
    template = """
    # Question Decomposition Prompt

    You are a research assistant helping break down complex questions into smaller, searchable sub-questions. For each query:

    1. First, identify the core components of the main question
    2. Then, generate specific sub-questions that:
    - Address each component individually
    - Are phrased for effective web searching
    - Range from basic background info to specific details
    - Follow a logical learning progression
    3. Finally, suggest 2-3 key search terms for each sub-question

    Format your response as follows:

    MAIN QUESTION: [Insert the original question]

    CORE COMPONENTS:
    - List the main concepts/elements that need to be researched
    - Identify any implicit assumptions or background knowledge needed

    SUB-QUESTIONS:
    1. [Basic background sub-question]
    Search terms: [term1], [term2], [term3]
    Purpose: [Brief explanation of why this information is needed]

    2. [More specific sub-question]
    Search terms: [term1], [term2], [term3]
    Purpose: [Brief explanation of why this information is needed]

    [Continue with additional sub-questions as needed]

    SYNTHESIS GUIDANCE:
    - Brief notes on how to combine the findings
    - Suggestions for connecting different pieces of information
    - Points to consider for forming a complete answer

    Example:

    MAIN QUESTION: "How did the Industrial Revolution impact urban development in Victorian London?"

    CORE COMPONENTS:
    - Industrial Revolution timeline and key features
    - Victorian London demographics and geography
    - Urban development patterns
    - Social and economic changes

    SUB-QUESTIONS:
    1. When did the Industrial Revolution begin in London, and what were its main technological changes?
    Search terms: "Industrial Revolution London timeline", "Victorian era industrialization", "steam power London factories"
    Purpose: Establishes historical context and primary technological drivers

    2. What was London's population growth pattern between 1800-1900?
    Search terms: "Victorian London population statistics", "London demographic change 19th century", "London urbanization rate"
    Purpose: Quantifies the scale of urban growth

    3. How did factory locations influence London's neighborhood development?
    Search terms: "Victorian London factory districts", "London industrial areas 1800s", "working class neighborhoods Victorian London"
    Purpose: Links industrial growth to specific urban changes

    4. What new types of infrastructure were built to support industrial London?
    Search terms: "Victorian London sewers", "London railway expansion 1800s", "Victorian infrastructure projects"
    Purpose: Identifies specific urban development responses

    SYNTHESIS GUIDANCE:
    - Connect population growth data with infrastructure development timeline
    - Link factory locations to neighborhood socioeconomic patterns
    - Consider how technological changes influenced building styles and city planning
    - Look for cause-and-effect relationships between industrial needs and urban solutions
    """,
    input_variables=["question"],
)

decompose_llm = decompose_prompt | llm