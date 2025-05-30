#!/usr/bin/env python3
"""
FastMCP Action Engine Test Suite - Optimized

Streamlined testing of the complete pipeline:
Query -> Decision -> Action -> Result
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
from modules.action import execute_query_full_pipeline
from modules.decision import create_decision_engine


class OptimizedActionEngineTests:
    """Streamlined test suite focusing on essential functionality"""

    def __init__(self):
        self.decision_engine = None

        # Essential test cases covering all strategies
        self.test_cases = [
            # Single Tool Strategy
            {
                "name": "Single Tool",
                "query": "What is 42 + 18?",
                "strategy": "single_tool",
                "description": "Basic arithmetic operation",
            },
            # Parallel Tools Strategy
            {
                "name": "Parallel Tools",
                "query": "What is 6 factorial and what is 15 squared?",
                "strategy": "parallel_tools",
                "description": "Independent calculations in parallel",
            },
            # Sequential Tools Strategy
            {
                "name": "Sequential Tools",
                "query": "Calculate sine of 1.0 and then square that result",
                "strategy": "sequential_tools",
                "description": "Dependent chain with variable passing",
            },
        ]

    async def initialize(self):
        """Initialize shared resources once"""
        print("🔧 Initializing test environment...")
        self.decision_engine = await create_decision_engine()
        print("✅ Test environment ready\n")

    async def test_strategy_detection(self):
        """Test strategy detection accuracy"""
        print("🧠 Testing Strategy Detection")
        print("-" * 35)

        all_correct = True
        for i, test in enumerate(self.test_cases, 1):
            try:
                decision = await self.decision_engine.analyze_decision(
                    test["query"], []
                )
                detected = str(decision.strategy).lower()
                expected = test["strategy"]

                is_correct = expected in detected
                status = "✅" if is_correct else "❌"

                print(f"{status} Test {i}: {test['name']}")
                print(f"   Query: {test['query']}")
                print(f"   Expected: {expected} | Detected: {detected}")
                print(f"   Tools: {[tc.tool_name for tc in decision.tool_calls]}")

                if not is_correct:
                    all_correct = False

            except Exception as e:
                print(f"❌ Test {i} failed: {e}")
                all_correct = False

            print()

        print(
            f"📊 Strategy Detection: {'✅ All Passed' if all_correct else '❌ Some Failed'}\n"
        )
        return all_correct

    async def test_full_execution(self):
        """Test complete pipeline execution"""
        print("🚀 Testing Full Pipeline Execution")
        print("-" * 40)

        all_successful = True
        total_time = 0

        for i, test in enumerate(self.test_cases, 1):
            try:
                print(f"🔍 Test {i}: {test['name']}")
                print(f"   Query: {test['query']}")

                # Execute the full pipeline
                result = await execute_query_full_pipeline(test["query"])

                # Track results
                success_status = "✅" if result.success else "❌"
                total_time += result.execution_time

                print(f"   {success_status} Success: {result.success}")
                print(f"   ⏱️  Time: {result.execution_time:.2f}s")
                print(f"   🎯 Strategy: {result.strategy}")

                # Show concise result
                if result.success:
                    if "Results:" in result.final_answer:
                        # Multiple results (parallel)
                        print(f"   📝 Results: Multiple tool outputs")
                    else:
                        # Single result
                        answer = result.final_answer.replace("✅ ", "").replace(
                            "\n", " "
                        )
                        if len(answer) > 60:
                            answer = answer[:57] + "..."
                        print(f"   📝 Answer: {answer}")
                else:
                    print(f"   ❌ Error: {result.error}")
                    all_successful = False

            except Exception as e:
                print(f"   ❌ Pipeline Error: {str(e)[:100]}...")
                all_successful = False

            print()

        avg_time = total_time / len(self.test_cases) if self.test_cases else 0
        print(f"📊 Execution Summary:")
        print(f"   Success Rate: {'100%' if all_successful else 'Some Failed'}")
        print(f"   Average Time: {avg_time:.2f}s")
        print(f"   Total Time: {total_time:.2f}s\n")

        return all_successful

    async def run_optimized_tests(self):
        """Run the complete optimized test suite"""
        print("🎯 FastMCP Action Engine - Optimized Test Suite")
        print("=" * 55)
        print("📋 Testing 3 core execution strategies with real tool calls")
        print("⚠️  Requires MCP servers running on ports 4201-4203\n")

        # Initialize once
        await self.initialize()

        # Run focused tests
        strategy_success = await self.test_strategy_detection()
        execution_success = await self.test_full_execution()

        # Final summary
        print("🏁 Test Suite Results")
        print("=" * 25)
        overall_success = strategy_success and execution_success

        print(
            f"🧠 Strategy Detection: {'✅ PASSED' if strategy_success else '❌ FAILED'}"
        )
        print(
            f"🚀 Pipeline Execution: {'✅ PASSED' if execution_success else '❌ FAILED'}"
        )
        print(
            f"🎯 Overall Status: {'✅ ALL TESTS PASSED' if overall_success else '❌ SOME TESTS FAILED'}"
        )

        if overall_success:
            print("\n🎉 FastMCP Action Engine is fully operational!")
        else:
            print("\n⚠️  Some issues detected - check logs above")

        return overall_success


async def main():
    """Optimized main test runner"""
    test_suite = OptimizedActionEngineTests()
    success = await test_suite.run_optimized_tests()
    return success


if __name__ == "__main__":
    asyncio.run(main())
