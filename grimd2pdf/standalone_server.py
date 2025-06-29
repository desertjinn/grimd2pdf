"""
Standalone MCP Tool Server for Markdown to PDF conversion.

This server can run in two modes:
1. MCP mode: Standard MCP protocol over stdio (default)
2. HTTP mode: REST API server for web/IDE integration
"""

import argparse
import asyncio
import json
import logging
import sys
import threading
from concurrent.futures import ThreadPoolExecutor
from typing import Dict, Any, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, File, UploadFile, Form
from fastapi.responses import JSONResponse, FileResponse
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
import uvicorn

from mcp.server import Server
from mcp.server.stdio import stdio_server
from mcp.server.session import ServerSession
from mcp.types import (
    CallToolRequest,
    ListToolsRequest,
    Tool,
    TextContent,
    JSONRPCRequest,
    JSONRPCResponse,
)

# Handle both relative and absolute imports for PyInstaller compatibility
try:
    from .server import convert_markdown_to_pdf, convert_markdown_file_to_pdf, health_check
except ImportError:
    # Fallback for when running as standalone script or PyInstaller binary
    try:
        from grimd2pdf.server import convert_markdown_to_pdf, convert_markdown_file_to_pdf, health_check
    except ImportError:
        # Last resort: try importing directly
        import sys
        import os
        # Add the parent directory to the path
        parent_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        if parent_dir not in sys.path:
            sys.path.insert(0, parent_dir)
        from grimd2pdf.server import convert_markdown_to_pdf, convert_markdown_file_to_pdf, health_check


# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

# Thread pool for handling concurrent requests
thread_pool = ThreadPoolExecutor(max_workers=4, thread_name_prefix="grimd2pdf-worker")


# MCP Server Implementation
class McpToolServer:
    """MCP Tool Server for Markdown to PDF conversion."""
    
    def __init__(self):
        self.server = Server("grimd2pdf")
        self._setup_tools()
    
    def _setup_tools(self):
        """Setup MCP tools."""
        
        @self.server.list_tools()
        async def list_tools() -> list[Tool]:
            """List available tools."""
            return [
                Tool(
                    name="convert_markdown_to_pdf",
                    description="Convert markdown content directly to PDF format",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "markdown_content": {
                                "type": "string",
                                "description": "The markdown text to convert to PDF"
                            },
                            "output_filename": {
                                "type": "string",
                                "description": "Optional filename for the PDF (without extension)"
                            },
                            "return_base64": {
                                "type": "boolean",
                                "description": "If True, returns PDF as base64 encoded string",
                                "default": False
                            }
                        },
                        "required": ["markdown_content"]
                    }
                ),
                Tool(
                    name="convert_markdown_file_to_pdf",
                    description="Convert a markdown file to PDF format",
                    inputSchema={
                        "type": "object",
                        "properties": {
                            "markdown_file_path": {
                                "type": "string",
                                "description": "Path to the markdown file to convert"
                            },
                            "output_filename": {
                                "type": "string",
                                "description": "Optional filename for the PDF (without extension)"
                            },
                            "return_base64": {
                                "type": "boolean",
                                "description": "If True, returns PDF as base64 encoded string",
                                "default": False
                            }
                        },
                        "required": ["markdown_file_path"]
                    }
                ),
                Tool(
                    name="health_check",
                    description="Check the health status of the markdown to PDF conversion service",
                    inputSchema={
                        "type": "object",
                        "properties": {}
                    }
                )
            ]
        
        @self.server.call_tool()
        async def call_tool(name: str, arguments: dict) -> list[TextContent]:
            """Handle tool calls."""
            try:
                if name == "convert_markdown_to_pdf":
                    result = convert_markdown_to_pdf(
                        markdown_content=arguments["markdown_content"],
                        output_filename=arguments.get("output_filename"),
                        return_base64=arguments.get("return_base64", False)
                    )
                elif name == "convert_markdown_file_to_pdf":
                    result = convert_markdown_file_to_pdf(
                        markdown_file_path=arguments["markdown_file_path"],
                        output_filename=arguments.get("output_filename"),
                        return_base64=arguments.get("return_base64", False)
                    )
                elif name == "health_check":
                    result = health_check()
                else:
                    raise ValueError(f"Unknown tool: {name}")
                
                return [TextContent(
                    type="text",
                    text=json.dumps(result, indent=2)
                )]
                
            except Exception as e:
                error_result = {
                    "success": False,
                    "error": str(e),
                    "message": f"Tool '{name}' failed: {str(e)}"
                }
                return [TextContent(
                    type="text",
                    text=json.dumps(error_result, indent=2)
                )]
    
    async def run_mcp_server(self):
        """Run the MCP server with stdio transport."""
        logger.info("Starting MCP Tool Server (stdio mode)")
        async with stdio_server() as (read_stream, write_stream):
            await self.server.run(
                read_stream,
                write_stream,
                self.server.create_initialization_options()
            )


# HTTP Server Implementation (FastAPI)
def create_http_app() -> FastAPI:
    """Create FastAPI application."""
    app = FastAPI(
        title="Grimd2pdf - Mystical Markdown to PDF Server",
        description="MCP-compatible HTTP server for converting markdown files to PDF with mystical powers",
        version="1.0.0"
    )
    
    # Add CORS middleware
    app.add_middleware(
        CORSMiddleware,
        allow_origins=["*"],
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )
    
    # Request models
    class ConvertMarkdownRequest(BaseModel):
        markdown_content: str
        output_filename: Optional[str] = None
        return_base64: bool = False
    
    class ConvertFileRequest(BaseModel):
        markdown_file_path: str
        output_filename: Optional[str] = None
        return_base64: bool = False
    
    # MCP Tool endpoints
    @app.get("/")
    async def root():
        """Root endpoint with MCP tool server information."""
        return {
            "name": "Grimd2pdf - Mystical Markdown to PDF Server",
            "version": "1.0.0",
            "protocol": "MCP-compatible HTTP API",
            "tools": [
                "convert_markdown_to_pdf",
                "convert_markdown_file_to_pdf", 
                "health_check"
            ],
            "endpoints": {
                "mcp_info": "/mcp/info",
                "mcp_tools": "/mcp/tools",
                "mcp_call": "/mcp/call",
                "health": "/health",
                "docs": "/docs"
            }
        }
    
    @app.get("/mcp/info")
    async def mcp_info():
        """MCP server information."""
        return {
            "name": "grimd2pdf",
            "version": "1.0.0",
            "protocol_version": "2024-11-05",
            "capabilities": {
                "tools": {}
            }
        }
    
    @app.get("/mcp/tools")
    async def list_mcp_tools():
        """List available MCP tools."""
        mcp_server = McpToolServer()
        tools = await mcp_server._setup_tools()  # This won't work as intended, need to refactor
        return {
            "tools": [
                {
                    "name": "convert_markdown_to_pdf",
                    "description": "Convert markdown content directly to PDF format",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "markdown_content": {"type": "string", "description": "The markdown text to convert to PDF"},
                            "output_filename": {"type": "string", "description": "Optional filename for the PDF (without extension)"},
                            "return_base64": {"type": "boolean", "description": "If True, returns PDF as base64 encoded string", "default": False}
                        },
                        "required": ["markdown_content"]
                    }
                },
                {
                    "name": "convert_markdown_file_to_pdf", 
                    "description": "Convert a markdown file to PDF format",
                    "inputSchema": {
                        "type": "object",
                        "properties": {
                            "markdown_file_path": {"type": "string", "description": "Path to the markdown file to convert"},
                            "output_filename": {"type": "string", "description": "Optional filename for the PDF (without extension)"},
                            "return_base64": {"type": "boolean", "description": "If True, returns PDF as base64 encoded string", "default": False}
                        },
                        "required": ["markdown_file_path"]
                    }
                },
                {
                    "name": "health_check",
                    "description": "Check the health status of the markdown to PDF conversion service",
                    "inputSchema": {"type": "object", "properties": {}}
                }
            ]
        }
    
    @app.post("/mcp/call")
    async def call_mcp_tool(request: dict):
        """Call an MCP tool."""
        try:
            tool_name = request.get("name")
            arguments = request.get("arguments", {})
            
            if tool_name == "convert_markdown_to_pdf":
                result = convert_markdown_to_pdf(
                    markdown_content=arguments["markdown_content"],
                    output_filename=arguments.get("output_filename"),
                    return_base64=arguments.get("return_base64", False)
                )
            elif tool_name == "convert_markdown_file_to_pdf":
                result = convert_markdown_file_to_pdf(
                    markdown_file_path=arguments["markdown_file_path"],
                    output_filename=arguments.get("output_filename"),
                    return_base64=arguments.get("return_base64", False)
                )
            elif tool_name == "health_check":
                result = health_check()
            else:
                raise ValueError(f"Unknown tool: {tool_name}")
            
            return {
                "content": [
                    {
                        "type": "text",
                        "text": json.dumps(result, indent=2)
                    }
                ]
            }
            
        except Exception as e:
            return JSONResponse(
                status_code=400,
                content={
                    "error": {
                        "code": -32602,
                        "message": str(e)
                    }
                }
            )
    
    # Direct HTTP endpoints for convenience
    @app.get("/health")
    async def health():
        """Health check endpoint."""
        result = health_check()
        status_code = 200 if result["success"] else 503
        return JSONResponse(status_code=status_code, content=result)
    
    @app.post("/convert")
    async def convert_markdown(request: ConvertMarkdownRequest):
        """Convert markdown content to PDF."""
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            thread_pool,
            convert_markdown_to_pdf,
            request.markdown_content,
            request.output_filename,
            request.return_base64
        )
        status_code = 200 if result["success"] else 400
        return JSONResponse(status_code=status_code, content=result)
    
    @app.post("/convert-file")
    async def convert_markdown_file_endpoint(request: ConvertFileRequest):
        """Convert a markdown file to PDF."""
        loop = asyncio.get_event_loop()
        result = await loop.run_in_executor(
            thread_pool,
            convert_markdown_file_to_pdf,
            request.markdown_file_path,
            request.output_filename,
            request.return_base64
        )
        status_code = 200 if result["success"] else 400
        return JSONResponse(status_code=status_code, content=result)
    
    @app.post("/upload")
    async def upload_and_convert(
        file: UploadFile = File(...),
        output_filename: Optional[str] = Form(None),
        return_base64: bool = Form(False)
    ):
        """Upload a markdown file and convert it to PDF."""
        try:
            if not file.filename.endswith(('.md', '.markdown')):
                raise HTTPException(status_code=400, detail="File must be a markdown file")
            
            content = await file.read()
            markdown_content = content.decode('utf-8')
            
            if not output_filename:
                output_filename = Path(file.filename).stem
            
            loop = asyncio.get_event_loop()
            result = await loop.run_in_executor(
                thread_pool,
                convert_markdown_to_pdf,
                markdown_content,
                output_filename,
                return_base64
            )
            
            status_code = 200 if result["success"] else 400
            return JSONResponse(status_code=status_code, content=result)
            
        except Exception as e:
            return JSONResponse(
                status_code=500,
                content={"success": False, "error": str(e)}
            )
    
    @app.get("/download/{filename}")
    async def download_file(filename: str):
        """Download a generated PDF file."""
        file_path = Path(filename)
        if not file_path.exists():
            raise HTTPException(status_code=404, detail="File not found")
        
        return FileResponse(
            path=str(file_path),
            filename=filename,
            media_type='application/pdf'
        )
    
    return app


def create_parser():
    """Create command line argument parser."""
    parser = argparse.ArgumentParser(
        description="Grimd2pdf - Mystical Markdown to PDF Server",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run as MCP server (default, stdio mode)
  grimd2pdf-server

  # Run as HTTP API server
  grimd2pdf-server --http --port 8000

  # Run HTTP server on custom host/port
  grimd2pdf-server --http --host 127.0.0.1 --port 9000

  # Run with debug logging
  grimd2pdf-server --http --debug --port 8000
        """
    )
    
    parser.add_argument(
        "--http",
        action="store_true",
        help="Run as HTTP API server instead of MCP stdio server"
    )
    
    parser.add_argument(
        "--host",
        default="0.0.0.0",
        help="Host to bind HTTP server to (default: 0.0.0.0, only used with --http)"
    )
    
    parser.add_argument(
        "--port",
        type=int,
        default=8000,
        help="Port for HTTP server (default: 8000, only used with --http)"
    )
    
    parser.add_argument(
        "--debug",
        action="store_true",
        help="Enable debug logging"
    )
    
    parser.add_argument(
        "--reload",
        action="store_true",
        help="Enable auto-reload for development (HTTP mode only)"
    )
    
    return parser


async def main_async():
    """Async main entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Configure logging
    if args.debug:
        logging.getLogger().setLevel(logging.DEBUG)
        logger.debug("Debug logging enabled")
    
    if args.http:
        # HTTP server mode
        logger.info(f"Starting Grimd2pdf HTTP Server on {args.host}:{args.port}")
        logger.info(f"MCP-compatible API available at http://{args.host}:{args.port}/mcp/")
        logger.info(f"API documentation at http://{args.host}:{args.port}/docs")
        
        app = create_http_app()
        config = uvicorn.Config(
            app,
            host=args.host,
            port=args.port,
            reload=args.reload,
            log_level="debug" if args.debug else "info"
        )
        server = uvicorn.Server(config)
        await server.serve()
    else:
        # MCP server mode (default)
        mcp_server = McpToolServer()
        await mcp_server.run_mcp_server()


def main():
    """Main entry point."""
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        logger.info("Server stopped by user")
    except Exception as e:
        logger.error(f"Server failed: {e}")
        sys.exit(1)


if __name__ == "__main__":
    main()