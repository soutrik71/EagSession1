#!/usr/bin/env python3
"""
FastMCP Action Engine Test Suite

This script demonstrates the complete pipeline:
Query -> Decision -> Action -> Result

It tests all execution strategies with actual tool calls
and shows how the system handles different types of queries.
"""

import asyncio
import os
import sys
from pathlib import Path

# Fix SSL cert issue for local testing
os.environ.pop("SSL_CERT_FILE", None)

# Add project root to path
sys.path.append(str(Path(__file__).parent))

# Import our modules
from modules.action import create_action_engine, execute_query_full_pipeline
from modules.decision import create_decision_engine


class ActionEngineTestSuite:
    """Comprehensive test suite for the action engine"""

    def __init__(self):
        self.test_cases = [
            {
                "name": "Single Tool - Simple Addition",
                "query": "What is 25 + 37?",
                "expected_strategy": "single_tool",
                "expected_tools": ["calculator_add"],
                "description": "Basic arithmetic operation requiring one tool",
            },
            {
                "name": "Parallel Tools - Independent Calculations",
                "query": "What is 5 factorial and what is 16 squared?",
                "expected_strategy": "parallel_tools",
                "expected_tools": ["calculator_factorial", "calculator_square"],
                "description": "Two independent calculations that can run in parallel",
            },
            {
                "name": "Sequential Tools - Dependent Chain",
                "query": "Calculate sine of 1.57 and then square that result",
                "expected_strategy": "sequential_tools",
                "expected_tools": ["calculator_sin", "calculator_square"],
                "description": "Chain of calculations where second depends on first",
            },
            {
                "name": "Complex Query - Mixed Operations",
                "query": "What is the square of 8, and also calculate 10 + 15 and then multiply those two results",
                "expected_strategy": "hybrid_tools",
                "expected_tools": [
                    "calculator_square",
                    "calculator_add",
                    "calculator_multiply",
                ],
                "description": "Complex query requiring hybrid execution strategy",
            },
        ]

    async def test_decision_to_action_pipeline(self):
        """Test the complete decision -> action pipeline"""
        print("🧪 Testing Decision -> Action Pipeline")
        print("=" * 50)

        decision_engine = await create_decision_engine()

        for i, test_case in enumerate(self.test_cases, 1):
            print(f"\n📋 Test Case {i}: {test_case['name']}")
            print(f"🔍 Query: {test_case['query']}")
            print(f"📖 Description: {test_case['description']}")

            try:
                # Step 1: Create decision
                print("🧠 Creating decision plan...")
                decision_result = await decision_engine.analyze_decision(
                    test_case["query"], test_case["expected_tools"]
                )

                print(f"  ✅ Strategy: {decision_result.strategy}")
                print(
                    f"  🔧 Tools: {[tc.tool_name for tc in decision_result.tool_calls]}"
                )
                print(f"  📝 Steps: {decision_result.total_steps}")

                # Step 2: Execute action (will be tested separately)
                print("  ⏳ (Action execution will be tested with servers)")

            except Exception as e:
                print(f"  ❌ Error: {e}")

    async def test_full_pipeline_with_servers(self):
        """Test the complete pipeline with actual server calls"""
        print("\n🚀 Testing Full Pipeline (Decision + Action)")
        print("=" * 50)
        print("⚠️  Note: This requires MCP servers to be running on ports 4201-4203")

        # Simple test cases that should work with basic servers
        simple_tests = [
            {"query": "What is 10 + 5?", "description": "Simple addition"},
            {"query": "What is 7 * 8?", "description": "Simple multiplication"},
        ]

        for test in simple_tests:
            print(f"\n🔍 Query: {test['query']}")
            print(f"📖 {test['description']}")

            try:
                result = await execute_query_full_pipeline(test["query"])

                print(f"✅ Success: {result.success}")
                print(f"🎯 Strategy: {result.strategy}")
                print(f"⏱️  Execution Time: {result.execution_time:.2f}s")
                print(f"📝 Final Answer: {result.final_answer}")

                if result.detailed_results:
                    print(
                        f"🔧 Tools Executed: {result.detailed_results.get('tools_executed', 0)}"
                    )
                    print(
                        f"✅ Successful: {result.detailed_results.get('successful_tools', 0)}"
                    )
                    if result.detailed_results.get("failed_tools", 0) > 0:
                        print(
                            f"❌ Failed: {result.detailed_results.get('failed_tools', 0)}"
                        )

            except Exception as e:
                print(f"❌ Pipeline Error: {e}")
                print("💡 Make sure MCP servers are running")

    async def test_action_engine_context_manager(self):
        """Test the action engine as a context manager"""
        print("\n🔧 Testing Action Engine Context Manager")
        print("=" * 45)

        try:
            from modules.decision import DecisionResult, ExecutionStrategy, ToolCall

            # Create a simple decision result manually
            test_decision = DecisionResult(
                strategy=ExecutionStrategy.SINGLE_TOOL,
                total_steps=1,
                tool_calls=[
                    ToolCall(
                        step=1,
                        tool_name="calculator_add",
                        parameters={"input": {"a": 15, "b": 25}},
                        dependency="none",
                        purpose="Add two numbers",
                    )
                ],
                execution_sequence="Single direct calculation",
                final_result_processing="Return numeric result",
                reasoning="Simple arithmetic operation",
            )

            print("📋 Testing with manually created decision:")
            print(f"  Strategy: {test_decision.strategy}")
            print(f"  Tool: {test_decision.tool_calls[0].tool_name}")
            print(f"  Parameters: {test_decision.tool_calls[0].parameters}")

            async with create_action_engine() as action_engine:
                print("✅ Action engine initialized successfully")

                result = await action_engine.execute_decision(
                    "What is 15 + 25?", test_decision
                )

                print(f"✅ Execution completed: {result.success}")
                print(f"📝 Answer: {result.final_answer}")

        except Exception as e:
            print(f"❌ Context manager test failed: {e}")
            print("💡 This is expected if servers are not running")

    async def test_execution_strategies(self):
        """Test different execution strategies in detail"""
        print("\n🎯 Testing Execution Strategies")
        print("=" * 40)

        strategy_tests = [
            {
                "name": "Single Tool Strategy",
                "query": "What is the square of 9?",
                "expected_tools": 1,
                "description": "One tool execution",
            },
            {
                "name": "Parallel Strategy Simulation",
                "query": "What is 5 factorial and 4 squared?",
                "expected_tools": 2,
                "description": "Independent parallel tools",
            },
            {
                "name": "Sequential Strategy Simulation",
                "query": "Calculate sine of 0.5 and then find its square",
                "expected_tools": 2,
                "description": "Dependent sequential tools",
            },
        ]

        decision_engine = await create_decision_engine()

        for test in strategy_tests:
            print(f"\n🧪 {test['name']}")
            print(f"🔍 Query: {test['query']}")

            try:
                # Just test decision making (action will need servers)
                decision = await decision_engine.analyze_decision(test["query"], [])

                print(f"  📊 Strategy: {decision.strategy}")
                print(
                    f"  🔢 Expected Tools: {test['expected_tools']}, Got: {len(decision.tool_calls)}"
                )
                print(f"  📝 Execution Sequence: {decision.execution_sequence[:100]}...")

                # Validate strategy selection
                strategy_str = str(decision.strategy).lower()
                if "single" in test["name"].lower() and "single" in strategy_str:
                    print("  ✅ Strategy correctly identified as single_tool")
                elif "parallel" in test["name"].lower() and "parallel" in strategy_str:
                    print("  ✅ Strategy correctly identified as parallel_tools")
                elif (
                    "sequential" in test["name"].lower()
                    and "sequential" in strategy_str
                ):
                    print("  ✅ Strategy correctly identified as sequential_tools")
                else:
                    print(
                        f"  ⚠️  Strategy detection: expected pattern for {test['name']}, got {decision.strategy}"
                    )

            except Exception as e:
                print(f"  ❌ Error: {e}")

    async def display_system_architecture(self):
        """Display the system architecture and flow"""
        print("\n🏗️  FastMCP Action Engine Architecture")
        print("=" * 45)
        print(
            """
        ┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
        │   User Query    │───▶│ Decision Engine │───▶│  Action Engine  │
        │  "What is 5+3?" │    │                 │    │                 │
        └─────────────────┘    └─────────────────┘    └─────────────────┘
                                        │                       │
                                        ▼                       ▼
                               ┌─────────────────┐    ┌─────────────────┐
                               │ DecisionResult  │    │ ToolCallExecutor│
                               │ • Strategy      │    │ • Single        │
                               │ • Tool Calls    │    │ • Parallel      │
                               │ • Dependencies  │    │ • Sequential    │
                               │ • Reasoning     │    │ • Hybrid        │
                               └─────────────────┘    └─────────────────┘
                                                               │
                                                               ▼
                                                    ┌─────────────────┐
                                                    │ FastMCP Session │
                                                    │ • Server 1      │
                                                    │ • Server 2      │
                                                    │ • Server 3      │
                                                    └─────────────────┘
        """
        )
        print("🔄 Execution Flow:")
        print("  1. Query Analysis → Decision Creation")
        print("  2. Strategy Selection → Tool Planning")
        print("  3. Execution Strategy → Tool Calling")
        print("  4. Result Processing → Final Answer")

    async def run_all_tests(self):
        """Run the complete test suite"""
        print("🎯 FastMCP Action Engine - Complete Test Suite")
        print("=" * 60)

        await self.display_system_architecture()
        await self.test_decision_to_action_pipeline()
        await self.test_execution_strategies()
        await self.test_action_engine_context_manager()
        await self.test_full_pipeline_with_servers()

        print("\n🏁 Test Suite Complete!")
        print("=" * 30)
        print("💡 To test with actual tool execution:")
        print("   1. Start servers: python server/server{1,2,3}_stream.py")
        print("   2. Run: python test_action_engine.py")
        print("   3. Check the full pipeline tests for actual results")


async def main():
    """Main test runner"""
    test_suite = ActionEngineTestSuite()
    await test_suite.run_all_tests()


if __name__ == "__main__":
    asyncio.run(main())
