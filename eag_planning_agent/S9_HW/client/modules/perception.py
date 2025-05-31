"""
FastMCP 2.0 Perception Module

LangChain-based perception engine that analyzes user queries, enhances them with
chat history context, and selects appropriate MCP servers and tools.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import List, Dict

# Add parent directory to path to import utils
sys.path.append(str(Path(__file__).parent.parent))

from pydantic import BaseModel, Field
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate

# Import utility functions for tool information
from tool_utils import get_server_tools_info, format_tools_for_prompt

# Import LLM utilities
from llm_utils import LLMUtils

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class SelectedTool(BaseModel):
    """Information about a selected tool"""

    tool_name: str = Field(description="Specific tool name")
    server: str = Field(description="Server name where the tool resides")
    reasoning: str = Field(description="Why this tool is needed")


class PerceptionResult(BaseModel):
    """Complete perception analysis result"""

    enhanced_question: str = Field(
        description="Standalone question incorporating context if needed"
    )
    intent: str = Field(description="Primary intent of the question")
    entities: List[str] = Field(
        description="Extracted important entities", default_factory=list
    )
    selected_servers: List[str] = Field(
        description="Selected MCP server names", default_factory=list
    )
    selected_tools: List[SelectedTool] = Field(
        description="Selected tools with reasoning", default_factory=list
    )
    reasoning: str = Field(
        description="Overall reasoning for server and tool selection"
    )


class FastMCPPerception:
    """
    LangChain-based perception engine for FastMCP 2.0.

    Analyzes user queries, enhances them with chat history context,
    and recommends appropriate MCP servers and tools.
    Uses LLMUtils for GPT-4o integration and Pydantic output parsing.
    """

    def __init__(self):
        """
        Initialize perception with LLM from llm_utils.py
        """
        # Initialize LLM utilities
        try:
            self.llm_utils = LLMUtils()
            self.llm = self.llm_utils.chat_model
            logger.info("✅ LLM initialized from llm_utils.py")
        except Exception as e:
            logger.error(f"❌ Failed to initialize LLM: {e}")
            raise

        # Initialize Pydantic parser
        self.parser = PydanticOutputParser(pydantic_object=PerceptionResult)

        # Chain and cache
        self.chain = None
        self._tools_info_cache = None

    async def _get_tools_info(self) -> str:
        """
        Get formatted tools information from live MCP servers.

        This method requires live MCP servers to be available and will raise
        an exception if they cannot be reached.

        Returns:
            Formatted tools information string

        Raises:
            ConnectionError: If MCP servers are unavailable
            ValueError: If no tools are discovered
        """
        if self._tools_info_cache is None:
            try:
                logger.info("🔄 Connecting to live MCP servers...")
                server_info = await get_server_tools_info()
                self._tools_info_cache = format_tools_for_prompt(server_info)
                logger.info(
                    f"✅ Successfully loaded tool information for {len(server_info)} servers"
                )
            except (ConnectionError, ValueError) as e:
                logger.error(f"❌ Failed to load live tool information: {e}")
                logger.error("💡 Please ensure all MCP servers are running:")
                logger.error("   - python server/server1_stream.py (Calculator)")
                logger.error("   - python server/server2_stream.py (Web Tools)")
                logger.error("   - python server/server3_stream.py (Document Search)")
                raise ConnectionError(f"MCP servers unavailable: {e}")
            except Exception as e:
                logger.error(f"❌ Unexpected error loading tool info: {e}")
                raise

        return self._tools_info_cache

    async def _initialize_chain(self):
        """Initialize the LangChain processing chain with partial variables"""
        if self.chain is not None:
            return

        try:
            # Load prompt template
            prompt_path = (
                Path(__file__).parent.parent / "prompts" / "perception_prompt.txt"
            )
            with open(prompt_path, "r") as f:
                prompt_template = f.read()

            # Get tools information for partial injection
            tools_info = await self._get_tools_info()

            # Create ChatPromptTemplate from the template
            prompt = ChatPromptTemplate.from_template(prompt_template)

            # Set up partial variables - these are injected once
            prompt = prompt.partial(
                tools_info=tools_info,
                format_instructions=self.parser.get_format_instructions(),
            )

            # Create the complete chain: prompt | llm | parser
            self.chain = prompt | self.llm | self.parser

            logger.info("✅ Perception chain initialized with partial variables")
            logger.info(f"📋 Tools info: {len(tools_info)} characters")
            logger.info(
                f"🔧 Format instructions: {len(self.parser.get_format_instructions())} characters"
            )

        except Exception as e:
            logger.error(f"❌ Chain initialization failed: {e}")
            raise

    async def analyze_query(
        self, user_query: str, chat_history: List[Dict[str, str]] = None
    ) -> PerceptionResult:
        """
        Analyze a user query and return structured perception results.

        Args:
            user_query: The user's question/input
            chat_history: List of previous conversation messages
                         Format: [{"sender": "human/ai", "content": "..."}]

        Returns:
            PerceptionResult with enhanced question, intent, entities, and tool selection
        """
        # Initialize chain if needed
        await self._initialize_chain()

        # Prepare inputs
        if chat_history is None:
            chat_history = []

        # Format chat history for prompt
        history_text = self._format_chat_history(chat_history)

        try:
            logger.info(
                f"🧠 Analyzing query: '{user_query[:50]}{'...' if len(user_query) > 50 else ''}'"
            )
            logger.info(f"📚 Chat history: {len(chat_history)} messages")

            # Invoke the chain with properly formatted inputs
            result = await self.chain.ainvoke(
                {"user_query": user_query, "chat_history": history_text}
            )

            logger.info(f"✅ Analysis complete - Intent: {result.intent}")
            logger.info(
                f"📋 Selected {len(result.selected_servers)} servers, {len(result.selected_tools)} tools"
            )

            return result

        except Exception as e:
            logger.error(f"❌ Perception analysis failed: {e}")
            # Return fallback result
            return self._create_fallback_result(user_query)

    def _format_chat_history(self, chat_history: List[Dict[str, str]]) -> str:
        """Format chat history for prompt injection"""
        if not chat_history:
            return "No previous conversation history."

        formatted_lines = []
        for i, message in enumerate(chat_history[-10:]):  # Last 10 messages
            sender = message.get("sender", "unknown")
            content = message.get("content", "")
            formatted_lines.append(f"{i+1}. {sender.upper()}: {content}")

        return "\n".join(formatted_lines)

    def _create_fallback_result(self, user_query: str) -> PerceptionResult:
        """
        Create a fallback result when analysis fails.

        Note: This should only be used when the LLM fails to process the query,
        not when servers are unavailable (which should raise an exception).
        """
        logger.warning("🔄 Creating fallback result due to LLM processing failure")
        return PerceptionResult(
            enhanced_question=user_query,
            intent="unknown",
            entities=[],
            selected_servers=[],  # Don't assume any servers are available
            selected_tools=[],
            reasoning="Fallback result due to LLM analysis failure - no servers selected",
        )

    async def refresh_tools_cache(self):
        """Refresh the cached tools information"""
        self._tools_info_cache = None
        await self._get_tools_info()
        logger.info("♻️ Tools cache refreshed")


# Convenience functions for easy usage


async def create_perception_engine() -> FastMCPPerception:
    """
    Create and initialize a perception engine.

    This function will verify that MCP servers are available during initialization.

    Returns:
        Initialized FastMCPPerception instance

    Raises:
        ConnectionError: If MCP servers are unavailable
        ValueError: If no tools are discovered from servers
    """
    try:
        perception = FastMCPPerception()
        await perception._initialize_chain()
        return perception
    except (ConnectionError, ValueError) as e:
        logger.error(f"❌ Failed to create perception engine: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error creating perception engine: {e}")
        raise


async def analyze_user_query(
    user_query: str, chat_history: List[Dict[str, str]] = None
) -> PerceptionResult:
    """
    Quick function to analyze a user query without managing perception instance.

    This function requires live MCP servers to be available.

    Args:
        user_query: The user's question
        chat_history: Optional chat history

    Returns:
        PerceptionResult

    Raises:
        ConnectionError: If MCP servers are unavailable
        ValueError: If no tools are discovered from servers
    """
    try:
        perception = await create_perception_engine()
        return await perception.analyze_query(user_query, chat_history)
    except (ConnectionError, ValueError) as e:
        logger.error(f"❌ Query analysis failed due to server unavailability: {e}")
        raise
    except Exception as e:
        logger.error(f"❌ Unexpected error during query analysis: {e}")
        raise


# Test function
async def test_perception():
    """
    Test the perception module.

    This test requires live MCP servers to be running.
    """
    print("🧪 Testing FastMCP Perception Engine")
    print("=" * 50)

    try:
        test_queries = [
            "What is 25 + 37?",
            "Search for information about FastMCP",
            "Find documents about AI and calculate the square root of 144",
        ]

        print("🔄 Initializing perception engine...")
        perception_engine = await create_perception_engine()
        print("✅ Perception engine initialized successfully")

        for i, query in enumerate(test_queries, 1):
            print(f"\n📝 Test {i}: '{query}'")
            try:
                result = await perception_engine.analyze_query(query)
                print(f"✅ Intent: {result.intent}")
                print(f"📋 Enhanced: {result.enhanced_question}")
                print(f"🖥️ Servers: {result.selected_servers}")
                print(f"🔧 Tools: {len(result.selected_tools)}")
                print(f"🔍 Reasoning: {result.reasoning}")
                print(f" 🔍 Entities: {result.entities}")
            except Exception as e:
                print(f"❌ Query {i} failed: {e}")

        print("\n✅ Perception engine testing completed")

    except ConnectionError as e:
        print(f"❌ Server connection failed: {e}")
        print("\n🚀 Please start the MCP servers first:")
        print("   python server/server1_stream.py  # Calculator")
        print("   python server/server2_stream.py  # Web Tools")
        print("   python server/server3_stream.py  # Document Search")
    except Exception as e:
        print(f"❌ Test setup failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_perception())
