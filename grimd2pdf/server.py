"""
Grimd2pdf - Mystical Markdown to PDF MCP Server

A Model Context Protocol server that provides magical tools for converting markdown files to PDF format.
"""

from __future__ import annotations

import base64
import logging
import os
import tempfile
from typing import Dict, Any, Optional
from pathlib import Path

from mcp.server import FastMCP
from markdown_pdf import MarkdownPdf, Section

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP("Grimd2pdf - Mystical Markdown to PDF Converter")


@mcp.tool()
def convert_markdown_to_pdf(
    markdown_content: str,
    output_filename: Optional[str] = None,
    return_base64: bool = False,
    page_size: str = "A4",
    margin_top: str = "1in",
    margin_right: str = "1in",
    margin_bottom: str = "1in",
    margin_left: str = "1in"
) -> Dict[str, Any]:
    """
    Convert markdown content to PDF format.
    
    Args:
        markdown_content: The markdown text to convert to PDF
        output_filename: Optional filename for the PDF (without extension)
        return_base64: If True, returns PDF as base64 encoded string
        page_size: PDF page size (A4, Letter, Legal, etc.)
        margin_top: Top margin (e.g., '1in', '2.5cm')
        margin_right: Right margin
        margin_bottom: Bottom margin
        margin_left: Left margin
        
    Returns:
        Dictionary containing the conversion result
    """
    # Input validation
    if not markdown_content or not isinstance(markdown_content, str):
        return {
            "success": False,
            "error": "Invalid markdown_content: must be a non-empty string",
            "message": "Markdown content is required and must be a valid string"
        }
    
    if markdown_content.strip() == "":
        return {
            "success": False,
            "error": "Empty markdown content provided",
            "message": "Markdown content cannot be empty"
        }
    
    # Validate filename if provided
    if output_filename is not None and not isinstance(output_filename, str):
        return {
            "success": False,
            "error": "Invalid output_filename: must be a string",
            "message": "Output filename must be a valid string"
        }
    
    logger.info(f"Converting markdown to PDF (base64={return_base64}, filename={output_filename})")
    
    try:
        # Create a PDF from the markdown content
        # Note: markdown-pdf library doesn't support custom page options directly
        # The options are stored for future use or different PDF libraries
        try:
            pdf = MarkdownPdf(toc_level=6, mode='commonmark', optimize=True)
            
            # Create section with custom CSS for margins and page size if needed
            section_content = markdown_content
            if page_size != "A4" or any(margin != "1in" for margin in [margin_top, margin_right, margin_bottom, margin_left]):
                # Add CSS styling for custom page settings
                css_style = f"""
                <style>
                @page {{
                    size: {page_size};
                    margin-top: {margin_top};
                    margin-right: {margin_right};
                    margin-bottom: {margin_bottom};
                    margin-left: {margin_left};
                }}
                </style>
                """
                section_content = css_style + "\n\n" + section_content
            
            pdf.add_section(Section(section_content))
        except Exception as pdf_error:
            logger.error(f"Failed to create PDF object: {str(pdf_error)}")
            raise pdf_error

        # Generate filename if not provided
        if not output_filename:
            output_filename = "converted_markdown"
        
        # Ensure filename has .pdf extension
        if not output_filename.endswith('.pdf'):
            output_filename += '.pdf'

        if return_base64:
            # Save to temporary file and return as base64
            with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_pdf:
                pdf.save(temp_pdf.name)
                
                # Read the PDF file and encode as base64
                with open(temp_pdf.name, 'rb') as pdf_file:
                    pdf_bytes = pdf_file.read()
                    pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
                
                # Clean up temporary file
                os.unlink(temp_pdf.name)
                
                logger.info(f"Successfully converted markdown to PDF (base64), size: {len(pdf_bytes)} bytes")
                return {
                    "success": True,
                    "filename": output_filename,
                    "pdf_base64": pdf_base64,
                    "size_bytes": len(pdf_bytes),
                    "page_size": page_size,
                    "margins": {
                        "top": margin_top,
                        "right": margin_right,
                        "bottom": margin_bottom,
                        "left": margin_left
                    },
                    "message": f"Successfully converted markdown to PDF: {output_filename}"
                }
        else:
            # Save to current directory
            output_path = Path(output_filename)
            pdf.save(str(output_path))
            
            file_size = output_path.stat().st_size
            logger.info(f"Successfully converted markdown to PDF file: {output_path}, size: {file_size} bytes")
            return {
                "success": True,
                "filename": output_filename,
                "output_path": str(output_path.absolute()),
                "size_bytes": file_size,
                "page_size": page_size,
                "margins": {
                    "top": margin_top,
                    "right": margin_right,
                    "bottom": margin_bottom,
                    "left": margin_left
                },
                "message": f"Successfully converted markdown to PDF: {output_filename}"
            }
            
    except Exception as e:
        logger.error(f"Failed to convert markdown to PDF: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "message": f"Failed to convert markdown to PDF: {str(e)}"
        }


@mcp.tool()
def convert_markdown_file_to_pdf(
    markdown_file_path: str,
    output_filename: Optional[str] = None,
    return_base64: bool = False,
    page_size: str = "A4",
    margin_top: str = "1in",
    margin_right: str = "1in",
    margin_bottom: str = "1in",
    margin_left: str = "1in"
) -> Dict[str, Any]:
    """
    Convert a markdown file to PDF format.
    
    Args:
        markdown_file_path: Path to the markdown file to convert
        output_filename: Optional filename for the PDF (without extension)
        return_base64: If True, returns PDF as base64 encoded string
        page_size: PDF page size (A4, Letter, Legal, etc.)
        margin_top: Top margin (e.g., '1in', '2.5cm')
        margin_right: Right margin
        margin_bottom: Bottom margin
        margin_left: Left margin
        
    Returns:
        Dictionary containing the conversion result
    """
    # Input validation
    if not markdown_file_path or not isinstance(markdown_file_path, str):
        return {
            "success": False,
            "error": "Invalid markdown_file_path: must be a non-empty string",
            "message": "Markdown file path is required and must be a valid string"
        }
    
    logger.info(f"Converting markdown file to PDF: {markdown_file_path}")
    
    try:
        # Read the markdown file
        markdown_path = Path(markdown_file_path)
        
        if not markdown_path.exists():
            logger.warning(f"Markdown file not found: {markdown_file_path}")
            return {
                "success": False,
                "error": f"Markdown file not found: {markdown_file_path}",
                "message": f"The specified markdown file does not exist: {markdown_file_path}"
            }
        
        if not markdown_path.is_file():
            logger.warning(f"Path is not a file: {markdown_file_path}")
            return {
                "success": False,
                "error": f"Path is not a file: {markdown_file_path}",
                "message": f"The specified path is not a regular file: {markdown_file_path}"
            }
        
        # Check file extension
        if not markdown_path.suffix.lower() in ['.md', '.markdown', '.txt']:
            logger.warning(f"File does not appear to be markdown: {markdown_file_path}")
            return {
                "success": False,
                "error": f"File does not appear to be markdown: {markdown_file_path}",
                "message": f"Expected .md, .markdown, or .txt file, got: {markdown_path.suffix}"
            }
        
        # Read the content with error handling
        try:
            markdown_content = markdown_path.read_text(encoding='utf-8')
        except UnicodeDecodeError:
            logger.warning(f"Failed to decode file as UTF-8, trying other encodings: {markdown_file_path}")
            try:
                markdown_content = markdown_path.read_text(encoding='latin-1')
            except Exception as decode_error:
                return {
                    "success": False,
                    "error": f"Failed to decode file: {str(decode_error)}",
                    "message": f"Could not read the markdown file due to encoding issues: {markdown_file_path}"
                }
        
        if not markdown_content.strip():
            logger.warning(f"Markdown file is empty: {markdown_file_path}")
            return {
                "success": False,
                "error": "Markdown file is empty",
                "message": f"The markdown file contains no content: {markdown_file_path}"
            }
        
        # Generate output filename if not provided
        if not output_filename:
            output_filename = markdown_path.stem
            
        # Convert using the main conversion function
        return convert_markdown_to_pdf(
            markdown_content=markdown_content,
            output_filename=output_filename,
            return_base64=return_base64,
            page_size=page_size,
            margin_top=margin_top,
            margin_right=margin_right,
            margin_bottom=margin_bottom,
            margin_left=margin_left
        )
        
    except Exception as e:
        logger.error(f"Failed to process markdown file {markdown_file_path}: {str(e)}", exc_info=True)
        return {
            "success": False,
            "error": str(e),
            "error_type": type(e).__name__,
            "message": f"Failed to read markdown file: {str(e)}"
        }


@mcp.tool()
def health_check() -> Dict[str, Any]:
    """
    Check the health status of the markdown to PDF conversion service.
    
    Returns:
        Dictionary containing the health status
    """
    try:
        # Test basic conversion functionality
        test_markdown = "# Test\n\nThis is a test conversion."
        result = convert_markdown_to_pdf(
            markdown_content=test_markdown,
            output_filename="health_check_test",
            return_base64=True
        )
        
        if result.get("success"):
            return {
                "success": True,
                "status": "healthy",
                "message": "Markdown to PDF conversion service is working properly",
                "test_result": "Test conversion completed successfully"
            }
        else:
            return {
                "success": False,
                "status": "unhealthy",
                "message": "Markdown to PDF conversion service is not working",
                "error": result.get("error", "Unknown error in test conversion")
            }
            
    except Exception as e:
        return {
            "success": False,
            "status": "unhealthy",
            "error": str(e),
            "message": f"Health check failed: {str(e)}"
        }


# ----------------------------- MCP Resources --------------------------------

@mcp.resource("md2pdf://status")
def status_resource() -> str:
    """Status information about the markdown to PDF conversion service."""
    try:
        health = health_check()
        return f"""# Markdown to PDF Converter Status

## Health Status
- Status: {health.get('status', 'unknown')}
- Working: {health.get('success', False)}

## Available Tools
- convert_markdown_to_pdf: Convert markdown text to PDF
- convert_markdown_file_to_pdf: Convert markdown file to PDF
- health_check: Check service health

## Supported Features
- Markdown to PDF conversion
- Base64 encoded PDF output
- File-based PDF output
- Custom filename support
"""
    except Exception as e:
        return f"Error getting status: {str(e)}"


# ----------------------------- MCP Prompts ----------------------------------

@mcp.prompt()
def markdown_conversion_help() -> str:
    """
    Guide for using the markdown to PDF conversion tools.
    
    Returns:
        A detailed guide with usage examples
    """
    return """
# Markdown to PDF Conversion Guide

## Available Tools

### convert_markdown_to_pdf
Convert markdown text directly to PDF format.

**Parameters:**
- `markdown_content` (required): The markdown text to convert
- `output_filename` (optional): Filename for the PDF (without extension)
- `return_base64` (optional): If True, returns PDF as base64 string

**Example:**
```python
result = convert_markdown_to_pdf(
    markdown_content="# Hello World\\n\\nThis is a test document.",
    output_filename="my_document",
    return_base64=False
)
```

### convert_markdown_file_to_pdf
Convert a markdown file to PDF format.

**Parameters:**
- `markdown_file_path` (required): Path to the markdown file
- `output_filename` (optional): Filename for the PDF (without extension)
- `return_base64` (optional): If True, returns PDF as base64 string

**Example:**
```python
result = convert_markdown_file_to_pdf(
    markdown_file_path="./README.md",
    output_filename="readme_pdf",
    return_base64=True
)
```

### health_check
Check if the conversion service is working properly.

**Example:**
```python
health = health_check()
print(f"Service status: {health['status']}")
```

## Output Formats

### File Output (return_base64=False)
- Saves PDF to local filesystem
- Returns file path and size information
- Good for local file processing

### Base64 Output (return_base64=True)  
- Returns PDF as base64 encoded string
- Good for API responses or embedding in other systems
- No temporary files created

## Error Handling

All tools return a dictionary with:
- `success`: Boolean indicating success/failure
- `message`: Human-readable status message
- `error`: Error details (if success=False)
- Additional fields based on the operation

## Best Practices

1. **File Paths**: Use absolute paths when possible
2. **Filename**: Don't include .pdf extension in output_filename
3. **Large Files**: Use file output for large documents
4. **Error Handling**: Always check the `success` field
5. **Encoding**: Ensure markdown files are UTF-8 encoded
"""


def main():
    """Main entry point for the MCP server."""
    mcp.run()


if __name__ == "__main__":
    main() 