# FastMCP Tools Server Documentation

## Overview

This is a comprehensive FastMCP tools server that provides mathematical calculations, geographical distance computation, and weather information retrieval. The server demonstrates various FastMCP patterns and best practices.

## Features

### 🔢 Mathematical Operations
- **Basic Arithmetic**: Addition, subtraction, multiplication, division
- **Trigonometric Functions**: Sine, cosine, tangent
- **Logarithmic Functions**: Logarithm with customizable base
- **Error Handling**: Division by zero, invalid logarithm inputs

### 🌍 Geographical Services
- **Distance Calculation**: Calculate great circle distance between any two places
- **Geocoding**: Convert place names to coordinates using OpenStreetMap
- **Unit Conversion**: Support for kilometers and miles
- **Haversine Formula**: Accurate earth distance calculations

### 🌤️ Weather Information
- **Current Weather**: Real-time weather conditions
- **Weather Forecasts**: Multi-day weather predictions (1-7 days)
- **SerpAPI Integration**: Powered by Google search results
- **Error Handling**: Comprehensive validation and error reporting

## Tools Available

### Mathematical Tools

#### `add(a: int, b: int) -> int`
Adds two integers.

#### `subtract(a: int, b: int) -> int`
Subtracts two integers.

#### `multiply(a: int, b: int) -> int`
Multiplies two integers.

#### `divide(a: int, b: int) -> float`
Divides two integers with zero-division protection.

#### `get_sine_value(x: float) -> float`
Calculates sine of an angle in radians.

#### `get_cosine_value(x: float) -> float`
Calculates cosine of an angle in radians.

#### `get_tangent_value(x: float) -> float`
Calculates tangent of an angle in radians.

#### `get_log_value(x: float, base: float = 10.0) -> float`
Calculates logarithm with specified base (default: 10).

### Geographical Tools

#### `calculate_distance_between_places(place1: str, place2: str, unit: str = "km") -> str`
Calculates the great circle distance between two places.

**Parameters:**
- `place1`: Name of the first place (e.g., "New York, USA")
- `place2`: Name of the second place (e.g., "London, UK")
- `unit`: Distance unit ("km" or "miles")

**Returns:** Formatted string with coordinates and distance.

### Weather Tools

#### `get_weather(input: WeatherInput) -> WeatherOutput`
Retrieves weather information using SerpAPI.

**WeatherInput:**
- `location`: Location name (e.g., "Paris, France")
- `days`: Number of forecast days (1-7)

**WeatherOutput:**
- `weather_info`: Formatted weather information
- `success`: Boolean indicating success/failure
- `error_message`: Error details if applicable

## Setup Instructions

### 1. Install Dependencies

```bash
pip install -r requirements.txt
```

### 2. Environment Configuration

Create a `.env` file in the project directory:

```env
# SerpAPI Configuration
SERP_API_KEY=your_serpapi_key_here
```

**Get your SerpAPI key:**
1. Visit [https://serpapi.com/](https://serpapi.com/)
2. Sign up for a free account
3. Copy your API key from the dashboard
4. Replace `your_serpapi_key_here` with your actual key

### 3. Running the Server

#### Standalone Server (Stdio Transport)
```bash
python tools_server.py
```

#### In-Memory Testing
```bash
python test_tools_client.py
```

## Code Architecture

### Error Handling Strategy

1. **Input Validation**: All tools validate inputs before processing
2. **Custom Exceptions**: Uses `ToolError` for tool-specific errors
3. **Graceful Degradation**: Weather tool returns structured error responses
4. **Type Safety**: Pydantic models ensure type correctness

### Design Patterns

#### 1. Simple Tools (Basic Math)
```python
@mcp.tool()
async def add(a: int, b: int) -> int:
    """Add two numbers"""
    return a + b
```

#### 2. Annotated Tools (Trigonometry)
```python
@mcp.tool()
async def get_sine_value(
    x: Annotated[float, Field(description="The angle in radians")],
) -> float:
    """Get the sine value of an angle"""
    return math.sin(x)
```

#### 3. Pydantic Model Tools (Weather)
```python
class WeatherInput(BaseModel):
    location: str = Field(description="Location to get weather for")
    days: int = Field(description="Number of days for forecast", default=1)

@mcp.tool()
async def get_weather(input: WeatherInput) -> WeatherOutput:
    # Implementation
```

### External API Integration

#### OpenStreetMap Nominatim (Free)
- **Purpose**: Geocoding place names to coordinates
- **Rate Limits**: Respectful usage with proper User-Agent
- **No API Key Required**

#### SerpAPI (Paid)
- **Purpose**: Weather information via Google search
- **Rate Limits**: Based on your plan
- **API Key Required**

## Testing

The test client (`test_tools_client.py`) provides comprehensive testing:

### Test Categories

1. **Basic Math Operations**: All arithmetic functions
2. **Error Handling**: Division by zero, invalid inputs
3. **Trigonometric Functions**: Sine, cosine, tangent
4. **Logarithmic Functions**: Various bases and edge cases
5. **Distance Calculations**: Multiple city pairs and units
6. **Weather Information**: Current weather and forecasts
7. **Input Validation**: Empty inputs, invalid parameters

### Running Tests

```bash
python test_tools_client.py
```

Expected output includes:
- ✅ Successful operations
- 🚫 Proper error handling
- 📊 Formatted results
- 🌍 Geographical calculations
- 🌤️ Weather information

## Error Scenarios Handled

### Mathematical Errors
- Division by zero
- Negative logarithm inputs
- Invalid logarithm bases

### Geographical Errors
- Empty place names
- Invalid location names
- Network connectivity issues
- Invalid distance units

### Weather Errors
- Missing API key
- Empty location names
- Invalid forecast days (outside 1-7 range)
- API rate limiting
- Network timeouts

## Best Practices Demonstrated

1. **Type Safety**: Comprehensive type hints and Pydantic models
2. **Error Handling**: Graceful error handling with meaningful messages
3. **Input Validation**: Thorough validation before processing
4. **Documentation**: Clear docstrings for all tools
5. **Testing**: Comprehensive test coverage
6. **Configuration**: Environment-based configuration
7. **Modularity**: Clean separation of concerns

## Extending the Server

### Adding New Mathematical Functions

```python
@mcp.tool()
async def your_math_function(
    param: Annotated[float, Field(description="Parameter description")]
) -> float:
    """Function description"""
    # Validate inputs
    if param < 0:
        raise ToolError("Parameter must be non-negative")
    
    # Perform calculation
    result = your_calculation(param)
    return result
```

### Adding New API Integrations

```python
class YourInput(BaseModel):
    param: str = Field(description="Parameter description")

class YourOutput(BaseModel):
    result: str = Field(description="Result description")
    success: bool = Field(description="Success status")
    error_message: str = Field(description="Error message", default="")

@mcp.tool()
async def your_api_tool(input: YourInput) -> YourOutput:
    try:
        # Validate inputs
        if not input.param.strip():
            return YourOutput(
                result="",
                success=False,
                error_message="Parameter cannot be empty"
            )
        
        # Make API call
        response = await make_api_call(input.param)
        
        return YourOutput(
            result=response,
            success=True,
            error_message=""
        )
    except Exception as e:
        return YourOutput(
            result="",
            success=False,
            error_message=str(e)
        )
```

## Troubleshooting

### Common Issues

1. **"SERP_API_KEY not found"**
   - Ensure `.env` file exists
   - Check API key is correctly set
   - Verify `.env` file is in the correct directory

2. **"Place not found" errors**
   - Use more specific location names
   - Include country names for clarity
   - Check internet connectivity

3. **Import errors**
   - Install all dependencies: `pip install -r requirements.txt`
   - Ensure Python 3.8+ is being used

4. **Connection timeouts**
   - Check internet connectivity
   - Verify API endpoints are accessible
   - Consider increasing timeout values

### Performance Optimization

1. **Caching**: Consider caching geocoding results
2. **Rate Limiting**: Implement rate limiting for API calls
3. **Async Operations**: All tools are async-ready
4. **Error Recovery**: Implement retry logic for network calls

This tools server demonstrates production-ready FastMCP patterns and can serve as a foundation for more complex applications. 