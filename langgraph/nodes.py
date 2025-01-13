import os
import logging
from dotenv import load_dotenv

load_dotenv()

from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

import qdrant_client
import dspy

# LlamaIndex core imports
from llama_index.core import VectorStoreIndex
from llama_index.core import Settings, Document

# LlamaIndex vector store import
from llama_index.vector_stores.qdrant import QdrantVectorStore

# Embedding model imports
from llama_index.embeddings.openai import OpenAIEmbedding

# LLM import
from llama_index.llms.openai import OpenAI

from langchain_core.messages import AIMessage, HumanMessage, SystemMessage, AnyMessage, RemoveMessage

from prompt import system_prompt, answer_prompt, grade_prompt
from google_search import search_all
from tavily_search import search
from state import DecomposeQuestion

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
llm = ChatOpenAI(model="gpt-4o-mini", streaming=True)
lm = dspy.LM('openai/gpt-4o-mini', api_key=OPENAI_API_KEY)
dspy.configure(lm=lm)
decompose_module = dspy.Predict(DecomposeQuestion)

Settings.llm = OpenAI(
    model="gpt-4o-mini",
    temperature=0.1,
    max_tokens=2048,
    streaming=True,
    api_key=OPENAI_API_KEY,
)
Settings.embed_model = OpenAIEmbedding(embed_batch_size=10, api_key=OPENAI_API_KEY)

class Nodes():
    def __init__(self):
        client = qdrant_client.QdrantClient(path="./db/")
        vector_store = QdrantVectorStore(client=client, collection_name="chatbot_RAG")
        index = VectorStoreIndex.from_vector_store(vector_store=vector_store)
        self.retriever = index.as_retriever(similarity_top_k=5)

    def retrieve_node(self, state):
        """Retrieve documents"""
        question = state["question"]
        documents = self.retriever.retrieve(question)
        return {"documents": documents}
    
    def should_continue(self, state):
        """Return the next node to execute"""

        messages = state["messages"]

        if len(messages) > 5:
            return "summarize_conversation"
        return END

    def summarize_conversation(self, state):
        # Get the current summary
        summary = state.get("summary", "")
        
        if summary:
            summary_message = (
                f"This is summary of the conversation to date: {summary}\n\n"
                "Extend the summary by taking into account the new mesages above:"
            )
        else:
            summary_message = "Create a summary of the conversation above:"
        
        # Add prompt to the history
        messages = state["messages"] + [HumanMessage(content=summary_message)]
        response = llm.invoke(messages)

        delete_messages = [RemoveMessage(id=m.id) for m in state["messages"][:-2]]
        return {"summary": response.content, "messages": delete_messages}
    
    def answer_node(self, state):
        """Return the final response"""
        document = state["documents"]
        question = state["question"]
        if type(document) == list:
            document = "\n\n".join(document)
        system_message = system_prompt.format()
        answer_message = answer_prompt.format(document=document, question=question)
        messages = [
            {"role": "system", "content": system_message},
            {"role": "user", "content": answer_message}
        ]
        response = llm.invoke(messages)
        # return {
        #     "documents": documents,
        #     "question": question,
        #     "response": response
        # }
        return {"generation": response}

    def grade_documents(self, state):
        """
        Determines whether the retrieved documents are relevant to the question.

        Args:
            state (dict): The current graph state

        Returns:
            state (dict): Updates documents key with only filtered relevant documents
        """
        documents = state["documents"]
        question = state["question"]
        filter_documents = []
        search = "No"

        retrieval_grader = grade_prompt | llm | JsonOutputParser()
        for doc in documents:
            document = doc.node.text
            score = retrieval_grader.invoke({"question": question, "documents": document})
            grade = score["score"]
            if grade == "yes":
                filter_documents.append(document)
        if len(filter_documents) == 0:
            search = "Yes"
        
        return {"documents": filter_documents, "search": search}
    
    def web_search(self, state):
        """
        Web search based on the re-phrased question.

        Args:
            state (dict): The current graph state

        Returns:
            state (dict): Updates documents key with appended web results
        """

        question = state["question"]
        response = decompose_module(question=question)
        # documents = search(response.sub_questions)
        documents = search_all(question)
        logging.info(f"Documents Lens: {len(documents)}")
        return {"documents": documents}
    
    def decide_to_generate(self, state):
        """
        Determines whether to generate an answer, or re-generate a question.

        Args:
            state (dict): The current graph state

        Returns:
            str: Binary decision for next node to call
        """
        search = state["search"]
        if search == "Yes":
            return "search"
        else:
            return "generate"
        
if __name__ == "__main__":
    from nodes import Nodes
    node = Nodes()
    res = node.grade_documents({"documents": ["document"], "question": "Help me write a code"})
    print(res)