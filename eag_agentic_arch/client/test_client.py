# Import and apply SSL certificate patch first (before any other imports)
from ssl_helper import patch_ssl_verification

patch_ssl_verification()

import os
import asyncio
import sys
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from langchain_core.runnables import RunnableSequence
from langchain_mcp_adapters.tools import load_mcp_tools

# Fix for Windows asyncio subprocess
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsProactorEventLoopPolicy())

# Import from relative paths since we're inside the client directory
from memory import ConversationMemory
from perception import get_perception_chain
from llm_provider import default_llm

# Setup conversation memory and perception chain
conversation_memory = ConversationMemory(conversation_id="travel-session")
perception_chain = get_perception_chain()

llm = default_llm.chat_model
print(f"LLM: \n\n{llm}\n\n")


def process_travel_query(
    user_query: str,
    conversation_memory: ConversationMemory = None,
    perception_chain: RunnableSequence = None,
):
    """Process a single iteration of the agent to extract travel search parameters.

    Args:
        user_query: The user's query about travel.
        conversation_memory: Optional ConversationMemory object with chat history.
        perception_chain: Optional perception chain to use. If None, a new one is created.

    Returns:
        A TravelSearch object with extracted parameters.
    """
    # Get chat history in the format expected by LangChain
    chat_history = conversation_memory.get_langchain_messages()

    # Add the current query to memory BEFORE processing
    conversation_memory.add_human_message(user_query)

    # Process the query with the chain
    result = perception_chain.invoke(
        {"user_query": user_query, "chat_history": chat_history}
    )

    # Store the result directly using model_dump()
    conversation_memory.add_ai_message(result.model_dump())

    # Save the conversation
    conversation_memory.save()


# Server parameters
server_params = StdioServerParameters(command="python", args=["server/server.py"])


async def main(llm, query):
    """Main function to run the client."""
    try:
        # Using a direct subprocess call instead of asyncio.subprocess
        import subprocess

        async with stdio_client(server_params) as (read, write):
            print("Connection established, creating session...")
            async with ClientSession(read, write) as session:
                print("Session created, initializing...")
                await session.initialize()
                print("Session initialized, loading tools...")
                tools = await load_mcp_tools(session)
                # add the tools to the model
                print("Tools loaded, binding to model...")
                llm_with_tools = llm.bind_tools(tools)
                print("Model bound to tools, invoking...")
                response = await llm_with_tools.ainvoke(query)

                print(f"Response: \n\n{response}\n\n")

                return response
    except Exception as e:
        print(f"Error occurred: {e}")
        import traceback

        traceback.print_exc()
        return f"Error: {str(e)}"


if __name__ == "__main__":
    query = "I want to search for flights from New York to Los Angeles on 2025-05-01 with return on 2025-05-05"
    try:
        asyncio.run(main(llm, query))
    except NotImplementedError as e:
        print(f"NotImplementedError: {e}")
        print("This is likely due to Windows asyncio subprocess issues.")
        print("Consider using a different approach for subprocess handling on Windows.")
