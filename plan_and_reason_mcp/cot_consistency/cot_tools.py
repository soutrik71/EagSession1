from typing import List, Tuple, Dict, Any
from mcp.server.fastmcp import FastMCP
from mcp.types import TextContent
from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich import box
import re

# Initialize console for rich text output
console = Console()
mcp = FastMCP("CoTCalculator")


@mcp.tool()
def show_reasoning(steps: List[str]) -> TextContent:
    """Show the step-by-step reasoning process.

    Args:
        steps: List of reasoning steps to display

    Returns:
        TextContent indicating success
    """
    console.print("[blue]FUNCTION CALL:[/blue] show_reasoning()")
    for i, step in enumerate(steps, 1):
        console.print(Panel(f"{step}", title=f"Step {i}", border_style="cyan"))
    return TextContent(type="text", text="Reasoning shown")


@mcp.tool()
def calculate(expression: str) -> TextContent:
    """Calculate the result of an expression.

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
    """Verify if a calculation is correct.

    Args:
        expression: Expression to evaluate
        expected: Expected result

    Returns:
        TextContent indicating if verification passed
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


def create_analysis_table() -> Table:
    """Create a table for step analysis.

    Returns:
        A configured Table object for displaying analysis
    """
    return Table(
        title="Step-by-Step Consistency Analysis",
        box=box.ROUNDED,
        show_header=True,
        header_style="bold cyan",
    )


def analyze_calculation(
    expression: str, result: float, step_num: int
) -> Tuple[List[str], List[str], List[str]]:
    """Analyze a single calculation step.

    Args:
        expression: The expression being evaluated
        result: The result of the calculation
        step_num: The step number in the sequence

    Returns:
        Tuple of (checks, issues, warnings)
    """
    checks = []
    issues = []
    warnings = []

    # 1. Basic Calculation Verification
    try:
        expected = eval(expression)
        if abs(float(expected) - float(result)) < 1e-10:
            checks.append("[green]✓ Calculation verified[/green]")
        else:
            issues.append(f"Step {step_num}: Calculation mismatch")
            checks.append("[red]✗ Calculation error[/red]")
    except Exception as e:
        warnings.append(f"Step {step_num}: Couldn't verify calculation")
        checks.append("[yellow]! Verification failed[/yellow]")

    # 2. Pattern Analysis
    operators = re.findall(r"[\+\-\*\/\(\)]", expression)
    if "(" in operators and ")" not in operators:
        warnings.append(f"Step {step_num}: Mismatched parentheses")
        checks.append("[red]✗ Invalid parentheses[/red]")

    # 3. Result Range Check
    if abs(result) > 1e6:
        warnings.append(f"Step {step_num}: Very large result")
        checks.append("[yellow]! Large result[/yellow]")
    elif abs(result) < 1e-6 and result != 0:
        warnings.append(f"Step {step_num}: Very small result")
        checks.append("[yellow]! Small result[/yellow]")

    return checks, issues, warnings


def analyze_dependencies(
    expression: str, result: float, step_num: int, previous: Tuple[str, float]
) -> Tuple[List[str], List[str], List[str]]:
    """Analyze dependencies between calculation steps.

    Args:
        expression: Current expression
        result: Current result
        step_num: Current step number
        previous: Previous step's (expression, result)

    Returns:
        Tuple of (checks, issues, warnings)
    """
    checks = []
    issues = []
    warnings = []

    if previous:
        prev_expr, prev_result = previous
        if str(prev_result) in expression:
            checks.append("[green]✓ Uses previous result[/green]")
            warnings.append(f"Step {step_num} builds on step {step_num-1}")
        else:
            checks.append("[blue]○ Independent step[/blue]")

        # Magnitude Check
        if result != 0 and prev_result != 0:
            ratio = abs(result / prev_result)
            if ratio > 1000:
                warnings.append(f"Step {step_num}: Large increase ({ratio:.2f}x)")
                checks.append("[yellow]! Large magnitude increase[/yellow]")
            elif ratio < 0.001:
                warnings.append(f"Step {step_num}: Large decrease ({1/ratio:.2f}x)")
                checks.append("[yellow]! Large magnitude decrease[/yellow]")

    return checks, issues, warnings


@mcp.tool()
def check_consistency(steps: List[Tuple[str, float]]) -> TextContent:
    """Check if calculation steps are consistent with each other.

    Args:
        steps: List of (expression, result) tuples

    Returns:
        TextContent containing analysis results
    """
    console.print("[blue]FUNCTION CALL:[/blue] check_consistency()")

    try:
        table = create_analysis_table()
        table.add_column("Step", style="cyan")
        table.add_column("Expression", style="blue")
        table.add_column("Result", style="green")
        table.add_column("Checks", style="yellow")

        all_issues = []
        all_warnings = []
        all_insights = []
        previous = None

        for i, (expression, result) in enumerate(steps, 1):
            # Analyze current step
            calc_checks, calc_issues, calc_warnings = analyze_calculation(
                expression, result, i
            )
            dep_checks, dep_issues, dep_warnings = analyze_dependencies(
                expression, result, i, previous
            )

            all_issues.extend(calc_issues)
            all_warnings.extend(calc_warnings)
            all_warnings.extend(dep_warnings)

            # Combine all checks
            checks = calc_checks + dep_checks

            # Add row to table
            table.add_row(f"Step {i}", expression, f"{result}", "\n".join(checks))

            previous = (expression, result)

        # Display Analysis
        console.print("\n[bold cyan]Consistency Analysis Report[/bold cyan]")
        console.print(table)

        if all_issues:
            console.print(
                Panel(
                    "\n".join(f"[red]• {issue}[/red]" for issue in all_issues),
                    title="Critical Issues",
                    border_style="red",
                )
            )

        if all_warnings:
            console.print(
                Panel(
                    "\n".join(
                        f"[yellow]• {warning}[/yellow]" for warning in all_warnings
                    ),
                    title="Warnings",
                    border_style="yellow",
                )
            )

        if all_insights:
            console.print(
                Panel(
                    "\n".join(f"[blue]• {insight}[/blue]" for insight in all_insights),
                    title="Analysis Insights",
                    border_style="blue",
                )
            )

        # Calculate consistency score
        total_checks = len(steps) * 5  # 5 types of checks per step
        passed_checks = total_checks - (len(all_issues) * 2 + len(all_warnings))
        consistency_score = (passed_checks / total_checks) * 100

        console.print(
            Panel(
                f"[bold]Consistency Score: {consistency_score:.1f}%[/bold]\n"
                f"Passed Checks: {passed_checks}/{total_checks}\n"
                f"Critical Issues: {len(all_issues)}\n"
                f"Warnings: {len(all_warnings)}\n"
                f"Insights: {len(all_insights)}",
                title="Summary",
                border_style=(
                    "green"
                    if consistency_score > 80
                    else "yellow" if consistency_score > 60 else "red"
                ),
            )
        )

        return TextContent(
            type="text",
            text=str(
                {
                    "consistency_score": consistency_score,
                    "issues": all_issues,
                    "warnings": all_warnings,
                    "insights": all_insights,
                }
            ),
        )
    except Exception as e:
        console.print(f"[red]Error in consistency check: {str(e)}[/red]")
        return TextContent(type="text", text=f"Error: {str(e)}")


if __name__ == "__main__":
    import sys

    if len(sys.argv) > 1 and sys.argv[1] == "dev":
        mcp.run()
    else:
        mcp.run(transport="stdio")
