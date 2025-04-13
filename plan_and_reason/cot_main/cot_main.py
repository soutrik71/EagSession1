import os
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from google import genai
import asyncio
from rich.console import Console
from rich.panel import Panel
from typing import Optional, List, Tuple

console = Console()


def setup_gemini() -> genai.Client:
    """Set up and return a configured Gemini client."""
    load_dotenv()
    api_key = os.getenv("GEMINI_API_KEY")
    if not api_key:
        raise ValueError("GEMINI_API_KEY not found in environment variables")
    return genai.Client(api_key=api_key)


async def generate_with_timeout(
    client: genai.Client, prompt: str, timeout: int = 10
) -> Optional[str]:
    """Generate content with timeout handling."""
    try:
        loop = asyncio.get_event_loop()
        response = await asyncio.wait_for(
            loop.run_in_executor(
                None,
                lambda: client.models.generate_content(
                    model="gemini-2.0-flash", contents=prompt
                ),
            ),
            timeout=timeout,
        )
        return response.text.strip() if response and response.text else None
    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")
        return None


def create_system_prompt() -> str:
    """Create the system prompt for the mathematical reasoning agent."""
    return """You are a mathematical reasoning agent that solves problems step by step.
You have access to these tools:
- show_reasoning(steps: list) - Show your step-by-step reasoning process
- calculate(expression: str) - Calculate the result of an expression
- verify(expression: str, expected: float) - Verify if a calculation is correct

First show your reasoning, then calculate and verify each step.

Respond with EXACTLY ONE line in one of these formats:
1. FUNCTION_CALL: function_name|param1|param2|...
2. FINAL_ANSWER: [answer]

Example:
User: Solve (2 + 3) * 4
Assistant: FUNCTION_CALL: show_reasoning|["1. First, solve inside parentheses: 2 + 3", "2. Then multiply the result by 4"]
User: Next step?
Assistant: FUNCTION_CALL: calculate|2 + 3
User: Result is 5. Let's verify this step.
Assistant: FUNCTION_CALL: verify|2 + 3|5
User: Verified. Next step?
Assistant: FUNCTION_CALL: calculate|5 * 4
User: Result is 20. Let's verify the final answer.
Assistant: FUNCTION_CALL: verify|(2 + 3) * 4|20
User: Verified correct.
Assistant: FINAL_ANSWER: [20]"""


def extract_function_call(result: str) -> Tuple[Optional[str], Optional[str]]:
    """Extract function name and arguments from the model response."""
    if not result.startswith("FUNCTION_CALL:"):
        return None, None
    _, function_info = result.split(":", 1)
    parts = [p.strip() for p in function_info.split("|")]
    return parts[0], parts[1] if len(parts) > 1 else None


async def handle_function_call(
    session: ClientSession,
    func_name: str,
    args: str,
    conversation_history: List[Tuple[str, float]],
) -> str:
    """Handle different types of function calls."""
    if func_name == "show_reasoning":
        steps = eval(args)
        await session.call_tool("show_reasoning", arguments={"steps": steps})
        return "Next step?"

    elif func_name == "calculate":
        calc_result = await session.call_tool(
            "calculate", arguments={"expression": args}
        )
        if calc_result.content:
            value = calc_result.content[0].text
            conversation_history.append((args, float(value)))
            return f"Result is {value}. Let's verify this step."

    elif func_name == "verify":
        expression, expected = args.split("|")
        await session.call_tool(
            "verify", arguments={"expression": expression, "expected": float(expected)}
        )
        return "Verified. Next step?"

    return ""


async def main():
    """Main function to run the Chain of Thought calculator."""
    try:
        console.print(Panel("Chain of Thought Calculator", border_style="cyan"))

        # Setup
        client = setup_gemini()
        server_params = StdioServerParameters(
            command="python", args=["cot_tools.py", "dev"]
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                try:
                    await session.initialize()

                    # Problem setup
                    system_prompt = create_system_prompt()
                    problem = "What is (23 + 7) * (15 - 8)"
                    console.print(Panel(f"Problem: {problem}", border_style="cyan"))

                    # Initialize conversation
                    prompt = (
                        f"{system_prompt}\n\nSolve this problem step by step: {problem}"
                    )
                    conversation_history = []

                    while True:
                        try:
                            response = await generate_with_timeout(client, prompt)
                            if not response:
                                break

                            console.print(f"\n[yellow]Assistant:[/yellow] {response}")

                            if response.startswith("FUNCTION_CALL:"):
                                func_name, args = extract_function_call(response)
                                if not func_name:
                                    break

                                user_response = await handle_function_call(
                                    session, func_name, args, conversation_history
                                )
                                if user_response:
                                    prompt += f"\nUser: {user_response}"
                                    prompt += f"\nAssistant: {response}"

                            elif response.startswith("FINAL_ANSWER:"):
                                # Verify the final answer against the original problem
                                if conversation_history:
                                    final_answer = float(
                                        response.split("[")[1].split("]")[0]
                                    )
                                    await session.call_tool(
                                        "verify",
                                        arguments={
                                            "expression": problem,
                                            "expected": final_answer,
                                        },
                                    )
                                break

                        except Exception as e:
                            console.print(f"[red]Error during conversation: {e}[/red]")
                            break

                    console.print("\n[green]Calculation completed![/green]")

                except Exception as e:
                    console.print(f"[red]Error in session: {e}[/red]")
                    raise

    except Exception as e:
        console.print(f"[red]Error in main: {e}[/red]")
        raise


if __name__ == "__main__":
    asyncio.run(main())
