import sys
import os

# Add the parent directory (eag_agentic_rag) to the Python path
current_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.abspath(os.path.join(current_dir, ".."))
sys.path.append(project_root)

# Add the current path and project root to the Python path to enable module imports
sys.path.insert(0, current_dir)
sys.path.insert(0, project_root)

from typing import List
from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableSequence
from dotenv import load_dotenv

# Load environment variables
load_dotenv()


class Process(BaseModel):
    """A specific sub-question and the tool required to address it."""

    sub_question: str = Field(description="The specific sub-question to be addressed")
    tool: str = Field(
        description="Tool name (websearch, gsuite, gmail, calculator, etc.)"
    )


class ContentSearch(BaseModel):
    enhanced_user_query: str = Field(
        description="The enhanced standalone user query based on current question and relevant history"
    )
    list_of_processes: List[Process] = Field(
        description="The list of processes to be executed, each with a sub-question and associated tool"
    )


system_prompt = """
You are an intelligent assistant designed to refine user queries using current input and prior context.
Your goal is to:
1. Create a standalone query that incorporates necessary context
2. Break it down into specific sub-questions with appropriate tools

Process:
1. Analyze the current user query to understand what is being asked
2. Check if the query has dependencies on chat history (pronouns, references, etc.)
3. If dependencies exist, create a standalone enhanced query by incorporating context from history
4. If no dependencies exist, use the original query as the enhanced query
5. Break down the enhanced query into sequential sub-questions with appropriate tools

Important rules for creating sub-questions:
- ONLY extract sub-questions that are DIRECTLY present in the enhanced query
- DO NOT add new information or questions that aren't in the enhanced query
- DO NOT invent sub-questions that aren't stated or implied in the enhanced query
- Break down the query into logical sequential parts that must be executed in order
- Assign the most appropriate tool for each sub-question
- A tool can be used only once in a query so club the sub-questions using the same tool if required

For identifying tools:
- search_web: For finding information online regading any topic (use tool "search_web")
- create_gsheet: For creating spreadsheets or documents to be shared with others via email (use tool "create_gsheet")
- send_email: For email-related tasks only if explicitly mentioned by the user with a specific email id 
  and task to be performed with subject and body (use tool "send_email")
- calendar: For scheduling tasks only if explicitly mentioned by the user with a specific date and time
- calculator: For mathematical operations only if explicitly mentioned by the user

**Inputs:**
- `chat_history`: A list of dictionaries, each with keys `sender` and `content`.
    {chat_history}
- `user_query`: The latest message from the user.
    {user_query}

**Output Format:**
{format_instructions}
"""


def get_perception_chain(llm) -> RunnableSequence:
    """
    Creates and returns the perception chain for extracting search parameters and breaking down queries.

    Args:
        llm: The LLM to use for the chain.

    Returns:
        A LangChain runnable sequence that takes a user query and chat history,
        and returns a ContentSearch object with enhanced query and structured processes.
    """

    # Set up a parser
    parser = PydanticOutputParser(pydantic_object=ContentSearch)

    prompt = ChatPromptTemplate.from_messages(
        [
            ("system", system_prompt),
            MessagesPlaceholder(variable_name="chat_history"),
            ("human", "The user query is: {user_query}"),
        ]
    )

    prompt = prompt.partial(format_instructions=parser.get_format_instructions())

    # Create and return the chain
    return prompt | llm | parser


async def process_conversation_and_enhance_query(
    history_store, conversation_list, chain, conv_id
):
    """
    Processes a list of user queries using the provided chain and history store.
    For each query, retrieves chat history, invokes the chain, stores the conversation,
    and returns enhanced queries and structured processes.

    Args:
        history_store: Object for storing and retrieving conversation history.
        conversation_list: List of user queries (strings) to process.
        chain: The chain object with an 'invoke' method.
        conv_id: The conversation id to store the conversation.

    Returns:
        Tuple of (enhanced_queries, list_of_processes) where list_of_processes contains
        structured information about sub-questions and tools.
    """
    enhanced_queries = []
    list_of_processes = []

    for user_query in conversation_list:
        # Retrieve chat history for the conversation
        chat_history = history_store.get_conversation_as_lc_messages(str(conv_id))
        # Invoke the chain to get the result - use await for async invocation
        result = await chain.ainvoke(
            {"user_query": user_query, "chat_history": chat_history}
        )
        # Store the conversation
        messages = [
            {"sender": "human", "content": user_query},
            {"sender": "ai", "content": result.enhanced_user_query},
        ]
        history_store.store_conversation(str(conv_id), messages)
        # Collect the enhanced user query and processes
        enhanced_queries.append(result.enhanced_user_query)
        list_of_processes.append(result.list_of_processes)
    return enhanced_queries, list_of_processes


if __name__ == "__main__":
    import asyncio
    from client.llm_provider import default_llm
    from client.utils import read_yaml_file
    from client.embedding_provider import OpenAIEmbeddingProvider
    from client.memory import ConversationMemory
    import uuid

    async def main():
        # llm provider
        llm = default_llm.chat_model
        embedder = OpenAIEmbeddingProvider().embeddings

        # read config
        config = read_yaml_file("client/config.yaml")
        print(config)

        history_index_name = config["history_index_name"]
        history_index_name = os.path.join(os.getcwd(), history_index_name)

        conv_id = uuid.uuid4()
        memory_store = ConversationMemory(
            embedder, index_folder=history_index_name, reset_index=True
        )

        # create perception chain
        perception_chain = get_perception_chain(llm)

        # process conversation and enhance query
        conversation_list = [
            "Search for the top 5 places to visit in France",
            "Search for the top 5 places to visit in India and convert into a google sheet for soutrik1991@gmail.com",
            "Search for the top 5 places to visit in USA and convert into a google sheet and "
            "draft an email to the soutrik1991@gmail.com with subject 'Top 5 places to visit in USA' and "
            "body 'Please find the top 5 places to visit in USA' and send it to soutrik1991@gmail.com",
        ]
        enhanced_queries, list_of_processes = (
            await process_conversation_and_enhance_query(
                memory_store, conversation_list, perception_chain, conv_id
            )
        )
        print("Enhanced Queries:")
        for query in enhanced_queries:
            print(f"- {query}")

        print("\nProcesses:")
        for i, processes in enumerate(list_of_processes):
            print(f"\nFor query {i+1}:")
            for process in processes:
                print(f"- Sub-question: {process.sub_question}")
                print(f"  Tool: {process.tool}")

    # Run the async main function
    asyncio.run(main())
