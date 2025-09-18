#!/usr/bin/env python3
"""
Test script for Wealthsimple RRSP PDF parser
"""

import sys
import os
import logging
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

# Set up logging
logging.basicConfig(level=logging.INFO, format='%(levelname)s: %(message)s')

from statements.wealthsimple_parser import WealthsimpleRRSPParser

def test_wealthsimple_parser():
    """Test the Wealthsimple parser with the PDF file"""
    
    pdf_file = "HQ4BDDB45CAD_person-007zdvlkVkxz_2025-06_v_0.pdf"
    
    if not os.path.exists(pdf_file):
        print(f"PDF file not found: {pdf_file}")
        return
    
    print(f"Testing Wealthsimple parser with: {pdf_file}")
    print("=" * 60)
    
    try:
        # Read the PDF file
        with open(pdf_file, 'rb') as f:
            file_content = f.read()
        
        # Create parser instance
        parser = WealthsimpleRRSPParser()
        
        # Check if parser can handle this file
        can_parse = parser.can_parse(file_content, pdf_file)
        print(f"Can parse: {can_parse}")
        
        if can_parse:
            # Parse the statement
            print("\nParsing statement...")
            statement_meta, transactions = parser.parse(file_content, pdf_file)
            
            print("\nStatement Metadata:")
            print("-" * 30)
            for key, value in statement_meta.items():
                print(f"{key}: {value}")
            
            print(f"\nPortfolio Equities Found: {len(transactions)}")
            print("-" * 30)
            
            for i, transaction in enumerate(transactions, 1):
                print(f"\nEquity {i}:")
                print(f"  Item: {transaction.get('item', 'N/A')}")
                print(f"  Amount: ${transaction.get('amount', 0):,.2f}")
                print(f"  Symbol: {transaction.get('symbol', 'N/A')}")
                print(f"  Shares: {transaction.get('shares', 0)}")
                print(f"  Price: ${transaction.get('price', 0):,.2f}")
                print(f"  Type: {transaction.get('type', 'N/A')}")
        
        else:
            print("Parser cannot handle this PDF file")
            
    except Exception as e:
        print(f"Error testing parser: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    test_wealthsimple_parser()
