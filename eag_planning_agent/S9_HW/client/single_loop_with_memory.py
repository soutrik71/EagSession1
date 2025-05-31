"""
Enhanced Single Loop with Memory Agent

This script demonstrates the complete pipeline with individual step memory saving:
1. Run perception and save outcome
2. Run decision and save outcome
3. Run action and save outcome
4. Save final query-tool-outcome to vector database
"""

import logging
from modules.perception import create_perception_engine
from modules.decision import create_decision_engine
from modules.action import execute_with_decision_result
from modules.mem_agent import create_memory_agent
import asyncio
from datetime import datetime

# Configure logging to reduce verbosity from third-party libraries
logging.basicConfig(
    level=logging.INFO,
    format="%(message)s",  # Simple format for our logs
    handlers=[logging.StreamHandler()],
)

# Suppress verbose logs from third-party libraries
logging.getLogger("mcp.server.lowlevel.server").setLevel(logging.WARNING)
logging.getLogger("mcp.client.streamable_http").setLevel(logging.WARNING)
logging.getLogger("httpx").setLevel(logging.WARNING)
logging.getLogger("urllib3").setLevel(logging.WARNING)
logging.getLogger("openai").setLevel(logging.WARNING)
logging.getLogger("asyncio").setLevel(logging.WARNING)

# Keep our application logs at INFO level
logging.getLogger("modules.perception").setLevel(logging.INFO)
logging.getLogger("modules.decision").setLevel(logging.INFO)
logging.getLogger("modules.action").setLevel(logging.INFO)
logging.getLogger("modules.mem_agent").setLevel(logging.INFO)
logging.getLogger("core.session").setLevel(logging.INFO)
logging.getLogger("core.tool_call").setLevel(logging.INFO)

# Test queries with different complexity types: simple, sequential, parallel
test_queries = [
    # Simple questions (with followup relationship)
    "What is 15 + 25?",  # Simple 1
    "Now multiply that result by 3",  # Simple 2 (followup to Simple 1)
    # Sequential operations
    "What is 100 - 30 and then add 15 to that result?",  # Sequential
    # Parallel operations
    "What is 8 * 7 and what is 64 divided by 8?",  # Parallel
    # Additional complex question
    "Calculate the factorial of 5",  # Simple 3
]


def format_chat_history_from_memory(session_history, current_conversation_id):
    """
    Format chat history from memory for perception module.

    Args:
        session_history: Session history from memory agent
        current_conversation_id: Current conversation ID to exclude

    Returns:
        List of chat history dictionaries in perception module format
    """
    if not session_history or not session_history.get("conversations"):
        return []

    chat_history = []

    # Sort conversations by ID to ensure proper order
    conversations = sorted(
        session_history["conversations"], key=lambda x: x["conversation_id"]
    )

    for conv in conversations:
        # Skip current conversation
        if conv["conversation_id"] == current_conversation_id:
            continue

        # Only include conversations with both perception and action data
        if conv.get("perception") and conv.get("action"):
            enhanced_question = conv["perception"]["enhanced_question"]
            final_answer = conv["action"]["final_answer"]

            # Clean up final answer (remove emojis and extra formatting)
            clean_answer = final_answer.replace("✅", "").replace(
                "📋 Results:", "Results:"
            )
            clean_answer = clean_answer.strip()

            # Add human message
            chat_history.append({"sender": "human", "content": enhanced_question})

            # Add assistant response
            chat_history.append({"sender": "ai", "content": clean_answer})

    return chat_history


def get_chat_history_summary(chat_history):
    """
    Get a summary string of chat history for display purposes.

    Args:
        chat_history: List of chat history dictionaries

    Returns:
        Summary string
    """
    if not chat_history:
        return "No previous conversation history"

    conversation_count = (
        len(chat_history) // 2
    )  # Each conversation has human + ai message
    return f"{conversation_count} previous conversation(s)"


async def run_single_query_with_memory(
    query: str, session_id: str, conversation_id: str, memory_agent
):
    """
    Run a single query through the complete pipeline with individual step memory saving.
    """
    print(f"\n{'='*80}")
    print(f"🔄 Processing: '{query}'")
    print(f"📋 Session: {session_id}, Conversation: {conversation_id}")
    print(f"{'='*80}")

    # Retrieve chat history from memory for this session
    session_history = memory_agent.get_session_history(session_id)
    chat_history = format_chat_history_from_memory(session_history, conversation_id)

    chat_summary = get_chat_history_summary(chat_history)
    print(f"📚 {chat_summary}")

    try:
        # Step 1: Perception
        print("\n🧠 Step 1: Running Perception Engine...")
        perception_engine = await create_perception_engine()
        perception_result = await perception_engine.analyze_query(query, chat_history)

        # Save perception outcome immediately
        memory_agent.save_perception_outcome(
            session_id, conversation_id, query, perception_result
        )
        print(f"✅ Perception saved - Intent: {perception_result.intent}")
        print(
            f"🔧 Selected tools: {[tool.tool_name for tool in perception_result.selected_tools]}"
        )

        # Step 2: Decision
        print("\n🎯 Step 2: Running Decision Engine...")
        decision_engine = await create_decision_engine()
        decision_result = await decision_engine.analyze_decision_from_perception(
            perception_result
        )

        # Save decision outcome immediately
        memory_agent.save_decision_outcome(session_id, conversation_id, decision_result)
        print(f"✅ Decision saved - Strategy: {decision_result.strategy}")
        print(f"📋 Total steps: {decision_result.total_steps}")

        # Step 3: Action
        print("\n⚡ Step 3: Running Action Engine...")
        action_result = await execute_with_decision_result(query, decision_result)

        # Save action outcome immediately
        memory_agent.save_action_outcome(session_id, conversation_id, action_result)
        print(f"✅ Action saved - Success: {action_result.success}")
        print(f"📝 Final answer: {action_result.final_answer}")
        print(f"⏱️ Execution time: {action_result.execution_time:.2f}s")

        # Step 4: Save final query-tool outcome to vector DB
        print("\n📊 Step 4: Saving to Vector Database...")
        await memory_agent.save_final_query_tool_outcome(session_id, conversation_id)
        print("✅ Complete pipeline outcome saved to vector database")

        return {
            "perception": perception_result,
            "decision": decision_result,
            "action": action_result,
        }

    except Exception as e:
        print(f"❌ Pipeline failed: {e}")
        import traceback

        traceback.print_exc()
        return None


async def test_memory_recommendations():
    """Test memory-based recommendations for similar queries."""
    print(f"\n{'='*80}")
    print("🧠 Testing Memory-Based Recommendations")
    print(f"{'='*80}")

    memory_agent = await create_memory_agent()

    # Test queries similar to those already processed
    recommendation_tests = [
        "What is 34 + 45?",  # Similar to addition queries
        "Calculate 6 factorial",  # Similar to factorial query
        "What is the square root of 225?",  # Similar to sqrt query
        "What is 9 * 6 and 72 divided by 9?",  # Similar to multi-op query
    ]

    for query in recommendation_tests:
        print(f"\n🔍 Query: '{query}'")

        # Get similar pattern from memory
        similar_outcome = await memory_agent.get_similar_query_outcome(
            query, confidence_threshold=0.4
        )

        if similar_outcome:
            print(f"✅ Found similar pattern: '{similar_outcome['query']}'")
            print(f"🎯 Similarity score: {similar_outcome['similarity_score']:.3f}")
            print(f"🔧 Recommended tools: {similar_outcome['tools_used']}")
            print(f"📊 Strategy: {similar_outcome['strategy']}")
            print(f"✅ Past success: {similar_outcome['success']}")
            print(f"⏱️ Avg execution time: {similar_outcome['execution_time']:.2f}s")
        else:
            print("❌ No similar patterns found in memory")
            print("💡 This would be a new pattern to learn from")


async def main():
    """
    Enhanced single loop demo testing different query types:
    1. Simple questions (with followup relationship using chat history)
    2. Sequential operations (step-by-step dependent tasks)
    3. Parallel operations (independent simultaneous tasks)
    4. Complex single operations
    """
    session_id = f"demo_session_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    print("🚀 Enhanced Single Loop with Memory Agent Demo")
    print("=" * 80)
    print(f"📂 Session ID: {session_id}")
    print("\n🎯 Testing Different Query Types:")
    print("  1. Simple questions (with followup)")
    print("  2. Sequential operations")
    print("  3. Parallel operations")
    print("  4. Complex single operations")
    print("=" * 80)

    memory_agent = await create_memory_agent()

    # Process each query with detailed descriptions
    query_descriptions = [
        "Simple Addition",  # Query 1
        "Followup Multiplication (uses chat history)",  # Query 2
        "Sequential Math (subtract then add)",  # Query 3
        "Parallel Math (multiply and divide)",  # Query 4
        "Factorial Calculation",  # Query 5
    ]

    for i, (query, description) in enumerate(zip(test_queries, query_descriptions), 1):
        conversation_id = f"conv_{i:03d}"

        print(f"\n{'='*80}")
        print(f"🔄 Query {i}: {description}")
        print(f"❓ Question: '{query}'")
        print(f"📋 Session: {session_id}, Conversation: {conversation_id}")
        print("=" * 80)

        result = await run_single_query_with_memory(
            query, session_id, conversation_id, memory_agent
        )

        if result:
            print(f"✅ Query {i} completed successfully")
        else:
            print(f"❌ Query {i} failed")

    # Test memory-based recommendations
    await test_memory_recommendations()

    # Show session summary
    print(f"\n{'='*80}")
    print("📊 Session Summary")
    print(f"{'='*80}")

    session_history = memory_agent.get_session_history(session_id)
    print(f"📂 Session ID: {session_id}")

    # Handle case where no conversations were processed successfully
    if session_history and "total_conversations" in session_history:
        print(f"💬 Total conversations: {session_history['total_conversations']}")

        for conv in session_history["conversations"]:
            print(f"\n  🔹 {conv['conversation_id']}: {conv['query']}")
            if conv["perception"]:
                print(f"    🧠 Intent: {conv['perception']['intent']}")
                print(f"    🔧 Tools: {conv['perception']['selected_tools']}")
            if conv["decision"]:
                print(f"    🎯 Strategy: {conv['decision']['strategy']}")
            if conv["action"]:
                print(f"    ⚡ Success: {conv['action']['success']}")
                print(f"    ⏱️ Time: {conv['action']['execution_time']:.2f}s")
    else:
        print("💬 No conversations were successfully processed")
        print("⚠️ This may be due to configuration or server connectivity issues")

    # Analytics
    print("📈 Tool Usage Analytics:")
    for tool_name in [
        "calculator_add",
        "calculator_multiply",
        "calculator_factorial",
        "calculator_subtract",
    ]:
        analytics = memory_agent.get_tool_success_analytics(tool_name)
        if analytics["usage_count"] > 0:
            print(
                f"  🔧 {tool_name}: {analytics['usage_count']} uses, {analytics['success_rate']*100:.1f}% success"
            )

    print("\n✅ Demo completed successfully!")
    print("💾 Memory storage location: memory_storage/")
    print(f"📊 Vector patterns stored: {len(memory_agent.pattern_storage)}")


if __name__ == "__main__":
    asyncio.run(main())
