# FastMCP Client-Server Implementation

This directory contains a working FastMCP client-server implementation based on the official [FastMCP documentation](https://gofastmcp.com/).

## Files Overview

- `basic_server.py` - FastMCP server with tools, resources, and prompts
- `basic_client.py` - **Working client using in-memory transport** ✅
- `basic_client_stdio.py` - Comprehensive client with stdio and fallback options
- `test_in_memory.py` - Standalone test demonstrating in-memory transport
- `basic_client_fixed.py` - Attempted stdio fix (Windows compatibility issues)

## Key Findings

### Issue: "Failed to initialize server session"

The original error occurred when trying to use **stdio transport** on Windows. This is a known compatibility issue with FastMCP on Windows systems.

### Solution: In-Memory Transport

Based on the [FastMCP Client Documentation](https://gofastmcp.com/clients/client), the **in-memory transport** is the recommended approach for:
- Testing and development
- Same-process communication
- Windows compatibility

## Working Implementation

### Server (`basic_server.py`)
```python
from fastmcp import FastMCP

mcp = FastMCP("basic_server")

@mcp.tool()
async def add(a: int, b: int) -> int:
    """Add two numbers together"""
    return a + b

# More tools, resources, and prompts...

if __name__ == "__main__":
    mcp.run()  # Default stdio transport
```

### Client (`basic_client.py`)
```python
from fastmcp import Client
from basic_server import mcp as server_instance

async def main():
    # In-memory transport - most reliable
    client = Client(server_instance)
    
    async with client:
        tools = await client.list_tools()
        result = await client.call_tool("add", {"a": 1, "b": 2})
        # ... more operations
```

## Transport Options

### 1. In-Memory Transport (Recommended)
- **Use case**: Testing, development, same-process communication
- **Pros**: Fast, reliable, works on all platforms
- **Cons**: Server and client must be in same process

```python
from basic_server import mcp as server_instance
client = Client(server_instance)
```

### 2. Stdio Transport
- **Use case**: Production, separate processes
- **Pros**: True client-server separation
- **Cons**: Windows compatibility issues

```python
client = Client("basic_server.py")  # Auto-infers PythonStdioTransport
```

### 3. HTTP Transport
- **Use case**: Remote servers, web deployments
- **Pros**: Network communication, scalable
- **Cons**: More complex setup

```python
client = Client("https://example.com/mcp")  # Auto-infers StreamableHttpTransport
```

## Running the Examples

### Quick Test (Recommended)
```bash
python basic_client.py
```

### Comprehensive Test with Fallback
```bash
python basic_client_stdio.py
```

### Standalone In-Memory Test
```bash
python test_in_memory.py
```

## Key FastMCP Patterns

### 1. Connection Lifecycle
Always use `async with` for proper connection management:
```python
async with client:
    # All operations here
    pass
# Connection automatically closed
```

### 2. Tool Definition
```python
@mcp.tool()
async def my_tool(param: str) -> str:
    """Tool description for LLM"""
    return f"Result: {param}"
```

### 3. Resource Definition
```python
@mcp.resource("config://version")
def get_version():
    return "1.0.0"

@mcp.resource("users://{user_id}/profile")
def get_profile(user_id: int):
    return {"id": user_id, "name": f"User {user_id}"}
```

### 4. Error Handling
```python
try:
    async with client:
        result = await client.call_tool("tool_name", {"arg": "value"})
except Exception as e:
    print(f"Error: {e}")
```

## Documentation References

- [FastMCP Client Overview](https://gofastmcp.com/clients/client)
- [FastMCP Transports](https://gofastmcp.com/clients/transports)
- [FastMCP GitHub Repository](https://github.com/jlowin/fastmcp)
- [FastMCP Quickstart](https://gofastmcp.com/getting-started/quickstart)

## Troubleshooting

### "Failed to initialize server session"
- **Cause**: Windows stdio transport compatibility issues
- **Solution**: Use in-memory transport (`Client(server_instance)`)

### Import Errors
- **Cause**: Missing FastMCP installation
- **Solution**: `pip install fastmcp` or `uv add fastmcp`

### Connection Timeouts
- **Cause**: Server not responding or path issues
- **Solution**: Check server script path and use absolute paths

## Best Practices

1. **Use in-memory transport for development and testing**
2. **Always use `async with` for client connections**
3. **Add proper error handling and timeouts**
4. **Test both transport methods if deploying to production**
5. **Follow FastMCP documentation patterns exactly**

This implementation demonstrates the correct FastMCP patterns and provides working solutions for the common Windows stdio transport issues.
