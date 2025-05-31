# FastMCP HTTP Stream Tools Server

This directory contains a FastMCP tools server that runs with HTTP streamable transport, providing mathematical operations, distance calculations, weather information, and context feature demonstrations.

## 🌐 HTTP Stream Transport

The server uses FastMCP's `streamable-http` transport, which provides:
- HTTP-based communication
- Real-time streaming capabilities
- Better network compatibility than stdio transport
- Support for web-based clients

## 📁 Files

### Server Files
- `tools_server_stream.py` - Main HTTP stream server with all tools
- `start_stream_server.py` - Helper script to start the server

### Client Files
- `test_tools_client_stream.py` - Comprehensive test client for HTTP stream server

### Documentation
- `STREAM_README.md` - This documentation file

## 🚀 Quick Start

### 1. Start the HTTP Stream Server

```bash
# Option 1: Direct execution
python tools_server_stream.py

# Option 2: Using the helper script
python start_stream_server.py
```

The server will start on `http://127.0.0.1:4200/mcp/`

### 2. Test the Server

In a separate terminal:

```bash
python test_tools_client_stream.py
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
- **Transport**: `streamable-http`
- **Host**: `127.0.0.1`
- **Port**: `4200`
- **Endpoint**: `/mcp/`
- **Log Level**: `debug`

## 🧪 Testing

The test client (`test_tools_client_stream.py`) performs comprehensive testing:

### Basic Tests
- ✅ Connection to HTTP stream server
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

### HTTP Stream Specific
- ✅ Multiple rapid requests
- ✅ Connection persistence
- ✅ Performance testing

## 📊 Context Features

The HTTP stream server includes full FastMCP Context integration:

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
# Check if port 4200 is already in use
netstat -an | grep 4200

# Try a different port by modifying tools_server_stream.py
mcp.run(transport="streamable-http", host="127.0.0.1", port=4201)
```

### Client Connection Issues
```bash
# Verify server is running
curl http://127.0.0.1:4200/mcp/

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

## 🌟 Features Demonstrated

### HTTP Transport Benefits
- **Network Compatibility**: Works across different network configurations
- **Web Integration**: Can be accessed by web-based MCP clients
- **Streaming Support**: Real-time communication with progress updates
- **Debugging**: HTTP requests can be inspected with standard tools

### FastMCP Context Integration
- **Comprehensive Logging**: All tools use context logging for better debugging
- **Progress Reporting**: Long-running operations show real-time progress
- **Request Tracking**: Each request has unique identifiers
- **Error Handling**: Proper error propagation through context

### Tool Variety
- **Mathematical**: Complete set of basic and advanced math operations
- **Geographic**: Real-world geocoding and distance calculations
- **Weather**: Live weather data integration
- **Demonstration**: Educational tools showing FastMCP capabilities

## 📝 Example Usage

```python
from fastmcp import Client

async def example():
    # Connect to HTTP stream server
    client = Client("http://127.0.0.1:4200/mcp/")
    
    async with client:
        # Test mathematical operation
        result = await client.call_tool("add", {"a": 10, "b": 20})
        print(f"10 + 20 = {result[0].text}")
        
        # Test distance calculation
        distance = await client.call_tool(
            "calculate_distance_between_places",
            {"place1": "New York", "place2": "Los Angeles", "unit": "miles"}
        )
        print(distance[0].text)
        
        # Test context features
        demo = await client.call_tool(
            "demonstrate_context_features",
            {"message": "Hello FastMCP!"}
        )
        print(demo[0].text)
```

## 🔗 Related Files

- See `test_tools_client_stdio.py` for stdio transport comparison
- See `tools_server_stdio.py` for stdio server implementation
- See main project README for overall FastMCP setup instructions 