#!/usr/bin/env python3
"""
Debug script to see exactly what the text looks like around portfolio equities
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pdfplumber
from io import BytesIO
import re

def debug_equities():
    """Debug the portfolio equities section"""
    
    pdf_file = "HQ4BDDB45CAD_person-007zdvlkVkxz_2025-06_v_0.pdf"
    
    if not os.path.exists(pdf_file):
        print(f"PDF file not found: {pdf_file}")
        return
    
    print(f"Debugging portfolio equities in: {pdf_file}")
    print("=" * 60)
    
    try:
        with open(pdf_file, 'rb') as f:
            file_content = f.read()
        
        with pdfplumber.open(BytesIO(file_content)) as pdf:
            for page_num, page in enumerate(pdf.pages, 1):
                text = page.extract_text()
                if text and ('portfolio equities' in text.lower() or 'equities' in text.lower()):
                    print(f"\n{'='*20} PAGE {page_num} - PORTFOLIO EQUITIES {'='*20}")
                    
                    lines = text.split('\n')
                    
                    # Find the portfolio equities section
                    for i, line in enumerate(lines):
                        if 'portfolio equities' in line.lower():
                            print(f"\nFound 'Portfolio Equities' at line {i}:")
                            print(f"  '{line}'")
                            
                            # Show context around this line
                            start = max(0, i-2)
                            end = min(len(lines), i+15)
                            
                            print(f"\nContext (lines {start}-{end}):")
                            for j in range(start, end):
                                marker = ">>> " if j == i else "    "
                                print(f"{marker}{j:2d}: '{lines[j]}'")
                            
                            # Look for specific equity lines
                            print(f"\nLooking for equity lines after line {i}:")
                            for j in range(i+1, min(len(lines), i+20)):
                                line_text = lines[j].strip()
                                
                                # Skip empty lines and headers
                                if not line_text or 'symbol' in line_text.lower() or 'quantity' in line_text.lower():
                                    continue
                                
                                # Look for lines that might contain equity data
                                if re.search(r'\b[A-Z]{2,5}\b', line_text) and re.search(r'\$[\d,]+\.?\d*', line_text):
                                    print(f"  Potential equity line {j}: '{line_text}'")
                                    
                                    # Try to extract ticker
                                    tickers = re.findall(r'\b([A-Z]{2,5})\b', line_text)
                                    print(f"    Found tickers: {tickers}")
                                    
                                    # Try to extract numbers
                                    numbers = re.findall(r'[\d,]+\.?\d*', line_text)
                                    print(f"    Found numbers: {numbers}")
                                    
                                    # Try to extract currency amounts
                                    currency_amounts = re.findall(r'\$[\d,]+\.?\d*', line_text)
                                    print(f"    Found currency amounts: {currency_amounts}")
                                    
                                    print()
                            
                            break
                    
                    break  # Only process the first page with portfolio equities
                    
    except Exception as e:
        print(f"Error debugging PDF: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    debug_equities()
