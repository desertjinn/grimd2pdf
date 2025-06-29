# Grimd2pdf - Mystical Markdown to PDF MCP Server

A mystical Model Context Protocol (MCP) server for converting Markdown files to PDF format. This enchanted tool provides both MCP protocol support and standalone HTTP API functionality with robust error handling, concurrent processing, and advanced PDF customization options.

## Features

✅ **MCP Protocol Support**: Full Model Context Protocol integration with tools, resources, and prompts
✅ **Multiple Conversion Modes**: Direct content conversion and file-based conversion
✅ **Advanced PDF Options**: Custom page sizes, margins, and formatting
✅ **Concurrent Processing**: Thread-pool based concurrent request handling
✅ **Robust Error Handling**: Comprehensive validation and error reporting
✅ **Base64 Output**: Optional base64 encoding for API integration
✅ **Health Monitoring**: Built-in health check functionality
✅ **Comprehensive Logging**: Detailed logging for monitoring and debugging
✅ **Multiple Deployment Modes**: MCP server or standalone HTTP API

## Installation

```bash
# Clone the repository
git clone <repository-url>
cd grimd2pdf

# Create virtual environment
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate

# Install dependencies
pip install -e .
```

## Quick Start

### 1. Running the Standalone HTTP Server

```bash
# Activate virtual environment
source venv/bin/activate

# Start HTTP server on port 8000
grimd2pdf-server --http --port 8000

# Server will be available at:
# - http://localhost:8000/docs (API documentation)
# - http://localhost:8000/health (health check)
# - http://localhost:8000/ (server info)
```

### 2. Running the MCP Server Locally

```bash
# Activate virtual environment
source venv/bin/activate

# Start MCP server (stdio mode)
grimd2pdf

# Or use the standalone server in MCP mode
grimd2pdf-server
```

## Usage

### As MCP Server (Default)

```bash
# Run as MCP server with stdio transport
grimd2pdf
```

### As HTTP API Server

```bash
# Run as HTTP API server
grimd2pdf-server --http --port 8000

# With custom configuration
grimd2pdf-server --http --host 127.0.0.1 --port 9000 --debug
```

### MCP Tools Available

#### 1. `convert_markdown_to_pdf`
Convert markdown content directly to PDF format.

**Parameters:**
- `markdown_content` (required): The markdown text to convert
- `output_filename` (optional): Filename for the PDF (without extension)
- `return_base64` (optional): If True, returns PDF as base64 string
- `page_size` (optional): PDF page size (A4, Letter, Legal, etc.)
- `margin_top/right/bottom/left` (optional): Page margins (e.g., '1in', '2.5cm')

**Example:**
```python
result = convert_markdown_to_pdf(
    markdown_content="# Hello World\n\nThis is a test document.",
    output_filename="my_document",
    return_base64=False,
    page_size="A4",
    margin_top="1.5in"
)
```

#### 2. `convert_markdown_file_to_pdf`
Convert a markdown file to PDF format.

**Parameters:**
- `markdown_file_path` (required): Path to the markdown file
- `output_filename` (optional): Filename for the PDF (without extension)
- `return_base64` (optional): If True, returns PDF as base64 string
- `page_size` (optional): PDF page size
- `margin_*` (optional): Page margins

**Example:**
```python
result = convert_markdown_file_to_pdf(
    markdown_file_path="./README.md",
    output_filename="readme_pdf",
    return_base64=True
)
```

#### 3. `health_check`
Check the health status of the conversion service.

**Example:**
```python
health = health_check()
print(f"Service status: {health['status']}")
```

### HTTP API Endpoints

When running in HTTP mode, the following endpoints are available:

- `GET /` - Server information and available endpoints
- `GET /health` - Health check endpoint
- `POST /convert` - Convert markdown content to PDF
- `POST /convert-file` - Convert markdown file to PDF
- `POST /upload` - Upload and convert markdown file
- `GET /download/{filename}` - Download generated PDF files
- `GET /mcp/info` - MCP server information
- `GET /mcp/tools` - List available MCP tools
- `POST /mcp/call` - Call MCP tools via HTTP
- `GET /docs` - API documentation (Swagger UI)

## Configuration

### Environment Variables

- `LOG_LEVEL`: Set logging level (DEBUG, INFO, WARNING, ERROR)
- `MAX_WORKERS`: Maximum number of worker threads for concurrent processing

### MCP Configuration

#### Local Development Setup

1. **Install the package locally:**
```bash
cd /path/to/grimd2pdf
source venv/bin/activate
pip install -e .
```

2. **Add to your MCP client configuration (e.g., Claude Desktop):**

Create or edit `~/Library/Application Support/Claude/claude_desktop_config.json`:
```json
{
  "mcpServers": {
    "grimd2pdf": {
      "command": "grimd2pdf",
      "args": []
    }
  }
}
```

3. **Alternative configuration with full path:**
```json
{
  "mcpServers": {
    "grimd2pdf": {
      "command": "/path/to/grimd2pdf/venv/bin/python",
      "args": ["-m", "grimd2pdf.server"]
    }
  }
}
```

#### Production Setup

For production deployment, you can install from PyPI (when published):
```bash
pip install grimd2pdf
```

Then use in MCP configuration:
```json
{
  "mcpServers": {
    "grimd2pdf": {
      "command": "grimd2pdf",
      "args": []
    }
  }
}
```

## Development

### Running Tests

```bash
# Install test dependencies
pip install -e ".[test]"

# Run tests
pytest tests/ -v

# Run with coverage
pytest tests/ --cov=grimd2pdf
```

### Code Quality

```bash
# Install development dependencies
pip install -e ".[test,build]"

# Run linting
ruff check .

# Run formatting
ruff format .
```

## Advanced Usage

### Custom PDF Styling

The server supports custom CSS styling for advanced PDF formatting:

```python
markdown_with_style = """
<style>
@page {
    size: A4;
    margin: 2cm;
}
body {
    font-family: 'Arial', sans-serif;
    font-size: 12pt;
}
</style>

# Your Document

Content goes here...
"""

result = convert_markdown_to_pdf(
    markdown_content=markdown_with_style,
    return_base64=True
)
```

### Batch Processing

```python
import asyncio
from concurrent.futures import ThreadPoolExecutor

async def batch_convert(files):
    loop = asyncio.get_event_loop()
    with ThreadPoolExecutor(max_workers=4) as executor:
        tasks = [
            loop.run_in_executor(
                executor,
                convert_markdown_file_to_pdf,
                file_path,
                None,
                True
            )
            for file_path in files
        ]
        results = await asyncio.gather(*tasks)
    return results
```

## Error Handling

All tools return a standardized response format:

```python
{
    "success": bool,              # Operation success status
    "message": str,              # Human-readable message
    "error": str,                # Error details (if success=False)
    "error_type": str,           # Error type (if success=False)
    "filename": str,             # Output filename (if success=True)    
    "size_bytes": int,           # PDF size in bytes (if success=True)
    "pdf_base64": str,           # Base64 PDF data (if requested)
    "output_path": str,          # File path (if file output)
    "page_size": str,            # Used page size
    "margins": dict              # Used margins
}
```

## Performance

- **Concurrent Processing**: Up to 4 concurrent conversions by default
- **Memory Efficient**: Streaming file processing for large documents
- **Fast Conversion**: Optimized PDF generation with markdown-pdf library
- **Caching**: Internal caching for repeated conversions (future feature)

## Troubleshooting

### Common Issues

1. **Import Error**: Ensure all dependencies are installed in the virtual environment
2. **Permission Denied**: Check file permissions for input/output directories
3. **Memory Issues**: For very large files, consider using file output instead of base64
4. **Encoding Issues**: Ensure markdown files are UTF-8 encoded

### Debug Mode

```bash
# Enable debug logging
grimd2pdf-server --http --debug --port 8000
```

### Health Check

```bash
# Test the service health
curl http://localhost:8000/health
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Add tests for new functionality
4. Ensure all tests pass
5. Submit a pull request

## License

MIT License - see LICENSE file for details.

## Support

For issues and questions:
- Create an issue on GitHub
- Review the troubleshooting section
- Check the API documentation at `/docs` when running HTTP mode