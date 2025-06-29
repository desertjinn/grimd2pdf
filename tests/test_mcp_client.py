#!/usr/bin/env python3
"""
Test script to validate MCP server functionality
"""
import asyncio
import json
import os
import sys
import tempfile
from pathlib import Path
import pytest
from mcp import ClientSession, StdioServerParameters
from mcp.client.stdio import stdio_client

@pytest.mark.asyncio
async def test_mcp_server():
    """Test the MCP server by calling the conversion tool"""
    
    # Get the current working directory (works in both local and CI)
    current_dir = Path.cwd()
    
    # Server parameters that work in any environment
    server_params = StdioServerParameters(
        command=sys.executable,  # Use the current Python interpreter
        args=["-m", "grimd2pdf.server"],
        cwd=str(current_dir)  # Use current directory instead of hardcoded path
    )
    
    # Create a temporary markdown file for testing
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as temp_file:
        temp_file.write("# Test Document\n\nThis is a test markdown document for MCP server testing.")
        temp_file_path = temp_file.name
    
    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                # Initialize the session
                await session.initialize()
                
                print("✓ MCP Server initialized successfully")
                
                # List available tools
                tools = await session.list_tools()
                print(f"✓ Available tools: {[tool.name for tool in tools.tools]}")
                
                # Test the conversion tool with the temporary file
                result = await session.call_tool(
                    "convert_markdown_to_pdf",
                    {
                        "markdown_content": "# Test Document\n\nThis is a test markdown document for MCP server testing.",
                        "output_filename": "mcp-server-test",
                        "return_base64": True
                    }
                )
                
                print("✓ Tool call completed")
                print(f"Result: {json.dumps(result.content[0].text, indent=2)}")
                
                return result
    finally:
        # Clean up the temporary file
        try:
            os.unlink(temp_file_path)
        except OSError:
            pass  # Ignore errors if file doesn't exist

if __name__ == "__main__":
    result = asyncio.run(test_mcp_server())