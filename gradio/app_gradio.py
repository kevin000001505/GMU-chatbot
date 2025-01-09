import os
from langgraph.pregel.remote import RemoteGraph
import gradio as gr

# Fetch environment variables
api_url = os.getenv("LANGSERVE_API_URL", "http://langgraph-api:8000")
graph_name = os.getenv("GRAPH_NAME", "rag_chatbot")

# Initialize RemoteGraph
remote_graph = RemoteGraph(graph_name, url=api_url)

def chatbot_response(question):
    response = remote_graph.invoke({"question": question})
    if response['generation']['content']:
        return response['generation']['content']
    return "I'm sorry, I don't have an answer for that."

# Define Gradio Interface
iface = gr.Interface(
    fn=chatbot_response,
    inputs="text",
    outputs="text",
    title="GMU Chatbot",
    description="Ask your questions to the GMU chatbot."
)

if __name__ == "__main__":
    iface.launch(server_name="0.0.0.0", server_port=8501)