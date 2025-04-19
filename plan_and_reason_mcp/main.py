from fastapi import FastAPI
from langchain_core.language_models import BaseLanguageModel
from langchain_community.llms import OpenAI
from langchain.text_splitter import RecursiveCharacterTextSplitter
from pydantic import BaseModel
import typer


def main():
    # Test FastAPI
    app = FastAPI()
    print("FastAPI imported successfully")

    # Test LangChain components
    text_splitter = RecursiveCharacterTextSplitter()
    print("LangChain components imported successfully")

    # Test Pydantic
    class TestModel(BaseModel):
        name: str

    print("Pydantic imported successfully")

    # Test Typer
    cli = typer.Typer()
    print("Typer imported successfully")

    print("All key packages imported successfully!")


if __name__ == "__main__":
    main()
