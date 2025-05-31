#!/usr/bin/env python3
"""
FastMCP Action Engine

This module orchestrates the execution of decisions made by the decision engine.
It takes a DecisionResult and uses the appropriate tool execution strategy
to execute the planned tool calls and return formatted results.
"""

import asyncio
import logging
import yaml
from pathlib import Path
from typing import Dict, List, Any, Optional
from dataclasses import dataclass
import sys

# Add the parent directory to Python path for imports
current_dir = Path(__file__).parent
client_dir = current_dir.parent
sys.path.insert(0, str(client_dir))

# Import core components
from core.session import FastMCPSession
from core.tool_call import create_tool_executor, ExecutionPlanResult
from modules.decision import DecisionResult, create_decision_engine

# Set up logging
logger = logging.getLogger(__name__)


@dataclass
class ActionResult:
    """Complete result of executing an action plan"""

    success: bool
    query: str
    strategy: str
    total_steps: int
    execution_time: float
    final_answer: str
    detailed_results: Dict[str, Any]
    tool_execution_log: List[str]
    error: Optional[str] = None


class FastMCPActionEngine:
    """
    Action execution engine that takes DecisionResult and executes the planned tools
    """

    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the action engine

        Args:
            config_path: Path to profiles.yaml config file (optional)
        """
        self.config_path = config_path or Path(__file__).parent.parent / "profiles.yaml"
        self.session = None
        self.executor = None
        self.logger = logging.getLogger(__name__)

    async def __aenter__(self):
        """Async context manager entry"""
        # Load configuration
        with open(self.config_path, "r") as f:
            config = yaml.safe_load(f)["mcp_client_config"]

        # Initialize session
        self.session = FastMCPSession(config)
        await self.session.__aenter__()

        # Create tool executor
        self.executor = await create_tool_executor(self.session)

        self.logger.info("✅ FastMCP Action Engine initialized")
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit"""
        if self.session:
            await self.session.__aexit__(exc_type, exc_val, exc_tb)
        self.logger.info("🔚 FastMCP Action Engine shutdown")

    def _format_tool_calls_for_execution(
        self, decision_result: DecisionResult
    ) -> List[Dict[str, Any]]:
        """
        Convert DecisionResult tool calls to executor format

        Args:
            decision_result: Decision result with tool call specifications

        Returns:
            List of tool call dictionaries for the executor
        """
        tool_calls = []

        for tc in decision_result.tool_calls:
            tool_call = {
                "tool_name": tc.tool_name,
                "parameters": tc.parameters,
                "step": tc.step,
                "dependency": tc.dependency,
                "purpose": tc.purpose,
                "result_variable": tc.result_variable,
            }
            tool_calls.append(tool_call)

        self.logger.info(f"📋 Formatted {len(tool_calls)} tool calls for execution")
        return tool_calls

    def _format_final_answer(
        self, decision_result: DecisionResult, execution_result: ExecutionPlanResult
    ) -> str:
        """
        Format the final answer based on execution results and decision strategy

        Args:
            decision_result: Original decision plan
            execution_result: Results of tool execution

        Returns:
            Formatted final answer string
        """
        if not execution_result.success:
            return f"❌ Execution failed: {execution_result.error}"

        # Single tool result - simple format
        if len(execution_result.tool_results) == 1:
            result = execution_result.tool_results[0]
            if result.success:
                return f"✅ {result.result}"
            else:
                return f"❌ {result.error}"

        # Multiple tools - format based on strategy
        strategy = str(decision_result.strategy).lower()

        if "parallel" in strategy:
            # Parallel results - show all results
            answer_parts = []
            for result in execution_result.tool_results:
                if result.success:
                    answer_parts.append(f"• {result.tool_name}: {result.result}")
                else:
                    answer_parts.append(f"• {result.tool_name}: ❌ {result.error}")
            return "📋 Results:\n" + "\n".join(answer_parts)

        elif "sequential" in strategy:
            # Sequential results - show the final result or chain
            successful_results = [r for r in execution_result.tool_results if r.success]
            if successful_results:
                final_result = successful_results[-1]  # Last successful result
                return f"✅ Final result: {final_result.result}"
            else:
                return "❌ Sequential execution failed"

        elif "hybrid" in strategy:
            # Hybrid strategy - intelligent formatting
            if execution_result.final_result:
                if isinstance(execution_result.final_result, dict):
                    # Multiple results
                    answer_parts = []
                    for key, value in execution_result.final_result.items():
                        clean_key = key.replace("step_", "").replace("_", " ").title()
                        answer_parts.append(f"• {clean_key}: {value}")
                    return "📋 Combined Results:\n" + "\n".join(answer_parts)
                else:
                    return f"✅ {execution_result.final_result}"
            else:
                return "❌ Hybrid execution incomplete"

        else:
            # Default format
            if execution_result.final_result:
                return f"✅ {execution_result.final_result}"
            else:
                return "✅ Execution completed"

    async def execute_decision(
        self, query: str, decision_result: DecisionResult
    ) -> ActionResult:
        """
        Execute a decision plan and return formatted results

        Args:
            query: Original user query
            decision_result: Decision plan from decision engine

        Returns:
            ActionResult with execution details and formatted answer
        """
        start_time = asyncio.get_event_loop().time()

        try:
            self.logger.info(f"🚀 Executing action plan: {decision_result.strategy}")
            self.logger.info(f"📝 Query: {query}")
            self.logger.info(
                f"🔧 Tools: {[tc.tool_name for tc in decision_result.tool_calls]}"
            )

            # Format tool calls for execution
            tool_calls = self._format_tool_calls_for_execution(decision_result)

            # Execute the strategy
            execution_result = await self.executor.execute_strategy(
                str(decision_result.strategy), tool_calls
            )

            # Format final answer
            final_answer = self._format_final_answer(decision_result, execution_result)

            execution_time = asyncio.get_event_loop().time() - start_time

            # Create detailed results
            detailed_results = {
                "strategy_used": str(decision_result.strategy),
                "tools_executed": len(execution_result.tool_results),
                "successful_tools": sum(
                    1 for r in execution_result.tool_results if r.success
                ),
                "failed_tools": sum(
                    1 for r in execution_result.tool_results if not r.success
                ),
                "execution_sequence": decision_result.execution_sequence,
                "tool_results": [
                    {
                        "tool": r.tool_name,
                        "step": r.step,
                        "success": r.success,
                        "result": r.result if r.success else r.error,
                        "execution_time": r.execution_time,
                    }
                    for r in execution_result.tool_results
                ],
                "reasoning": decision_result.reasoning,
            }

            self.logger.info(f"✅ Action execution completed in {execution_time:.2f}s")

            return ActionResult(
                success=execution_result.success,
                query=query,
                strategy=str(decision_result.strategy),
                total_steps=decision_result.total_steps,
                execution_time=execution_time,
                final_answer=final_answer,
                detailed_results=detailed_results,
                tool_execution_log=execution_result.execution_log,
                error=execution_result.error,
            )

        except Exception as e:
            execution_time = asyncio.get_event_loop().time() - start_time
            error_msg = f"Action execution failed: {str(e)}"
            self.logger.error(f"❌ {error_msg}")

            return ActionResult(
                success=False,
                query=query,
                strategy=(
                    str(decision_result.strategy) if decision_result else "unknown"
                ),
                total_steps=0,
                execution_time=execution_time,
                final_answer=f"❌ Execution failed: {error_msg}",
                detailed_results={"error": error_msg},
                tool_execution_log=[error_msg],
                error=error_msg,
            )


def create_action_engine(config_path: Optional[str] = None) -> FastMCPActionEngine:
    """
    Factory function to create an action engine

    Args:
        config_path: Path to configuration file (optional)

    Returns:
        FastMCPActionEngine instance
    """
    return FastMCPActionEngine(config_path)


async def execute_query_full_pipeline(
    query: str, config_path: Optional[str] = None
) -> ActionResult:
    """
    Complete pipeline: Query -> Decision -> Action -> Result

    This is a convenience function that runs the complete pipeline:
    1. Create decision engine
    2. Analyze query to create decision plan
    3. Execute decision plan using action engine
    4. Return formatted results

    Args:
        query: User query to process
        config_path: Path to configuration file (optional)

    Returns:
        ActionResult with complete execution details
    """
    try:
        # Step 1: Create decision plan
        logger.info(f"🧠 Analyzing query: {query}")
        decision_engine = await create_decision_engine()
        decision_result = await decision_engine.analyze_decision(query, [])

        # Step 2: Execute decision plan
        logger.info(f"🎯 Executing plan: {decision_result.strategy}")
        async with create_action_engine(config_path) as action_engine:
            result = await action_engine.execute_decision(query, decision_result)

        return result

    except Exception as e:
        error_msg = f"Full pipeline execution failed: {str(e)}"
        logger.error(f"❌ {error_msg}")

        return ActionResult(
            success=False,
            query=query,
            strategy="pipeline_failed",
            total_steps=0,
            execution_time=0.0,
            final_answer=f"❌ {error_msg}",
            detailed_results={"error": error_msg},
            tool_execution_log=[error_msg],
            error=error_msg,
        )


async def execute_with_decision_result(
    query: str, decision_result: DecisionResult, config_path: Optional[str] = None
) -> ActionResult:
    """
    Execute action plan with pre-computed decision result

    This function allows you to execute an action plan when you already have
    a DecisionResult from a previous analysis. Useful when you want to:
    - Reuse decision analysis
    - Execute with modified decision parameters
    - Separate decision making from execution phases

    Args:
        query: Original user query
        decision_result: Pre-computed decision plan from decision engine
        config_path: Path to configuration file (optional)

    Returns:
        ActionResult with execution details and formatted answer
    """
    try:
        logger.info(
            f"🎯 Executing pre-computed decision plan: {decision_result.strategy}"
        )
        logger.info(f"📝 Query: {query}")
        logger.info(f"🔧 Tools: {[tc.tool_name for tc in decision_result.tool_calls]}")

        # Execute decision plan using action engine
        async with create_action_engine(config_path) as action_engine:
            result = await action_engine.execute_decision(query, decision_result)

        return result

    except Exception as e:
        error_msg = f"Decision execution failed: {str(e)}"
        logger.error(f"❌ {error_msg}")

        return ActionResult(
            success=False,
            query=query,
            strategy=str(decision_result.strategy) if decision_result else "unknown",
            total_steps=0,
            execution_time=0.0,
            final_answer=f"❌ {error_msg}",
            detailed_results={"error": error_msg},
            tool_execution_log=[error_msg],
            error=error_msg,
        )


# Example usage and testing
async def test_full_pipeline():
    """Test the full pipeline that does both decision and action"""
    print("🧪 Testing Full Pipeline (Decision + Action)")
    print("=" * 50)

    test_queries = [
        "What is 25 + 37?",
        "What is 5 factorial and 16 squared?",
        "Calculate sine of 1.5 and then square that result",
    ]

    for query in test_queries:
        print(f"\n🔍 Query: {query}")
        try:
            # Uses execute_query_full_pipeline which does both decision and action
            result = await execute_query_full_pipeline(query)
            print(f"✅ Success: {result.success}")
            print(f"🎯 Strategy: {result.strategy}")
            print(f"⏱️  Time: {result.execution_time:.2f}s")
            print(f"📝 Answer: {result.final_answer}")

        except Exception as e:
            print(f"❌ Error: {e}")


async def test_with_handcoded_decision():
    """Test using handcoded decision result with execute_with_decision_result"""
    print("\n🧪 Testing Handcoded Decision Result")
    print("=" * 50)

    # Import decision types for handcoding
    from modules.decision import ToolCall, ExecutionStrategy

    # Handcode a simple decision result for "What is 25 + 37?"
    query = "What is 25 + 37?"

    # Create a handcoded decision result
    handcoded_decision = DecisionResult(
        strategy=ExecutionStrategy.SINGLE_TOOL,
        total_steps=1,
        tool_calls=[
            ToolCall(
                step=1,
                tool_name="calculator_add",
                parameters={"input": {"a": 25, "b": 37}},
                dependency="none",
                purpose="Add 25 and 37 together",
                result_variable="add_result",
            )
        ],
        execution_sequence="Single step: execute add(25, 37)",
        final_result_processing="Return the sum directly as the final answer",
        reasoning="Simple addition operation requiring only the calculator add tool",
    )

    print(f"🔍 Query: {query}")
    print(f"🧠 Handcoded Strategy: {handcoded_decision.strategy}")
    print(
        f"🔧 Handcoded Tools: {[tc.tool_name for tc in handcoded_decision.tool_calls]}"
    )

    try:
        # Use execute_with_decision_result with handcoded decision
        result = await execute_with_decision_result(query, handcoded_decision)

        print(f"✅ Success: {result.success}")
        print(f"⏱️  Time: {result.execution_time:.2f}s")
        print(f"📝 Answer: {result.final_answer}")

    except Exception as e:
        print(f"❌ Error: {e}")


async def test_separated_decision_and_action():
    """Test separating decision making from action execution using LLM decision"""
    print("\n🧪 Testing Separated Decision and Action (LLM Decision)")
    print("=" * 60)

    query = "What is 25 + 37?"

    try:
        # Step 1: Create decision separately using LLM
        print(f"🧠 Step 1: Analyzing query: {query}")
        decision_engine = await create_decision_engine()
        decision_result = await decision_engine.analyze_decision(query, [])

        print(f"📋 Decision: {decision_result.strategy}")
        print(f"🔧 Tools: {[tc.tool_name for tc in decision_result.tool_calls]}")

        # Step 2: Execute with pre-computed decision using standalone function
        print("🎯 Step 2: Executing pre-computed decision...")
        result = await execute_with_decision_result(query, decision_result)

        print(f"✅ Success: {result.success}")
        print(f"⏱️  Time: {result.execution_time:.2f}s")
        print(f"📝 Answer: {result.final_answer}")

        # Step 3: Alternative - Use action engine directly
        print("🔄 Step 3: Alternative direct usage...")
        async with create_action_engine() as action_engine:
            direct_result = await action_engine.execute_decision(query, decision_result)
            print(f"✅ Direct Success: {direct_result.success}")
            print(f"📝 Direct Answer: {direct_result.final_answer}")

    except Exception as e:
        print(f"❌ Error: {e}")


async def main():
    """Run all tests"""
    await test_full_pipeline()
    await test_with_handcoded_decision()
    await test_separated_decision_and_action()


if __name__ == "__main__":
    asyncio.run(main())
