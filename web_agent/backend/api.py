from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from typing import Optional, Dict, Any
import uvicorn
from datetime import datetime

from utils.tool_calling_exec import (
    get_prompt,
    llm_with_tools,
    execute_tool_calls,
    tools_dict,
)

# Initialize FastAPI app
app = FastAPI(
    title="News and Financial Research Assistant",
    description="API for getting financial information and news about companies",
    version="1.0.0",
)

# Configure CORS with more permissive settings for development
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, replace with specific origins
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["*"],
)


# Pydantic models for request/response
class QuestionRequest(BaseModel):
    question: str = Field(..., description="The question about a company")


class HealthResponse(BaseModel):
    status: str = Field(..., description="Status of the API")
    timestamp: datetime = Field(..., description="Current server timestamp")
    version: str = Field(..., description="API version")


class ToolCallResponse(BaseModel):
    tool_name: str
    args: Dict[str, Any]
    result: str


class QuestionResponse(BaseModel):
    question: str
    answer: str
    tool_calls: Optional[list[ToolCallResponse]] = None
    error: Optional[str] = None


@app.get("/health", response_model=HealthResponse)
async def health_check():
    """
    Health check endpoint to verify API is running.
    """
    return HealthResponse(
        status="healthy", timestamp=datetime.utcnow(), version="1.0.0"
    )


@app.post("/ask", response_model=QuestionResponse)
async def ask_question(request: QuestionRequest):
    """
    Endpoint to ask questions about companies and get financial information/news.
    """
    try:
        # Generate prompt and AI response
        messages = get_prompt(request.question)
        ai_msg = llm_with_tools.invoke(messages)

        # Execute any tool calls contained in the AI response
        tool_results = execute_tool_calls(tools_dict, ai_msg)

        # Format tool calls for response if available
        tool_calls = []
        if hasattr(ai_msg, "tool_calls") and ai_msg.tool_calls:
            for tool_call in ai_msg.tool_calls:
                tool_calls.append(
                    ToolCallResponse(
                        tool_name=tool_call["name"],
                        args=tool_call["args"],
                        result=tool_results,
                    )
                )

        return QuestionResponse(
            question=request.question,
            answer=ai_msg.content if hasattr(ai_msg, "content") else tool_results,
            tool_calls=tool_calls,
        )

    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Error processing question: {str(e)}"
        )


if __name__ == "__main__":
    # Updated module path for uvicorn: "backend.api:app"
    # if this file is located in the backend directory.
    uvicorn.run(
        "backend.api:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
    )
