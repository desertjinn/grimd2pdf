#!/usr/bin/env python3
"""Simple test script to convert the sample markdown file using the MCP server directly."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from grimd2pdf.server import convert_markdown_file_to_pdf

def main():
    # Convert the sample markdown file to PDF
    result = convert_markdown_file_to_pdf(
        markdown_file_path="sample-document.md",
        output_filename="sample-document-converted",
        return_base64=False
    )
    
    if result["success"]:
        print(f"✅ Conversion successful!")
        print(f"📄 Output file: {result['output_path']}")
        print(f"📏 File size: {result['size_bytes']} bytes")
        print(f"💬 Message: {result['message']}")
    else:
        print(f"❌ Conversion failed!")
        print(f"💬 Error: {result['error']}")
        print(f"💬 Message: {result['message']}")

if __name__ == "__main__":
    main()