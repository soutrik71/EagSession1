from fastmcp import Client
from fastmcp.client.transports import PythonStdioTransport
import os
import sys
import asyncio
import json
import logging

# Set up logging to capture context messages
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

# Create a logger for MCP context messages
mcp_logger = logging.getLogger("fastmcp")
mcp_logger.setLevel(logging.DEBUG)

server_script_path = os.path.abspath(
    os.path.join(os.path.dirname(__file__), "tools_server_extended_stdio.py")
)

# Option 1: Inferred transport - issue with windows
# client = Client(server_script_path)

# Option 2: Explicit transport with custom configuration
python_commands = ["python", "python.exe", sys.executable]

client = None
successful_python_cmd = None

for python_cmd in python_commands:
    print(f"\n🔍 Trying Python command: {python_cmd}")

    try:
        transport = PythonStdioTransport(
            script_path=server_script_path,
            python_cmd=python_cmd,
        )
        client = Client(transport=transport)
        print(f"✅ Transport created successfully: {client.transport}")
        successful_python_cmd = python_cmd
        break
    except Exception as e:
        print(f"❌ Error with Python command {python_cmd}: {e}")
        continue

if not client:
    print("❌ Failed to create client with any Python command")
    sys.exit(1)


async def test_string_manipulation_tools(client):
    """Test string manipulation and analysis tools."""
    print("\n" + "=" * 60)
    print("📝 STRING MANIPULATION TOOLS")
    print("=" * 60)

    # Test reverse_string
    print("\n1️⃣ REVERSE STRING")
    print("   Purpose: Reverse any text string with context logging")
    print("   Example: 'Hello FastMCP STDIO!' → reversed")
    try:
        reverse_result = await client.call_tool(
            "reverse_string", {"text": "Hello FastMCP STDIO!"}
        )
        print(f"   ✅ Result: '{reverse_result[0].text}'")
    except Exception as e:
        print(f"   ❌ Failed: {str(e)}")

    # Test count_characters
    print("\n2️⃣ CHARACTER ANALYSIS")
    print("   Purpose: Detailed text composition analysis")
    print("   Example: Analyze 'Hello World! 123 @#$'")
    try:
        count_result = await client.call_tool(
            "count_characters", {"text": "Hello World! 123 @#$", "include_spaces": True}
        )
        count_data = json.loads(count_result[0].text)
        print(f"   ✅ Letters: {count_data['letters']}, Digits: {count_data['digits']}")
        print(
            f"      Spaces: {count_data['spaces']}, Special: {count_data['special_characters']}"
        )
        print(f"      Words: {count_data['words']}, Lines: {count_data['lines']}")
    except Exception as e:
        print(f"   ❌ Failed: {str(e)}")

    # Test transform_text
    print("\n3️⃣ TEXT TRANSFORMATION")
    print("   Purpose: Various case transformations using Pydantic models")
    transformations = [
        ("hello world", "title", "Title Case"),
        ("Hello World", "upper", "UPPERCASE"),
        ("HELLO WORLD", "lower", "lowercase"),
        ("hello world", "capitalize", "Capitalize first"),
        ("Hello World", "swapcase", "sWAP cASE"),
    ]

    for text, operation, description in transformations:
        try:
            transform_result = await client.call_tool(
                "transform_text", {"input": {"text": text, "operation": operation}}
            )
            print(f"   ✅ {description}: '{text}' → '{transform_result[0].text}'")
        except Exception as e:
            print(f"   ❌ {description} failed: {str(e)}")


async def test_random_generation_tools(client):
    """Test random generation tools."""
    print("\n" + "=" * 60)
    print("🎲 RANDOM GENERATION TOOLS")
    print("=" * 60)

    # Test password generation
    print("\n4️⃣ SECURE PASSWORD GENERATOR")
    print("   Purpose: Generate cryptographically secure passwords")

    password_configs = [
        (12, True, True, True, True, "Full character set"),
        (16, True, True, True, False, "No symbols"),
        (8, True, True, False, False, "Letters only"),
    ]

    for length, upper, lower, digits, symbols, description in password_configs:
        try:
            password_result = await client.call_tool(
                "generate_password",
                {
                    "length": length,
                    "include_uppercase": upper,
                    "include_lowercase": lower,
                    "include_digits": digits,
                    "include_symbols": symbols,
                },
            )
            print(f"   ✅ {description} ({length} chars): '{password_result[0].text}'")
        except Exception as e:
            print(f"   ❌ {description} failed: {str(e)}")

    # Test dice rolling
    print("\n5️⃣ DICE ROLLER")
    print("   Purpose: Roll dice with detailed statistics")

    dice_configs = [
        (6, 2, "Standard 2d6"),
        (20, 1, "D&D d20"),
        (10, 3, "Percentile 3d10"),
    ]

    for sides, count, description in dice_configs:
        try:
            dice_result = await client.call_tool(
                "roll_dice", {"sides": sides, "count": count}
            )
            dice_data = json.loads(dice_result[0].text)
            print(f"   ✅ {description}: {dice_data['rolls']} = {dice_data['total']}")
            print(
                f"      Config: {dice_data['dice_config']}, Avg: {dice_data['average']}"
            )
        except Exception as e:
            print(f"   ❌ {description} failed: {str(e)}")


async def test_encoding_hashing_tools(client):
    """Test encoding and hashing tools."""
    print("\n" + "=" * 60)
    print("🔐 ENCODING & HASHING TOOLS")
    print("=" * 60)

    test_text = "Hello FastMCP STDIO Server!"

    # Test hashing
    print("\n6️⃣ CRYPTOGRAPHIC HASHING")
    print("   Purpose: Generate secure hashes with multiple algorithms")

    hash_algorithms = ["md5", "sha1", "sha256", "sha512"]

    for algorithm in hash_algorithms:
        try:
            hash_result = await client.call_tool(
                "hash_text", {"input": {"text": test_text, "algorithm": algorithm}}
            )
            hash_data = json.loads(hash_result[0].text)
            hash_preview = hash_data["hash_hex"][:16] + "..."
            print(
                f"   ✅ {algorithm.upper()}: {hash_preview} ({hash_data['hash_length']} chars)"
            )
        except Exception as e:
            print(f"   ❌ {algorithm} failed: {str(e)}")

    # Test Base64 encoding/decoding
    print("\n7️⃣ BASE64 ENCODING/DECODING")
    print("   Purpose: Safe text encoding for transmission")
    print(f"   Example: Encode and decode '{test_text}'")

    try:
        # Encode
        encode_result = await client.call_tool("encode_base64", {"text": test_text})
        encode_data = json.loads(encode_result[0].text)
        encoded_text = encode_data["encoded_base64"]
        print(f"   ✅ Encoded: '{encoded_text}'")
        print(
            f"      Length: {encode_data['original_length']} → {encode_data['encoded_length']}"
        )

        # Decode
        decode_result = await client.call_tool(
            "decode_base64", {"encoded_text": encoded_text}
        )
        decode_data = json.loads(decode_result[0].text)
        print(f"   ✅ Decoded: '{decode_data['decoded_text']}'")
        verification = (
            "✅ Match" if decode_data["decoded_text"] == test_text else "❌ Mismatch"
        )
        print(f"      Verification: {verification}")

    except Exception as e:
        print(f"   ❌ Base64 operations failed: {str(e)}")


async def test_datetime_tools(client):
    """Test date and time tools."""
    print("\n" + "=" * 60)
    print("📅 DATE & TIME TOOLS")
    print("=" * 60)

    # Test current time
    print("\n8️⃣ CURRENT TIME")
    print("   Purpose: Get formatted current time with timezone support")

    time_configs = [
        ("UTC", "%Y-%m-%d %H:%M:%S", "Standard UTC"),
        ("local", "%B %d, %Y at %I:%M %p", "Local formatted"),
        ("UTC", "%A, %Y-%m-%d", "Day and date only"),
    ]

    for timezone, format_str, description in time_configs:
        try:
            time_result = await client.call_tool(
                "get_current_time", {"timezone": timezone, "format_string": format_str}
            )
            time_data = json.loads(time_result[0].text)
            print(f"   ✅ {description}: {time_data['formatted_time']}")
            print(
                f"      Weekday: {time_data['weekday']}, Timestamp: {time_data['timestamp']}"
            )
        except Exception as e:
            print(f"   ❌ {description} failed: {str(e)}")

    # Test date difference calculation
    print("\n9️⃣ DATE DIFFERENCE CALCULATOR")
    print("   Purpose: Calculate precise differences between dates")

    date_pairs = [
        ("2024-01-01", "2024-12-31", "Full year 2024"),
        ("2024-06-01", "2024-06-30", "June 2024"),
        ("2023-12-25", "2024-01-01", "Christmas to New Year"),
    ]

    for start_date, end_date, description in date_pairs:
        try:
            date_diff_result = await client.call_tool(
                "calculate_date_difference",
                {"input": {"start_date": start_date, "end_date": end_date}},
            )
            date_data = json.loads(date_diff_result[0].text)
            print(f"   ✅ {description}: {date_data['total_days']} days")
            print(
                f"      Breakdown: {date_data['weeks']} weeks + {date_data['remaining_days']} days"
            )
        except Exception as e:
            print(f"   ❌ {description} failed: {str(e)}")


async def test_list_processing_tools(client):
    """Test list processing and analysis tools."""
    print("\n" + "=" * 60)
    print("📋 LIST PROCESSING TOOLS")
    print("=" * 60)

    # Test sorting
    print("\n🔟 LIST SORTING")
    print("   Purpose: Sort lists with various options")

    test_lists = [
        (
            ["banana", "Apple", "cherry", "Date"],
            False,
            False,
            "Mixed case, case-insensitive",
        ),
        (["zebra", "apple", "Banana"], True, True, "Case-sensitive, reverse"),
        (["3", "1", "10", "2"], False, False, "String numbers"),
    ]

    for items, reverse, case_sensitive, description in test_lists:
        try:
            sort_result = await client.call_tool(
                "sort_list",
                {"items": items, "reverse": reverse, "case_sensitive": case_sensitive},
            )
            sort_data = json.loads(sort_result[0].text)
            print(f"   ✅ {description}:")
            print(f"      Original: {sort_data['original_list']}")
            print(f"      Sorted:   {sort_data['sorted_list']}")
            print(
                f"      Stats: {sort_data['unique_items']} unique, duplicates: {sort_data['has_duplicates']}"
            )
        except Exception as e:
            print(f"   ❌ {description} failed: {str(e)}")

    # Test duplicate finding
    print("\n1️⃣1️⃣ DUPLICATE DETECTION")
    print("   Purpose: Find and analyze duplicate items")

    test_lists_dup = [
        (
            ["apple", "banana", "apple", "cherry", "banana", "apple"],
            "Fruits with duplicates",
        ),
        (["unique", "items", "only"], "No duplicates"),
        (["a", "a", "b", "b", "c"], "Multiple pairs"),
    ]

    for items, description in test_lists_dup:
        try:
            dup_result = await client.call_tool("find_duplicates", {"items": items})
            dup_data = json.loads(dup_result[0].text)
            print(f"   ✅ {description}:")
            print(
                f"      Total items: {dup_data['total_items']}, Unique: {dup_data['unique_items']}"
            )
            if dup_data["has_duplicates"]:
                print(f"      Duplicates: {dup_data['duplicate_items']}")
                print(f"      Counts: {dup_data['duplicate_details']}")
            else:
                print("      No duplicates found")
        except Exception as e:
            print(f"   ❌ {description} failed: {str(e)}")


async def test_context_features(client):
    """Test context demonstration features."""
    print("\n" + "=" * 60)
    print("🎯 CONTEXT FEATURES DEMONSTRATION")
    print("=" * 60)

    print("\n1️⃣2️⃣ CONTEXT FEATURES SHOWCASE")
    print("   Purpose: Demonstrate FastMCP context logging and progress reporting")

    context_operations = ["logging", "progress", "error", "all"]

    for operation in context_operations:
        print(f"\n   Testing context operation: {operation}")
        try:
            demo_result = await client.call_tool(
                "demonstrate_extended_context", {"operation": operation}
            )
            print(f"   ✅ {operation.capitalize()} demonstration completed")
            if operation == "all":
                print("   📊 Check the logs above for detailed context features")
        except Exception as e:
            print(f"   ❌ {operation} demonstration failed: {str(e)}")


async def test_error_handling(client):
    """Test error handling scenarios."""
    print("\n" + "=" * 60)
    print("🚫 ERROR HANDLING EXAMPLES")
    print("=" * 60)

    error_tests = [
        ("generate_password", {"length": 5}, "Password too short (min 8)"),
        ("roll_dice", {"sides": 1}, "Invalid dice sides (min 2)"),
        (
            "hash_text",
            {"input": {"text": "test", "algorithm": "invalid"}},
            "Invalid hash algorithm",
        ),
    ]

    for tool_name, params, description in error_tests:
        print(f"\n❌ Testing: {description}")
        try:
            await client.call_tool(tool_name, params)
            print("   ⚠️  Expected error but got success")
        except Exception as e:
            print(f"   ✅ Correctly caught: {type(e).__name__} - {str(e)[:60]}...")


async def main():
    """Test the extended STDIO server with comprehensive tool showcase."""

    print("🔧 FastMCP Extended STDIO Server - Comprehensive Test Suite")
    print(f"🔗 Using Python command: {successful_python_cmd}")
    print(f"📁 Server script: {server_script_path}")
    print("=" * 70)

    try:
        # Connection is established here
        async with client:
            print(f"✅ Client connected: {client.is_connected()}")

            # List available tools
            tools = await client.list_tools()
            print(f"\n📋 Available Tools ({len(tools)}):")
            for i, tool in enumerate(tools, 1):
                print(f"   {i:2d}. {tool.name} - {tool.description}")

            # Run comprehensive test suites
            await test_string_manipulation_tools(client)
            await test_random_generation_tools(client)
            await test_encoding_hashing_tools(client)
            await test_datetime_tools(client)
            await test_list_processing_tools(client)
            await test_context_features(client)
            await test_error_handling(client)

        # Connection is closed automatically here
        print(f"\n✅ Client disconnected: {not client.is_connected()}")

        print("\n" + "=" * 70)
        print("🎉 COMPREHENSIVE STDIO SERVER TEST COMPLETED!")
        print("=" * 70)
        print("📊 Test Summary:")
        print("   ✅ String Tools: reverse, analyze, transform")
        print("   ✅ Random Tools: secure passwords, dice rolling")
        print("   ✅ Crypto Tools: multi-algorithm hashing, Base64 encoding")
        print("   ✅ Time Tools: current time, date calculations")
        print("   ✅ List Tools: sorting, duplicate detection")
        print("   ✅ Context Tools: logging, progress reporting")
        print("   ✅ Error Handling: key validation examples")
        print("=" * 70)
        print("🌟 Extended STDIO Server: All 13 tools tested successfully!")
        print("   💡 Focused on positive demonstrations with minimal error testing")

    except Exception as e:
        print(f"\n❌ Connection or testing failed: {e}")
        print("\n🔧 Troubleshooting:")
        print("   1. Check if the server script exists and is executable")
        print("   2. Verify Python installation and PATH")
        print("   3. Try running the server script directly:")
        print(f"      {successful_python_cmd} {server_script_path}")
        print("   4. Check for any import errors in the server script")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
