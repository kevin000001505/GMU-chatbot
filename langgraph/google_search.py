import os
import asyncio
import time


from dotenv import load_dotenv
from googlesearch import search
from crawl4ai import AsyncWebCrawler, CacheMode
from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize LLM only once at the top
llm = ChatOpenAI(model="gpt-4o-mini")

decompose_prompt = PromptTemplate(
    template = """
    You will be provided with a query, and your task is to generate a list of top 3 keywords that might provide the most information that can answer the query. Please list the keywords separated by newline characters without numbering or bullet points.
    Qurey: {Query}
    """,
    input_variables=["Query"]
)
decompose_llm = decompose_prompt | llm

async def multiple_crawl(links):
    """Crawl multiple URLs and return a list of crawl4ai results."""
    async with AsyncWebCrawler(verbose=True) as crawler:
        word_count_threshold = 100
        results = await crawler.arun_many(
            urls=links,
            word_count_threshold=word_count_threshold,
            exclude_external_links=True,
            exclude_social_media_links=True,
            remove_overlay_elements=True,
            cache_mode=CacheMode.READ_ONLY,
            fit_markdown=True,
            verbose=True
        )
        return results

async def async_search(query):
    """Asynchronously execute the synchronous search function."""
    loop = asyncio.get_event_loop()
    return await loop.run_in_executor(None, list, search(f"Geroge Mason University - {query}", num=1, stop=1, pause=2))

async def handle_queries(queries):
    """Handle multiple search queries concurrently."""
    all_urls = set()
    tasks = [async_search(query) for query in queries]
    results = await asyncio.gather(*tasks)
    for sublist in results:
        for url in sublist:
            all_urls.add(url)
    return list(all_urls)

def search_all(query):
    """Search for the given queries and return the crawl4ai results."""
    response = decompose_llm.invoke({"Query": query})
    queries = response.content.split("\n")
    all_urls = asyncio.run(handle_queries(queries))
    crawl_results = asyncio.run(multiple_crawl(all_urls))
    documents = "\n\n".join(item.markdown for item in crawl_results)
    return documents

if __name__ == '__main__':
    start_time = time.perf_counter()
    query = "What should I prepare as a freshman?"
    response = decompose_llm.invoke({"Query": query})
    queries = response.content.split("\n")
    all_urls = asyncio.run(handle_queries(queries))
    end_time = time.perf_counter()    # End the timer
    elapsed_time = end_time - start_time
    print(f"search('{queries}') took {elapsed_time:.4f} seconds\n")

    crawl_results = asyncio.run(multiple_crawl(all_urls))
    documents = "\n\n".join(item.markdown for item in crawl_results)
    breakpoint()
    print(documents)