import sys
import os

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))
from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableSequence
from dotenv import load_dotenv


# Load environment variables
load_dotenv()

# Clear SSL_CERT_FILE environment variable if set
if "SSL_CERT_FILE" in os.environ:
    del os.environ["SSL_CERT_FILE"]


class WebContentSearch(BaseModel):
    enhanced_user_query: str = Field(
        description="The enhanced user query to be searched on the web for similar content stored in the memory"
    )
    no_of_results: int = Field(
        1,
        description="The number of results to be returned from the web search corresponding to the user query",
    )


system_prompt = """
You are an intelligent assistant designed to refine user queries using current input and prior context. "
"Your goal is to construct a precise, context-aware enhanced query that reflects the user's true intent.\n\n"
"Your responsibilities are:\n"
"1. Analyze the current user message to understand the core request.\n"
"2. Examine the chat history (a list of messages with sender and content) to identify:\n"
"   - Any contextually relevant information.\n"
"   - Follow-ups or references to previous discussions.\n"
"3. Determine whether the current query is:\n"
"   a. A continuation of a previous topic.\n"
"   b. A new, unrelated query.\n\n"
"Based on this analysis, follow the appropriate path:\n\n"
"**If the current message relates to previous topics:**\n"
"- Incorporate relevant prior context into the enhanced query.\n"
"- Clarify ambiguous references or pronouns using information from the chat history.\n"
"- Resolve under-specified requests by grounding them in previous conversations.\n\n"
"**If the message is a new topic:**\n"
"- Focus solely on the current message.\n"
"- Do not infer or inject unrelated context from chat history.\n\n"
"**Process for forming the enhanced user query:**\n"
"1. Carefully review the current message.\n"
"2. Analyze the chat history (most recent last) to extract relevant past content.\n"
"3. Identify if the user is building on a previous conversation.\n"
"4. Integrate any necessary clarifications, references, or details from the chat history.\n"
"5. Output a concise, context-enriched, unambiguous enhanced query.\n\n"
"**Inputs:**\n"
"- `chat_history`: A list of dictionaries, each with keys `sender` and `content`.\n"
"    {chat_history}\n"
"- `user_query`: The latest message from the user.\n"
"    {user_query}\n\n"
"**Output Format:**\n"
"{format_instructions}\n"
    """


def get_perception_chain(llm) -> RunnableSequence:
    """
    Creates and returns the perception chain for extracting travel search parameters.

    Args:
        default_llm: The default LLM to use for the chain.

    Returns:
        A LangChain runnable sequence that takes a user query and chat history,
        and returns a TravelSearch object.
    """

    # Set up a parser
    parser = PydanticOutputParser(pydantic_object=WebContentSearch)

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


def process_conversation_and_enhance_query(
    history_store, conversation_list, chain, conv_id
):
    """
    Processes a list of user queries (conversation_list) using the provided chain and history store.
    For each user query, it retrieves the chat history, invokes the chain, stores the conversation,
    and returns a list of enhanced user queries.

    Args:
        history_store: The object responsible for storing and retrieving conversation history.
        conversation_list: List of user queries (strings) to process.
        chain: The chain object with an 'invoke' method.
        conv_id: The conversation id to store the conversation.

    Returns:
        List of enhanced user queries (one for each user query in conversation_list).
    """
    enhanced_queries = []
    for user_query in conversation_list:
        # Retrieve chat history for the conversation
        chat_history = history_store.get_conversation_as_lc_messages(str(conv_id))
        # Invoke the chain to get the result
        result = chain.invoke({"user_query": user_query, "chat_history": chat_history})
        # Store the conversation
        messages = [
            {"sender": "human", "content": user_query},
            {"sender": "ai", "content": result.enhanced_user_query},
        ]
        history_store.store_conversation(str(conv_id), messages)
        # Collect the enhanced user query
        enhanced_queries.append(result.enhanced_user_query)
    return enhanced_queries


if __name__ == "__main__":
    from url_rag.utility.llm_provider import default_llm
    from url_rag.utility.utils import read_yaml_file
    from url_rag.utility.embedding_provider import OpenAIEmbeddingProvider
    from url_rag.client.memory import ConversationMemory
    import uuid

    # llm provider
    llm = default_llm.chat_model
    embedder = OpenAIEmbeddingProvider().embeddings
    # read config
    config = read_yaml_file("url_rag/utility/config.yaml")
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
        "What is the capital of France?",
        "Tell me more about its history.",
        "List two famous landmarks in that city.",
    ]
    enhanced_queries = process_conversation_and_enhance_query(
        memory_store, conversation_list, perception_chain, conv_id
    )
    print(enhanced_queries)
