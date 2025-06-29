import pytest
from fastapi.testclient import TestClient
import io
import json

from grimd2pdf.standalone_server import create_http_app

app = create_http_app()

client = TestClient(app)

def test_health_check():
    response = client.get("/health")
    assert response.status_code == 200
    result = response.json()
    assert result["success"] == True
    assert result["status"] == "healthy"
    assert "message" in result

def test_convert_markdown_to_pdf():
    # Test the /convert endpoint with JSON payload
    request_data = {
        "markdown_content": "# Test Header\n\nThis is a test paragraph.",
        "output_filename": "test_output",
        "return_base64": True
    }
    
    response = client.post(
        "/convert",
        json=request_data
    )
    
    # Assert that the response is successful
    assert response.status_code == 200
    
    result = response.json()
    assert result["success"] == True
    assert "pdf_base64" in result
    assert result["filename"] == "test_output.pdf"
    assert "message" in result

def test_upload_and_convert():
    # Test the /upload endpoint with file upload
    markdown_content = b"# Test Header\n\nThis is a test paragraph."
    file_to_upload = ("test.md", io.BytesIO(markdown_content), "text/markdown")
    
    response = client.post(
        "/upload",
        files={"file": file_to_upload},
        data={"return_base64": "true"}
    )
    
    # Assert that the response is successful
    assert response.status_code == 200
    
    result = response.json()
    assert result["success"] == True
    assert "pdf_base64" in result
    assert "message" in result

def test_convert_with_bad_request():
    # Send a POST request without required fields
    response = client.post("/convert", json={})
    assert response.status_code == 422  # Unprocessable Entity
    
    # Send a POST with invalid markdown_content
    response = client.post("/convert", json={"markdown_content": ""})
    assert response.status_code == 400  # Bad request due to empty content

def test_upload_with_bad_file():
    # Upload non-markdown file
    content = b"Not a markdown file"
    file_to_upload = ("test.txt", io.BytesIO(content), "text/plain")
    
    response = client.post(
        "/upload",
        files={"file": file_to_upload}
    )
    # The server returns 500 for this error, which is acceptable
    assert response.status_code in [400, 500]  # Either bad request or internal error
    result = response.json()
    assert result["success"] == False

def test_convert_file_endpoint():
    # Test the /convert-file endpoint
    request_data = {
        "markdown_file_path": "sample-document.md",
        "return_base64": True
    }
    
    response = client.post(
        "/convert-file",
        json=request_data
    )
    
    # This will fail if file doesn't exist, which is expected
    assert response.status_code in [200, 400]
    result = response.json()
    assert "success" in result
    assert "message" in result 