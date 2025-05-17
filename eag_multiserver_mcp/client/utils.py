import yaml
import os
import shutil
import json
from datetime import datetime
from enum import Enum


# Define verbosity levels for logging
class LogLevel(Enum):
    ERROR = 0
    WARN = 1
    INFO = 2
    DEBUG = 3
    TRACE = 4


# Global log level setting - can be changed programmatically
CURRENT_LOG_LEVEL = LogLevel.DEBUG


def set_log_level(level: LogLevel):
    """Set the global log level for the application"""
    global CURRENT_LOG_LEVEL
    CURRENT_LOG_LEVEL = level
    log(f"Log level set to {level.name}", level=LogLevel.INFO)


def log(message, level=LogLevel.INFO, console_only=False):
    """
    Log a message with timestamp and appropriate level.

    Args:
        message: The message to log
        level: LogLevel enum indicating importance
        console_only: Whether to only print to console and not to log file
    """
    if level.value <= CURRENT_LOG_LEVEL.value:
        timestamp = get_timestamp()
        level_prefix = f"[{level.name}]"
        formatted_message = f"[{timestamp}] {level_prefix} {message}"

        print(formatted_message)

        # Additional logging to file could be added here if needed
        if not console_only and level.value <= LogLevel.INFO.value:
            # Could log to a file or other destination
            pass


def read_yaml_file(file_path):
    """
    Read a YAML file and return its contents.
    """
    try:
        with open(file_path, "r") as file:
            data = yaml.safe_load(file)
        return data
    except FileNotFoundError:
        log(f"Config file not found: {file_path}", level=LogLevel.WARN)
        return {}
    except Exception as e:
        log(f"Error reading config file {file_path}: {e}", level=LogLevel.ERROR)
        return {}


def check_and_reset_index(index_name: str, reset_index: bool) -> None:
    """
    Check if the index needs to be reset based on configuration

    Args:
        index_name: Path to the index folder
        reset_index: Whether to reset the index
    """
    if reset_index and os.path.exists(index_name):
        log(f"Resetting index at '{index_name}'", level=LogLevel.WARN)
        try:
            shutil.rmtree(index_name)
            log(f"Successfully deleted index folder", level=LogLevel.INFO)
        except Exception as e:
            log(f"Error deleting index folder: {e}", level=LogLevel.ERROR)
    elif not reset_index and os.path.exists(index_name):
        log("Using existing index at '{}'".format(index_name), level=LogLevel.INFO)


# Helper function for consistent timestamps
def get_timestamp(format="%H:%M:%S"):
    """Get a formatted timestamp string"""
    return datetime.now().strftime(format)


def format_json_content(content):
    """Format JSON content for display"""
    if not isinstance(content, str):
        return content

    if content.startswith("{") or content.startswith("["):
        try:
            parsed_json = json.loads(content)
            return json.dumps(parsed_json, indent=2)
        except json.JSONDecodeError:
            pass
    return content


def filter_chat_history(chat_history):
    """Filter chat history to only include human and AI messages"""
    if not chat_history:
        return []

    return [
        msg
        for msg in chat_history
        if isinstance(msg, dict) and msg.get("role") in ["human", "ai"]
    ]


def save_conversation(conversation_id, query, messages, output_dir):
    """Save conversation messages to a file"""
    timestamp = get_timestamp("%Y%m%d_%H%M%S")
    filename = f"conversation_{conversation_id}_{timestamp}.json"
    filepath = os.path.join(output_dir, filename)

    # Create a structured representation of the conversation
    conversation_data = {
        "id": conversation_id,
        "timestamp": datetime.now().isoformat(),
        "query": query,
        "messages": [
            {
                "type": type(msg).__name__,
                "content": msg.content if hasattr(msg, "content") else str(msg),
                "has_tool_calls": hasattr(msg, "tool_calls") and bool(msg.tool_calls),
            }
            for msg in messages
        ],
    }

    # Save to file
    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(conversation_data, f, indent=2)

    log(f"Conversation saved to: {filepath}", level=LogLevel.INFO)
    return filepath


def display_conversation_history(conversation_id, memory_store):
    """Display the conversation history from the memory store"""
    if not memory_store:
        log("Memory store not available", level=LogLevel.WARN)
        return

    print("\n" + "=" * 50)
    print(f"CONVERSATION HISTORY: {conversation_id}")
    print("=" * 50)

    # Get the conversation from memory
    conversation = memory_store.get_conversation(conversation_id)

    if not conversation:
        print("No conversation history found")
        return

    for i, msg in enumerate(conversation, 1):
        sender = msg.get("sender", "unknown").upper()
        content = format_json_content(msg.get("content", ""))

        print(f"\n{i}. {sender}:")
        print("-" * 40)
        print(content)

    print("\n" + "=" * 50)


def print_conversation_summary(
    conversation_id, query, response, messages, step_outputs
):
    """Print a summary of the conversation results"""
    print("\n" + "=" * 50)
    print(f"CONVERSATION SUMMARY: {conversation_id}")
    print("=" * 50)
    print(f"Query: {query}")

    # Print step completion
    print("\nProcessing Steps:")
    for i, step in enumerate(step_outputs["steps"], 1):
        status_icon = "✅" if step["status"] == "completed" else "❌"
        print(f"{i}. {status_icon} {step['name']}")

    # Print message chain summary
    print("\nMessage Chain:")
    for i, msg in enumerate(messages, 1):
        msg_type = type(msg).__name__
        content_preview = (
            msg.content[:100] + "..." if len(msg.content) > 100 else msg.content
        )
        print(f"{i}. {msg_type}: {content_preview}")

    # Final result stats
    print("\nFinal answer source count:", end=" ")
    for msg in messages:
        if hasattr(msg, "content") and isinstance(msg.content, str):
            if msg.content.startswith("{") and "urls" in msg.content:
                try:
                    content_json = json.loads(msg.content)
                    if "urls" in content_json:
                        print(f"{len(content_json['urls'])} URLs retrieved")
                except json.JSONDecodeError:
                    pass

    print("=" * 50)
    print("To view full conversation details, check the saved conversation file.")
    print("=" * 50)


def save_session_summary(conversation_id, queries, results, output_dir):
    """Save a summary of the conversation session"""
    session_summary = {
        "session_id": conversation_id,
        "timestamp": datetime.now().isoformat(),
        "queries_count": len(queries),
        "conversations": [
            {
                "id": conversation_id,
                "query": r["query"],
                "message_count": len(r["messages"]),
                "steps_completed": sum(
                    1 for s in r["step_outputs"]["steps"] if s["status"] == "completed"
                ),
            }
            for r in results
        ],
    }

    session_file = os.path.join(output_dir, f"session_{conversation_id}.json")
    with open(session_file, "w", encoding="utf-8") as f:
        json.dump(session_summary, f, indent=2)

    log(f"Session summary saved to: {session_file}", level=LogLevel.INFO)
    return session_file
