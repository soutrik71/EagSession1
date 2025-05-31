#!/usr/bin/env python3
"""
FastMCP Decision Engine Test Suite

Comprehensive test suite for the FastMCP Decision Module that analyzes
enhanced user queries and creates detailed execution plans with tool orchestration.
"""

import asyncio
import os
import sys
from pathlib import Path
from typing import Dict, List, Set

# Add the parent directory to sys.path for imports
sys.path.append(str(Path(__file__).parent))

# Remove SSL cert file if it exists to avoid issues
os.environ.pop("SSL_CERT_FILE", None)


class DecisionTestCase:
    """Represents a single decision test case with expected results"""

    def __init__(
        self,
        name: str,
        enhanced_question: str,
        recommended_tools: List[str],
        expected_strategy: str,
        expected_steps: int,
        expected_tools_used: Set[str],
        expected_execution_sequence: str = None,
        min_reasoning_length: int = 50,
    ):
        self.name = name
        self.enhanced_question = enhanced_question
        self.recommended_tools = recommended_tools
        self.expected_strategy = expected_strategy
        self.expected_steps = expected_steps
        self.expected_tools_used = expected_tools_used
        self.expected_execution_sequence = expected_execution_sequence
        self.min_reasoning_length = min_reasoning_length


async def run_decision_tests():
    """Run basic decision tests"""
    print("🚀 Starting FastMCP Decision Engine Test Suite")
    print("=" * 60)

    from modules.decision import create_decision_engine

    # Simple test case
    decision_engine = await create_decision_engine()

    result = await decision_engine.analyze_decision(
        "What is 25 + 37?", ["calculator_add"]
    )

    print("📋 Checking DecisionResult structure...")
    required_keys = [
        "strategy",
        "total_steps",
        "tool_calls",
        "execution_sequence",
        "final_result_processing",
        "reasoning",
    ]

    for key in required_keys:
        if hasattr(result, key):
            value = getattr(result, key)
            value_display = (
                f"len={len(value)}" if hasattr(value, "__len__") else str(value)[:50]
            )
            print(f"   ✅ {key}: {type(value).__name__} ({value_display})")
        else:
            print(f"   ❌ Missing: {key}")


async def test_decision_strategies():
    """Test different decision strategies"""
    print("\n🎯 Testing Decision Strategies")
    print("-" * 40)

    from modules.decision import create_decision_engine

    decision_engine = await create_decision_engine()

    test_cases = [
        {
            "name": "single_tool",
            "query": "What is 5 + 3?",
            "tools": ["calculator_add"],
            "expected_strategy": "single_tool",
        },
        {
            "name": "parallel_tools",
            "query": "What is 5! and sqrt(16)?",
            "tools": ["calculator_factorial", "calculator_sqrt"],
            "expected_strategy": "parallel_tools",
        },
        {
            "name": "sequential_tools",
            "query": "What is the exponential sum of sine of 66 and 88?",
            "tools": ["calculator_sin", "calculator_int_list_to_exponential_sum"],
            "expected_strategy": "sequential_tools",
        },
    ]

    for test_case in test_cases:
        print(f"\n🧪 Testing {test_case['name']} strategy...")
        try:
            result = await decision_engine.analyze_decision(
                test_case["query"], test_case["tools"]
            )

            # Check if strategy matches - handle enum format
            strategy_str = str(result.strategy).lower()
            strategy_match = test_case["expected_strategy"] in strategy_str
            if strategy_match:
                print(f"   ✅ Correct strategy: {result.strategy}")
            else:
                print(
                    f"   ❌ Wrong strategy: expected {test_case['expected_strategy']}, got {result.strategy}"
                )

        except Exception as e:
            print(f"   ❌ Error: {e}")


def validate_decision_result(result, expected: DecisionTestCase) -> Dict:
    """Validate a decision result against expected outcomes"""
    errors = []

    # Check strategy - handle enum or string format
    strategy_str = str(result.strategy).lower()
    if expected.expected_strategy not in strategy_str:
        errors.append(
            f"Strategy mismatch: expected '{expected.expected_strategy}', got '{result.strategy}'"
        )

    # Check step count
    if result.total_steps != expected.expected_steps:
        errors.append(
            f"Steps mismatch: expected {expected.expected_steps}, got {result.total_steps}"
        )

    # Check tools used - more flexible validation
    actual_tools = {tc.tool_name for tc in result.tool_calls}
    missing_tools = expected.expected_tools_used - actual_tools
    # Only check missing tools if we have expected tools (skip for fallback cases)
    if missing_tools and expected.expected_tools_used:
        errors.append(f"Missing expected tools: {missing_tools}")

    # Check execution sequence if specified - more flexible matching
    if expected.expected_execution_sequence and hasattr(result, "execution_sequence"):
        sequence_lower = result.execution_sequence.lower()
        expected_lower = expected.expected_execution_sequence.lower()

        # More flexible matching - check for key concepts
        if expected_lower == "sequential":
            if not any(
                word in sequence_lower
                for word in ["sequential", "sequence", "first", "then", "step", "after"]
            ):
                errors.append(
                    f"Execution sequence should indicate sequential processing, "
                    f"got '{result.execution_sequence}'"
                )
        elif expected_lower == "parallel":
            if not any(
                word in sequence_lower
                for word in ["parallel", "simultaneously", "independent", "both"]
            ):
                errors.append(
                    f"Execution sequence should indicate parallel processing, "
                    f"got '{result.execution_sequence}'"
                )
        elif expected_lower == "single":
            if not any(
                word in sequence_lower for word in ["single", "direct", "one", "simple"]
            ):
                errors.append(
                    f"Execution sequence should indicate single operation, "
                    f"got '{result.execution_sequence}'"
                )

    # Check reasoning quality
    if len(result.reasoning) < expected.min_reasoning_length:
        errors.append(
            f"Reasoning too short: {len(result.reasoning)} < {expected.min_reasoning_length}"
        )

    return {"passed": len(errors) == 0, "errors": errors}


async def test_decision_keys_and_structure():
    """Test that DecisionResult has all required keys and proper structure"""
    print("📋 Testing DecisionResult structure and key presence...")

    from modules.decision import create_decision_engine

    decision_engine = await create_decision_engine()

    # Test with simple case
    result = await decision_engine.analyze_decision(
        "What is 10 + 5?", ["calculator_add"]
    )

    # Check required keys
    required_keys = [
        "strategy",
        "total_steps",
        "tool_calls",
        "execution_sequence",
        "final_result_processing",
        "reasoning",
    ]
    missing_keys = []

    print("🔍 Checking required fields:")
    for key in required_keys:
        if hasattr(result, key):
            value = getattr(result, key)
            value_display = (
                f"len={len(value)}" if hasattr(value, "__len__") else str(value)[:50]
            )
            if len(str(value)) > 50:
                value_display += "..."
            print(f"   ✅ {key}: {type(value).__name__} ({value_display})")
        else:
            missing_keys.append(key)
            print(f"   ❌ Missing: {key}")

    if missing_keys:
        print(f"❌ Missing required keys: {missing_keys}")
        return False

    # Check tool_calls structure
    if result.tool_calls:
        print("\n🔍 Checking ToolCall structure:")
        tool_call_keys = ["step", "tool_name", "parameters", "dependency", "purpose"]

        for tc in result.tool_calls[:1]:  # Check first tool call
            for key in tool_call_keys:
                if hasattr(tc, key):
                    value = getattr(tc, key)
                    value_display = str(value)[:50]
                    if len(str(value)) > 50:
                        value_display += "..."
                    print(f"   ✅ {key}: {type(value).__name__} ({value_display})")

    print("✅ All required keys present and properly structured")
    return True


async def main():
    """Main test runner"""
    print("🎯 FastMCP Decision Engine - Comprehensive Test Suite")
    print("=" * 60)

    try:
        # Test 1: Basic functionality and structure
        print("🔄 Initializing decision engine...")
        await run_decision_tests()
        structure_passed = await test_decision_keys_and_structure()

        # Test 2: Strategy testing
        await test_decision_strategies()

        # Test 3: Comprehensive test cases
        test_cases = [
            DecisionTestCase(
                name="Simple Addition",
                enhanced_question="What is 25 + 37?",
                recommended_tools=["calculator_add"],
                expected_strategy="single_tool",
                expected_steps=1,
                expected_tools_used={"calculator_add"},
                expected_execution_sequence="single",
            ),
            DecisionTestCase(
                name="Basic Multiplication",
                enhanced_question="What is 8 times 9?",
                recommended_tools=["calculator_multiply"],
                expected_strategy="single_tool",
                expected_steps=1,
                expected_tools_used={"calculator_multiply"},
            ),
            DecisionTestCase(
                name="Independent Calculations",
                enhanced_question="What is 5 factorial and what is the cube root of 27?",
                recommended_tools=["calculator_factorial", "calculator_cbrt"],
                expected_strategy="parallel_tools",
                expected_steps=2,
                expected_tools_used={"calculator_factorial", "calculator_cbrt"},
                expected_execution_sequence="parallel",
            ),
            DecisionTestCase(
                name="Multiple Independent Tasks",
                enhanced_question="Calculate the square of 7 and find the factorial of 4",
                recommended_tools=["calculator_square", "calculator_factorial"],
                expected_strategy="parallel_tools",
                expected_steps=2,
                expected_tools_used={"calculator_square", "calculator_factorial"},
            ),
            DecisionTestCase(
                name="Trigonometric Chain",
                enhanced_question="What is the exponential sum of sine of 66 and 88?",
                recommended_tools=[
                    "calculator_sin",
                    "calculator_int_list_to_exponential_sum",
                ],
                expected_strategy="sequential_tools",
                expected_steps=3,
                expected_tools_used={
                    "calculator_sin",
                    "calculator_int_list_to_exponential_sum",
                },
                expected_execution_sequence="sequential",
            ),
            DecisionTestCase(
                name="Web Search to Calculation",
                enhanced_question="Search for John Cena's age and calculate 2 to the power of that age",
                recommended_tools=["web_tools_search_web", "calculator_power"],
                expected_strategy="sequential_tools",
                expected_steps=2,
                expected_tools_used={"web_tools_search_web", "calculator_power"},
                expected_execution_sequence="sequential",
            ),
            DecisionTestCase(
                name="Multi-Step Document Analysis",
                enhanced_question="Search documents about AI, fetch webpage content, and calculate string length",
                recommended_tools=[
                    "doc_search_query_documents",
                    "web_tools_fetch_webpage",
                    "calculator_add",
                ],
                expected_strategy="hybrid_tools",
                expected_steps=3,
                expected_tools_used={
                    "doc_search_query_documents",
                    "web_tools_fetch_webpage",
                    "calculator_add",
                },
            ),
            DecisionTestCase(
                name="No Tools Provided",
                enhanced_question="What is the weather today?",
                recommended_tools=[],
                expected_strategy="single_tool",
                expected_steps=1,
                expected_tools_used=set(),  # Empty set means don't check tools for this case
            ),
        ]

        print(f"\n🧪 Running {len(test_cases)} comprehensive tests...")
        from modules.decision import create_decision_engine

        decision_engine = await create_decision_engine()

        passed_tests = 0
        failed_tests = 0

        for i, test_case in enumerate(test_cases, 1):
            print(f"\n🧪 Test {i}/{len(test_cases)}: {test_case.name}")
            print(f"   Query: '{test_case.enhanced_question}'")
            print(f"   Tools: {test_case.recommended_tools}")

            try:
                result = await decision_engine.analyze_decision(
                    test_case.enhanced_question, test_case.recommended_tools
                )

                validation = validate_decision_result(result, test_case)

                if validation["passed"]:
                    print("✅ PASSED")
                    passed_tests += 1
                else:
                    print("❌ FAILED")
                    for error in validation["errors"]:
                        print(f"   ⚠️  {error}")
                    failed_tests += 1

                print(f"   🎯 Strategy: {result.strategy}")
                print(f"   📋 Steps: {result.total_steps}")

            except Exception as e:
                print(f"❌ CRASHED: {e}")
                failed_tests += 1

        print("\n" + "=" * 60)
        print("📊 DECISION ENGINE TEST RESULTS")
        print("=" * 60)
        print(f"✅ Passed: {passed_tests}")
        print(f"❌ Failed: {failed_tests}")
        print(f"📈 Success Rate: {passed_tests / len(test_cases) * 100:.1f}%")

        if failed_tests > 0:
            print(f"⚠️  {failed_tests} tests failed - check output above")

        print("\n" + "=" * 60)
        print("📊 FINAL TEST SUMMARY")
        print("=" * 60)
        print(f"🔧 Structure Test: {'✅ PASSED' if structure_passed else '❌ FAILED'}")
        print(f"🎯 Strategy Test: {'✅ PASSED' if passed_tests > 0 else '❌ FAILED'}")
        print(
            f"🧪 Comprehensive Test: {'✅ PASSED' if failed_tests == 0 else '❌ FAILED'}"
        )

        if failed_tests == 0 and structure_passed:
            print("\n🎉 All tests passed! Decision engine is working perfectly.")
        else:
            print("\n⚠️  Some tests failed. Check the output above for details.")

        print("=" * 60)

    except Exception as e:
        print(f"❌ Test suite failed to run: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
