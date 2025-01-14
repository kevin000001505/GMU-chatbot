import os
from langgraph.pregel.remote import RemoteGraph
import gradio as gr

# Fetch environment variables
api_url = os.getenv("LANGSERVE_API_URL", "http://langgraph-api:8000")
graph_name = os.getenv("GRAPH_NAME", "rag_chatbot")

# Initialize RemoteGraph
remote_graph = RemoteGraph(graph_name, url=api_url)

def chatbot_response(question: str):
    response = remote_graph.invoke({"question": question})
    if response['generation']['content']:
        return response['generation']['content']
    return "I'm sorry, I don't have an answer for that."

def chatbot_response_stream(question: str, history):
    full_response = ""
    for msg, metadata in remote_graph.stream({"question": question}, stream_mode="messages"):
        if (metadata.get("langgraph_node") == "answer_node"):
            full_response += msg['content']
            yield full_response


# Define Gradio Interface
iface = gr.ChatInterface(
    fn=chatbot_response_stream,
    title="GMU Chatbot",
    type="messages",
)

if __name__ == "__main__":
    iface.launch(server_name="0.0.0.0", server_port=8501, share=False)