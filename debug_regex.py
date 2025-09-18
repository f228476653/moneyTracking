#!/usr/bin/env python3
"""
Debug the regex pattern used in the Wealthsimple parser
"""

import re

def test_regex():
    """Test the regex pattern with the actual lines from the PDF"""
    
    # These are the actual lines from the debug output
    test_lines = [
        "Enbridge Inc ENB 162.2873 162.2873 $61.75 CAD $10,021.24 $9,500.57",
        "iShare Trust - Core U.S. Aggbd Et AGG 58.8353 58.8353 $99.20 USD $7,962.68 $8,090.91",
        "Vanguard Total Bond Market ETF BND 91.3274 91.3274 $73.63 USD $9,174.14 $9,320.93"
    ]
    
    print("Testing regex pattern with actual PDF lines")
    print("=" * 60)
    
    # The regex pattern I'm using
    pattern = r'^\s*([\d,]+\.?\d*)\s+([\d,]+\.?\d*)\s+\$([\d,]+\.?\d*)\s+([A-Z]{3})\s+\$([\d,]+\.?\d*)\s+\$([\d,]+\.?\d*)'
    
    for i, line in enumerate(test_lines, 1):
        print(f"\nLine {i}: {line}")
        
        # Find all ticker symbols
        tickers = re.findall(r'\b([A-Z]{2,5})\b', line)
        print(f"  Found tickers: {tickers}")
        
        # For each ticker, test the pattern
        for ticker in tickers:
            if ticker in ['CAD', 'USD', 'ETF', 'INC', 'TRUST', 'TOTAL', 'US']:
                print(f"    Skipping {ticker} (common word)")
                continue
                
            ticker_pos = line.find(ticker)
            after_ticker = line[ticker_pos + len(ticker):]
            print(f"    After '{ticker}': '{after_ticker}'")
            
            # Test the pattern
            match = re.search(pattern, after_ticker)
            if match:
                print(f"    ✓ Pattern matched!")
                print(f"      Shares: {match.group(1)}")
                print(f"      Segregated: {match.group(2)}")
                print(f"      Price: {match.group(3)}")
                print(f"      Currency: {match.group(4)}")
                print(f"      Market Value: {match.group(5)}")
                print(f"      Book Cost: {match.group(6)}")
            else:
                print(f"    ✗ Pattern did not match")
                
                # Try a simpler pattern
                simple_pattern = r'([\d,]+\.?\d*)\s+([\d,]+\.?\d*)\s+\$([\d,]+\.?\d*)\s+([A-Z]{3})\s+\$([\d,]+\.?\d*)\s+\$([\d,]+\.?\d*)'
                simple_match = re.search(simple_pattern, after_ticker)
                if simple_match:
                    print(f"    ✓ Simple pattern matched!")
                else:
                    print(f"    ✗ Simple pattern also failed")

if __name__ == "__main__":
    test_regex()
