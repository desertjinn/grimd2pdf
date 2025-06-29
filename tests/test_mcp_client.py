#!/usr/bin/env python3
"""
Test script to validate MCP server functionality
"""
import asyncio
import json
import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

@pytest.mark.asyncio
async def test_mcp_server():
    """Test the MCP server by calling the conversion tool"""
    
    # Server parameters matching mcp.json
    server_params = StdioServerParameters(
        command="python",
        args=["-m", "grimd2pdf.server"],
        cwd="/Users/rohit/workspace/mcp/grimd2pdf",
        env={
            "PATH": "/Users/rohit/workspace/mcp/grimd2pdf/venv/bin:/opt/homebrew/bin:/usr/local/bin:/usr/bin:/bin"
        }
    )
    
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            # Initialize the session
            await session.initialize()
            
            print("✓ MCP Server initialized successfully")
            
            # List available tools
            tools = await session.list_tools()
            print(f"✓ Available tools: {[tool.name for tool in tools.tools]}")
            
            # Test the conversion tool
            result = await session.call_tool(
                "convert_markdown_file_to_pdf",
                {
                    "markdown_file_path": "test-document.md",
                    "output_filename": "mcp-server-test"
                }
            )
            
            print("✓ Tool call completed")
            print(f"Result: {json.dumps(result.content[0].text, indent=2)}")
            
            return result

if __name__ == "__main__":
    result = asyncio.run(test_mcp_server())