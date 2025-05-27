# LLM Utils - Simple LangChain Integration

A simple utility class that provides LangChain chat model (GPT-4o) and embedding model (text-embedding-3-small) objects.
Handles SSL certificate issues and supports both sync and async operations.

## Installation

```bash
pip install langchain-openai httpx
```

## Usage

### Basic Usage
```python
from llm_utils import LLMUtils

# Initialize (will prompt for API key if not set in environment)
llm_utils = LLMUtils()

# Or provide API key directly
llm_utils = LLMUtils(api_key="your-openai-api-key")

# Use the chat model (sync)
response = llm_utils.chat_model.invoke("Hello, how are you?")
print(response.content)

# Use the embedding model (sync)
embeddings = llm_utils.embedding_model.embed_query("Text to embed")
print(f"Embedding dimensions: {len(embeddings)}")
```

### Async Usage
```python
import asyncio
from llm_utils import LLMUtils

async def main():
    llm_utils = LLMUtils()
    
    # Use chat model (async)
    response = await llm_utils.chat_model.ainvoke("Hello async!")
    print(response.content)
    
    # Use embedding model (async)
    embeddings = await llm_utils.embedding_model.aembed_query("Async text to embed")
    print(f"Embedding dimensions: {len(embeddings)}")

# Run async code
asyncio.run(main())
```

## Features

- **SSL Certificate Handling**: Automatically handles SSL certificate issues common on Windows systems
- **Sync & Async Support**: Both `.invoke()/.embed_query()` and `.ainvoke()/.aembed_query()` methods work
- **Automatic Fallback**: If custom HTTP clients fail, falls back to default configuration
- **Environment Management**: Handles API key setup and problematic SSL environment variables

## Available Models

- `llm_utils.chat_model` - GPT-4o chat model (supports `.invoke()` and `.ainvoke()`)
- `llm_utils.embedding_model` - text-embedding-3-small embedding model (supports `.embed_query()` and `.aembed_query()`)
