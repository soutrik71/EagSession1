import asyncio
from fastmcp import Client
import logging
import sys

# Import the extended tools server instance
from tools_server_extended import mcp as extended_server

# Set up logging to capture context messages
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
    handlers=[logging.StreamHandler(sys.stdout)],
)

# Create a logger for MCP context messages
mcp_logger = logging.getLogger("fastmcp")
mcp_logger.setLevel(logging.DEBUG)


async def main():
    """Test the extended tools server with one clear example per tool."""

    print("🔧 FastMCP Extended Tools Server - Tool Showcase")
    print("🔗 Using in-memory transport for testing")
    print("=" * 60)

    # Create client using in-memory transport
    client = Client(extended_server)

    try:
        async with client:
            print(f"✅ Connected to extended server: {client.is_connected()}")

            # List available tools
            tools = await client.list_tools()
            print(f"\n📋 Available Tools ({len(tools)}):")
            for i, tool in enumerate(tools, 1):
                print(f"   {i:2d}. {tool.name}")

            # =================================================================
            # STRING MANIPULATION TOOLS
            # =================================================================
            print("\n" + "=" * 60)
            print("📝 STRING MANIPULATION TOOLS")
            print("=" * 60)

            # Tool 1: reverse_string
            print("\n1️⃣ REVERSE STRING")
            print("   Purpose: Reverse any text string")
            print("   Example: 'Hello World' → 'dlroW olleH'")
            reverse_result = await client.call_tool(
                "reverse_string", {"text": "Hello FastMCP!"}
            )
            print(f"   Result: '{reverse_result[0].text}'")

            # Tool 2: count_characters
            print("\n2️⃣ CHARACTER ANALYSIS")
            print(
                "   Purpose: Analyze text composition (letters, digits, spaces, etc.)"
            )
            print("   Example: Count different character types in text")
            count_result = await client.call_tool(
                "count_characters", {"text": "Hello World! 123", "include_spaces": True}
            )
            import json

            count_data = json.loads(count_result[0].text)
            print(
                f"   Result: {count_data['letters']} letters, {count_data['digits']} digits, {count_data['spaces']} spaces"
            )

            # Tool 3: transform_text
            print("\n3️⃣ TEXT TRANSFORMATION")
            print(
                "   Purpose: Change text case (upper, lower, title, capitalize, swapcase)"
            )
            print("   Example: Convert to title case")
            transform_result = await client.call_tool(
                "transform_text",
                {"input": {"text": "hello world", "operation": "title"}},
            )
            print(f"   Result: '{transform_result[0].text}'")

            # =================================================================
            # RANDOM GENERATION TOOLS
            # =================================================================
            print("\n" + "=" * 60)
            print("🎲 RANDOM GENERATION TOOLS")
            print("=" * 60)

            # Tool 4: generate_password
            print("\n4️⃣ PASSWORD GENERATOR")
            print(
                "   Purpose: Generate secure random passwords with customizable options"
            )
            print("   Example: 12-character password with all character types")
            password_result = await client.call_tool(
                "generate_password", {"length": 12}
            )
            print(f"   Result: '{password_result[0].text}'")

            # Tool 5: roll_dice
            print("\n5️⃣ DICE ROLLER")
            print("   Purpose: Roll dice with customizable sides and count")
            print("   Example: Roll 2 six-sided dice")
            dice_result = await client.call_tool("roll_dice", {"sides": 6, "count": 2})
            dice_data = json.loads(dice_result[0].text)
            print(
                f"   Result: Rolled {dice_data['rolls']} = Total: {dice_data['total']}"
            )

            # =================================================================
            # ENCODING/HASHING TOOLS
            # =================================================================
            print("\n" + "=" * 60)
            print("🔐 ENCODING & HASHING TOOLS")
            print("=" * 60)

            test_text = "Hello FastMCP!"

            # Tool 6: hash_text
            print("\n6️⃣ TEXT HASHER")
            print(
                "   Purpose: Generate cryptographic hashes (MD5, SHA1, SHA256, SHA512)"
            )
            print("   Example: Generate SHA256 hash")
            hash_result = await client.call_tool(
                "hash_text", {"input": {"text": test_text, "algorithm": "sha256"}}
            )
            hash_data = json.loads(hash_result[0].text)
            print(f"   Result: {hash_data['hash_hex'][:32]}...")

            # Tool 7: encode_base64
            print("\n7️⃣ BASE64 ENCODER")
            print("   Purpose: Encode text to Base64 format")
            print("   Example: Encode text for safe transmission")
            encode_result = await client.call_tool("encode_base64", {"text": test_text})
            encode_data = json.loads(encode_result[0].text)
            print(f"   Result: '{encode_data['encoded_base64']}'")

            # Tool 8: decode_base64
            print("\n8️⃣ BASE64 DECODER")
            print("   Purpose: Decode Base64 encoded text back to original")
            print("   Example: Decode the previously encoded text")
            decode_result = await client.call_tool(
                "decode_base64", {"encoded_text": encode_data["encoded_base64"]}
            )
            decode_data = json.loads(decode_result[0].text)
            print(f"   Result: '{decode_data['decoded_text']}'")

            # =================================================================
            # DATE/TIME TOOLS
            # =================================================================
            print("\n" + "=" * 60)
            print("📅 DATE & TIME TOOLS")
            print("=" * 60)

            # Tool 9: get_current_time
            print("\n9️⃣ CURRENT TIME")
            print(
                "   Purpose: Get current date/time with custom formatting and timezone"
            )
            print("   Example: Get current UTC time")
            time_result = await client.call_tool(
                "get_current_time",
                {"timezone": "UTC", "format_string": "%Y-%m-%d %H:%M:%S"},
            )
            time_data = json.loads(time_result[0].text)
            print(f"   Result: {time_data['formatted_time']} ({time_data['weekday']})")

            # Tool 10: calculate_date_difference
            print("\n🔟 DATE DIFFERENCE CALCULATOR")
            print("   Purpose: Calculate difference between two dates")
            print("   Example: Days between New Year and Christmas 2024")
            date_diff_result = await client.call_tool(
                "calculate_date_difference",
                {"input": {"start_date": "2024-01-01", "end_date": "2024-12-25"}},
            )
            date_data = json.loads(date_diff_result[0].text)
            print(
                f"   Result: {date_data['total_days']} days ({date_data['weeks']} weeks)"
            )

            # =================================================================
            # LIST PROCESSING TOOLS
            # =================================================================
            print("\n" + "=" * 60)
            print("📋 LIST PROCESSING TOOLS")
            print("=" * 60)

            test_list = ["banana", "apple", "Cherry", "date", "apple"]

            # Tool 11: sort_list
            print("\n1️⃣1️⃣ LIST SORTER")
            print("   Purpose: Sort lists with case sensitivity and reverse options")
            print(f"   Example: Sort {test_list} (case-insensitive)")
            sort_result = await client.call_tool(
                "sort_list", {"items": test_list, "case_sensitive": False}
            )
            sort_data = json.loads(sort_result[0].text)
            print(f"   Result: {sort_data['sorted_list']}")

            # Tool 12: find_duplicates
            print("\n1️⃣2️⃣ DUPLICATE FINDER")
            print("   Purpose: Find and count duplicate items in lists")
            print(f"   Example: Find duplicates in {test_list}")
            duplicate_result = await client.call_tool(
                "find_duplicates", {"items": test_list}
            )
            dup_data = json.loads(duplicate_result[0].text)
            print(
                f"   Result: Found {dup_data['duplicate_count']} duplicates: {dup_data['duplicate_items']}"
            )

            # =================================================================
            # CONTEXT DEMONSTRATION
            # =================================================================
            print("\n" + "=" * 60)
            print("🎯 CONTEXT FEATURES DEMONSTRATION")
            print("=" * 60)

            # Tool 13: demonstrate_extended_context
            print("\n1️⃣3️⃣ CONTEXT FEATURES DEMO")
            print("   Purpose: Showcase FastMCP context logging and progress reporting")
            print("   Example: Demonstrate all context features")
            demo_result = await client.call_tool(
                "demonstrate_extended_context", {"operation": "all"}
            )
            print("   Result: Context demonstration completed (check logs above)")

            # =================================================================
            # ERROR HANDLING EXAMPLES
            # =================================================================
            print("\n" + "=" * 60)
            print("🚫 ERROR HANDLING EXAMPLES")
            print("=" * 60)

            print("\n❌ Testing invalid password length (too short)...")
            try:
                await client.call_tool("generate_password", {"length": 5})
            except Exception as e:
                print(f"   ✅ Correctly caught: {type(e).__name__}")

            print("\n❌ Testing invalid hash algorithm...")
            try:
                await client.call_tool(
                    "hash_text", {"input": {"text": "test", "algorithm": "invalid"}}
                )
            except Exception as e:
                print(f"   ✅ Correctly caught: {type(e).__name__}")

        print("\n" + "=" * 60)
        print("✅ EXTENDED TOOLS SERVER SHOWCASE COMPLETE!")
        print("=" * 60)
        print("📊 Summary of 13 Available Tools:")
        print("   • String Tools: reverse, analyze, transform")
        print("   • Random Tools: password generator, dice roller")
        print("   • Crypto Tools: hash generator, Base64 encoder/decoder")
        print("   • Time Tools: current time, date calculations")
        print("   • List Tools: sorting, duplicate detection")
        print("   • Demo Tool: context features showcase")
        print("=" * 60)

    except Exception as e:
        print(f"\n❌ Error during testing: {e}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
