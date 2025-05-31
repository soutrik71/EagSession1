# FastMCP SSE (Server-Sent Events) Tools Server

This directory contains a FastMCP tools server that runs with SSE (Server-Sent Events) transport, providing mathematical operations, distance calculations, weather information, and context feature demonstrations.

## 📡 SSE Transport

The server uses FastMCP's `sse` transport, which provides:
- Server-Sent Events based communication
- Real-time streaming capabilities
- Unidirectional server-to-client communication
- Better performance for streaming data
- Native browser support

## 📁 Files

### Server Files
- `tools_server_sse.py` - Main SSE server with all tools
- `start_sse_server.py` - Helper script to start the server

### Client Files
- `test_tools_client_sse.py` - Comprehensive test client for SSE server

### Documentation
- `SSE_README.md` - This documentation file

## 🚀 Quick Start

### 1. Start the SSE Server

```bash
# Option 1: Direct execution
python tools_server_sse.py

# Option 2: Using the helper script
python start_sse_server.py
```

The server will start on `http://127.0.0.1:4201/sse`

### 2. Test the Server

In a separate terminal:

```bash
python test_tools_client_sse.py
```

## 🛠️ Available Tools

### Mathematical Operations
- `add(a, b)` - Add two numbers
- `subtract(a, b)` - Subtract two numbers  
- `multiply(a, b)` - Multiply two numbers
- `divide(a, b)` - Divide two numbers (with zero-division protection)

### Trigonometric Functions
- `get_sine_value(x)` - Calculate sine of angle in radians
- `get_cosine_value(x)` - Calculate cosine of angle in radians
- `get_tangent_value(x)` - Calculate tangent of angle in radians

### Logarithm Functions
- `get_log_value(x, base=10.0)` - Calculate logarithm with custom base

### Geographic Tools
- `calculate_distance_between_places(place1, place2, unit="km")` - Calculate distance between two places using OpenStreetMap geocoding and Haversine formula

### Weather Information
- `get_weather(input: WeatherInput)` - Get weather information using SerpAPI
  - Requires `SERP_API_KEY` environment variable
  - Supports 1-7 day forecasts

### Context Demonstration
- `demonstrate_context_features(message)` - Showcase FastMCP context features including logging and progress reporting

## 🔧 Configuration

### Environment Variables

Create a `.env` file for optional features:

```env
# Required for weather functionality
SERP_API_KEY=your_serpapi_key_here
```

### Server Configuration

The server runs with these settings:
- **Transport**: `sse` (Server-Sent Events)
- **Host**: `127.0.0.1`
- **Port**: `4201`
- **Endpoint**: `/sse`
- **Log Level**: `debug`

## 🧪 Testing

The test client (`test_tools_client_sse.py`) performs comprehensive testing:

### Basic Tests
- ✅ Connection to SSE server
- ✅ Tool listing and availability
- ✅ Context features demonstration

### Mathematical Operations
- ✅ Addition, subtraction, multiplication, division
- ✅ Error handling (division by zero)
- ✅ Trigonometric functions (sin, cos, tan)
- ✅ Logarithm calculations with custom bases

### Geographic Features
- ✅ Distance calculation between cities
- ✅ Unit conversion (km/miles)
- ✅ Error handling (invalid places, units)

### Weather Information
- ✅ Current weather retrieval
- ✅ Multi-day forecasts
- ✅ Error handling (invalid locations, API key issues)

### SSE Specific Features
- ✅ Multiple rapid requests
- ✅ Concurrent request handling
- ✅ Real-time streaming performance
- ✅ Connection persistence

## 📊 Context Features

The SSE server includes full FastMCP Context integration:

### Logging Levels
- `ctx.debug()` - Debug information
- `ctx.info()` - General information
- `ctx.warning()` - Warning messages
- `ctx.error()` - Error messages

### Progress Reporting
- `ctx.report_progress(current, total, message)` - Real-time progress updates

### Context Information
- `ctx.request_id` - Unique request identifier
- `ctx.client_id` - Client identifier
- `ctx.http_request()` - HTTP request capabilities

## 🔍 Troubleshooting

### Server Won't Start
```bash
# Check if port 4201 is already in use
netstat -an | grep 4201

# Try a different port by modifying tools_server_sse.py
mcp.run(transport="sse", host="127.0.0.1", port=4202)
```

### Client Connection Issues
```bash
# Verify server is running
curl http://127.0.0.1:4201/sse

# Check firewall settings
# Ensure localhost connections are allowed
```

### Weather Tool Issues
```bash
# Verify SERP_API_KEY is set
echo $SERP_API_KEY

# Check .env file exists and contains the key
cat .env
```

### Import Errors
```bash
# Install required dependencies
pip install fastmcp requests python-dotenv pydantic

# Verify FastMCP installation
python -c "import fastmcp; print(fastmcp.__version__)"
```

## 🌟 SSE Transport Benefits

### Performance Advantages
- **Low Latency**: Direct server-to-client streaming
- **Efficient**: Minimal protocol overhead
- **Scalable**: Handles multiple concurrent connections well
- **Real-time**: Immediate data delivery

### Browser Compatibility
- **Native Support**: Built-in browser EventSource API
- **Automatic Reconnection**: Browser handles connection recovery
- **CORS Support**: Cross-origin resource sharing compatible
- **Streaming**: Continuous data flow without polling

### Development Benefits
- **Simple Protocol**: Easy to debug and monitor
- **HTTP Based**: Works with existing infrastructure
- **Firewall Friendly**: Uses standard HTTP ports
- **Logging**: Easy to trace requests and responses

## 📝 Example Usage

```python
from fastmcp import Client

async def example():
    # Connect to SSE server
    client = Client("http://127.0.0.1:4201/sse")
    
    async with client:
        # Test mathematical operation
        result = await client.call_tool("add", {"a": 15, "b": 25})
        print(f"15 + 25 = {result[0].text}")
        
        # Test distance calculation
        distance = await client.call_tool(
            "calculate_distance_between_places",
            {"place1": "Boston", "place2": "New York", "unit": "miles"}
        )
        print(distance[0].text)
        
        # Test context features
        demo = await client.call_tool(
            "demonstrate_context_features",
            {"message": "Hello SSE!"}
        )
        print(demo[0].text)
```

## 🔄 Concurrent Testing

The SSE implementation includes specific tests for concurrent operations:

```python
# Test concurrent requests
concurrent_tasks = []
for i in range(3):
    task = client.call_tool("multiply", {"a": i + 1, "b": (i + 1) * 10})
    concurrent_tasks.append(task)

concurrent_results = await asyncio.gather(*concurrent_tasks)
```

## 📊 Performance Comparison

| Feature | SSE | HTTP Stream | Stdio |
|---------|-----|-------------|-------|
| **Latency** | Low | Medium | Low |
| **Throughput** | High | High | Medium |
| **Browser Support** | Native | Limited | None |
| **Debugging** | Easy | Easy | Difficult |
| **Concurrency** | Excellent | Good | Limited |
| **Real-time** | Excellent | Good | Good |

## 🔗 Related Files

- See `test_tools_client_stream.py` for HTTP stream transport comparison
- See `tools_server_stream.py` for HTTP stream server implementation
- See `test_tools_client_stdio.py` for stdio transport comparison
- See main project README for overall FastMCP setup instructions

## 🚀 Advanced Features

### Real-time Progress Streaming
The SSE transport excels at streaming real-time progress updates:

```python
# Distance calculation with live progress updates
await client.call_tool(
    "calculate_distance_between_places",
    {"place1": "Tokyo", "place2": "Sydney", "unit": "km"}
)
# Progress: 0% → 25% → 50% → 75% → 100% streamed in real-time
```

### Context Logging Stream
All context logging is streamed live to the client:

```python
# Weather request with detailed logging stream
await client.call_tool(
    "get_weather",
    {"input": {"location": "London", "days": 3}}
)
# Real-time logs: API request → data processing → result formatting
```

This makes SSE ideal for applications requiring real-time feedback and monitoring. 