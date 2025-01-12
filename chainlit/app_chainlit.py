import os
import chainlit as cl
from langgraph.pregel.remote import RemoteGraph


api_url = os.getenv("LANGSERVE_API_URL", "http://langgraph-api:8000")
graph_name = os.getenv("GRAPH_NAME", "rag_chatbot")

# Initialize RemoteGraph
remote_graph = RemoteGraph(graph_name, url=api_url)

@cl.on_message
async def chat_with_gmu(message: cl.Message):
    """
    Handles user messages and streams responses using Chainlit.
    """
    status_message = await cl.Message(
        content="🔄 Scraping the website, please wait..."
    ).send()
    try:
        mesg = cl.Message(content="")  # Create a Chainlit message

        async for msg, metadata in remote_graph.astream({"question": message.content}, stream_mode="messages"):
            if (
                metadata.get("langgraph_node") == "answer_node"
            ):  
                await mesg.stream_token(msg['content'])

        # Finalize the response message
        await mesg.update()
    except Exception as e:
        await cl.Message(
            content=f"❌ An error occurred while scraping: {str(e)}"
        ).send()
    finally:
        # 5. Remove the initial status message
        await status_message.delete()



@cl.on_chat_start
async def start():
    await cl.Message(
        author="Assistant", content="Hello! I'm an AI assistant. How may I help you?"
    ).send()
