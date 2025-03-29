import os
from dotenv import load_dotenv, find_dotenv
from typing import Optional

from langchain_openai import AzureChatOpenAI
from langchain_core.callbacks import (
    AsyncCallbackManagerForToolRun,
    CallbackManagerForToolRun,
)
from langchain_core.tools import BaseTool
from langchain_core.messages import HumanMessage, SystemMessage
from pydantic import BaseModel, Field

from utils.web_utils import (
    get_stock_symbol_alpha_vantage,
    get_company_financials,
    get_news_headlines,
)
from utils.company_symbols import get_symbol_from_mapping
from loguru import logger

# Load environment variables once
load_dotenv(find_dotenv())

# Initialize the Azure OpenAI LLM
llm = AzureChatOpenAI(
    azure_deployment=os.getenv("AZURE_DEPLOYMENT_NAME"),
    azure_endpoint=os.getenv("AZURE_OPENAI_ENDPOINT"),
    api_key=os.getenv("AZURE_OPENAI_API_KEY"),
    openai_api_version=os.getenv("OPENAI_API_VERSION"),
    temperature=0,
)


def execute_tool_calls(tools_dict: dict, model_output) -> str:
    """
    Execute tool calls based on the model's output.

    Args:
        tools_dict: Dictionary mapping tool names to tool objects.
        model_output: Output from the LLM containing tool calls.

    Returns:
        str: Combined result of executed tool calls.
    """
    if not hasattr(model_output, "tool_calls") or not model_output.tool_calls:
        return "No tool calls found in model output"

    results = []
    for tool_call in model_output.tool_calls:
        tool_name = tool_call["name"]
        if tool_name not in tools_dict:
            results.append(f"Tool {tool_name} not found in available tools")
            continue

        tool = tools_dict[tool_name]
        try:
            result = tool.invoke(tool_call["args"])
            results.append(result)
        except Exception as e:
            results.append(f"Error executing {tool_name}: {str(e)}")

    return "\n".join(results)


# Define input models for the tools
class CompanyFinancialsInput(BaseModel):
    company_name: str = Field(
        ..., description="Name of the company to get financials for"
    )


class CompanyNewsInput(BaseModel):
    company_name: str = Field(..., description="Name of the company to get news for")


# Tool to retrieve company financials
class CompanyFinancialsTool(BaseTool):
    name: str = "GetCompanyFinancials"
    description: str = "Get financial information for a company by name"
    args_schema: Optional[type[BaseModel]] = CompanyFinancialsInput

    def _run(
        self, company_name: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Retrieve financial information for the specified company."""
        if not company_name:
            return "Company name is required"

        # Try getting symbol from Alpha Vantage first
        symbols = get_stock_symbol_alpha_vantage(company_name)
        logger.info(f"Symbols from alpha vantage: {symbols}")

        # Filter for symbols where 'region': 'United States'
        symbols_fin = [
            symbol for symbol in symbols if symbol["region"] == "United States"
        ]
        if symbols_fin:
            # Use the first symbol found
            symbol = symbols_fin[0]["symbol"]
            logger.info(f"Using symbol from Alpha Vantage: {symbol}")
        else:
            # Try getting symbol from our mapping
            symbol = get_symbol_from_mapping(company_name)
            logger.info(f"Using symbol from mapping: {symbol}")

        if not symbol:
            return f"No stock symbol found for {company_name}. Please try with a different company name or check the spelling."

        logger.info(f"Getting financials for {symbol}")
        return get_company_financials(symbol)

    async def _arun(
        self,
        company_name: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        return self._run(company_name, run_manager=run_manager.get_sync())


# Tool to retrieve company news
class CompanyNewsTool(BaseTool):
    name: str = "GetCompanyNews"
    description: str = "Get recent news headlines for a company by name"
    args_schema: Optional[type[BaseModel]] = CompanyNewsInput

    def _run(
        self, company_name: str, run_manager: Optional[CallbackManagerForToolRun] = None
    ) -> str:
        """Retrieve recent news headlines for the specified company."""
        if not company_name:
            return "Company name is required"
        return get_news_headlines(company_name)

    async def _arun(
        self,
        company_name: str,
        run_manager: Optional[AsyncCallbackManagerForToolRun] = None,
    ) -> str:
        return self._run(company_name, run_manager=run_manager.get_sync())


# Create tool instances and mapping
company_financials_tool = CompanyFinancialsTool()
company_news_tool = CompanyNewsTool()

# tool dictionary
tools_dict = {
    company_financials_tool.name: company_financials_tool,
    company_news_tool.name: company_news_tool,
}

tools = [company_financials_tool, company_news_tool]

# Bind tools to the LLM
llm_with_tools = llm.bind_tools(tools, parallel_tool_calls=False)


def get_prompt(question: str):
    """
    Generate conversation prompt including system instructions and the user's question.
    """
    system_message = (
        "You are a news and financial research assistant with access to two specialized tools:\n\n"
        "1. GetCompanyFinancials:\n"
        "   - Purpose: Retrieves detailed financial information for a company\n"
        "   - Input: Company name (e.g., 'Apple', 'Microsoft')\n"
        "   - Use this when users ask about financial data, earnings, or financial metrics\n\n"
        "2. GetCompanyNews:\n"
        "   - Purpose: Fetches recent news headlines about a company\n"
        "   - Input: Company name (e.g., 'Apple', 'Microsoft')\n"
        "   - Use this when users ask about recent news, updates, or company developments\n\n"
        "Your task is to:\n"
        "1. Analyze the user's question carefully\n"
        "2. Determine which tool(s) would be most appropriate\n"
        "3. Use the tool(s) to gather relevant information\n"
        "4. Provide a clear, concise response based on the information retrieved\n\n"
        "Always use the appropriate tools rather than making assumptions or providing general information."
    )
    return [SystemMessage(content=system_message), HumanMessage(content=question)]


# Example usage
if __name__ == "__main__":
    # Uncomment the question you want to test
    question = "What is the financial information for Microsoft?"
    # question = "What is the latest news for Microsoft?"
    messages = get_prompt(question)
    ai_msg = llm_with_tools.invoke(messages)
    output = execute_tool_calls(tools_dict, ai_msg)
    print(output)
