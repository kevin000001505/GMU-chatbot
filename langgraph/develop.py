import os
from dotenv import load_dotenv

# LlamaIndex core imports
from llama_index.core import VectorStoreIndex
from llama_index.core import Settings

# LlamaIndex vector store import
from llama_index.vector_stores.qdrant import QdrantVectorStore

# Embedding model imports
from llama_index.embeddings.openai import OpenAIEmbedding

from langgraph.graph import StateGraph, START, END
from langgraph.graph.message import add_messages
from langchain_openai import ChatOpenAI

# LLM import
from llama_index.llms.groq import Groq

from typing import TypedDict, List
from nodes import Nodes
node = Nodes()


class GraphState(TypedDict):
    question: str
    generation: str
    search: str
    documents: List[str]
    steps: List[str]

# Load environment variables
load_dotenv()

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
GROK_API_KEY = os.getenv("GROK_API_KEYs")

Settings.llm = Groq(model="llama-3.1-70b-versatile")
Settings.embed_model = OpenAIEmbedding(embed_batch_size=10, api_key=OPENAI_API_KEY)
llm = ChatOpenAI(model="gpt-4o-mini")


workflow = StateGraph(GraphState)
workflow.add_node("retrieve_node", node.retrieve_node)
workflow.add_node("grade_documents", node.grade_documents)
workflow.add_node("web_search", node.web_search)
workflow.add_node("answer_node", node.answer_node)

workflow.add_edge(START, "retrieve_node")
workflow.add_edge("retrieve_node", "grade_documents")
workflow.add_conditional_edges(
    "grade_documents", 
    node.decide_to_generate,
    {
        "search": "web_search",
        "generate": "answer_node"
    },
)
workflow.add_edge("web_search", "answer_node")
workflow.add_edge("answer_node", END)

graph = workflow.compile()