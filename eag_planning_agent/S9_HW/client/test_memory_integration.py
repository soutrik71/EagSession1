"""
Memory Agent Demo - Understanding How mem_agent.py Works Under the Hood

This simplified test demonstrates:
1. Individual step saving (perception, decision, action)
2. Conversation history storage and retrieval
3. Vector database storage and similarity search
4. Detailed output showing internal workings
"""

import asyncio
import logging
import sys
from pathlib import Path
import json

# Add parent directory for imports
sys.path.append(str(Path(__file__).parent))

# Import pipeline components
from modules.perception import create_perception_engine
from modules.decision import create_decision_engine
from modules.action import execute_with_decision_result
from modules.mem_agent import create_memory_agent

# Import the new chat history functions from single_loop_with_memory
from single_loop_with_memory import (
    format_chat_history_from_memory,
    get_chat_history_summary,
)

# Set up logging
logging.basicConfig(level=logging.INFO)


def print_section(title):
    """Print a formatted section header."""
    print(f"\n{'='*80}")
    print(f"🔍 {title}")
    print(f"{'='*80}")


def print_subsection(title):
    """Print a formatted subsection header."""
    print(f"\n{'-'*60}")
    print(f"📋 {title}")
    print(f"{'-'*60}")


async def run_pipeline_with_detailed_memory_demo(
    session_id: str, conversation_id: str, query: str, memory_agent
):
    """
    Run pipeline with detailed output showing memory operations.
    """
    print_section(f"Processing Query: '{query}'")
    print(f"📋 Session: {session_id}, Conversation: {conversation_id}")

    # Show chat history retrieval process
    print_subsection("Chat History Retrieval Process")
    session_history = memory_agent.get_session_history(session_id)
    print("📊 Session history structure:")
    print(f"  - Total conversations: {session_history.get('total_conversations', 0)}")
    print(
        f"  - Available conversations: {[c['conversation_id'] for c in session_history.get('conversations', [])]}"
    )

    # Debug: Show what data is available for each conversation
    for conv in session_history.get("conversations", []):
        conv_id = conv["conversation_id"]
        has_perception = bool(conv.get("perception"))
        has_action = bool(conv.get("action"))
        print(f"  - {conv_id}: perception={has_perception}, action={has_action}")
        if has_action:
            print(f"    Final answer: {conv['action']['final_answer'][:50]}...")

    chat_history = format_chat_history_from_memory(session_history, conversation_id)
    chat_summary = get_chat_history_summary(chat_history)
    print(f"📚 {chat_summary}")

    if chat_history:
        print("💬 Chat history being passed to perception:")
        for i, msg in enumerate(chat_history, 1):
            print(f"  {i}. {msg['sender'].upper()}: {msg['content'][:100]}...")
    else:
        print("💬 No chat history available for this conversation")

    try:
        # Step 1: Perception with detailed output
        print_subsection("STEP 1: Perception Engine")
        perception_engine = await create_perception_engine()
        perception_result = await perception_engine.analyze_query(query, chat_history)

        print("🧠 Perception Result:")
        print(f"  - Enhanced Question: {perception_result.enhanced_question}")
        print(f"  - Intent: {perception_result.intent}")
        print(f"  - Entities: {perception_result.entities}")
        print(f"  - Selected Servers: {perception_result.selected_servers}")
        print(
            f"  - Selected Tools: {[tool.tool_name for tool in perception_result.selected_tools]}"
        )
        print(f"  - Reasoning: {perception_result.reasoning}")

        # Save and show what's being saved
        memory_agent.save_perception_outcome(
            session_id, conversation_id, query, perception_result
        )
        print("\n💾 Saved Perception Data:")
        conv_record = memory_agent.get_conversation(session_id, conversation_id)
        if conv_record and conv_record.perception:
            print(f"  - Enhanced Question: {conv_record.perception.enhanced_question}")
            print(f"  - Intent: {conv_record.perception.intent}")
            print(f"  - Selected Tools: {conv_record.perception.selected_tools}")

        # Step 2: Decision with detailed output
        print_subsection("STEP 2: Decision Engine")
        decision_engine = await create_decision_engine()
        decision_result = await decision_engine.analyze_decision_from_perception(
            perception_result
        )

        print("🎯 Decision Result:")
        print(f"  - Strategy: {decision_result.strategy}")
        print(f"  - Total Steps: {decision_result.total_steps}")
        print(f"  - Tool Calls: {len(decision_result.tool_calls)}")
        for i, tool_call in enumerate(decision_result.tool_calls, 1):
            print(f"    {i}. {tool_call.tool_name}: {tool_call.parameters}")

        # Save and show what's being saved
        memory_agent.save_decision_outcome(session_id, conversation_id, decision_result)
        print("\n💾 Saved Decision Data:")
        conv_record = memory_agent.get_conversation(session_id, conversation_id)
        if conv_record and conv_record.decision:
            print(f"  - Strategy: {conv_record.decision.strategy}")
            print(f"  - Tool Names: {conv_record.decision.tool_names}")
            print(f"  - Total Steps: {conv_record.decision.total_steps}")

        # Step 3: Action with detailed output
        print_subsection("STEP 3: Action Engine")
        action_result = await execute_with_decision_result(query, decision_result)

        print("⚡ Action Result:")
        print(f"  - Success: {action_result.success}")
        print(f"  - Execution Time: {action_result.execution_time:.2f}s")
        print(f"  - Total Steps: {action_result.total_steps}")
        print(f"  - Final Answer: {action_result.final_answer}")

        # Save and show what's being saved
        memory_agent.save_action_outcome(session_id, conversation_id, action_result)
        print("\n💾 Saved Action Data:")
        conv_record = memory_agent.get_conversation(session_id, conversation_id)
        if conv_record and conv_record.action:
            print(f"  - Success: {conv_record.action.success}")
            print(f"  - Execution Time: {conv_record.action.execution_time}")
            print(f"  - Final Answer: {conv_record.action.final_answer[:100]}...")

        # Step 4: Vector Database Storage
        print_subsection("STEP 4: Vector Database Storage")
        print("🔗 Saving query-tool-outcome pattern to vector database...")
        await memory_agent.save_final_query_tool_outcome(session_id, conversation_id)

        print("💾 Vector Database Pattern Saved:")
        print(f"  - Total patterns in DB: {len(memory_agent.pattern_storage)}")
        if memory_agent.pattern_storage:
            latest_pattern = memory_agent.pattern_storage[-1]
            print(f"  - Latest pattern query: {latest_pattern.query}")
            print(f"  - Tools used: {latest_pattern.tools_used}")
            print(f"  - Strategy: {latest_pattern.strategy}")
            print(f"  - Success: {latest_pattern.success}")

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


async def demo_memory_agent_internals():
    """
    Comprehensive demo showing how mem_agent.py works under the hood.
    """
    print_section("Memory Agent Internal Demo - 2 Questions Only")

    try:
        # Initialize memory agent
        print("🔧 Initializing Memory Agent...")
        memory_agent = await create_memory_agent()
        print("✅ Memory agent initialized")
        print(f"📊 Starting state - Sessions: {len(memory_agent.list_sessions())}")

        # Demo with just 2 questions to show progression
        demo_cases = [
            {
                "session_id": "demo_session_internal",
                "conversation_id": "conv_001",
                "query": "What is 15 + 25?",
                "description": "First question - No chat history",
            },
            {
                "session_id": "demo_session_internal",
                "conversation_id": "conv_002",
                "query": "Now multiply that result by 3",
                "description": "Second question - Uses chat history from first",
            },
        ]

        results = []
        for i, case in enumerate(demo_cases, 1):
            print(f"\n\n🔹 DEMO CASE {i}: {case['description']}")

            result = await run_pipeline_with_detailed_memory_demo(
                case["session_id"], case["conversation_id"], case["query"], memory_agent
            )

            if result:
                results.append({**case, "result": result})

        # Show complete session storage
        print_section("Complete Session Storage Analysis")
        session_history = memory_agent.get_session_history("demo_session_internal")
        print("📋 Complete Session Data Structure:")
        print(f"  - Session ID: demo_session_internal")
        print(f"  - Total Conversations: {session_history['total_conversations']}")

        for conv in session_history["conversations"]:
            print(f"\n  🔹 Conversation: {conv['conversation_id']}")
            print(f"    - Query: {conv['query']}")
            print(f"    - Timestamp: {conv['timestamp']}")

            if conv.get("perception"):
                print(
                    f"    - Perception: Intent={conv['perception']['intent']}, Tools={conv['perception']['selected_tools']}"
                )
            if conv.get("decision"):
                print(
                    f"    - Decision: Strategy={conv['decision']['strategy']}, Steps={conv['decision']['total_steps']}"
                )
            if conv.get("action"):
                print(
                    f"    - Action: Success={conv['action']['success']}, Time={conv['action']['execution_time']}s"
                )

        # Show vector database analysis
        print_section("Vector Database Analysis")
        print(f"📊 Vector Database Contents:")
        print(f"  - Total patterns stored: {len(memory_agent.pattern_storage)}")

        for i, pattern in enumerate(
            memory_agent.pattern_storage[-2:], 1
        ):  # Show last 2 patterns
            print(f"\n  🔹 Pattern {len(memory_agent.pattern_storage) - 2 + i}:")
            print(f"    - Query: {pattern.query}")
            print(f"    - Tools: {pattern.tools_used}")
            print(f"    - Strategy: {pattern.strategy}")
            print(f"    - Success: {pattern.success}")
            print(f"    - Execution Time: {pattern.execution_time}s")

        # Demonstrate similarity search
        print_section("Vector Similarity Search Demo")
        test_query = "What is 20 + 30?"
        print(f"🔍 Testing similarity for: '{test_query}'")

        similar_outcome = await memory_agent.get_similar_query_outcome(
            test_query, confidence_threshold=0.3
        )
        if similar_outcome:
            print("✅ Found similar pattern:")
            print(f"  - Similar query: {similar_outcome['query']}")
            print(f"  - Similarity score: {similar_outcome['similarity_score']:.3f}")
            print(f"  - Recommended tools: {similar_outcome['tools_used']}")
            print(f"  - Past success: {similar_outcome['success']}")
        else:
            print("❌ No similar patterns found")

        # Final summary
        print_section("Memory Agent Demo Summary")
        print("✅ Successfully demonstrated:")
        print("  🔹 Individual step saving (perception, decision, action)")
        print("  🔹 Session-based conversation storage")
        print("  🔹 Chat history retrieval and formatting")
        print("  🔹 Vector database pattern storage")
        print("  🔹 Similarity search functionality")
        print(f"\n📊 Final Statistics:")
        print(f"  - Conversations processed: {len(results)}")
        print(f"  - Sessions created: {len(memory_agent.list_sessions())}")
        print(f"  - Vector patterns: {len(memory_agent.pattern_storage)}")

    except Exception as e:
        print(f"❌ Demo failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(demo_memory_agent_internals())
