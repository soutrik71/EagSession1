#!/usr/bin/env python3
"""
Start the FastMCP SSE (Server-Sent Events) Tools Server

This script starts the tools server with SSE transport
on http://127.0.0.1:4201/sse
"""

import sys
import os

# Add the current directory to Python path to import the server
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

try:
    from tools_server_sse import mcp

    print("✅ Successfully imported tools_server_sse")
except ImportError as e:
    print(f"❌ Failed to import tools_server_sse: {e}")
    sys.exit(1)


def main():
    """Start the SSE server"""
    print("🚀 Starting FastMCP SSE (Server-Sent Events) Tools Server")
    print("=" * 55)
    print("🌐 Server will be available at: http://127.0.0.1:4201/sse")
    print("📡 Transport: SSE (Server-Sent Events)")
    print("📋 Available tools:")
    print("   • Mathematical operations (add, subtract, multiply, divide)")
    print("   • Trigonometric functions (sine, cosine, tangent)")
    print("   • Logarithm calculations")
    print("   • Distance calculation between places")
    print("   • Weather information (requires SERP_API_KEY)")
    print("   • Context features demonstration")
    print("=" * 55)
    print("💡 To test the server, run: python test_tools_client_sse.py")
    print("🛑 Press Ctrl+C to stop the server")
    print("=" * 55)

    try:
        # Start the server with SSE transport
        mcp.run(
            transport="sse",
            host="127.0.0.1",
            port=4201,
            path="/sse",
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
