# FastMCP Multi-Server Implementation - Complete Guide

This directory contains a comprehensive FastMCP (Model Control Protocol) implementation demonstrating multiple transport types, server configurations, and client patterns. This README serves as the complete documentation for understanding and using this codebase.

## 🌟 Overview

This implementation showcases FastMCP's ability to:
- **Multiple Transport Types**: STDIO, HTTP Stream, and SSE (Server-Sent Events)
- **Multi-Server Architecture**: Connect to multiple servers simultaneously
- **Comprehensive Tool Sets**: Math operations, string manipulation, weather data, distance calculations
- **Context Features**: Logging, progress reporting, and error handling
- **Cross-Platform Compatibility**: Windows and Unix-like systems

## 📁 File Structure

### 🖥️ Server Implementations

| File | Transport | Port | Description |
|------|-----------|------|-------------|
| `tools_server_extended_stdio.py` | STDIO | N/A | Extended tools with string manipulation, encoding, date/time |
| `tools_server_stdio.py` | STDIO | N/A | Basic math, weather, distance calculation tools |
| `tools_server_stream.py` | HTTP Stream | 4200 | Same tools as stdio but over HTTP |
| `tools_server_sse.py` | SSE | 4201 | Same tools as stdio but over Server-Sent Events |

### 🔧 Server Launchers

| File | Purpose |
|------|---------|
| `start_stream_server.py` | Launches HTTP Stream server on port 4200 |
| `start_sse_server.py` | Launches SSE server on port 4201 |

### 👥 Client Implementations

| File | Transport | Description |
|------|-----------|-------------|
| `test_client_stdio.py` | STDIO | Single STDIO server client with fallback options |
| `test_client_stream.py` | HTTP Stream | Single HTTP Stream server client with retry logic |
| `test_client_sse.py` | SSE | Single SSE server client with retry logic |
| `test_multi_server_client.py` | **Multi-Transport** | **Connects to all three server types simultaneously** |

## 🚀 Quick Start

### 1. Start All Servers

```bash
# Terminal 1: Start HTTP Stream Server
python start_stream_server.py

# Terminal 2: Start SSE Server  
python start_sse_server.py

# Terminal 3: STDIO server starts automatically with multi-server client
```

### 2. Run Multi-Server Client

```bash
# Test all servers simultaneously
python test_multi_server_client.py
```

### 3. Test Individual Servers

```bash
# Test individual transports
python test_client_stdio.py
python test_client_stream.py
python test_client_sse.py
```

## 🏗️ Architecture Deep Dive

### Multi-Server Configuration

The multi-server client (`test_multi_server_client.py`) uses this configuration:

```python
config = {
    "mcpServers": {
        # STDIO server for extended tools
        "stdio_tools": {
            "command": "python",
            "args": ["./tools_server_extended_stdio.py"],
            "env": {"DEBUG": "true"}
        },
        # HTTP Stream server for math and weather tools
        "stream_tools": {
            "url": "http://127.0.0.1:4200/mcp/",
            "transport": "streamable-http",
        },
        # SSE server for real-time tools
        "sse_tools": {
            "url": "http://127.0.0.1:4201/sse", 
            "transport": "sse"
        },
    }
}
```

### Tool Naming Convention

Each server prefixes its tools with the server name:
- **STDIO tools**: `stdio_tools_*` (e.g., `stdio_tools_reverse_string`)
- **Stream tools**: `stream_tools_*` (e.g., `stream_tools_add`)
- **SSE tools**: `sse_tools_*` (e.g., `sse_tools_add`)

## 🛠️ Server Details

### 1. Extended STDIO Server (`tools_server_extended_stdio.py`)

**Purpose**: Comprehensive tool server with advanced string manipulation and utility functions.

**Key Features**:
- **String Operations**: Reverse, count characters, transform case
- **Random Generation**: Secure passwords, dice rolling
- **Encoding/Hashing**: Base64, MD5, SHA256, SHA512
- **Date/Time**: Current time, date calculations
- **List Processing**: Sorting, duplicate detection
- **Context Demonstration**: Advanced logging and progress reporting

**Tools Available**:
```python
# String manipulation
stdio_tools_reverse_string(text: str) -> str
stdio_tools_count_characters(text: str, include_spaces: bool) -> Dict
stdio_tools_transform_text(input: TextTransformInput) -> str

# Random generation
stdio_tools_generate_password(length: int, options...) -> str
stdio_tools_roll_dice(sides: int, count: int) -> Dict

# Encoding/Hashing
stdio_tools_hash_text(input: HashInput) -> Dict
stdio_tools_encode_base64(text: str) -> Dict
stdio_tools_decode_base64(encoded_text: str) -> Dict

# Date/Time
stdio_tools_get_current_time(timezone: str, format_string: str) -> Dict
stdio_tools_calculate_date_difference(input: DateCalculationInput) -> Dict

# List operations
stdio_tools_sort_list(items: List[str], options...) -> Dict
stdio_tools_find_duplicates(items: List[str]) -> Dict

# Context features
stdio_tools_demonstrate_extended_context(operation: str) -> str
```

### 2. Basic STDIO Server (`tools_server_stdio.py`)

**Purpose**: Core mathematical and utility operations.

**Key Features**:
- **Basic Math**: Add, subtract, multiply, divide with error handling
- **Trigonometry**: Sine, cosine, tangent calculations
- **Logarithms**: Configurable base logarithm calculations
- **Geography**: Distance calculation between places using OpenStreetMap
- **Weather**: Weather information using SerpAPI (requires API key)
- **Context Demo**: Logging and progress reporting demonstration

### 3. HTTP Stream Server (`tools_server_stream.py`)

**Purpose**: Same functionality as basic STDIO server but over HTTP transport.

**Configuration**:
```python
mcp.run(
    transport="streamable-http",
    host="127.0.0.1",
    port=4200,
    log_level="debug",
)
```

**Access URL**: `http://127.0.0.1:4200/mcp/`

### 4. SSE Server (`tools_server_sse.py`)

**Purpose**: Same functionality as basic STDIO server but over Server-Sent Events.

**Configuration**:
```python
mcp.run(
    transport="sse",
    host="127.0.0.1",
    port=4201,
    path="/sse",
    log_level="debug",
)
```

**Access URL**: `http://127.0.0.1:4201/sse`

## 👥 Client Implementations

### 1. Multi-Server Client (`test_multi_server_client.py`)

**Purpose**: Demonstrates FastMCP's ability to connect to multiple servers with different transports simultaneously.

**Key Features**:
- **Concurrent Connections**: Connects to STDIO, HTTP Stream, and SSE servers
- **Tool Discovery**: Lists and categorizes tools by server prefix
- **Comprehensive Testing**: Tests all tool types across all servers
- **Error Handling**: Graceful failure when servers are unavailable
- **Performance Testing**: Concurrent requests across different transports

**Test Categories**:
1. **STDIO Server Tools**: String operations, password generation, time functions
2. **HTTP Stream Tools**: Math operations, trigonometry, weather, distance
3. **SSE Tools**: Real-time operations, rapid requests
4. **Context Features**: Logging and progress reporting across all servers
5. **Error Handling**: Division by zero, invalid inputs
6. **Concurrent Operations**: Simultaneous requests to all server types

### 2. Individual Transport Clients

#### STDIO Client (`test_client_stdio.py`)
- **Transport**: `PythonStdioTransport`
- **Fallback Strategy**: Multiple Python command attempts
- **Windows Compatibility**: Handles Windows-specific Python executable paths

#### HTTP Stream Client (`test_client_stream.py`)
- **Transport**: `StreamableHttpTransport`
- **URL**: `http://127.0.0.1:4200/mcp/`
- **Features**: Retry logic, SSL handling, performance testing

#### SSE Client (`test_client_sse.py`)
- **Transport**: `SSETransport`
- **URL**: `http://127.0.0.1:4201/sse`
- **Features**: Real-time event handling, rapid request testing

## 🔧 Configuration & Setup

### Environment Variables

Create a `.env` file for optional features:
```bash
# Optional: For weather functionality
SERP_API_KEY=your_serpapi_key_here

# Optional: For debugging
DEBUG=true
```

### Dependencies

```bash
# Install FastMCP
pip install fastmcp

# Or using uv
uv add fastmcp

# Additional dependencies
pip install requests python-dotenv pydantic tenacity
```

### SSL Configuration

For local testing, SSL verification is disabled:
```python
os.environ.pop("SSL_CERT_FILE", None)
```

## 🧪 Testing Scenarios

### 1. Full Multi-Server Test

```bash
python test_multi_server_client.py
```

**Expected Output**:
- ✅ Connection to all three server types
- 📋 Tool discovery (35+ tools across all servers)
- 🖥️ STDIO tool testing (string operations, utilities)
- 🌐 HTTP Stream tool testing (math, weather, distance)
- 📡 SSE tool testing (real-time operations)
- 🎯 Context feature demonstrations
- ⚡ Concurrent request testing

### 2. Individual Server Tests

Each client tests the same core functionality but over different transports:

```bash
# Test STDIO transport
python test_client_stdio.py

# Test HTTP Stream transport  
python test_client_stream.py

# Test SSE transport
python test_client_sse.py
```

### 3. Server Startup Tests

```bash
# Start servers individually
python start_stream_server.py
python start_sse_server.py

# STDIO server starts automatically with client
```

## 🔍 Key Implementation Patterns

### 1. Multi-Server Client Pattern

```python
from fastmcp import Client

# Multi-server configuration
config = {
    "mcpServers": {
        "server1": {"command": "python", "args": ["server1.py"]},
        "server2": {"url": "http://localhost:4200/mcp/", "transport": "streamable-http"},
        "server3": {"url": "http://localhost:4201/sse", "transport": "sse"}
    }
}

client = Client(config)

async def main():
    async with client:
        # Tools are prefixed with server names
        result1 = await client.call_tool("server1_tool", {"param": "value"})
        result2 = await client.call_tool("server2_tool", {"param": "value"})
        result3 = await client.call_tool("server3_tool", {"param": "value"})
```

### 2. Context-Aware Tool Pattern

```python
@mcp.tool()
async def advanced_tool(
    param: Annotated[str, Field(description="Parameter description")],
    ctx: Context
) -> str:
    """Tool with context logging and progress reporting"""
    await ctx.info(f"Processing: {param}")
    await ctx.report_progress(0, 100, "Starting...")
    
    # Processing logic here
    
    await ctx.report_progress(100, 100, "Complete!")
    return result
```

### 3. Pydantic Model Pattern

```python
class ToolInput(BaseModel):
    text: str = Field(description="Input text")
    operation: str = Field(description="Operation type")

@mcp.tool()
async def structured_tool(input: ToolInput, ctx: Context = None) -> str:
    """Tool using Pydantic models for structured input"""
    return f"Processed {input.text} with {input.operation}"
```

### 4. Error Handling Pattern

```python
@mcp.tool()
async def safe_tool(value: int, ctx: Context = None) -> str:
    """Tool with comprehensive error handling"""
    try:
        if value < 0:
            if ctx:
                await ctx.error(f"Invalid value: {value}")
            raise ToolError("Value must be positive")
        
        result = process_value(value)
        if ctx:
            await ctx.info(f"Successfully processed: {value}")
        return result
        
    except Exception as e:
        if ctx:
            await ctx.error(f"Processing failed: {str(e)}")
        raise ToolError(f"Tool execution failed: {str(e)}")
```

## 🚨 Troubleshooting

### Common Issues & Solutions

#### 1. "Failed to initialize server session"
**Cause**: STDIO transport issues on Windows
**Solution**: 
- Use the multi-server client which handles this automatically
- Check Python executable paths in `test_client_stdio.py`

#### 2. Connection Refused (HTTP/SSE)
**Cause**: Servers not running
**Solution**:
```bash
# Start the required servers
python start_stream_server.py  # For HTTP Stream
python start_sse_server.py     # For SSE
```

#### 3. SSL Certificate Errors
**Cause**: Local SSL configuration issues
**Solution**: SSL verification is automatically disabled for local testing

#### 4. Import Errors
**Cause**: Missing dependencies
**Solution**:
```bash
pip install fastmcp requests python-dotenv pydantic tenacity
```

#### 5. Weather API Errors
**Cause**: Missing SERP_API_KEY
**Solution**: Add to `.env` file or weather tools will show helpful error messages

### Debug Mode

Enable debug logging in any client:
```python
logging.basicConfig(level=logging.DEBUG)
mcp_logger = logging.getLogger("fastmcp")
mcp_logger.setLevel(logging.DEBUG)
```

## 🌐 Transport Comparison

| Feature | STDIO | HTTP Stream | SSE |
|---------|-------|-------------|-----|
| **Setup Complexity** | Simple | Medium | Medium |
| **Network Required** | No | Yes | Yes |
| **Real-time Events** | Limited | Yes | Excellent |
| **Scalability** | Low | High | High |
| **Windows Compatibility** | Issues | Excellent | Excellent |
| **Development Speed** | Fast | Medium | Medium |
| **Production Ready** | Yes* | Yes | Yes |

*STDIO has Windows compatibility issues but works well on Unix-like systems.

## 📈 Performance Characteristics

### STDIO Transport
- **Latency**: Lowest (direct process communication)
- **Throughput**: High for single client
- **Concurrency**: Limited by process model

### HTTP Stream Transport  
- **Latency**: Medium (HTTP overhead)
- **Throughput**: High with connection pooling
- **Concurrency**: Excellent (stateless)

### SSE Transport
- **Latency**: Medium (HTTP + event stream)
- **Throughput**: High for real-time updates
- **Concurrency**: Excellent (persistent connections)

## 🔮 Advanced Usage

### Custom Transport Configuration

```python
# Custom HTTP transport with authentication
transport = StreamableHttpTransport(
    url="https://api.example.com/mcp/",
    headers={"Authorization": "Bearer token"}
)
client = Client(transport)

# Custom SSE transport with parameters
transport = SSETransport(
    url="https://events.example.com/sse",
    params={"channel": "tools"}
)
client = Client(transport)
```

### Resource Management

```python
# Proper resource cleanup
async def managed_client_usage():
    async with client:
        # All operations here
        tools = await client.list_tools()
        for tool in tools:
            result = await client.call_tool(tool.name, {})
    # Client automatically disconnected
```

### Concurrent Multi-Server Operations

```python
async def concurrent_operations():
    async with client:
        # Execute operations on different servers concurrently
        tasks = [
            client.call_tool("stdio_tools_reverse_string", {"text": "hello"}),
            client.call_tool("stream_tools_add", {"a": 1, "b": 2}),
            client.call_tool("sse_tools_multiply", {"a": 3, "b": 4})
        ]
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        return results
```

## 📚 References

- [FastMCP Official Documentation](https://gofastmcp.com/)
- [FastMCP Client Guide](https://gofastmcp.com/clients/client)
- [FastMCP Transports](https://gofastmcp.com/clients/transports)
- [FastMCP GitHub Repository](https://github.com/jlowin/fastmcp)
- [Model Control Protocol Specification](https://spec.modelcontextprotocol.io/)

## 🎯 Best Practices

1. **Always use `async with` for client connections**
2. **Implement proper error handling with context logging**
3. **Use Pydantic models for complex tool inputs**
4. **Test all transport types in your environment**
5. **Monitor server health in production deployments**
6. **Use environment variables for configuration**
7. **Implement graceful degradation when servers are unavailable**
8. **Follow the tool naming conventions for multi-server setups**

## 🏆 Success Metrics

When everything is working correctly, you should see:

✅ **Multi-Server Client**: 35+ tools discovered across 3 servers  
✅ **STDIO Tools**: String manipulation, encoding, date/time operations  
✅ **HTTP Stream Tools**: Math operations, weather, distance calculations  
✅ **SSE Tools**: Real-time operations and rapid requests  
✅ **Context Features**: Logging and progress reporting across all servers  
✅ **Error Handling**: Graceful failure and recovery  
✅ **Concurrent Operations**: Simultaneous requests across different transports  

This implementation demonstrates FastMCP's full capabilities and serves as a comprehensive reference for building production-ready MCP applications.
