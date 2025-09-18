#!/usr/bin/env python3
"""
Analyze PDF structure to understand Wealthsimple statement format
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import pdfplumber
from io import BytesIO

def analyze_pdf():
    """Analyze the PDF structure"""
    
    pdf_file = "HQ4BDDB45CAD_person-007zdvlkVkxz_2025-06_v_0.pdf"
    
    if not os.path.exists(pdf_file):
        print(f"PDF file not found: {pdf_file}")
        return
    
    print(f"Analyzing PDF: {pdf_file}")
    print("=" * 60)
    
    try:
        with open(pdf_file, 'rb') as f:
            file_content = f.read()
        
        with pdfplumber.open(BytesIO(file_content)) as pdf:
            print(f"Total pages: {len(pdf.pages)}")
            
            for page_num, page in enumerate(pdf.pages, 1):
                print(f"\n{'='*20} PAGE {page_num} {'='*20}")
                
                # Extract text
                text = page.extract_text()
                if text:
                    print(f"Text length: {len(text)} characters")
                    print("First 500 characters:")
                    print(text[:500])
                    print("\nLast 500 characters:")
                    print(text[-500:])
                    
                    # Look for specific keywords
                    keywords = ['portfolio', 'equities', 'symbol', 'shares', 'price', 'value', 'weight']
                    found_keywords = []
                    for keyword in keywords:
                        if keyword.lower() in text.lower():
                            found_keywords.append(keyword)
                    
                    if found_keywords:
                        print(f"\nFound keywords: {found_keywords}")
                        
                        # Show context around keywords
                        for keyword in found_keywords:
                            print(f"\nContext around '{keyword}':")
                            lines = text.split('\n')
                            for i, line in enumerate(lines):
                                if keyword.lower() in line.lower():
                                    start = max(0, i-2)
                                    end = min(len(lines), i+3)
                                    for j in range(start, end):
                                        marker = ">>> " if j == i else "    "
                                        print(f"{marker}{lines[j]}")
                
                # Extract tables
                tables = page.extract_tables()
                if tables:
                    print(f"\nFound {len(tables)} tables")
                    for table_num, table in enumerate(tables):
                        print(f"\nTable {table_num + 1}:")
                        print(f"Rows: {len(table)}")
                        if table:
                            print(f"Columns: {len(table[0]) if table[0] else 0}")
                            
                            # Show first few rows
                            for i, row in enumerate(table[:5]):
                                print(f"Row {i}: {row}")
                            
                            if len(table) > 5:
                                print(f"... and {len(table) - 5} more rows")
                
                # Look for specific sections
                if 'portfolio' in text.lower() or 'equities' in text.lower():
                    print("\n*** PORTFOLIO SECTION FOUND ***")
                    # Extract lines around portfolio section
                    lines = text.split('\n')
                    portfolio_lines = []
                    for i, line in enumerate(lines):
                        if any(keyword in line.lower() for keyword in ['portfolio', 'equities']):
                            start = max(0, i-5)
                            end = min(len(lines), i+20)
                            portfolio_lines.extend(lines[start:end])
                    
                    if portfolio_lines:
                        print("Portfolio section content:")
                        for line in portfolio_lines:
                            print(f"  {line}")
                
                print("\n" + "="*60)
                
    except Exception as e:
        print(f"Error analyzing PDF: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    analyze_pdf()
