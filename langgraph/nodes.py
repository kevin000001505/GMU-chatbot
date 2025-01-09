import os
import logging
from dotenv import load_dotenv

load_dotenv()

from langchain_openai import ChatOpenAI
from langchain.prompts import PromptTemplate
from langchain_core.output_parsers import JsonOutputParser

import qdrant_client

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

from google_search import search_all

OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
llm = ChatOpenAI(model="gpt-4o-mini")

Settings.llm = OpenAI(
    model="gpt-4o-mini",
    temperature=0.1,
    max_tokens=1024,
    streaming=True,
    api_key=OPENAI_API_KEY,
)
Settings.embed_model = OpenAIEmbedding(embed_batch_size=10, api_key=OPENAI_API_KEY)

# Prompt
prompt = PromptTemplate(
    template="""You are a teacher grading a quiz. You will be given: 
    1/ a QUESTION
    2/ A FACT provided by the student
    
    You are grading RELEVANCE RECALL:
    A score of 1 means that ANY of the statements in the FACT are relevant to the QUESTION. 
    A score of 0 means that NONE of the statements in the FACT are relevant to the QUESTION. 
    1 is the highest (best) score. 0 is the lowest score you can give. 
    
    Explain your reasoning in a step-by-step manner. Ensure your reasoning and conclusion are correct. 
    
    Avoid simply stating the correct answer at the outset.
    
    Question: {question} \n
    Fact: \n\n {documents} \n\n
    
    Give a binary score 'yes' or 'no' score to indicate whether the document is relevant to the question. \n
    Provide the binary score as a JSON with a single key 'score' and no premable or explanation.
    """,
    input_variables=["question", "documents"],
)

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
        documents = state["documents"]
        question = state["question"]
        document = "\n\n".join(documents)

        # Create an answer using the retrieved document
        prompt = f"""
        Based on the retrieved document:
        {document}

        Respond to the following user query:
        {question}
        """

        response = llm.invoke(prompt)
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

        retrieval_grader = prompt | llm | JsonOutputParser()
        for doc in documents:
            document = doc.node.text
            score = retrieval_grader.invoke({"question": question, "documents": document})
            grade = score["score"]
            if grade == "yes":
                filter_documents.append(document)
        if len(filter_documents) == 0:
            search = "Yes"
        
        return {"documents": filter_documents, "search": search}
        # return {"documents": filter_documents, "question": question, "search": search}
    
    def web_search(self, state):
        """
        Web search based on the re-phrased question.

        Args:
            state (dict): The current graph state

        Returns:
            state (dict): Updates documents key with appended web results
        """

        question = state["question"]
        documents = search_all(question)
        logging.info(f"Documents Lens: {len(documents)}")
        return {"documents": documents}
        # return {"documents": documents, "question": question}
    
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