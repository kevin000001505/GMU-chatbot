import os
from langgraph.pregel.remote import RemoteGraph
import gradio as gr

# Fetch environment variables
api_url = os.getenv("LANGSERVE_API_URL", "http://langgraph-api:8000")
graph_name = os.getenv("GRAPH_NAME", "rag_chatbot")

# Initialize RemoteGraph
remote_graph = RemoteGraph("GMU_chatbot", url="http://localhost:62214")

def chatbot_response(question: str):
    response = remote_graph.invoke({"question": question})
    if response['generation']['content']:
        return response['generation']['content']
    return "I'm sorry, I don't have an answer for that."

async def chatbot_response_stream(question: str):
    for msg, metadata in remote_graph.stream({"question": question}, stream_mode="messages"):
        if (
            metadata.get("langgraph_node") == "answer_node"
        ):  
            yield msg['content']


# Define Gradio Interface
iface = gr.Interface(
    fn=chatbot_response_stream,
    inputs="text",
    outputs="text",
    title="GMU Chatbot",
    description="Ask your questions to the GMU chatbot."
)

if __name__ == "__main__":
    iface.launch(server_name="0.0.0.0", server_port=8501)