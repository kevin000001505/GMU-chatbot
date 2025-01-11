import os
import time
import asyncio
import dspy



from state import ExtractInfo, DecomposeQuestion
from dotenv import load_dotenv
from googlesearch import search
from crawl4ai import AsyncWebCrawler, CacheMode
from langchain_openai import ChatOpenAI

load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")

# Initialize LLM only once at the top
llm = ChatOpenAI(model="gpt-4o-mini")
lm = dspy.LM('openai/gpt-4o-mini', api_key=OPENAI_API_KEY)
dspy.configure(lm=lm)
asy_extract = dspy.asyncify(dspy.Predict(ExtractInfo))
decompose_module = dspy.Predict(DecomposeQuestion)


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
    return await loop.run_in_executor(None, list, search(f"Geroge Mason University - {query}", num=4, stop=4, pause=2))

async def handle_queries(queries):
    """Handle multiple search queries concurrently."""
    all_urls = set()
    tasks = [async_search(query) for query in queries]
    results = await asyncio.gather(*tasks)
    for sublist in results:
        for url in sublist:
            all_urls.add(url)
    return list(all_urls)

def search_all(query) -> list:
    """Search for the given queries and return the crawl4ai results."""
    # Decompose the query into multiple queries
    response = decompose_module(question=query)
    queries = response.sub_questions

    # Search for multiple queries and get the URLs
    all_urls = asyncio.run(handle_queries(queries))

    # Crawl the URLs and get the results
    crawl_results = asyncio.run(multiple_crawl(all_urls))
    raw_documents = [item.markdown for item in crawl_results]
    results = clean_content(query, raw_documents)
    documents = [item.extract_content for item in results]
    return documents

def clean_content(query, documents) -> list:
    """Clean the content by removing the unnecessary characters."""
    return asyncio.run(process_all_contents(query, documents))

async def process_all_contents(query, contents):
    # Create tasks by directly calling the module.apredict for each content
    tasks = [asy_extract(text=content, query=query) for content in contents]
    results = await asyncio.gather(*tasks)  # Run tasks concurrently
    return results



if __name__ == '__main__':
    start_time = time.perf_counter()
    query = "What should I prepare as a freshman?"
    response = decompose_module(question=query)
    queries = response.sub_questions
    print("search: ", queries)
    all_urls = asyncio.run(handle_queries(queries))

    crawl_results = asyncio.run(multiple_crawl(all_urls))
    raw_documents = [item.markdown for item in crawl_results]
    results = clean_content(query, raw_documents)
    documents = [item.extract_content for item in results]
    end_time = time.perf_counter()    # End the timer
    elapsed_time = end_time - start_time
    print(f"search('{queries}') took {elapsed_time:.4f} seconds\n")
    print(documents)