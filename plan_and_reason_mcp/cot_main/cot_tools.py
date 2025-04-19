from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent
from rich.console import Console
from rich.panel import Panel
from typing import List, Optional, Union

# Initialize console and MCP server
console = Console()
mcp = FastMCP("CoTCalculator")


def create_step_panel(step: str, step_number: int) -> Panel:
    """Create a rich panel for displaying a reasoning step.

    Args:
        step: The reasoning step text
        step_number: The step number in the sequence

    Returns:
        A rich Panel object for display
    """
    return Panel(f"{step}", title=f"Step {step_number}", border_style="cyan")


@mcp.tool()
def show_reasoning(steps: List[str]) -> TextContent:
    """Display the step-by-step reasoning process.

    Args:
        steps: List of reasoning steps to display

    Returns:
        TextContent confirming the display
    """
    console.print("[blue]FUNCTION CALL:[/blue] show_reasoning()")
    for i, step in enumerate(steps, 1):
        console.print(create_step_panel(step, i))
    return TextContent(type="text", text="Reasoning shown")


@mcp.tool()
def calculate(expression: str) -> TextContent:
    """Calculate the result of a mathematical expression.

    Args:
        expression: Mathematical expression to evaluate

    Returns:
        TextContent containing the result or error message
    """
    console.print("[blue]FUNCTION CALL:[/blue] calculate()")
    console.print(f"[blue]Expression:[/blue] {expression}")
    try:
        result = eval(expression)
        console.print(f"[green]Result:[/green] {result}")
        return TextContent(type="text", text=str(result))
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        return TextContent(type="text", text=f"Error: {str(e)}")


@mcp.tool()
def verify(expression: str, expected: float) -> TextContent:
    """Verify if a calculation matches the expected result.

    Args:
        expression: Mathematical expression to evaluate
        expected: Expected result of the calculation

    Returns:
        TextContent indicating if the verification passed or failed
    """
    console.print("[blue]FUNCTION CALL:[/blue] verify()")
    console.print(f"[blue]Verifying:[/blue] {expression} = {expected}")
    try:
        actual = float(eval(expression))
        is_correct = abs(actual - float(expected)) < 1e-10

        if is_correct:
            console.print(f"[green]✓ Correct! {expression} = {expected}[/green]")
        else:
            console.print(
                f"[red]✗ Incorrect! {expression} should be {actual}, got {expected}[/red]"
            )

        return TextContent(type="text", text=str(is_correct))
    except Exception as e:
        console.print(f"[red]Error:[/red] {str(e)}")
        return TextContent(type="text", text=f"Error: {str(e)}")


def run_server(dev_mode: bool = False) -> None:
    """Run the MCP server in either development or production mode.

    Args:
        dev_mode: If True, run in development mode with console output
    """
    if dev_mode:
        console.print(
            Panel("CoT Tools Server (Development Mode)", border_style="magenta")
        )
        mcp.run()
    else:
        mcp.run(transport="stdio")


if __name__ == "__main__":
    import sys

    dev_mode = len(sys.argv) > 1 and sys.argv[1] == "dev"
    run_server(dev_mode)
