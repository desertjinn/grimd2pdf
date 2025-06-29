"""
Tests for the MCP server functionality.
"""

import pytest
import json
from grimd2pdf.server import convert_markdown_to_pdf, convert_markdown_file_to_pdf, health_check


def test_convert_markdown_to_pdf_basic():
    """Test basic markdown to PDF conversion."""
    markdown_content = "# Test Header\n\nThis is a test paragraph with **bold** text."
    
    result = convert_markdown_to_pdf(
        markdown_content=markdown_content,
        output_filename="test_output",
        return_base64=True
    )
    
    assert result["success"] is True
    assert "pdf_base64" in result
    assert result["filename"] == "test_output.pdf"
    assert result["size_bytes"] > 0
    assert "page_size" in result
    assert "margins" in result


def test_convert_markdown_to_pdf_with_options():
    """Test markdown to PDF conversion with custom options."""
    markdown_content = "# Test Header\n\nThis is a test with custom options."
    
    result = convert_markdown_to_pdf(
        markdown_content=markdown_content,
        output_filename="custom_test",
        return_base64=True,
        page_size="Letter",
        margin_top="2in",
        margin_left="1.5in"
    )
    
    assert result["success"] is True
    assert result["page_size"] == "Letter"
    assert result["margins"]["top"] == "2in"
    assert result["margins"]["left"] == "1.5in"


def test_convert_markdown_invalid_input():
    """Test conversion with invalid input."""
    # Test empty content
    result = convert_markdown_to_pdf(markdown_content="")
    assert result["success"] is False
    assert "empty" in result["error"].lower()
    
    # Test None content
    result = convert_markdown_to_pdf(markdown_content=None)
    assert result["success"] is False


def test_convert_markdown_file_to_pdf():
    """Test converting a markdown file to PDF."""
    # Create a temporary markdown file
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.md', delete=False) as temp_file:
        temp_file.write("# File Test\n\nThis is content from a file.")
        temp_file_path = temp_file.name
    
    try:
        result = convert_markdown_file_to_pdf(
            markdown_file_path=temp_file_path,
            return_base64=True
        )
        
        assert result["success"] is True
        assert "pdf_base64" in result
        assert result["size_bytes"] > 0
    finally:
        os.unlink(temp_file_path)


def test_convert_markdown_file_not_found():
    """Test conversion with non-existent file."""
    result = convert_markdown_file_to_pdf(
        markdown_file_path="/nonexistent/file.md"
    )
    
    assert result["success"] is False
    assert "not found" in result["error"].lower()


def test_convert_markdown_file_invalid_extension():
    """Test conversion with invalid file extension."""
    import tempfile
    import os
    
    with tempfile.NamedTemporaryFile(mode='w', suffix='.invalid', delete=False) as temp_file:
        temp_file.write("# Test content")
        temp_file_path = temp_file.name
    
    try:
        result = convert_markdown_file_to_pdf(
            markdown_file_path=temp_file_path
        )
        
        assert result["success"] is False
        assert "markdown" in result["error"].lower()
    finally:
        os.unlink(temp_file_path)


def test_health_check():
    """Test the health check functionality."""
    result = health_check()
    
    assert "success" in result
    assert "status" in result
    assert "message" in result
    
    if result["success"]:
        assert result["status"] == "healthy"
    else:
        assert result["status"] == "unhealthy"


def test_large_markdown_content():
    """Test conversion with large markdown content."""
    # Create large markdown content (simulate large document)
    large_content = "# Large Document\n\n"
    for i in range(100):
        large_content += f"## Section {i}\n\nThis is section {i} with some content. " * 10
        large_content += "\n\n"
    
    result = convert_markdown_to_pdf(
        markdown_content=large_content,
        return_base64=True
    )
    
    assert result["success"] is True
    assert result["size_bytes"] > 1000  # Should be a substantial PDF


def test_markdown_with_special_characters():
    """Test conversion with special characters and Unicode."""
    markdown_content = """# Test with Special Characters

## Unicode Test
- Emoji: 🚀 💻 📊
- Accents: café, naïve, résumé
- Symbols: © ® ™ ± ≤ ≥

## Code Block
```python
def hello_world():
    print("Hello, 世界!")
```

## Table
| Name | Age | City |
|------|-----|------|
| José | 25  | São Paulo |
| Åse  | 30  | Oslo |
"""
    
    result = convert_markdown_to_pdf(
        markdown_content=markdown_content,
        return_base64=True
    )
    
    assert result["success"] is True
    assert result["size_bytes"] > 0


def test_concurrent_requests():
    """Test handling multiple concurrent conversion requests."""
    import threading
    import time
    
    results = []
    errors = []
    
    def convert_worker(worker_id):
        try:
            markdown_content = f"# Worker {worker_id}\n\nThis is content from worker {worker_id}."
            result = convert_markdown_to_pdf(
                markdown_content=markdown_content,
                output_filename=f"worker_{worker_id}",
                return_base64=True
            )
            results.append(result)
        except Exception as e:
            errors.append(str(e))
    
    # Start multiple threads
    threads = []
    for i in range(5):
        thread = threading.Thread(target=convert_worker, args=(i,))
        threads.append(thread)
        thread.start()
    
    # Wait for all threads to complete
    for thread in threads:
        thread.join()
    
    # Check results
    assert len(errors) == 0, f"Errors occurred: {errors}"
    assert len(results) == 5
    
    for result in results:
        assert result["success"] is True
        assert result["size_bytes"] > 0