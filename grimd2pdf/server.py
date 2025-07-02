"""
Grimd2pdf - Mystical Markdown to PDF MCP Server

A Model Context Protocol server that provides magical tools for converting markdown files to PDF format.
"""

from __future__ import annotations

import base64
import logging
import os
import tempfile
import re
from typing import Dict, Any, Optional, List, Tuple
from pathlib import Path

from mcp.server import FastMCP
from markdown_pdf import MarkdownPdf, Section

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Initialize MCP server
mcp = FastMCP("Grimd2pdf - Mystical Markdown to PDF Converter")


def sanitize_markdown_content(content: str) -> Tuple[str, List[str]]:
    """
    Sanitize and fix common markdown formatting issues that cause PDF conversion errors.
    
    Args:
        content: Raw markdown content
        
    Returns:
        Tuple of (sanitized_content, list_of_warnings)
    """
    warnings = []
    sanitized = content
    
    # Remove null bytes and control characters that can cause issues
    sanitized = re.sub(r'[\x00-\x08\x0b\x0c\x0e-\x1f\x7f-\x9f]', '', sanitized)
    
    # Fix common table formatting issues
    lines = sanitized.split('\n')
    fixed_lines = []
    in_table = False
    table_columns = 0
    
    for i, line in enumerate(lines):
        stripped_line = line.strip()
        
        # Detect table rows
        if '|' in stripped_line and stripped_line:
            if not in_table:
                in_table = True
                table_columns = stripped_line.count('|') + 1
                # Check if previous line should be a table header
                if i > 0 and fixed_lines and not fixed_lines[-1].strip().startswith('|'):
                    # Add table header separator if missing
                    pipe_count = stripped_line.count('|')
                    if pipe_count >= 1:  # At least one column
                        separator = '|' + '---|' * (pipe_count if pipe_count >= 2 else 2)
                        if not separator.endswith('|'):
                            separator += '|'
                        fixed_lines.append(separator)
                        warnings.append(f"Added missing table header separator at line {i+1}")
            
            # Fix malformed table rows
            if stripped_line.startswith('|') and not stripped_line.endswith('|'):
                line = line.rstrip() + '|'
                warnings.append(f"Fixed incomplete table row at line {i+1}")
            elif not stripped_line.startswith('|') and stripped_line.endswith('|'):
                line = '|' + line
                warnings.append(f"Fixed incomplete table row at line {i+1}")
            elif not stripped_line.startswith('|') and not stripped_line.endswith('|'):
                # Line has pipes but isn't properly formatted as table row
                line = '|' + line.rstrip() + '|'
                warnings.append(f"Fixed incomplete table row at line {i+1}")
                
        elif in_table and stripped_line and '|' not in stripped_line:
            # Check if this might be a continuation of table data without pipes
            # Split by common delimiters to see if it looks like tabular data
            potential_cells = None
            
            # Try different separators
            for sep in ['\t', '  ', ' ']:  # Tab, double space, single space
                if sep in stripped_line:
                    potential_cells = [cell.strip() for cell in stripped_line.split(sep) if cell.strip()]
                    break
            
            # If we found what looks like tabular data, convert it to table row
            if potential_cells and len(potential_cells) >= 2:
                line = '| ' + ' | '.join(potential_cells) + ' |'
                warnings.append(f"Converted plain text to table row at line {i+1}")
            else:
                in_table = False
        elif in_table and not stripped_line:
            # Empty line - end of table
            in_table = False
        else:
            in_table = False
            
        fixed_lines.append(line)
    
    sanitized = '\n'.join(fixed_lines)
    
    # Fix heading hierarchy issues
    headings = re.findall(r'^(#{1,6})\s+(.+)$', sanitized, re.MULTILINE)
    if headings:
        # Check for heading level jumps that might cause hierarchy errors
        prev_level = 0
        heading_fixes = []
        
        for match in re.finditer(r'^(#{1,6})\s+(.+)$', sanitized, re.MULTILINE):
            current_level = len(match.group(1))
            if prev_level > 0 and current_level > prev_level + 1:
                # Found a level jump (e.g., # to ###)
                # Fix by reducing to appropriate level
                proper_level = prev_level + 1
                proper_heading = '#' * proper_level + ' ' + match.group(2)
                heading_fixes.append((match.group(0), proper_heading))
                warnings.append(f"Fixed heading hierarchy jump from level {prev_level} to {current_level}")
                prev_level = proper_level
            else:
                prev_level = current_level
        
        # Apply heading fixes
        for old_heading, new_heading in heading_fixes:
            sanitized = sanitized.replace(old_heading, new_heading, 1)
    
    # Fix list formatting issues
    sanitized = re.sub(r'^(\s*)-(\S)', r'\1- \2', sanitized, flags=re.MULTILINE)
    sanitized = re.sub(r'^(\s*)\*(\S)', r'\1* \2', sanitized, flags=re.MULTILINE)
    sanitized = re.sub(r'^(\s*)\d+\.(\S)', r'\1\g<0> \2', sanitized, flags=re.MULTILINE)
    
    # Fix code block formatting
    sanitized = re.sub(r'^```(\w+)?\n\n', r'```\1\n', sanitized, flags=re.MULTILINE)
    
    # Remove excessive blank lines that can cause parsing issues
    sanitized = re.sub(r'\n{4,}', '\n\n\n', sanitized)
    
    # Ensure content ends with a newline
    if not sanitized.endswith('\n'):
        sanitized += '\n'
    
    return sanitized, warnings


def validate_markdown_structure(content: str) -> Tuple[bool, List[str]]:
    """
    Validate markdown structure and identify potential issues.
    
    Args:
        content: Markdown content to validate
        
    Returns:
        Tuple of (is_valid, list_of_errors)
    """
    errors = []
    
    # Check for empty content
    if not content.strip():
        errors.append("Content is empty")
        return False, errors
    
    # Check for malformed tables
    lines = content.split('\n')
    in_table_context = False
    
    for i, line in enumerate(lines, 1):
        stripped_line = line.strip()
        
        # Detect if we're in a table context
        if '|' in stripped_line and stripped_line:
            # Count pipes to ensure table consistency
            pipe_count = stripped_line.count('|')
            
            # Only report as malformed if it looks like it's trying to be a table row
            # but doesn't have enough separators
            if pipe_count >= 1:  # Has at least one pipe, so might be table-related
                if pipe_count < 2 and (stripped_line.startswith('|') or stripped_line.endswith('|')):
                    # Looks like a malformed table row (starts or ends with pipe but not enough pipes)
                    errors.append(f"Malformed table row at line {i}: insufficient column separators")
                # If it has pipes but doesn't start/end with them, it might just be content with pipes
                # We'll let the sanitization handle it
            in_table_context = True
        elif in_table_context and not stripped_line:
            # Empty line after table context
            in_table_context = False
        elif in_table_context and stripped_line and '|' not in stripped_line:
            # Non-table content after table context
            in_table_context = False
    
    # Check for heading structure
    headings = re.findall(r'^(#{1,6})\s+(.+)$', content, re.MULTILINE)
    if not headings:
        # No headings found - could be valid, just warn
        pass
    else:
        # Check for extremely deep nesting that might cause issues
        max_level = max(len(h[0]) for h in headings)
        if max_level > 6:
            errors.append(f"Heading level too deep: {max_level} (maximum is 6)")
    
    # Check for unclosed code blocks
    code_blocks = content.count('```')
    if code_blocks % 2 != 0:
        errors.append("Unclosed code block detected")
    
    # Check for extremely long lines that might cause rendering issues
    for i, line in enumerate(lines, 1):
        if len(line) > 10000:  # Arbitrary but reasonable limit
            errors.append(f"Extremely long line at {i}: {len(line)} characters")
    
    return len(errors) == 0, errors


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
        # Sanitize and validate markdown content
        sanitized_content, sanitization_warnings = sanitize_markdown_content(markdown_content)
        is_valid, validation_errors = validate_markdown_structure(sanitized_content)
        
        if not is_valid:
            logger.warning(f"Markdown validation failed: {validation_errors}")
            return {
                "success": False,
                "error": f"Invalid markdown structure: {'; '.join(validation_errors)}",
                "message": "The provided markdown content has structural issues that prevent PDF conversion",
                "validation_errors": validation_errors,
                "sanitization_warnings": sanitization_warnings
            }
        
        if sanitization_warnings:
            logger.info(f"Applied markdown sanitization fixes: {sanitization_warnings}")
        
        # Create a PDF from the markdown content
        try:
            logger.debug("Creating MarkdownPdf object")
            pdf = MarkdownPdf(toc_level=6, mode='commonmark', optimize=True)
            
            # Create section with custom CSS for margins and page size if needed
            section_content = sanitized_content
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
            
            logger.debug("Adding section to PDF")
            pdf.add_section(Section(section_content))
            
        except Exception as pdf_error:
            logger.error(f"Failed to create PDF object: {str(pdf_error)}")
            
            # Check for specific error patterns and provide better error messages
            error_str = str(pdf_error).lower()
            if "hierarchy" in error_str:
                return {
                    "success": False,
                    "error": f"Markdown hierarchy error: {str(pdf_error)}",
                    "message": "The markdown content has heading or structure issues. Try using simpler heading levels or check table formatting.",
                    "suggested_fix": "Ensure headings progress logically (# then ## then ###) and tables have proper formatting with | separators",
                    "sanitization_warnings": sanitization_warnings
                }
            elif "table" in error_str or "row" in error_str:
                return {
                    "success": False,
                    "error": f"Markdown table error: {str(pdf_error)}",
                    "message": "The markdown content has table formatting issues.",
                    "suggested_fix": "Check that all table rows have the same number of columns and proper | separators",
                    "sanitization_warnings": sanitization_warnings
                }
            else:
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
                logger.debug(f"Saving PDF to temporary file: {temp_pdf.name}")
                pdf.save(temp_pdf.name)
                
                # Read the PDF file and encode as base64
                with open(temp_pdf.name, 'rb') as pdf_file:
                    pdf_bytes = pdf_file.read()
                    pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
                
                # Clean up temporary file
                os.unlink(temp_pdf.name)
                
                logger.info(f"Successfully converted markdown to PDF (base64), size: {len(pdf_bytes)} bytes")
                result = {
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
                
                if sanitization_warnings:
                    result["sanitization_warnings"] = sanitization_warnings
                    result["message"] += f" (Applied {len(sanitization_warnings)} formatting fixes)"
                
                return result
        else:
            # Save to current directory
            output_path = Path(output_filename)
            logger.debug(f"Saving PDF to file: {output_path}")
            try:
                pdf.save(str(output_path))
                file_size = output_path.stat().st_size
                logger.info(f"Successfully converted markdown to PDF file: {output_path}, size: {file_size} bytes")
                result = {
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
            except PermissionError as perm_err:
                # Fallback: return base64 instead of writing to disk
                logger.warning(f"Permission error while saving PDF: {perm_err}. Falling back to base64 response.")
                with tempfile.NamedTemporaryFile(suffix=".pdf", delete=False) as temp_pdf:
                    pdf.save(temp_pdf.name)
                    with open(temp_pdf.name, 'rb') as pdf_file:
                        pdf_bytes = pdf_file.read()
                        pdf_base64 = base64.b64encode(pdf_bytes).decode('utf-8')
                    os.unlink(temp_pdf.name)
                result = {
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
                    "fallback_to_base64": True,
                    "message": "File-system permissions prevented writing PDF to disk; returned base64 instead"
                }
            
            if sanitization_warnings:
                result["sanitization_warnings"] = sanitization_warnings
                result["message"] += f" (Applied {len(sanitization_warnings)} formatting fixes)"
            
            return result
            
    except Exception as e:
        logger.error(f"Failed to convert markdown to PDF: {str(e)}", exc_info=True)
        
        # Provide specific error information based on the error type
        error_str = str(e).lower()
        if "hierarchy" in error_str or "bad hierarchy level" in error_str:
            return {
                "success": False,
                "error": str(e),
                "error_type": type(e).__name__,
                "message": "PDF conversion failed due to markdown hierarchy issues. This often happens with malformed tables or incorrect heading levels.",
                "suggested_fixes": [
                    "Check table formatting: ensure all rows have the same number of columns",
                    "Verify heading hierarchy: use # then ## then ### progression",
                    "Remove any special characters or malformed content",
                    "Ensure tables have proper header separators (---|---|---)"
                ],
                "common_causes": [
                    "LLM-generated content with inconsistent table formatting",
                    "Missing table header separators",
                    "Heading level jumps (e.g., # directly to ###)",
                    "Malformed table rows with inconsistent column counts"
                ]
            }
        else:
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