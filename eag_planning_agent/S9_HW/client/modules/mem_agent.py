"""
FastMCP 2.0 Memory Agent

Comprehensive memory management system that stores:
1. Conversations by Session ID -> Conversation ID hierarchy (local JSON)
2. Module outcomes (perception, decision, action) with key information
3. Query-tool-response patterns using FAISS + OpenAI embeddings in tool_history
4. Tool usage analytics for future perception recommendations

Enables the perception module to learn from past successful/failed tool usage patterns.
"""

import json
import asyncio
import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from pathlib import Path
import sys

# Add parent directory to path to enable imports
sys.path.append(str(Path(__file__).parent.parent))

import faiss
from pydantic import BaseModel, Field

# Import required modules
from llm_utils import LLMUtils
from modules.perception import PerceptionResult
from modules.decision import DecisionResult
from modules.action import ActionResult

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ConversationMessage(BaseModel):
    """Single message in a conversation"""

    timestamp: str
    sender: str  # 'human', 'ai', 'system'
    content: str
    metadata: Optional[Dict[str, Any]] = Field(default_factory=dict)


class PerceptionSummary(BaseModel):
    """Most important information from perception module output"""

    enhanced_question: str
    intent: str
    selected_servers: List[str]
    selected_tools: List[str]  # Just tool names for simplicity
    reasoning: str


class DecisionSummary(BaseModel):
    """Most important information from decision module output"""

    strategy: str
    total_steps: int
    tool_names: List[str]  # Extracted from tool_calls
    reasoning: str


class ActionSummary(BaseModel):
    """Most important information from action module output"""

    success: bool
    execution_time: float
    final_answer: str
    tools_executed: int
    error: Optional[str] = None


class ConversationRecord(BaseModel):
    """Complete record for a single conversation within a session"""

    session_id: str
    conversation_id: str
    query: str
    timestamp: str
    perception: Optional[PerceptionSummary] = None
    decision: Optional[DecisionSummary] = None
    action: Optional[ActionSummary] = None
    messages: List[ConversationMessage] = Field(default_factory=list)


class QueryToolPattern(BaseModel):
    """Pattern for query-tool-response storage in vector DB"""

    session_id: str
    conversation_id: str
    timestamp: str
    query: str
    tools_used: List[str]
    servers_used: List[str]
    strategy: str
    success: bool
    execution_time: float
    final_outcome: str
    error: Optional[str] = None
    confidence_score: float  # For future ranking


class MemoryAgent:
    """
    Comprehensive memory management for FastMCP 2.0 system.

    Features:
    - Session-based conversation storage (conversation_history/)
    - Query-tool-response patterns in vector database (tool_history/)
    - Analytics for tool usage recommendations
    - Dual retrieval: session-based + similarity-based
    """

    def __init__(
        self,
        base_dir: str = "../memory_storage",
        conversation_dir: str = "conversation_history",
        tool_dir: str = "tool_history",
    ):
        """
        Initialize memory agent with folder-based storage.

        Args:
            base_dir: Base directory for all memory storage (relative to client folder)
            conversation_dir: Subdirectory for conversation history
            tool_dir: Subdirectory for tool history vector DB
        """
        # Resolve the base directory relative to the client folder
        client_dir = Path(__file__).parent.parent  # Go up to client folder
        self.base_dir = (client_dir / base_dir).resolve()
        self.conversation_dir = self.base_dir / conversation_dir
        self.tool_dir = self.base_dir / tool_dir

        # Create directories
        self.base_dir.mkdir(exist_ok=True)
        self.conversation_dir.mkdir(exist_ok=True)
        self.tool_dir.mkdir(exist_ok=True)

        # Session-based storage (in memory cache)
        self.sessions: Dict[str, Dict[str, ConversationRecord]] = {}

        # Initialize LLM utils for embeddings
        try:
            self.llm_utils = LLMUtils()
            self.embedding_model = self.llm_utils.embedding_model
            logger.info("✅ Memory agent initialized with OpenAI embeddings")
        except Exception as e:
            logger.error(f"❌ Failed to initialize embeddings: {e}")
            raise

        # Vector database for query-tool patterns
        self.vector_index = None
        self.pattern_storage: List[QueryToolPattern] = []
        self._initialize_vector_db()

        # Load existing session data
        self._load_sessions_from_disk()

    def _initialize_vector_db(self):
        """Initialize FAISS vector database for query-tool patterns."""
        try:
            index_file = self.tool_dir / "query_tool_patterns.index"
            metadata_file = self.tool_dir / "patterns_metadata.json"

            if index_file.exists() and metadata_file.exists():
                # Load existing index
                self.vector_index = faiss.read_index(str(index_file))
                with open(metadata_file, "r") as f:
                    patterns_data = json.load(f)
                    self.pattern_storage = [
                        QueryToolPattern(**pattern) for pattern in patterns_data
                    ]
                logger.info(
                    f"✅ Loaded existing vector index with {len(self.pattern_storage)} patterns"
                )
            else:
                # Create new index
                sample_embedding = self.embedding_model.embed_query("sample text")
                self.vector_index = faiss.IndexFlatL2(len(sample_embedding))
                logger.info("✅ Created new vector index for query-tool patterns")

        except Exception as e:
            logger.error(f"❌ Failed to initialize vector database: {e}")
            raise

    def _save_vector_db(self):
        """Save vector database to disk."""
        try:
            index_file = self.tool_dir / "query_tool_patterns.index"
            metadata_file = self.tool_dir / "patterns_metadata.json"

            faiss.write_index(self.vector_index, str(index_file))

            patterns_data = [pattern.model_dump() for pattern in self.pattern_storage]
            with open(metadata_file, "w") as f:
                json.dump(patterns_data, f, indent=2)

            logger.info(
                f"✅ Saved vector database with {len(self.pattern_storage)} patterns"
            )
        except Exception as e:
            logger.error(f"❌ Failed to save vector database: {e}")

    def _load_sessions_from_disk(self):
        """Load all session data from conversation_history directory."""
        try:
            for session_file in self.conversation_dir.glob("session_*.json"):
                session_id = session_file.stem.replace("session_", "")

                with open(session_file, "r") as f:
                    session_data = json.load(f)

                # Convert to ConversationRecord objects
                conversations = {}
                for conv_id, conv_data in session_data.items():
                    conversations[conv_id] = ConversationRecord(**conv_data)

                self.sessions[session_id] = conversations

            logger.info(f"✅ Loaded {len(self.sessions)} sessions from disk")

        except Exception as e:
            logger.error(f"❌ Failed to load sessions: {e}")

    def _save_session_to_disk(self, session_id: str):
        """Save a specific session to disk."""
        try:
            session_file = self.conversation_dir / f"session_{session_id}.json"

            if session_id in self.sessions:
                # Convert ConversationRecord objects to dict
                session_data = {
                    conv_id: record.model_dump()
                    for conv_id, record in self.sessions[session_id].items()
                }

                with open(session_file, "w") as f:
                    json.dump(session_data, f, indent=2)

                logger.info(f"💾 Saved session {session_id} to disk")

        except Exception as e:
            logger.error(f"❌ Failed to save session {session_id}: {e}")

    # Session and Conversation Management
    def save_conversation_message(
        self,
        session_id: str,
        conversation_id: str,
        sender: str,
        content: str,
        metadata: Optional[Dict] = None,
    ):
        """Save a single message to conversation within a session."""
        # Initialize session if not exists
        if session_id not in self.sessions:
            self.sessions[session_id] = {}

        # Initialize conversation if not exists
        if conversation_id not in self.sessions[session_id]:
            self.sessions[session_id][conversation_id] = ConversationRecord(
                session_id=session_id,
                conversation_id=conversation_id,
                query="",  # Will be set when pipeline completes
                timestamp=datetime.now().isoformat(),
            )

        message = ConversationMessage(
            timestamp=datetime.now().isoformat(),
            sender=sender,
            content=content,
            metadata=metadata or {},
        )

        self.sessions[session_id][conversation_id].messages.append(message)
        logger.info(
            f"💬 Saved message to session {session_id}, conversation {conversation_id}"
        )

    def get_conversation(
        self, session_id: str, conversation_id: str
    ) -> Optional[ConversationRecord]:
        """Retrieve conversation by session and conversation ID."""
        return self.sessions.get(session_id, {}).get(conversation_id)

    def get_session_conversations(
        self, session_id: str
    ) -> Dict[str, ConversationRecord]:
        """Get all conversations for a session."""
        return self.sessions.get(session_id, {})

    def list_sessions(self) -> List[str]:
        """List all session IDs."""
        return list(self.sessions.keys())

    # Individual Step Outcome Storage
    def save_perception_outcome(
        self,
        session_id: str,
        conversation_id: str,
        query: str,
        perception_result: PerceptionResult,
    ):
        """Save perception outcome independently."""
        # Initialize session and conversation if needed
        if session_id not in self.sessions:
            self.sessions[session_id] = {}

        if conversation_id not in self.sessions[session_id]:
            self.sessions[session_id][conversation_id] = ConversationRecord(
                session_id=session_id,
                conversation_id=conversation_id,
                query=query,
                timestamp=datetime.now().isoformat(),
            )

        # Update conversation with perception outcome
        conversation = self.sessions[session_id][conversation_id]
        conversation.query = query
        conversation.perception = PerceptionSummary(
            enhanced_question=perception_result.enhanced_question,
            intent=perception_result.intent,
            selected_servers=perception_result.selected_servers,
            selected_tools=[
                tool.tool_name for tool in perception_result.selected_tools
            ],
            reasoning=perception_result.reasoning,
        )

        # Save session to disk
        self._save_session_to_disk(session_id)
        logger.info(
            f"🧠 Saved perception outcome for session {session_id}, conversation {conversation_id}"
        )

    def save_decision_outcome(
        self,
        session_id: str,
        conversation_id: str,
        decision_result: DecisionResult,
    ):
        """Save decision outcome independently."""
        if session_id in self.sessions and conversation_id in self.sessions[session_id]:
            conversation = self.sessions[session_id][conversation_id]
            conversation.decision = DecisionSummary(
                strategy=decision_result.strategy.value,
                total_steps=decision_result.total_steps,
                tool_names=[call.tool_name for call in decision_result.tool_calls],
                reasoning=decision_result.reasoning,
            )

            # Save session to disk
            self._save_session_to_disk(session_id)
            logger.info(
                f"🎯 Saved decision outcome for session {session_id}, conversation {conversation_id}"
            )
        else:
            logger.warning(
                f"⚠️ Conversation {conversation_id} not found in session {session_id}"
            )

    def save_action_outcome(
        self,
        session_id: str,
        conversation_id: str,
        action_result: ActionResult,
    ):
        """Save action outcome independently."""
        if session_id in self.sessions and conversation_id in self.sessions[session_id]:
            conversation = self.sessions[session_id][conversation_id]
            detailed = action_result.detailed_results
            conversation.action = ActionSummary(
                success=action_result.success,
                execution_time=action_result.execution_time,
                final_answer=action_result.final_answer,
                tools_executed=detailed.get("tools_executed", 0),
                error=action_result.error,
            )

            # Save session to disk
            self._save_session_to_disk(session_id)
            logger.info(
                f"⚡ Saved action outcome for session {session_id}, conversation {conversation_id}"
            )
        else:
            logger.warning(
                f"⚠️ Conversation {conversation_id} not found in session {session_id}"
            )

    async def save_final_query_tool_outcome(
        self,
        session_id: str,
        conversation_id: str,
    ):
        """
        Save final query-server-tool-outcome to vector database.
        Call this after all individual steps are completed.
        """
        if session_id in self.sessions and conversation_id in self.sessions[session_id]:
            conversation = self.sessions[session_id][conversation_id]

            # Ensure all components are present
            if not all(
                [conversation.perception, conversation.decision, conversation.action]
            ):
                logger.warning(
                    f"⚠️ Incomplete pipeline for session {session_id}, conversation {conversation_id}"
                )
                return

            # Create query-tool pattern for vector storage
            pattern = QueryToolPattern(
                session_id=session_id,
                conversation_id=conversation_id,
                timestamp=datetime.now().isoformat(),
                query=conversation.query,
                tools_used=conversation.perception.selected_tools,
                servers_used=conversation.perception.selected_servers,
                strategy=conversation.decision.strategy,
                success=conversation.action.success,
                execution_time=conversation.action.execution_time,
                final_outcome=conversation.action.final_answer,
                error=conversation.action.error,
                confidence_score=1.0 if conversation.action.success else 0.2,
            )

            # Add to vector database
            await self._add_pattern_to_vector_db(pattern)
            logger.info(
                f"📊 Saved final query-tool outcome for session {session_id}, conversation {conversation_id}"
            )
        else:
            logger.warning(
                f"⚠️ Conversation {conversation_id} not found in session {session_id}"
            )

    async def _add_pattern_to_vector_db(self, pattern: QueryToolPattern):
        """Add query-tool pattern to vector database."""
        try:
            # Create embedding for the query
            embedding = await self.embedding_model.aembed_query(pattern.query)

            # Add to FAISS index
            import numpy as np

            embedding_array = np.array(embedding, dtype=np.float32).reshape(1, -1)
            self.vector_index.add(embedding_array)

            # Store pattern metadata
            self.pattern_storage.append(pattern)

            # Save to disk
            self._save_vector_db()

            logger.info(f"🔗 Added pattern to vector DB: {pattern.query[:50]}...")

        except Exception as e:
            logger.error(f"❌ Failed to add pattern to vector DB: {e}")

    # Complete Pipeline Storage (for backward compatibility)
    async def save_complete_pipeline_outcome(
        self,
        session_id: str,
        conversation_id: str,
        query: str,
        perception_result: PerceptionResult,
        decision_result: DecisionResult,
        action_result: ActionResult,
    ):
        """
        Save complete pipeline outcome - convenience method that calls individual step methods.
        """
        # Save individual steps
        self.save_perception_outcome(
            session_id, conversation_id, query, perception_result
        )
        self.save_decision_outcome(session_id, conversation_id, decision_result)
        self.save_action_outcome(session_id, conversation_id, action_result)

        # Save final query-tool outcome to vector DB
        await self.save_final_query_tool_outcome(session_id, conversation_id)

        logger.info(
            f"📊 Saved complete pipeline outcome for session {session_id}, conversation {conversation_id}"
        )

    # Retrieval Method 1: Session-based retrieval
    def get_session_history(self, session_id: str) -> Dict[str, Any]:
        """
        Method 1: Retrieve historical outcomes by session ID.

        Returns structured JSON with query, perception, decision, action data.
        """
        if session_id not in self.sessions:
            return {
                "session_id": session_id,
                "conversations": [],
                "error": "Session not found",
            }

        conversations_data = []
        for conv_id, record in self.sessions[session_id].items():
            conv_data = {
                "conversation_id": conv_id,
                "query": record.query,
                "timestamp": record.timestamp,
                "perception": (
                    record.perception.model_dump() if record.perception else None
                ),
                "decision": record.decision.model_dump() if record.decision else None,
                "action": record.action.model_dump() if record.action else None,
                "message_count": len(record.messages),
            }
            conversations_data.append(conv_data)

        return {
            "session_id": session_id,
            "conversations": conversations_data,
            "total_conversations": len(conversations_data),
        }

    # Retrieval Method 2: Similarity-based retrieval
    async def get_similar_query_outcome(
        self, query: str, confidence_threshold: float = 0.7
    ) -> Optional[Dict[str, Any]]:
        """
        Method 2: Retrieve most contextually similar top-1 query + server + tool + action.

        Uses vector DB similarity with high confidence threshold.
        """
        if len(self.pattern_storage) == 0:
            return None

        try:
            # Create embedding for current query
            query_embedding = await self.embedding_model.aembed_query(query)

            # Search similar patterns
            import numpy as np

            query_array = np.array(query_embedding, dtype=np.float32).reshape(1, -1)

            # Get top-1 most similar pattern
            distances, indices = self.vector_index.search(query_array, 1)

            if len(indices[0]) > 0 and indices[0][0] < len(self.pattern_storage):
                idx = indices[0][0]
                pattern = self.pattern_storage[idx]
                similarity_score = 1.0 / (
                    1.0 + distances[0][0]
                )  # Convert distance to similarity

                # Only return if similarity meets confidence threshold
                if similarity_score >= confidence_threshold:
                    return {
                        "similarity_score": similarity_score,
                        "query": pattern.query,
                        "servers_used": pattern.servers_used,
                        "tools_used": pattern.tools_used,
                        "strategy": pattern.strategy,
                        "success": pattern.success,
                        "execution_time": pattern.execution_time,
                        "final_outcome": pattern.final_outcome,
                        "error": pattern.error,
                        "confidence": pattern.confidence_score,
                        "timestamp": pattern.timestamp,
                        "session_id": pattern.session_id,
                        "conversation_id": pattern.conversation_id,
                    }

            return None

        except Exception as e:
            logger.error(f"❌ Failed to get similar query outcome: {e}")
            return None

    # Analytics and utility methods
    def get_tool_success_analytics(self, tool_name: str) -> Dict[str, Any]:
        """Get success analytics for a specific tool."""
        tool_patterns = [p for p in self.pattern_storage if tool_name in p.tools_used]

        if not tool_patterns:
            return {"tool_name": tool_name, "usage_count": 0}

        successful = [p for p in tool_patterns if p.success]
        failed = [p for p in tool_patterns if not p.success]

        avg_execution_time = sum(p.execution_time for p in tool_patterns) / len(
            tool_patterns
        )

        return {
            "tool_name": tool_name,
            "usage_count": len(tool_patterns),
            "success_count": len(successful),
            "failure_count": len(failed),
            "success_rate": (
                len(successful) / len(tool_patterns) if tool_patterns else 0
            ),
            "avg_execution_time": avg_execution_time,
            "recommendation": (
                "recommended"
                if len(successful) / len(tool_patterns) > 0.7
                else "use_with_caution"
            ),
        }

    def get_conversation_analytics(
        self, session_id: str, conversation_id: str
    ) -> Dict[str, Any]:
        """Get complete analytics for a specific conversation."""
        conversation = self.get_conversation(session_id, conversation_id)

        if not conversation:
            return {"error": "Conversation not found"}

        return {
            "session_id": session_id,
            "conversation_id": conversation_id,
            "query": conversation.query,
            "timestamp": conversation.timestamp,
            "message_count": len(conversation.messages),
            "perception": (
                conversation.perception.model_dump()
                if conversation.perception
                else None
            ),
            "decision": (
                conversation.decision.model_dump() if conversation.decision else None
            ),
            "action": conversation.action.model_dump() if conversation.action else None,
            "has_complete_pipeline": all(
                [conversation.perception, conversation.decision, conversation.action]
            ),
        }


# Convenience functions for easy usage


async def create_memory_agent(
    base_dir: str = "../memory_storage",
    conversation_dir: str = "conversation_history",
    tool_dir: str = "tool_history",
) -> MemoryAgent:
    """Create and initialize a memory agent."""
    try:
        memory_agent = MemoryAgent(base_dir, conversation_dir, tool_dir)
        return memory_agent
    except Exception as e:
        logger.error(f"❌ Failed to create memory agent: {e}")
        raise


# Test function
async def test_memory_agent():
    """Test the memory agent with sample data."""
    print("🧪 Testing FastMCP Memory Agent")
    print("=" * 50)

    try:
        # Create memory agent
        memory_agent = await create_memory_agent()

        # Test session and conversation storage
        session_id = "test_session_1"
        conversation_id = "test_conv_1"

        memory_agent.save_conversation_message(
            session_id, conversation_id, "human", "What is 25 + 37?"
        )
        memory_agent.save_conversation_message(
            session_id, conversation_id, "ai", "The sum is 62"
        )

        # Test similarity-based retrieval (empty initially)
        similar_outcome = await memory_agent.get_similar_query_outcome(
            "What is 30 + 40?"
        )
        print(f"Initial similar outcome: {similar_outcome}")

        # Test session history retrieval
        session_history = memory_agent.get_session_history(session_id)
        print(f"Session history: {session_history}")

        # Test conversation analytics
        analytics = memory_agent.get_conversation_analytics(session_id, conversation_id)
        print(f"Conversation analytics: {analytics}")

        # Test tool analytics
        tool_analytics = memory_agent.get_tool_success_analytics("calculator_add")
        print(f"Tool analytics: {tool_analytics}")

        print("✅ Memory agent testing completed successfully")

    except Exception as e:
        print(f"❌ Memory agent test failed: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(test_memory_agent())
