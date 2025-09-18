#!/usr/bin/env python3
"""
Test script to see what text is actually extracted from the PDF
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pdfplumber
from io import BytesIO

def test_text_extraction():
    """Test what text is actually extracted from the PDF"""
    
    pdf_file = "HQ4BDDB45CAD_person-007zdvlkVkxz_2025-06_v_0.pdf"
    
    if not os.path.exists(pdf_file):
        print(f"PDF file not found: {pdf_file}")
        return
    
    print(f"Testing text extraction from: {pdf_file}")
    print("=" * 60)
    
    try:
        with open(pdf_file, 'rb') as f:
            file_content = f.read()
        
        with pdfplumber.open(BytesIO(file_content)) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if text:
                    print(f"\nPage {page_num} text length: {len(text)}")
                    
                    # Check for portfolio equities keywords
                    text_lower = text.lower()
                    if 'portfolio equities' in text_lower:
                        print(f"✓ Found 'portfolio equities' in page {page_num}")
                    else:
                        print(f"✗ 'portfolio equities' NOT found in page {page_num}")
                    
                    if 'equities' in text_lower:
                        print(f"✓ Found 'equities' in page {page_num}")
                    else:
                        print(f"✗ 'equities' NOT found in page {page_num}")
                    
                    # Show a snippet around portfolio equities if found
                    if 'portfolio equities' in text_lower:
                        print(f"\nContext around 'portfolio equities':")
                        lines = text.split('\n')
                        for i, line in enumerate(lines):
                            if 'portfolio equities' in line.lower():
                                start = max(0, i-2)
                                end = min(len(lines), i+5)
                                for j in range(start, end):
                                    marker = ">>> " if j == i else "    "
                                    print(f"{marker}{j:2d}: {lines[j]}")
                                break
                    
                    # Only process the first page for now
                    break
                    
    except Exception as e:
        print(f"Error testing text extraction: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_text_extraction()
