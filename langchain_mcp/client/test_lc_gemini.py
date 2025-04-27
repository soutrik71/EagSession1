from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate
from langchain.output_parsers import PydanticOutputParser
from pydantic import BaseModel, Field
import os


load_dotenv()

# Configure API key
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables")

# Initialize the model according to the latest docs
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro",  # You can switch to gemini-2.0-flash-001 if available
    google_api_key=GOOGLE_API_KEY,
    temperature=0,
    max_tokens=2048,
    timeout=None,
    max_retries=2,
    safety_settings={
        0: 0,  # HARM_CATEGORY_DANGEROUS_CONTENT: BLOCK_NONE
        1: 0,  # HARM_CATEGORY_HARASSMENT: BLOCK_NONE
        2: 0,  # HARM_CATEGORY_HATE_SPEECH: BLOCK_NONE
        3: 0,  # HARM_CATEGORY_SEXUALLY_EXPLICIT: BLOCK_NONE
    },
    top_p=0.8,
    top_k=40,
)


# Define joke structure
class Joke(BaseModel):
    setup: str = Field(description="question to set up a joke")
    punchline: str = Field(description="answer to resolve the joke")


try:
    # Method 1: Direct message invocation as shown in the docs
    print("\n--- Method 1: Direct Message Invocation ---")
    messages = [
        (
            "system",
            "You are a professional comedian. Create a joke that is both funny and appropriate.",
        ),
        ("human", "Tell me a joke with a setup and punchline."),
    ]
    ai_msg = llm.invoke(messages)
    print(ai_msg.content)

    # Method 2: Using structured output with PydanticOutputParser
    print("\n--- Method 2: With Pydantic Parser ---")
    parser = PydanticOutputParser(pydantic_object=Joke)

    prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a professional comedian. Create a joke that is both funny and appropriate.",
            ),
            ("human", "{format_instructions}\n\nUser Query: {query}"),
        ]
    )

    # Create the chain using the pipe syntax from the docs
    chain = prompt | llm | parser

    # Invoke with parameters
    output = chain.invoke(
        {
            "format_instructions": parser.get_format_instructions(),
            "query": "Tell me a joke.",
        }
    )

    print(f"Setup: {output.setup}")
    print(f"Punchline: {output.punchline}")

    # Method 3: Basic chaining example
    print("\n--- Method 3: Basic Chaining Example ---")
    translator_prompt = ChatPromptTemplate.from_messages(
        [
            (
                "system",
                "You are a helpful assistant that translates {input_language} to {output_language}.",
            ),
            ("human", "{input}"),
        ]
    )

    translator_chain = translator_prompt | llm

    translation = translator_chain.invoke(
        {
            "input_language": "English",
            "output_language": "French",
            "input": "I love programming.",
        }
    )

    print(f"Translation: {translation.content}")

except Exception as e:
    print(f"Error: {e}")
    import langchain_core

    try:
        import importlib.metadata

        genai_version = importlib.metadata.version("langchain-google-genai")
        print(f"LangChain Core version: {langchain_core.__version__}")
        print(f"LangChain Google GenAI version: {genai_version}")
    except Exception:
        print(f"LangChain Core version: {langchain_core.__version__}")
        print("Could not determine LangChain Google GenAI version")
