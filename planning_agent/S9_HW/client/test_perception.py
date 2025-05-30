#!/usr/bin/env python3
"""
Fast Ground Truth Test Suite for FastMCP Perception Engine

Tests only essential tools and validates against expected ground truth results.
Focuses on speed and accuracy validation rather than comprehensive coverage.
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


class GroundTruthTest:
    """Represents a single ground truth test case"""

    def __init__(
        self,
        name: str,
        query: str,
        expected_servers: Set[str],
        expected_tools: Set[str],
        expected_intent: str = None,
        chat_history: List[Dict] = None,
    ):
        self.name = name
        self.query = query
        self.expected_servers = expected_servers
        self.expected_tools = expected_tools
        self.expected_intent = expected_intent
        self.chat_history = chat_history or []


# Ground Truth Test Cases - Focus on key functionality
GROUND_TRUTH_TESTS = [
    # Calculator Server Tests (2 key tools)
    GroundTruthTest(
        name="Basic Addition",
        query="What is 15 plus 25?",
        expected_servers={"calculator"},
        expected_tools={"calculator_add"},
        expected_intent="mathematical_calculation",
    ),
    GroundTruthTest(
        name="Power Calculation",
        query="Calculate 2 to the power of 8",
        expected_servers={"calculator"},
        expected_tools={"calculator_power"},
        expected_intent="mathematical_calculation",
    ),
    # Web Tools Server Tests (2 key tools)
    GroundTruthTest(
        name="Web Search",
        query="Search for Python programming tutorials",
        expected_servers={"web_tools"},
        expected_tools={"web_tools_search_web"},
        expected_intent="web_search",
    ),
    GroundTruthTest(
        name="Fetch Webpage",
        query="Fetch content from https://example.com",
        expected_servers={"web_tools"},
        expected_tools={"web_tools_fetch_webpage"},
        expected_intent="web_content_retrieval",
    ),
    # Document Search Server Tests (1 key tool)
    GroundTruthTest(
        name="Document Query",
        query="Find documents about machine learning",
        expected_servers={"doc_search"},
        expected_tools={"doc_search_query_documents"},
        expected_intent="document_search",
    ),
    # Multi-server Tests
    GroundTruthTest(
        name="Multi-Server Query",
        query="Search web for Python info and calculate 5 factorial",
        expected_servers={"web_tools", "calculator"},
        expected_tools={"web_tools_search_web", "calculator_factorial"},
        expected_intent="multi_task",
    ),
    # Context-Aware Test
    GroundTruthTest(
        name="Context Enhancement",
        query="Now multiply that by 2",
        expected_servers={"calculator"},
        expected_tools={"calculator_multiply"},
        expected_intent="mathematical_calculation",
        chat_history=[
            {"role": "user", "content": "What is 15 + 25?"},
            {"role": "assistant", "content": "15 + 25 = 40"},
        ],
    ),
]


async def run_ground_truth_tests():
    """Run focused ground truth tests"""
    print("🎯 FastMCP Perception Engine - Ground Truth Test Suite")
    print("=" * 60)

    try:
        from modules.perception import FastMCPPerception

        # Create perception engine once
        print("🔄 Initializing perception engine...")
        engine = FastMCPPerception()
        print("✅ Perception engine ready")

        passed = 0
        failed = 0

        for i, test in enumerate(GROUND_TRUTH_TESTS, 1):
            print(f"\n🧪 Test {i}/{len(GROUND_TRUTH_TESTS)}: {test.name}")
            print(f"   Query: '{test.query}'")

            try:
                # Run perception analysis
                result = await engine.analyze_query(test.query, test.chat_history)

                # Validate results against ground truth
                validation_results = validate_ground_truth(result, test)

                if validation_results["passed"]:
                    print("✅ PASSED")
                    passed += 1
                else:
                    print("❌ FAILED")
                    for error in validation_results["errors"]:
                        print(f"   ⚠️  {error}")
                    failed += 1

                # Show key results
                print(f"   🎯 Servers: {result.selected_servers}")
                print(f"   🔧 Tools: {[t.tool_name for t in result.selected_tools]}")

            except Exception as e:
                print(f"❌ CRASHED: {e}")
                failed += 1

        # Summary
        print("\n" + "=" * 60)
        print("📊 GROUND TRUTH TEST RESULTS")
        print("=" * 60)
        print(f"✅ Passed: {passed}")
        print(f"❌ Failed: {failed}")
        print(f"📈 Success Rate: {passed/(passed+failed)*100:.1f}%")

        if failed == 0:
            print("🏆 ALL GROUND TRUTH TESTS PASSED!")
        else:
            print(f"⚠️  {failed} tests failed - check output above")

        return passed == len(GROUND_TRUTH_TESTS)

    except ConnectionError as e:
        print(f"❌ Server connection failed: {e}")
        print("\n🚀 Please start the MCP servers:")
        print("   python server/server1_stream.py")
        print("   python server/server2_stream.py")
        print("   python server/server3_stream.py")
        return False
    except Exception as e:
        print(f"❌ Test setup failed: {e}")
        import traceback

        traceback.print_exc()
        return False


def validate_ground_truth(result, expected: GroundTruthTest) -> Dict:
    """
    Validate perception result against ground truth expectations

    Returns:
        Dict with 'passed' bool and 'errors' list
    """
    errors = []

    # Check servers (most important)
    actual_servers = set(result.selected_servers)
    if not expected.expected_servers.issubset(actual_servers):
        missing = expected.expected_servers - actual_servers
        errors.append(f"Missing servers: {missing}")

    # Check tools (most important)
    actual_tools = set(t.tool_name for t in result.selected_tools)
    if not expected.expected_tools.issubset(actual_tools):
        missing = expected.expected_tools - actual_tools
        errors.append(f"Missing tools: {missing}")

    # Check intent with semantic flexibility (less critical)
    if expected.expected_intent:
        intent_passed = _check_intent_semantic_match(
            result.intent, expected.expected_intent
        )
        if not intent_passed:
            # Only warn, don't fail the test for intent mismatches
            print(
                f"   ℹ️  Intent variation: expected '{expected.expected_intent}', got '{result.intent}' (acceptable)"
            )

    # Check enhanced question for context tests
    if expected.chat_history and "that" in expected.query.lower():
        if (
            "40" not in result.enhanced_question
            and "result" not in result.enhanced_question.lower()
        ):
            errors.append("Context not properly incorporated in enhanced question")

    return {"passed": len(errors) == 0, "errors": errors}


def _check_intent_semantic_match(actual_intent: str, expected_intent: str) -> bool:
    """
    Check if intents are semantically equivalent

    Returns:
        True if intents match semantically
    """
    # Normalize intents for comparison
    actual = actual_intent.lower().replace("_", " ")
    expected = expected_intent.lower().replace("_", " ")

    # Define semantic equivalents
    semantic_groups = [
        {"mathematical calculation", "math calculation", "calculation", "mathematical"},
        {"web search", "search", "web query"},
        {
            "web content retrieval",
            "web content extraction",
            "content retrieval",
            "content extraction",
        },
        {"document search", "document retrieval", "document query", "doc search"},
        {"multi task", "combined task", "multiple task", "multi operation"},
    ]

    # Check if both intents belong to the same semantic group
    for group in semantic_groups:
        if any(term in actual for term in group) and any(
            term in expected for term in group
        ):
            return True

    # Exact match fallback
    return actual == expected


async def quick_server_test():
    """Quick test to verify servers are accessible"""
    print("\n🔍 Quick Server Connectivity Test")
    print("-" * 40)

    try:
        from tool_utils import get_server_tools_tuples

        tools_info = await get_server_tools_tuples()

        if not tools_info:
            print("❌ No tools found - servers may be down")
            return False

        servers = set(server for server, _, _ in tools_info)
        print(f"✅ Connected to {len(servers)} servers: {servers}")

        # Check we have the essential tools
        tool_names = set(name for _, name, _ in tools_info)
        essential_tools = {
            "calculator_add",
            "calculator_power",
            "web_tools_search_web",
            "web_tools_fetch_webpage",
            "doc_search_query_documents",
        }

        missing = essential_tools - tool_names
        if missing:
            print(f"⚠️  Missing essential tools: {missing}")
            return False

        print(f"✅ All {len(essential_tools)} essential tools available")
        return True

    except Exception as e:
        print(f"❌ Server test failed: {e}")
        return False


async def main():
    """Main test runner"""
    # Quick server check first
    server_ok = await quick_server_test()
    if not server_ok:
        print("\n🚀 Please start MCP servers and try again")
        return

    # Run ground truth tests
    success = await run_ground_truth_tests()

    print("\n" + "=" * 60)
    if success:
        print(
            "🎉 All ground truth tests passed! Perception engine is working correctly."
        )
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
    print("=" * 60)


if __name__ == "__main__":
    asyncio.run(main())
