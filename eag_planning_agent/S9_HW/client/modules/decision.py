"""
FastMCP 2.0 Decision Module

LangChain-based decision engine that analyzes enhanced user queries and recommended tools
to create detailed execution plans with proper tool orchestration.
"""

import asyncio
import logging
import sys
from pathlib import Path
from typing import List, Dict, Optional, Any
from enum import Enum

# Add parent directory to path to import utils
sys.path.append(str(Path(__file__).parent.parent))

from pydantic import BaseModel, Field, validator, model_validator
from langchain_core.output_parsers import PydanticOutputParser
from langchain_core.prompts import ChatPromptTemplate

# Import utility functions for tool information
from tool_utils import get_filtered_tools_summary, get_tools_for_prompt

# Import LLM utilities
from llm_utils import LLMUtils

# Import PerceptionResult from perception module
from modules.perception import PerceptionResult

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ExecutionStrategy(str, Enum):
    """Enumeration of execution strategies"""

    SINGLE_TOOL = "single_tool"
    PARALLEL_TOOLS = "parallel_tools"
    SEQUENTIAL_TOOLS = "sequential_tools"
    HYBRID_TOOLS = "hybrid_tools"


class ToolCall(BaseModel):
    """Essential information about a single tool call in the execution plan"""

    step: int = Field(description="Execution step number (1-based indexing)", ge=1)
    tool_name: str = Field(description="Exact tool name to call", min_length=1)
    parameters: Dict[str, Any] = Field(
        description="Parameters for the tool call in format {'input': {...}}"
    )
    dependency: str = Field(
        description="What this step depends on (e.g., 'none', 'step_1', 'steps_1_and_2')"
    )
    purpose: str = Field(
        description="Why this tool is needed and what sub-question it addresses",
        min_length=10,
    )
    result_variable: Optional[str] = Field(
        default=None,
        description="Variable name for referencing this result in subsequent steps",
    )

    @validator("tool_name")
    def validate_tool_name_format(cls, v):
        if not v or not isinstance(v, str):
            raise ValueError("Tool name must be a non-empty string")
        return v

    @validator("parameters")
    def validate_parameters_structure(cls, v):
        if not isinstance(v, dict) or "input" not in v:
            raise ValueError("Parameters must be a dictionary with 'input' key")
        return v


class DecisionResult(BaseModel):
    """Complete decision analysis and execution plan"""

    strategy: ExecutionStrategy = Field(description="Overall execution strategy")
    total_steps: int = Field(description="Total number of steps in the plan", ge=1)
    tool_calls: List[ToolCall] = Field(description="Detailed tool call specifications")
    execution_sequence: str = Field(
        description="Description of execution sequence and dependencies"
    )
    final_result_processing: str = Field(
        description="How to combine and present final results"
    )
    reasoning: str = Field(
        description="Reasoning for the chosen strategy and tool sequence", min_length=30
    )

    @model_validator(mode="after")
    def validate_consistency(cls, values):
        """Validate consistency between fields"""
        if isinstance(values, dict):
            # Handle dict case (shouldn't happen in v2 but just in case)
            total_steps = values.get("total_steps", 0)
            tool_calls = values.get("tool_calls", [])
            strategy = values.get("strategy")
        else:
            # Handle model instance case (Pydantic v2)
            total_steps = values.total_steps
            tool_calls = values.tool_calls
            strategy = values.strategy

        # Check that tool_calls length matches total_steps
        if len(tool_calls) != total_steps:
            raise ValueError(
                f"Number of tool calls ({len(tool_calls)}) must match total_steps ({total_steps})"
            )

        # Check strategy consistency
        if strategy == ExecutionStrategy.SINGLE_TOOL and total_steps != 1:
            raise ValueError("Single tool strategy must have exactly 1 step")
        elif (
            strategy
            in [
                ExecutionStrategy.PARALLEL_TOOLS,
                ExecutionStrategy.SEQUENTIAL_TOOLS,
                ExecutionStrategy.HYBRID_TOOLS,
            ]
            and total_steps < 2
        ):
            raise ValueError(f"{strategy.value} strategy must have at least 2 steps")

        # Validate step numbers are sequential and start from 1
        if tool_calls:
            step_numbers = [tc.step for tc in tool_calls]
            expected_steps = list(range(1, total_steps + 1))
            if sorted(step_numbers) != expected_steps:
                raise ValueError(
                    f"Step numbers must be sequential 1-{total_steps}, got {sorted(step_numbers)}"
                )

        return values


class FastMCPDecision:
    """
    LangChain-based decision engine for FastMCP 2.0.

    Analyzes enhanced user queries and recommended tools to create
    detailed execution plans with proper tool orchestration.
    """

    def __init__(self):
        """Initialize decision engine with LLM from llm_utils.py"""
        try:
            self.llm_utils = LLMUtils()
            self.llm = self.llm_utils.chat_model
            logger.info("✅ LLM initialized from llm_utils.py")
        except Exception as e:
            logger.error(f"❌ Failed to initialize LLM: {e}")
            raise

        # Initialize Pydantic parser
        self.parser = PydanticOutputParser(pydantic_object=DecisionResult)

        # Chain cache
        self.chain = None

    async def _initialize_chain(self):
        """Initialize the LangChain processing chain with partial variables"""
        if self.chain is not None:
            return

        try:
            # Load prompt template
            prompt_path = (
                Path(__file__).parent.parent / "prompts" / "decision_prompt.txt"
            )
            with open(prompt_path, "r", encoding="utf-8") as f:
                prompt_template = f.read()

            # Create ChatPromptTemplate from the template
            prompt = ChatPromptTemplate.from_template(prompt_template)

            # Set up partial variables - output_instructions injected once
            prompt = prompt.partial(
                output_instructions=self.parser.get_format_instructions()
            )

            # Create the complete chain: prompt | llm | parser
            self.chain = prompt | self.llm | self.parser

            logger.info("✅ Decision chain initialized with partial variables")

        except Exception as e:
            logger.error(f"❌ Chain initialization failed: {e}")
            raise

    async def analyze_decision(
        self, enhanced_question: str, recommended_tools: List[str]
    ) -> DecisionResult:
        """
        Analyze an enhanced user query and create a detailed execution plan.

        Args:
            enhanced_question: The enhanced/standalone question from perception module
            recommended_tools: List of tool names recommended by perception module

        Returns:
            DecisionResult with detailed execution plan and tool orchestration
        """
        # Initialize chain if needed
        await self._initialize_chain()

        try:
            logger.info(
                f"🧠 Analyzing decision for: '{enhanced_question[:50]}{'...' if len(enhanced_question) > 50 else ''}'"
            )
            logger.info(f"🔧 Recommended tools: {recommended_tools}")

            # Get filtered tool descriptions for the recommended tools
            logger.info("📋 Fetching filtered tool descriptions...")

            # If no tools are recommended, get all available tools
            if not recommended_tools:
                logger.info(
                    "🔧 No recommended tools provided, fetching all available tools..."
                )
                tool_descriptions = await get_tools_for_prompt()
            else:
                tool_descriptions = await get_filtered_tools_summary(recommended_tools)

            logger.info(f"📋 Tool descriptions: {len(tool_descriptions)} characters")

            # Invoke the chain with properly formatted inputs
            result = await self.chain.ainvoke(
                {
                    "enhanced_question": enhanced_question,
                    "tool_descriptions": tool_descriptions,
                }
            )

            logger.info(f"✅ Decision analysis complete - Strategy: {result.strategy}")
            logger.info(
                f"📋 Generated {result.total_steps} steps with {len(result.tool_calls)} tool calls"
            )

            return result

        except Exception as e:
            logger.error(f"❌ Decision analysis failed: {e}")
            # Return fallback result
            return self._create_fallback_result(enhanced_question, recommended_tools)

    async def analyze_decision_from_perception(
        self, perception_result: PerceptionResult
    ) -> DecisionResult:
        """
        Analyze a perception result and create a detailed execution plan.

        This is a convenience method that extracts the necessary data from
        a PerceptionResult object and calls the main analyze_decision method.

        Args:
            perception_result: The result from perception module

        Returns:
            DecisionResult with detailed execution plan and tool orchestration
        """
        # Extract enhanced_question from perception result
        enhanced_question = perception_result.enhanced_question

        # Extract tool names from selected_tools
        recommended_tools = [
            tool.tool_name for tool in perception_result.selected_tools
        ]

        logger.info("🔄 Converting PerceptionResult to decision inputs")
        logger.info(f"📝 Enhanced question: {enhanced_question}")
        logger.info(
            f"🔧 Extracted {len(recommended_tools)} tool names: {recommended_tools}"
        )

        # Call the main analyze_decision method
        return await self.analyze_decision(enhanced_question, recommended_tools)

    def _create_fallback_result(
        self, enhanced_question: str, recommended_tools: List[str]
    ) -> DecisionResult:
        """Create a fallback result when analysis fails."""
        logger.warning("🔄 Creating fallback result due to LLM processing failure")

        if not recommended_tools:
            return DecisionResult(
                strategy=ExecutionStrategy.SINGLE_TOOL,
                total_steps=1,
                tool_calls=[
                    ToolCall(
                        step=1,
                        tool_name="fallback_error",
                        parameters={"input": {}},
                        dependency="none",
                        purpose="No tools available - fallback error handler",
                    )
                ],
                execution_sequence="Single fallback step due to no available tools",
                final_result_processing="Return error message about no tools available",
                reasoning="No tools were recommended by perception module",
            )

        # Create simple single-tool fallback using first recommended tool
        fallback_tool = recommended_tools[0]

        return DecisionResult(
            strategy=ExecutionStrategy.SINGLE_TOOL,
            total_steps=1,
            tool_calls=[
                ToolCall(
                    step=1,
                    tool_name=fallback_tool,
                    parameters={"input": {}},
                    dependency="none",
                    purpose=f"Fallback execution using {fallback_tool} due to LLM analysis failure",
                )
            ],
            execution_sequence="Single fallback tool execution",
            final_result_processing="Manual review required - fallback execution with incomplete parameters",
            reasoning="Fallback result due to LLM analysis failure - using first recommended tool",
        )


# Convenience functions for easy usage


async def create_decision_engine() -> FastMCPDecision:
    """Create and initialize a decision engine."""
    try:
        decision = FastMCPDecision()
        await decision._initialize_chain()
        return decision
    except Exception as e:
        logger.error(f"❌ Failed to create decision engine: {e}")
        raise


async def analyze_enhanced_query(
    enhanced_question: str, recommended_tools: List[str]
) -> DecisionResult:
    """Quick function to analyze an enhanced query without managing decision instance."""
    try:
        decision_engine = await create_decision_engine()
        return await decision_engine.analyze_decision(
            enhanced_question, recommended_tools
        )
    except Exception as e:
        logger.error(f"❌ Decision analysis failed: {e}")
        raise


# Test function
async def test_decision():
    """Test the decision module with various query types."""
    print("🧪 Testing FastMCP Decision Engine")
    print("=" * 50)

    try:
        test_cases = [
            {
                "enhanced_question": "What is 25 + 37?",
                "recommended_tools": ["calculator_add"],
                "expected_strategy": "single_tool",
            },
            {
                "enhanced_question": "What is 5 factorial and what is the cube root of 27?",
                "recommended_tools": ["calculator_factorial", "calculator_cbrt"],
                "expected_strategy": "parallel_tools",
            },
            {
                "enhanced_question": "What is the exponential sum of sine of 66 and 88?",
                "recommended_tools": [
                    "calculator_sin",
                    "calculator_int_list_to_exponential_sum",
                ],
                "expected_strategy": "sequential_tools",
            },
            {
                "enhanced_question": "Search for John Cena's age and calculate 2 to the power of that age",
                "recommended_tools": ["web_tools_search_web", "calculator_power"],
                "expected_strategy": "sequential_tools",
            },
        ]

        print("🔄 Initializing decision engine...")
        decision_engine = await create_decision_engine()
        print("✅ Decision engine initialized successfully")

        for i, test_case in enumerate(test_cases, 1):
            print(f"\n📝 Test {i}: '{test_case['enhanced_question']}'")
            print(f"🔧 Tools: {test_case['recommended_tools']}")

            try:
                result = await decision_engine.analyze_decision(
                    test_case["enhanced_question"], test_case["recommended_tools"]
                )

                print(
                    f"✅ Strategy: {result.strategy} (expected: {test_case['expected_strategy']})"
                )
                print(f"📋 Steps: {result.total_steps}")
                print(f"🔄 Sequence: {result.execution_sequence}")
                print(f"🔍 Reasoning: {result.reasoning[:100]}...")

            except Exception as e:
                print(f"❌ Test {i} failed: {e}")

        print("\n✅ Decision engine testing completed")

    except Exception as e:
        print(f"❌ Test setup failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_decision())
