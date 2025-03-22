import os
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, HttpUrl
from typing import Optional
from dotenv import load_dotenv
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.prompts import ChatPromptTemplate
from langchain.chains import LLMChain
import tempfile
import git
import shutil
import uvicorn

load_dotenv()

app = FastAPI(
    title="Git Repository Analyzer",
    description="API for analyzing Git repositories using Gemini AI",
    version="1.0.0",
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["chrome-extension://*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Configure Gemini
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
if not GOOGLE_API_KEY:
    raise ValueError("GOOGLE_API_KEY not found in environment variables")

# Configure LangChain Gemini with correct model name and configuration
llm = ChatGoogleGenerativeAI(
    model="gemini-1.5-pro",
    google_api_key=GOOGLE_API_KEY,
    temperature=0.0,
    convert_system_message_to_human=True,
    safety_settings=[
        {"category": "HARM_CATEGORY_DANGEROUS_CONTENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HARASSMENT", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_HATE_SPEECH", "threshold": "BLOCK_NONE"},
        {"category": "HARM_CATEGORY_SEXUALLY_EXPLICIT", "threshold": "BLOCK_NONE"},
    ],
    max_output_tokens=2048,
    top_p=0.8,
    top_k=40,
)


class RepoRequest(BaseModel):
    """Request model for repository analysis"""

    repo_url: HttpUrl

    class Config:
        json_schema_extra = {
            "example": {"repo_url": "https://github.com/username/repository.git"}
        }


class AnalysisResponse(BaseModel):
    """Response model for repository analysis"""

    analysis: str
    status: str = "success"
    message: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "analysis": "Detailed analysis of the repository...",
                "status": "success",
                "message": "Repository analyzed successfully",
            }
        }


class ErrorResponse(BaseModel):
    """Error response model"""

    status: str = "error"
    detail: str
    message: Optional[str] = None

    class Config:
        json_schema_extra = {
            "example": {
                "status": "error",
                "detail": "Failed to clone repository",
                "message": "Invalid repository URL",
            }
        }


def clone_repo(repo_url: str) -> str:
    """Clone a repository and return its path."""
    temp_dir = tempfile.mkdtemp()
    try:
        git.Repo.clone_from(repo_url, temp_dir)
        return temp_dir
    except Exception as e:
        try:
            shutil.rmtree(temp_dir, ignore_errors=True)
        except Exception:
            pass
        raise HTTPException(
            status_code=400, detail=f"Failed to clone repository: {str(e)}"
        )


def analyze_code_structure(repo_path: str) -> str:
    """Analyze the code structure of the repository."""
    try:
        file_structure = []
        for root, dirs, files in os.walk(repo_path):
            if ".git" in dirs:
                dirs.remove(".git")

            rel_path = os.path.relpath(root, repo_path)
            if rel_path == ".":
                rel_path = ""

            for file in files:
                file_path = os.path.join(rel_path, file)
                file_structure.append(file_path)

        # Create an enhanced prompt template
        prompt_template = ChatPromptTemplate.from_messages(
            [
                (
                    "system",
                    """You are an expert code analyst. Analyze the repository structure and provide a comprehensive analysis.
            Focus on:
            1. Architecture and Design Patterns
            2. Code Organization and Structure
            3. Dependencies and External Libraries
            4. Main Components and Their Interactions
            5. Data Flow and Control Flow
            6. Potential Areas for Improvement
            
            Be specific and technical in your analysis.""",
                ),
                (
                    "human",
                    """Please analyze this repository structure:
            {file_structure}
            
            Provide a detailed technical analysis following the focus areas mentioned above.""",
                ),
            ]
        )

        # Create and run the chain
        chain = LLMChain(llm=llm, prompt=prompt_template)
        # Using invoke instead of run as per deprecation warning
        analysis = chain.invoke({"file_structure": chr(10).join(file_structure)})[
            "text"
        ]

        return analysis
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to analyze repository: {str(e)}"
        )


@app.post(
    "/analyze-repo",
    response_model=AnalysisResponse,
    responses={
        200: {"description": "Successful analysis"},
        400: {"model": ErrorResponse, "description": "Invalid request"},
        500: {"model": ErrorResponse, "description": "Server error"},
    },
)
async def analyze_repo(request: RepoRequest):
    """
    Analyze a Git repository and provide a detailed technical analysis.

    Args:
        request: RepoRequest containing the repository URL

    Returns:
        AnalysisResponse containing the analysis results
    """
    repo_path = None
    try:
        repo_path = clone_repo(str(request.repo_url))
        analysis = analyze_code_structure(repo_path)
        return AnalysisResponse(
            analysis=analysis,
            status="success",
            message="Repository analyzed successfully",
        )
    except HTTPException as e:
        raise e
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"An unexpected error occurred: {str(e)}"
        )
    finally:
        if repo_path:
            try:
                shutil.rmtree(repo_path, ignore_errors=True)
            except Exception:
                pass


if __name__ == "__main__":
    uvicorn.run(app, host="0.0.0.0", port=8000)
