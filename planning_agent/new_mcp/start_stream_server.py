#!/usr/bin/env python3
"""
Start the FastMCP HTTP Stream Tools Server

This script starts the tools server with HTTP streamable transport
on http://127.0.0.1:4200/mcp/
"""

import sys
import os

# Add the current directory to Python path to import the server
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from tools_server_stream import mcp

    print("✅ Successfully imported tools_server_stream")
except ImportError as e:
    print(f"❌ Failed to import tools_server_stream: {e}")
    sys.exit(1)


def main():
    """Start the HTTP stream server"""
    print("🚀 Starting FastMCP HTTP Stream Tools Server")
    print("=" * 50)
    print("🌐 Server will be available at: http://127.0.0.1:4200/mcp/")
    print("📋 Available tools:")
    print("   • Mathematical operations (add, subtract, multiply, divide)")
    print("   • Trigonometric functions (sine, cosine, tangent)")
    print("   • Logarithm calculations")
    print("   • Distance calculation between places")
    print("   • Weather information (requires SERP_API_KEY)")
    print("   • Context features demonstration")
    print("=" * 50)
    print("💡 To test the server, run: python test_tools_client_stream.py")
    print("🛑 Press Ctrl+C to stop the server")
    print("=" * 50)

    try:
        # Start the server with HTTP streamable transport
        mcp.run(
            transport="streamable-http",
            host="127.0.0.1",
            port=4200,
            log_level="debug",
        )
    except KeyboardInterrupt:
        print("\n🛑 Server stopped by user")
    except Exception as e:
        print(f"\n❌ Server error: {e}")
        import traceback

        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
