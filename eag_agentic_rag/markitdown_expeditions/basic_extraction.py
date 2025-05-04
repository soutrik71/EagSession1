"""
MarkItDown is a lightweight Python utility for converting various files to Markdown for use with LLMs and related text analysis pipelines
We will implement it in a basic way and also with openai
"""

from markitdown import MarkItDown
from dotenv import load_dotenv
import os
from openai import OpenAI

# basic extraction

# md = MarkItDown(enable_plugins=False)  # Set to True to enable plugins
# result = md.convert(
#     "/home/azureuser/cloudfiles/code/Users/Soutrik.Chowdhury/EagSession1/eag_agentic_rag/docs/BestRagTech.pdf"
# )
# print(result.text_content)

# openai extraction

load_dotenv()

openai_api_key = os.getenv("OPENAI_API_KEY")
openai_api_base = os.getenv("OPENAI_API_BASE")

if not openai_api_key:
    raise ValueError("OPENAI_API_KEY is not set in the environment variables.")

client = OpenAI(api_key=openai_api_key, base_url=openai_api_base)
md = MarkItDown(llm_client=client, llm_model="gpt-4o")
result = md.convert(
    "/home/azureuser/cloudfiles/code/Users/Soutrik.Chowdhury/EagSession1/eag_agentic_rag/docs/Payment_Receipt.pdf"
)
print(result.text_content)
