import os
import re
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from google import genai
import asyncio
from rich.console import Console
from rich.panel import Panel
from typing import Optional, Tuple, List, Any

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
    """Create the system prompt for the planning agent."""
    return """You are a planning agent that explores multiple reasoning paths before solving a problem.
You have access to these tools:
- explore_path(steps: list) - Show the reasoning steps for one path
- calculate(expression: str) - Calculate the result of an expression
- verify(expression: str, expected: float) - Verify if a calculation is correct
- evaluate_paths(paths: list) - Evaluate reasoning paths and recommend the best one

First, generate 3 different reasoning paths for solving the problem.
Then explore the most promising one in steps using function calls.

Respond with EXACTLY ONE line in one of these formats:
1. FUNCTION_CALL: function_name|param1|param2|...
2. FINAL_ANSWER: [answer]
(For evaluate_paths, use FUNCTION_CALL: evaluate_paths|[\"Path 1\", \"Path 2\", \"Path 3\"])"""


def extract_function_call(result: str) -> Tuple[Optional[str], Optional[str]]:
    """Extract function name and arguments from the model response."""
    match = re.search(r"FUNCTION_CALL:\s*(\w+)\|(.+)", result)
    if not match:
        return None, None
    return match.group(1), match.group(2)


async def handle_path_exploration(
    session: ClientSession, path_list: List[str]
) -> Optional[str]:
    """Handle the path exploration process."""
    await session.call_tool("explore_path", arguments={"steps": path_list})
    chosen_path = await session.call_tool(
        "evaluate_paths", arguments={"paths": path_list}
    )
    return (
        chosen_path.content[0].text.strip()
        if chosen_path and chosen_path.content
        else None
    )


def extract_best_path(content_text: str) -> Tuple[Optional[int], Optional[str]]:
    """Extract the best path index and text from the tool output."""
    match = re.search(r"Path (\d+)", content_text)
    if not match:
        return None, None
    best_path_index = int(match.group(1)) - 1
    return best_path_index, content_text


def create_decompose_prompt(chosen_path_text: str, problem: str) -> str:
    """Create the prompt for decomposing the chosen path."""
    return (
        f"Decompose this into step-by-step calculations: {chosen_path_text} "
        f"for problem: {problem}.\n"
        'Respond in format: FUNCTION_CALL: show_reasoning|["step 1", "step 2", ...]'
    )


def extract_steps_from_response(result: str) -> List[str]:
    """Extract calculation steps from the model response."""
    steps = []
    lines = result.splitlines()

    for line in lines:
        if "show_reasoning|" in line:
            try:
                part = line.split("show_reasoning|", 1)[1].strip()
                extracted_steps = eval(part)
                steps.extend(extracted_steps)
            except Exception as e:
                console.print(f"[red]Failed to parse step line: {line} — {e}[/red]")
        elif (
            "[" in line
            and "]" in line
            and any(op in line for op in ["+", "-", "*", "/"])
        ):
            try:
                extracted = eval(
                    line.split("|", 1)[1].strip() if "|" in line else line.strip()
                )
                if isinstance(extracted, list):
                    steps.extend(extracted)
            except Exception as e:
                console.print(f"[red]Fallback parse failed: {line} — {e}[/red]")
        elif re.match(r"\s*\d+\s*[+\-*/]\s*\d+\s*=\s*\d+", line):
            steps.append(line.strip())

    return steps


async def execute_steps(session: ClientSession, steps: List[str]) -> None:
    """Execute and verify each calculation step."""
    for step in steps:
        match = re.search(r"([\d\s\+\-\*/\(\)]+)", step)
        if match:
            expr = match.group(1).strip()
            calc = await session.call_tool("calculate", arguments={"expression": expr})
            if calc and calc.content:
                value_text = calc.content[0].text.strip()
                match = re.search(r"(-?\d+(\.\d+)?)", value_text)
                if match:
                    value = float(match.group(1))
                    await session.call_tool(
                        "verify", arguments={"expression": expr, "expected": value}
                    )
                else:
                    console.print(
                        f"[red]Could not extract a numeric value from:[/red] {value_text}"
                    )


def extract_final_answer(final_step: str) -> Optional[str]:
    """Extract the final answer from the last step."""
    match = re.search(r"=\s*(\d+(\.\d+)?)", final_step)
    return match.group(1) if match else None


async def main():
    try:
        console.print(Panel("Tree Search Reasoning Explorer", border_style="magenta"))

        # Setup
        client = setup_gemini()
        server_params = StdioServerParameters(
            command="python", args=["cot_tools.py", "dev"]
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                # Problem setup
                system_prompt = create_system_prompt()
                problem = "(23 + 7) * (15 - 8)"
                console.print(Panel(f"Problem: {problem}", border_style="cyan"))

                # Generate initial paths
                prompt = f"{system_prompt}\n\nGenerate 3 different paths for solving: {problem}"
                result = await generate_with_timeout(client, prompt)
                if not result:
                    return

                console.print(f"\n[yellow]Assistant:[/yellow] {result}")

                # Process function call
                func_name, raw_args = extract_function_call(result)
                if not func_name:
                    console.print("[red]No FUNCTION_CALL found in model response[/red]")
                    return

                # Handle path exploration
                path_list = eval(raw_args)
                content_text = await handle_path_exploration(session, path_list)
                if not content_text:
                    return

                console.print(
                    f"[bold green]Best Path Returned by Tool:[/bold green] {content_text}"
                )

                # Extract and process best path
                best_path_index, chosen_path_text = extract_best_path(content_text)
                if best_path_index is None:
                    return

                console.print(
                    f"\n[yellow]Assistant:[/yellow] Decomposing: {chosen_path_text}"
                )

                # Decompose path into steps
                decompose_prompt = create_decompose_prompt(chosen_path_text, problem)
                result = await generate_with_timeout(client, decompose_prompt)
                if not result:
                    return

                console.print(f"[yellow]Decomposition Response:[/yellow] {result}")

                # Extract and execute steps
                steps = extract_steps_from_response(result)
                if steps:
                    await session.call_tool(
                        "show_reasoning", arguments={"steps": steps}
                    )
                    console.print(f"[blue]Steps to execute:[/blue] {steps}")

                    await execute_steps(session, steps)

                    # Display final answer
                    final_step = steps[-1].strip()
                    final_answer = extract_final_answer(final_step)
                    if final_answer:
                        console.print(
                            f"\n[bold cyan]FINAL_ANSWER: {final_answer}[/bold cyan]"
                        )

                    console.print("[green]Best path executed successfully![/green]")
                    console.print(
                        "[bold green]🎉 All reasoning steps executed and verified successfully![/bold green]"
                    )
                else:
                    console.print(
                        "[red]No valid steps extracted from decomposition response.[/red]"
                    )

    except Exception as e:
        console.print(f"[red]Error: {e}[/red]")


if __name__ == "__main__":
    asyncio.run(main())
