#!/usr/bin/env python3
"""Comprehensive test script for markdown to PDF conversion with error handling."""

import sys
import os
sys.path.insert(0, os.path.dirname(__file__))

from grimd2pdf.server import convert_markdown_to_pdf, convert_markdown_file_to_pdf, sanitize_markdown_content, validate_markdown_structure

def test_basic_conversion():
    """Test basic conversion functionality."""
    print("🧪 Testing basic conversion...")
    
    result = convert_markdown_to_pdf(
        markdown_content="# Test\n\nBasic conversion test.",
        output_filename="basic_test",
        return_base64=True
    )
    
    if result["success"]:
        print("✅ Basic conversion successful!")
        print(f"📏 File size: {result['size_bytes']} bytes")
    else:
        print(f"❌ Basic conversion failed: {result['error']}")
    
    return result["success"]


def test_malformed_table_scenarios():
    """Test various malformed table scenarios that cause hierarchy errors."""
    print("\n🧪 Testing malformed table scenarios...")
    
    test_cases = [
        {
            "name": "Missing table separators",
            "content": """# Report
| Name | Age | City |
| Alice | 25 | New York |
| Bob | 30 | London |
""",
            "should_fix": True
        },
        {
            "name": "Inconsistent pipe separators",
            "content": """# Data
| Column 1 | Column 2 | Column 3
Alice | 25 | New York |
| Bob | 30 | London
""",
            "should_fix": True
        },
        {
            "name": "Table with missing header separator",
            "content": """# Statistics
| Metric | Value |
100 | 25.5
200 | 30.1
""",
            "should_fix": True
        },
        {
            "name": "Complex malformed table",
            "content": """# Complex Case
| Name | Details | Notes
|---|---|
| Test User | Some very long details that might cause issues with formatting | Important notes here
Missing pipe at start | More details | Notes |
| Final row | Final details | Final notes |
""",
            "should_fix": True
        }
    ]
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases):
        print(f"\n  📋 Test {i+1}: {test_case['name']}")
        
        # First test sanitization
        sanitized, warnings = sanitize_markdown_content(test_case['content'])
        print(f"    🔧 Applied {len(warnings)} fixes")
        for warning in warnings:
            print(f"      - {warning}")
        
        # Then test conversion
        result = convert_markdown_to_pdf(
            markdown_content=test_case['content'],
            output_filename=f"test_table_{i+1}",
            return_base64=True
        )
        
        if result["success"]:
            print(f"    ✅ Conversion successful")
            if "sanitization_warnings" in result:
                print(f"    🔧 Applied sanitization fixes: {len(result['sanitization_warnings'])}")
        else:
            print(f"    ❌ Conversion failed: {result['error']}")
            all_passed = False
    
    return all_passed


def test_heading_hierarchy_issues():
    """Test heading hierarchy problems that cause errors."""
    print("\n🧪 Testing heading hierarchy issues...")
    
    test_cases = [
        {
            "name": "Heading level jumps",
            "content": """# Main Title

#### Deeply nested without intermediate levels

Some content here.

# Another main title

##### Even deeper nesting issue

More content.
""",
            "should_fix": True
        },
        {
            "name": "Extremely deep headings",
            "content": """# Level 1
## Level 2
### Level 3
#### Level 4
##### Level 5
###### Level 6

This should be fine, but let's test edge cases.
""",
            "should_fix": False
        },
        {
            "name": "Mixed heading and table issues", 
            "content": """# Report

### Immediate jump to level 3

| Metric | Value
| Speed | Fast |
| Size | Large

##### Another big jump

More content here.
""",
            "should_fix": True
        }
    ]
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases):
        print(f"\n  📊 Test {i+1}: {test_case['name']}")
        
        # Test sanitization
        sanitized, warnings = sanitize_markdown_content(test_case['content'])
        print(f"    🔧 Applied {len(warnings)} fixes")
        
        # Test conversion
        result = convert_markdown_to_pdf(
            markdown_content=test_case['content'],
            output_filename=f"test_heading_{i+1}",
            return_base64=True
        )
        
        if result["success"]:
            print(f"    ✅ Conversion successful")
        else:
            print(f"    ❌ Conversion failed: {result['error']}")
            all_passed = False
    
    return all_passed


def test_llm_generated_content():
    """Test typical LLM-generated content that often causes issues."""
    print("\n🧪 Testing typical LLM-generated content scenarios...")
    
    # This mimics content that LLMs often generate with formatting issues
    llm_content = """# Analysis Report

## Executive Summary
This report contains analysis of our data.

#### Key Findings
Note the heading jump from level 2 to 4.

| Metric | Q1 | Q2 | Q3 | Q4
Sales | $100K | $120K | $110K | $130K |
| Growth | 5% | 20% | -8% | 18%
Customers | 1000 | 1200 | 1150 | 1300 |

##### Detailed Analysis

The data shows:
-No space after dash
* No space after asterisk
1.No space after number

```python
# Code block with issues

def example():
    return "test"


```

## Recommendations

Based on our findings:

### Implementation

| Task | Owner | Status
| Setup | Alice | Complete |
| Testing | Bob | In Progress
| Deploy | Charlie | Pending |

##### Next Steps

More content here.
"""
    
    print("  🤖 Testing LLM-generated content with multiple issues...")
    
    # Test sanitization first
    sanitized, warnings = sanitize_markdown_content(llm_content)
    print(f"    🔧 Applied {len(warnings)} sanitization fixes:")
    for warning in warnings:
        print(f"      - {warning}")
    
    # Test validation
    is_valid, errors = validate_markdown_structure(sanitized)
    print(f"    ✓ Validation result: {'Valid' if is_valid else 'Invalid'}")
    if errors:
        print(f"    ⚠️  Validation errors:")
        for error in errors:
            print(f"      - {error}")
    
    # Test conversion
    result = convert_markdown_to_pdf(
        markdown_content=llm_content,
        output_filename="llm_generated_test",
        return_base64=True
    )
    
    if result["success"]:
        print("    ✅ LLM content conversion successful!")
        print(f"    📏 File size: {result['size_bytes']} bytes")
        if "sanitization_warnings" in result:
            print(f"    🔧 Conversion applied {len(result['sanitization_warnings'])} fixes")
        return True
    else:
        print(f"    ❌ LLM content conversion failed: {result['error']}")
        if "suggested_fixes" in result:
            print("    💡 Suggested fixes:")
            for fix in result["suggested_fixes"]:
                print(f"      - {fix}")
        return False


def test_edge_cases():
    """Test edge cases and extreme scenarios."""
    print("\n🧪 Testing edge cases...")
    
    test_cases = [
        {
            "name": "Empty content",
            "content": "",
            "should_succeed": False
        },
        {
            "name": "Only whitespace",
            "content": "   \n  \n   ",
            "should_succeed": False
        },
        {
            "name": "Special characters",
            "content": "# Test\n\nContent with special chars: ñáéíóú ©®™ 🚀💻📊",
            "should_succeed": True
        },
        {
            "name": "Very long line",
            "content": "# Test\n\n" + "A" * 5000 + "\n\nMore content.",
            "should_succeed": True
        }
    ]
    
    all_passed = True
    
    for i, test_case in enumerate(test_cases):
        print(f"\n  🔍 Test {i+1}: {test_case['name']}")
        
        result = convert_markdown_to_pdf(
            markdown_content=test_case['content'],
            output_filename=f"edge_case_{i+1}",
            return_base64=True
        )
        
        success_expected = test_case['should_succeed']
        actual_success = result["success"]
        
        if actual_success == success_expected:
            print(f"    ✅ Expected result: {'Success' if success_expected else 'Failure'}")
        else:
            print(f"    ❌ Unexpected result. Expected: {'Success' if success_expected else 'Failure'}, Got: {'Success' if actual_success else 'Failure'}")
            print(f"    📝 Error: {result.get('error', 'N/A')}")
            all_passed = False
    
    return all_passed


def main():
    """Run all conversion tests."""
    print("🚀 Starting comprehensive markdown to PDF conversion tests...")
    
    test_results = []
    
    # Run all test suites
    test_results.append(("Basic conversion", test_basic_conversion()))
    test_results.append(("Malformed tables", test_malformed_table_scenarios()))
    test_results.append(("Heading hierarchy", test_heading_hierarchy_issues()))
    test_results.append(("LLM-generated content", test_llm_generated_content()))
    test_results.append(("Edge cases", test_edge_cases()))
    
    # Summary
    print(f"\n{'='*60}")
    print("📊 TEST SUMMARY")
    print(f"{'='*60}")
    
    total_tests = len(test_results)
    passed_tests = sum(1 for _, result in test_results if result)
    
    for test_name, result in test_results:
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"{test_name:<25} {status}")
    
    print(f"\n📈 Overall Result: {passed_tests}/{total_tests} test suites passed")
    
    if passed_tests == total_tests:
        print("🎉 All tests passed! The markdown sanitization system is working correctly.")
        return True
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return False


if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)