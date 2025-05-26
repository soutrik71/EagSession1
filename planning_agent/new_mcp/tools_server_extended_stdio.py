from fastmcp import FastMCP, Context
from typing import Annotated, List, Dict, Any
import random
import string
import hashlib
import base64
import datetime
from fastmcp.exceptions import ToolError
from dotenv import load_dotenv
from pydantic import BaseModel, Field

# Load environment variables
load_dotenv()

mcp = FastMCP(name="ExtendedToolsServer")


# =============================================================================
# STRING MANIPULATION TOOLS
# =============================================================================


@mcp.tool()
async def reverse_string(
    text: Annotated[str, Field(description="The text to reverse")], ctx: Context
) -> str:
    """Reverse a string with context logging"""
    await ctx.info(f"Reversing string: '{text}'")
    result = text[::-1]
    await ctx.info(f"Reversed result: '{result}'")
    return result


@mcp.tool()
async def count_characters(
    text: Annotated[str, Field(description="The text to analyze")],
    include_spaces: Annotated[
        bool, Field(description="Whether to include spaces in count")
    ] = True,
    ctx: Context = None,
) -> Dict[str, int]:
    """Count characters in a string with detailed analysis"""
    if ctx:
        await ctx.info(f"Analyzing text: '{text}' (include_spaces: {include_spaces})")
        await ctx.report_progress(0, 100, "Starting character analysis...")

    # Basic counts
    total_chars = len(text)
    letters = sum(1 for c in text if c.isalpha())
    digits = sum(1 for c in text if c.isdigit())
    spaces = sum(1 for c in text if c.isspace())
    special_chars = total_chars - letters - digits - spaces

    if ctx:
        await ctx.report_progress(50, 100, "Calculating character statistics...")

    result = {
        "total_characters": total_chars if include_spaces else total_chars - spaces,
        "letters": letters,
        "digits": digits,
        "spaces": spaces,
        "special_characters": special_chars,
        "words": len(text.split()) if text.strip() else 0,
        "lines": len(text.splitlines()),
    }

    if ctx:
        await ctx.info(f"Character analysis complete: {result}")
        await ctx.report_progress(100, 100, "Character analysis finished!")

    return result


class TextTransformInput(BaseModel):
    text: str = Field(description="The text to transform")
    operation: str = Field(
        description="Transform operation: 'upper', 'lower', 'title', 'capitalize', 'swapcase'"
    )


@mcp.tool()
async def transform_text(input: TextTransformInput, ctx: Context = None) -> str:
    """Transform text case with various operations using Pydantic model"""
    if ctx:
        await ctx.info(f"Transforming text with operation: {input.operation}")

    valid_operations = ["upper", "lower", "title", "capitalize", "swapcase"]

    if input.operation not in valid_operations:
        if ctx:
            await ctx.error(f"Invalid operation: {input.operation}")
        raise ToolError(f"Operation must be one of: {', '.join(valid_operations)}")

    operations = {
        "upper": input.text.upper(),
        "lower": input.text.lower(),
        "title": input.text.title(),
        "capitalize": input.text.capitalize(),
        "swapcase": input.text.swapcase(),
    }

    result = operations[input.operation]

    if ctx:
        await ctx.info(f"Text transformed: '{input.text}' -> '{result}'")

    return result


# =============================================================================
# RANDOM GENERATION TOOLS
# =============================================================================


@mcp.tool()
async def generate_password(
    length: Annotated[
        int, Field(description="Password length (8-128 characters)")
    ] = 12,
    include_uppercase: Annotated[
        bool, Field(description="Include uppercase letters")
    ] = True,
    include_lowercase: Annotated[
        bool, Field(description="Include lowercase letters")
    ] = True,
    include_digits: Annotated[bool, Field(description="Include digits")] = True,
    include_symbols: Annotated[
        bool, Field(description="Include special symbols")
    ] = True,
    ctx: Context = None,
) -> str:
    """Generate a secure random password with customizable options"""
    if ctx:
        await ctx.info(f"Generating password with length {length}")
        await ctx.report_progress(0, 100, "Validating password parameters...")

    # Validate length
    if length < 8 or length > 128:
        if ctx:
            await ctx.error(f"Invalid password length: {length}")
        raise ToolError("Password length must be between 8 and 128 characters")

    # Build character set
    chars = ""
    if include_lowercase:
        chars += string.ascii_lowercase
    if include_uppercase:
        chars += string.ascii_uppercase
    if include_digits:
        chars += string.digits
    if include_symbols:
        chars += "!@#$%^&*()_+-=[]{}|;:,.<>?"

    if not chars:
        if ctx:
            await ctx.error("No character types selected")
        raise ToolError("At least one character type must be selected")

    if ctx:
        await ctx.report_progress(50, 100, "Generating secure password...")

    # Generate password
    password = "".join(random.choice(chars) for _ in range(length))

    if ctx:
        await ctx.info(f"Password generated successfully (length: {len(password)})")
        await ctx.report_progress(100, 100, "Password generation complete!")

    return password


@mcp.tool()
async def roll_dice(
    sides: Annotated[int, Field(description="Number of sides on the die")] = 6,
    count: Annotated[int, Field(description="Number of dice to roll")] = 1,
    ctx: Context = None,
) -> Dict[str, Any]:
    """Roll dice and return detailed results"""
    if ctx:
        await ctx.info(f"Rolling {count} dice with {sides} sides each")

    # Validate inputs
    if sides < 2 or sides > 100:
        if ctx:
            await ctx.error(f"Invalid number of sides: {sides}")
        raise ToolError("Number of sides must be between 2 and 100")

    if count < 1 or count > 20:
        if ctx:
            await ctx.error(f"Invalid number of dice: {count}")
        raise ToolError("Number of dice must be between 1 and 20")

    # Roll dice
    rolls = [random.randint(1, sides) for _ in range(count)]

    result = {
        "rolls": rolls,
        "total": sum(rolls),
        "average": round(sum(rolls) / len(rolls), 2),
        "minimum": min(rolls),
        "maximum": max(rolls),
        "dice_config": f"{count}d{sides}",
    }

    if ctx:
        await ctx.info(f"Dice roll result: {result}")

    return result


# =============================================================================
# ENCODING/HASHING TOOLS
# =============================================================================


class HashInput(BaseModel):
    text: str = Field(description="Text to hash")
    algorithm: str = Field(
        description="Hash algorithm: 'md5', 'sha1', 'sha256', 'sha512'",
        default="sha256",
    )


@mcp.tool()
async def hash_text(input: HashInput, ctx: Context = None) -> Dict[str, str]:
    """Generate hash of text using various algorithms"""
    if ctx:
        await ctx.info(f"Hashing text with {input.algorithm} algorithm")

    valid_algorithms = ["md5", "sha1", "sha256", "sha512"]

    if input.algorithm not in valid_algorithms:
        if ctx:
            await ctx.error(f"Invalid algorithm: {input.algorithm}")
        raise ToolError(f"Algorithm must be one of: {', '.join(valid_algorithms)}")

    # Generate hash
    text_bytes = input.text.encode("utf-8")

    if input.algorithm == "md5":
        hash_obj = hashlib.md5(text_bytes)
    elif input.algorithm == "sha1":
        hash_obj = hashlib.sha1(text_bytes)
    elif input.algorithm == "sha256":
        hash_obj = hashlib.sha256(text_bytes)
    elif input.algorithm == "sha512":
        hash_obj = hashlib.sha512(text_bytes)

    hex_hash = hash_obj.hexdigest()

    result = {
        "original_text": input.text,
        "algorithm": input.algorithm,
        "hash_hex": hex_hash,
        "hash_length": len(hex_hash),
    }

    if ctx:
        await ctx.info(f"Hash generated: {input.algorithm} -> {hex_hash[:16]}...")

    return result


@mcp.tool()
async def encode_base64(
    text: Annotated[str, Field(description="Text to encode in Base64")],
    ctx: Context = None,
) -> Dict[str, str]:
    """Encode text to Base64 format"""
    if ctx:
        await ctx.info(f"Encoding text to Base64: '{text[:50]}...'")

    try:
        # Encode to bytes then to base64
        text_bytes = text.encode("utf-8")
        encoded_bytes = base64.b64encode(text_bytes)
        encoded_text = encoded_bytes.decode("utf-8")

        result = {
            "original_text": text,
            "encoded_base64": encoded_text,
            "original_length": len(text),
            "encoded_length": len(encoded_text),
        }

        if ctx:
            await ctx.info(
                f"Base64 encoding complete: {len(text)} -> {len(encoded_text)} chars"
            )

        return result

    except Exception as e:
        if ctx:
            await ctx.error(f"Base64 encoding failed: {str(e)}")
        raise ToolError(f"Failed to encode text: {str(e)}")


@mcp.tool()
async def decode_base64(
    encoded_text: Annotated[str, Field(description="Base64 encoded text to decode")],
    ctx: Context = None,
) -> Dict[str, str]:
    """Decode Base64 encoded text"""
    if ctx:
        await ctx.info(f"Decoding Base64 text: '{encoded_text[:50]}...'")

    try:
        # Decode from base64 to bytes then to string
        encoded_bytes = encoded_text.encode("utf-8")
        decoded_bytes = base64.b64decode(encoded_bytes)
        decoded_text = decoded_bytes.decode("utf-8")

        result = {
            "encoded_text": encoded_text,
            "decoded_text": decoded_text,
            "encoded_length": len(encoded_text),
            "decoded_length": len(decoded_text),
        }

        if ctx:
            await ctx.info(
                f"Base64 decoding complete: {len(encoded_text)} -> {len(decoded_text)} chars"
            )

        return result

    except Exception as e:
        if ctx:
            await ctx.error(f"Base64 decoding failed: {str(e)}")
        raise ToolError(f"Failed to decode text: {str(e)}")


# =============================================================================
# DATE/TIME TOOLS
# =============================================================================


@mcp.tool()
async def get_current_time(
    timezone: Annotated[
        str, Field(description="Timezone (e.g., 'UTC', 'local')")
    ] = "UTC",
    format_string: Annotated[
        str, Field(description="Date format string")
    ] = "%Y-%m-%d %H:%M:%S",
    ctx: Context = None,
) -> Dict[str, str]:
    """Get current date and time with formatting options"""
    if ctx:
        await ctx.info(f"Getting current time for timezone: {timezone}")

    try:
        if timezone.lower() == "utc":
            current_time = datetime.datetime.utcnow()
            tz_info = "UTC"
        else:
            current_time = datetime.datetime.now()
            tz_info = "Local"

        formatted_time = current_time.strftime(format_string)

        result = {
            "formatted_time": formatted_time,
            "timezone": tz_info,
            "format_used": format_string,
            "iso_format": current_time.isoformat(),
            "timestamp": int(current_time.timestamp()),
            "year": current_time.year,
            "month": current_time.month,
            "day": current_time.day,
            "hour": current_time.hour,
            "minute": current_time.minute,
            "second": current_time.second,
            "weekday": current_time.strftime("%A"),
        }

        if ctx:
            await ctx.info(f"Current time: {formatted_time} ({tz_info})")

        return result

    except Exception as e:
        if ctx:
            await ctx.error(f"Time retrieval failed: {str(e)}")
        raise ToolError(f"Failed to get current time: {str(e)}")


class DateCalculationInput(BaseModel):
    start_date: str = Field(description="Start date in YYYY-MM-DD format")
    end_date: str = Field(description="End date in YYYY-MM-DD format")


@mcp.tool()
async def calculate_date_difference(
    input: DateCalculationInput, ctx: Context = None
) -> Dict[str, Any]:
    """Calculate the difference between two dates"""
    if ctx:
        await ctx.info(
            f"Calculating difference between {input.start_date} and {input.end_date}"
        )

    try:
        # Parse dates
        start = datetime.datetime.strptime(input.start_date, "%Y-%m-%d")
        end = datetime.datetime.strptime(input.end_date, "%Y-%m-%d")

        # Calculate difference
        diff = end - start

        result = {
            "start_date": input.start_date,
            "end_date": input.end_date,
            "total_days": diff.days,
            "total_seconds": int(diff.total_seconds()),
            "weeks": diff.days // 7,
            "remaining_days": diff.days % 7,
            "years": diff.days // 365,
            "is_future": diff.days > 0,
            "is_past": diff.days < 0,
            "absolute_days": abs(diff.days),
        }

        if ctx:
            await ctx.info(f"Date difference: {diff.days} days")

        return result

    except ValueError as e:
        if ctx:
            await ctx.error(f"Invalid date format: {str(e)}")
        raise ToolError(f"Invalid date format. Use YYYY-MM-DD: {str(e)}")
    except Exception as e:
        if ctx:
            await ctx.error(f"Date calculation failed: {str(e)}")
        raise ToolError(f"Failed to calculate date difference: {str(e)}")


# =============================================================================
# LIST/ARRAY TOOLS
# =============================================================================


@mcp.tool()
async def sort_list(
    items: Annotated[List[str], Field(description="List of items to sort")],
    reverse: Annotated[bool, Field(description="Sort in descending order")] = False,
    case_sensitive: Annotated[bool, Field(description="Case sensitive sorting")] = True,
    ctx: Context = None,
) -> Dict[str, Any]:
    """Sort a list of items with various options"""
    if ctx:
        await ctx.info(
            f"Sorting {len(items)} items (reverse: {reverse}, case_sensitive: {case_sensitive})"
        )

    try:
        original_items = items.copy()

        if case_sensitive:
            sorted_items = sorted(items, reverse=reverse)
        else:
            sorted_items = sorted(items, key=str.lower, reverse=reverse)

        result = {
            "original_list": original_items,
            "sorted_list": sorted_items,
            "item_count": len(items),
            "reverse_order": reverse,
            "case_sensitive": case_sensitive,
            "unique_items": len(set(items)),
            "has_duplicates": len(items) != len(set(items)),
        }

        if ctx:
            await ctx.info(f"Sorting complete: {len(items)} items processed")

        return result

    except Exception as e:
        if ctx:
            await ctx.error(f"List sorting failed: {str(e)}")
        raise ToolError(f"Failed to sort list: {str(e)}")


@mcp.tool()
async def find_duplicates(
    items: Annotated[
        List[str], Field(description="List of items to check for duplicates")
    ],
    ctx: Context = None,
) -> Dict[str, Any]:
    """Find duplicate items in a list"""
    if ctx:
        await ctx.info(f"Checking {len(items)} items for duplicates")

    try:
        seen = set()
        duplicates = set()

        for item in items:
            if item in seen:
                duplicates.add(item)
            else:
                seen.add(item)

        duplicate_counts = {}
        for item in items:
            if item in duplicates:
                duplicate_counts[item] = items.count(item)

        result = {
            "original_list": items,
            "total_items": len(items),
            "unique_items": len(seen),
            "duplicate_items": list(duplicates),
            "duplicate_count": len(duplicates),
            "duplicate_details": duplicate_counts,
            "has_duplicates": len(duplicates) > 0,
        }

        if ctx:
            await ctx.info(
                f"Duplicate check complete: {len(duplicates)} duplicates found"
            )

        return result

    except Exception as e:
        if ctx:
            await ctx.error(f"Duplicate finding failed: {str(e)}")
        raise ToolError(f"Failed to find duplicates: {str(e)}")


# =============================================================================
# CONTEXT DEMONSTRATION TOOL
# =============================================================================


@mcp.tool()
async def demonstrate_extended_context(
    operation: Annotated[
        str,
        Field(
            description="Operation to demonstrate: 'logging', 'progress', 'error', 'all'"
        ),
    ] = "all",
    ctx: Context = None,
) -> str:
    """Demonstrate extended context features with different operation types"""
    if not ctx:
        return "Context not available - this tool requires FastMCP context to demonstrate features"

    try:
        await ctx.debug(f"🔍 Starting extended context demonstration: {operation}")

        if operation in ["logging", "all"]:
            await ctx.info("📝 Demonstrating logging levels...")
            await ctx.debug("🐛 This is a debug message")
            await ctx.info("ℹ️ This is an info message")
            await ctx.warning("⚠️ This is a warning message")

        if operation in ["progress", "all"]:
            await ctx.info("📊 Demonstrating progress reporting...")
            for i in range(0, 101, 25):
                await ctx.report_progress(i, 100, f"Processing step {i//25 + 1}/5...")
                import asyncio

                await asyncio.sleep(0.1)

        if operation in ["error", "all"]:
            await ctx.info("🚨 Demonstrating error handling...")
            try:
                # Simulate an error condition
                if operation == "error":
                    raise ValueError("This is a demonstration error")
            except ValueError as e:
                await ctx.error(f"❌ Caught demonstration error: {str(e)}")

        # Access context information
        request_id = ctx.request_id
        client_id = ctx.client_id or "Unknown"

        response = f"""
🎯 Extended Context Demonstration Complete!

🔧 Operation: {operation}
🆔 Request ID: {request_id}
👤 Client ID: {client_id}

✅ Demonstrated features:
- Advanced logging patterns
- Progress reporting with steps
- Error handling and recovery
- Context information access

💡 This extended server provides additional tools for:
- String manipulation and analysis
- Random generation (passwords, dice)
- Encoding/hashing operations
- Date/time calculations
- List processing and analysis
        """.strip()

        await ctx.info("✅ Extended context demonstration completed successfully")
        return response

    except Exception as e:
        if ctx:
            await ctx.error(f"❌ Extended context demonstration failed: {str(e)}")
        return f"Error during extended context demonstration: {str(e)}"


if __name__ == "__main__":
    mcp.run()
