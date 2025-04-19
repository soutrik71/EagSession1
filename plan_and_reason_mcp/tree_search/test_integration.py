import os
import asyncio
import subprocess
import signal
import sys
from dotenv import load_dotenv
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client
from google import genai
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()


async def start_tool_server():
    """Start the cot_tools.py server in development mode."""
    try:
        process = subprocess.Popen(
            [sys.executable, "cot_tools.py", "dev"],
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
        )
        # Wait a bit for the server to start
        await asyncio.sleep(2)
        return process
    except Exception as e:
        console.print(f"[red]Error starting tool server: {e}[/red]")
        return None


async def stop_tool_server(process):
    """Stop the tool server process."""
    if process:
        process.terminate()
        try:
            process.wait(timeout=5)
        except subprocess.TimeoutExpired:
            process.kill()


async def test_gemini():
    """Test Gemini API connection and response."""
    try:
        load_dotenv()
        api_key = os.getenv("GEMINI_API_KEY")
        if not api_key:
            console.print(
                "[red]Error: GEMINI_API_KEY not found in environment variables[/red]"
            )
            return False

        client = genai.Client(api_key=api_key)
        prompt = "What is 2 + 2?"

        response = client.models.generate_content(
            model="gemini-2.0-flash", contents=prompt
        )

        if response and response.text:
            console.print("[green]✓ Gemini API Test Successful[/green]")
            console.print(f"[blue]Response:[/blue] {response.text.strip()}")
            return True
        else:
            console.print("[red]Error: No response from Gemini API[/red]")
            return False
    except Exception as e:
        console.print(f"[red]Error testing Gemini API: {e}[/red]")
        return False


async def test_tools():
    """Test tool communication through StdioServerParameters."""
    tool_server = None
    try:
        # Start the tool server
        tool_server = await start_tool_server()
        if not tool_server:
            return False

        server_params = StdioServerParameters(
            command=sys.executable, args=["cot_tools.py", "dev"]
        )

        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()

                # Test each tool with timeout
                tools = [
                    ("calculate", {"expression": "2 + 2"}),
                    ("verify", {"expression": "2 + 2", "expected": 4}),
                    ("show_reasoning", {"steps": ["Step 1: 2 + 2", "Step 2: = 4"]}),
                ]

                results = []
                for tool_name, args in tools:
                    try:
                        # Add timeout to each tool call
                        response = await asyncio.wait_for(
                            session.call_tool(tool_name, arguments=args), timeout=5
                        )
                        success = response and response.content
                        results.append((tool_name, success))
                        if success:
                            console.print(
                                f"[green]✓ {tool_name} test successful[/green]"
                            )
                        else:
                            console.print(
                                f"[red]✗ {tool_name} test failed - no content[/red]"
                            )
                    except asyncio.TimeoutError:
                        console.print(f"[red]✗ {tool_name} test timed out[/red]")
                        results.append((tool_name, False))
                    except Exception as e:
                        console.print(f"[red]Error testing {tool_name}: {e}[/red]")
                        results.append((tool_name, False))

                # Display results in a table
                table = Table(title="Tool Test Results")
                table.add_column("Tool", style="cyan")
                table.add_column("Status", style="green")

                for tool_name, success in results:
                    status = "✓" if success else "✗"
                    table.add_row(tool_name, status)

                console.print(table)

                return all(success for _, success in results)
    except Exception as e:
        console.print(f"[red]Error testing tools: {e}[/red]")
        return False
    finally:
        # Always stop the tool server
        if tool_server:
            await stop_tool_server(tool_server)


async def main():
    console.print(Panel("Integration Test Suite", border_style="magenta"))

    # Test Gemini
    console.print("\n[bold]Testing Gemini API...[/bold]")
    gemini_success = await test_gemini()

    # Test Tools
    console.print("\n[bold]Testing Tool Communication...[/bold]")
    tools_success = await test_tools()

    # Summary
    console.print("\n[bold]Test Summary:[/bold]")
    console.print(
        f"Gemini API: {'[green]✓ PASS[/green]' if gemini_success else '[red]✗ FAIL[/red]'}"
    )
    console.print(
        f"Tool Communication: {'[green]✓ PASS[/green]' if tools_success else '[red]✗ FAIL[/red]'}"
    )

    if gemini_success and tools_success:
        console.print("\n[bold green]🎉 All tests passed successfully![/bold green]")
    else:
        console.print(
            "\n[bold red]⚠ Some tests failed. Please check the errors above.[/bold red]"
        )


if __name__ == "__main__":
    asyncio.run(main())
