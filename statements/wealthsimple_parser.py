"""
Wealthsimple RRSP PDF statement parser
"""

import pdfplumber
import re
from datetime import datetime
from typing import List, Dict, Any, Tuple
import logging
from decimal import Decimal
import decimal
from io import BytesIO

from .base import BaseStatementParser

logger = logging.getLogger(__name__)


class WealthsimpleRRSPParser(BaseStatementParser):
    """Parser specifically for Wealthsimple RRSP PDF statements"""
    
    def __init__(self):
        self.supported_formats = ['.pdf']
    
    def can_parse(self, file_content: bytes, filename: str) -> bool:
        """Check if this is a Wealthsimple RRSP PDF statement"""
        if not filename.lower().endswith('.pdf'):
            return False
        
        try:
            # Try to read the PDF to check if it's a Wealthsimple statement
            with pdfplumber.open(BytesIO(file_content)) as pdf:
                if len(pdf.pages) > 0:
                    first_page = pdf.pages[0]
                    text = first_page.extract_text()
                    if text:
                        # Look for Wealthsimple indicators
                        wealthsimple_indicators = [
                            'wealthsimple', 'rrsp', 'portfolio', 'equities'
                        ]
                        text_lower = text.lower()
                        return any(indicator in text_lower for indicator in wealthsimple_indicators)
        except Exception as e:
            logger.warning(f"Error checking PDF: {e}")
        
        return False
    
    def parse(self, file_content: bytes, filename: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Parse the Wealthsimple RRSP PDF and extract portfolio equities data"""
        try:
            with pdfplumber.open(BytesIO(file_content)) as pdf:
                # Extract statement metadata
                statement_meta = self._extract_statement_meta(filename, pdf)
                
                # Extract portfolio equities data
                portfolio_data = self._extract_portfolio_equities(pdf)
                
                # Convert portfolio data to transaction-like format for compatibility
                transactions = self._convert_portfolio_to_transactions(portfolio_data)
                
                return statement_meta, transactions
                
        except Exception as e:
            logger.error(f"Error parsing Wealthsimple PDF: {e}")
            raise ValueError(f"Could not parse Wealthsimple PDF: {e}")
    
    def _extract_statement_meta(self, filename: str, pdf) -> Dict[str, Any]:
        """Extract basic statement metadata"""
        meta = {
            'bank_name': 'Wealthsimple',
            'account_number': 'RRSP Account',
            'account_abbr': 'WS_RRSP',
            'statement_type': 'PDF',
            'statement_from_date': None,
            'statement_to_date': None,
        }
        
        # Try to extract dates from the PDF
        try:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    # Look for date patterns
                    date_patterns = [
                        r'(\d{1,2}/\d{1,2}/\d{4})',  # MM/DD/YYYY
                        r'(\d{4}-\d{1,2}-\d{1,2})',  # YYYY-MM-DD
                        r'(\d{1,2}-\d{1,2}-\d{4})',  # MM-DD-YYYY
                    ]
                    
                    for pattern in date_patterns:
                        dates = re.findall(pattern, text)
                        if dates:
                            # Try to parse the first date found
                            try:
                                parsed_date = datetime.strptime(dates[0], '%m/%d/%Y').date()
                                if not meta['statement_from_date']:
                                    meta['statement_from_date'] = parsed_date
                                elif not meta['statement_to_date']:
                                    meta['statement_to_date'] = parsed_date
                                break
                            except ValueError:
                                try:
                                    parsed_date = datetime.strptime(dates[0], '%Y-%m-%d').date()
                                    if not meta['statement_from_date']:
                                        meta['statement_from_date'] = parsed_date
                                    elif not meta['statement_to_date']:
                                        meta['statement_to_date'] = parsed_date
                                    break
                                except ValueError:
                                    try:
                                        parsed_date = datetime.strptime(dates[0], '%m-%d-%Y').date()
                                        if not meta['statement_from_date']:
                                            meta['statement_from_date'] = parsed_date
                                        elif not meta['statement_to_date']:
                                            meta['statement_to_date'] = parsed_date
                                        break
                                    except ValueError:
                                        continue
        except Exception as e:
            logger.warning(f"Could not extract dates from PDF: {e}")
        
        return meta
    
    def _extract_portfolio_equities(self, pdf) -> List[Dict[str, Any]]:
        """Extract portfolio equities table data from the PDF"""
        portfolio_data = []
        
        try:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    logger.info(f"Processing page with {len(text)} characters")
                    logger.info(f"Text contains 'portfolio equities': {'portfolio equities' in text.lower()}")
                    logger.info(f"Text contains 'equities': {'equities' in text.lower()}")
                    
                    # Look for portfolio equities section
                    if 'portfolio equities' in text.lower() or 'equities' in text.lower():
                        logger.info("Found portfolio equities section, processing...")
                        # Try to extract table data first
                        tables = page.extract_tables()
                        
                        for table in tables:
                            if self._is_portfolio_equities_table(table):
                                portfolio_data.extend(self._parse_equities_table(table))
                                break
                        
                        # If no tables found, try to parse text patterns
                        if not portfolio_data:
                            portfolio_data.extend(self._parse_equities_from_text(text))
                        
                        # Also try to parse the specific Wealthsimple format
                        wealthsimple_equities = self._parse_wealthsimple_specific_format(text)
                        if wealthsimple_equities:
                            portfolio_data.extend(wealthsimple_equities)
                        
                        break
                    else:
                        logger.info("No portfolio equities section found on this page")
        except Exception as e:
            logger.warning(f"Error extracting portfolio equities: {e}")
        
        return portfolio_data
    
    def _is_portfolio_equities_table(self, table) -> bool:
        """Check if a table contains portfolio equities data"""
        if not table or len(table) < 2:
            return False
        
        # Check header row for equity-related keywords
        header_row = table[0]
        if header_row:
            header_text = ' '.join(str(cell) for cell in header_row if cell).lower()
            equity_keywords = ['symbol', 'name', 'shares', 'price', 'value', 'weight', 'return']
            return any(keyword in header_text for keyword in equity_keywords)
        
        return False
    
    def _parse_equities_table(self, table) -> List[Dict[str, Any]]:
        """Parse portfolio equities table data"""
        equities = []
        
        try:
            # Skip header row
            for row in table[1:]:
                if row and len(row) >= 3:
                    equity = self._parse_equity_row(row)
                    if equity:
                        equities.append(equity)
        except Exception as e:
            logger.warning(f"Error parsing equities table row: {e}")
        
        return equities
    
    def _parse_equity_row(self, row) -> Dict[str, Any]:
        """Parse a single equity row from the table"""
        try:
            # Clean and extract data from row
            cleaned_row = [str(cell).strip() if cell else '' for cell in row]
            
            # Look for symbol, name, shares, price, value
            symbol = ''
            name = ''
            shares = Decimal('0')
            price = Decimal('0')
            value = Decimal('0')
            
            # Try to identify columns by content patterns
            for i, cell in enumerate(cleaned_row):
                cell_lower = cell.lower()
                
                # Symbol is usually short (1-5 chars) and uppercase
                if len(cell) <= 5 and cell.isupper() and not symbol:
                    symbol = cell
                
                # Name is usually longer text
                elif len(cell) > 5 and not name and not cell.replace('.', '').replace(',', '').isdigit():
                    name = cell
                
                # Shares - look for decimal numbers
                elif self._is_numeric(cell) and shares == Decimal('0'):
                    try:
                        shares = Decimal(cell.replace(',', ''))
                    except:
                        pass
                
                # Price - look for currency-like numbers
                elif self._is_numeric(cell) and price == Decimal('0'):
                    try:
                        price = Decimal(cell.replace('$', '').replace(',', ''))
                    except:
                        pass
                
                # Value - look for currency-like numbers
                elif self._is_numeric(cell) and value == Decimal('0'):
                    try:
                        value = Decimal(cell.replace('$', '').replace(',', ''))
                    except:
                        pass
            
            if symbol or name:
                return {
                    'symbol': symbol,
                    'name': name,
                    'shares': shares,
                    'price': price,
                    'value': value,
                    'type': 'EQUITY'
                }
        
        except Exception as e:
            logger.warning(f"Error parsing equity row: {e}")
        
        return None
    
    def _parse_equities_from_text(self, text: str) -> List[Dict[str, Any]]:
        """Parse equities data from text when table extraction fails"""
        equities = []
        
        try:
            # Look for patterns like "SYMBOL - Company Name - Shares - Price - Value"
            # This is a fallback method when table extraction doesn't work
            lines = text.split('\n')
            
            for line in lines:
                if any(keyword in line.lower() for keyword in ['symbol', 'shares', 'price', 'value']):
                    # Try to extract equity information from text line
                    equity = self._parse_equity_from_text_line(line)
                    if equity:
                        equities.append(equity)
        
        except Exception as e:
            logger.warning(f"Error parsing equities from text: {e}")
        
        return equities
    
    def _parse_equity_from_text_line(self, line: str) -> Dict[str, Any]:
        """Parse equity information from a text line"""
        try:
            # This is a simplified parser for text-based equity data
            # Look for common patterns in Wealthsimple statements
            
            # Pattern: SYMBOL - Company Name - Shares - Price - Value
            parts = line.split('-')
            if len(parts) >= 3:
                symbol = parts[0].strip()
                name = parts[1].strip() if len(parts) > 1 else ''
                
                # Try to extract numeric values
                numeric_values = re.findall(r'[\d,]+\.?\d*', line)
                
                shares = Decimal('0')
                price = Decimal('0')
                value = Decimal('0')
                
                if len(numeric_values) >= 3:
                    try:
                        shares = Decimal(numeric_values[0].replace(',', ''))
                        price = Decimal(numeric_values[1].replace(',', ''))
                        value = Decimal(numeric_values[2].replace(',', ''))
                    except:
                        pass
                
                if symbol and symbol.isupper() and len(symbol) <= 5:
                    return {
                        'symbol': symbol,
                        'name': name,
                        'shares': shares,
                        'price': price,
                        'value': value,
                        'type': 'EQUITY'
                    }
        
        except Exception as e:
            logger.warning(f"Error parsing equity from text line: {e}")
        
        return None
    
    def _is_numeric(self, text: str) -> bool:
        """Check if text represents a numeric value"""
        if not text:
            return False
        
        # Remove common non-numeric characters
        cleaned = text.replace('$', '').replace(',', '').replace('%', '').replace('(', '').replace(')', '')
        
        try:
            float(cleaned)
            return True
        except ValueError:
            return False
    
    def _parse_wealthsimple_format(self, text: str) -> List[Dict[str, Any]]:
        """Parse the specific Wealthsimple RRSP format found in the PDF"""
        equities = []
        
        try:
            lines = text.split('\n')
            
            # Look for the pattern: Company Name SYMBOL shares shares $price currency $market_value $book_cost
            for i, line in enumerate(lines):
                line = line.strip()
                
                # Skip empty lines and headers
                if not line or 'symbol' in line.lower() or 'quantity' in line.lower():
                    continue
                
                # Look for lines that contain company names and ticker symbols
                # Pattern: "Company Name SYMBOL number number $price currency $value $cost"
                
                # Try to find ticker symbols (usually 1-5 uppercase letters)
                ticker_match = re.search(r'\b([A-Z]{1,5})\b', line)
                if not ticker_match:
                    continue
                
                ticker = ticker_match.group(1)
                
                # Look for numeric values (shares, price, market value, book cost)
                numeric_values = re.findall(r'[\d,]+\.?\d*', line)
                currency_values = re.findall(r'\$[\d,]+\.?\d*', line)
                
                if len(numeric_values) >= 3 and len(currency_values) >= 2:
                    try:
                        # Extract values
                        shares = Decimal(numeric_values[0].replace(',', ''))
                        price_str = currency_values[0].replace('$', '').replace(',', '')
                        price = Decimal(price_str)
                        market_value_str = currency_values[1].replace('$', '').replace(',', '')
                        market_value = Decimal(market_value_str)
                        book_cost_str = currency_values[2].replace('$', '').replace(',', '') if len(currency_values) > 2 else '0'
                        book_cost = Decimal(book_cost_str)
                        
                        # Extract company name (everything before the ticker)
                        company_name = line[:line.find(ticker)].strip()
                        if company_name.endswith('-'):
                            company_name = company_name[:-1].strip()
                        
                        # Determine currency
                        currency = 'CAD'
                        if 'USD' in line:
                            currency = 'USD'
                        
                        equity = {
                            'symbol': ticker,
                            'name': company_name,
                            'shares': shares,
                            'price': price,
                            'value': market_value,
                            'book_cost': book_cost,
                            'currency': currency,
                            'type': 'EQUITY'
                        }
                        
                        equities.append(equity)
                        
                    except (ValueError, IndexError) as e:
                        logger.debug(f"Could not parse line: {line} - {e}")
                        continue
            
            # If we didn't find anything with the above method, try a more specific approach
            if not equities:
                equities = self._parse_wealthsimple_specific_format(text)
                
        except Exception as e:
            logger.warning(f"Error parsing Wealthsimple format: {e}")
        
        return equities
    
    def _parse_wealthsimple_specific_format(self, text: str) -> List[Dict[str, Any]]:
        """Parse the specific Wealthsimple format based on the actual PDF structure"""
        equities = []
        
        try:
            # Based on the debug output, the exact format is:
            # Line 38: 'Enbridge Inc ENB 162.2873 162.2873 $61.75 CAD $10,021.24 $9,500.57'
            # Line 40: 'iShare Trust - Core U.S. Aggbd Et AGG 58.8353 58.8353 $99.20 USD $7,962.68 $8,090.91'
            # Line 41: 'Vanguard Total Bond Market ETF BND 91.3274 91.3274 $73.63 USD $9,174.14 $9,320.93'
            
            lines = text.split('\n')
            logger.info(f"Parsing {len(lines)} lines for Wealthsimple format")
            
            # Find the start of the holdings section
            start_idx = -1
            for i, line in enumerate(lines):
                if 'portfolio equities' in line.lower():
                    start_idx = i
                    logger.info(f"Found 'Portfolio Equities' at line {i}")
                    break
            
            if start_idx == -1:
                logger.info("No portfolio equities section found")
                return equities
            
            # Look for the symbol header line (should be the next line or close by)
            symbol_line_idx = -1
            for i in range(start_idx + 1, min(len(lines), start_idx + 5)):
                if 'symbol' in lines[i].lower():
                    symbol_line_idx = i
                    logger.info(f"Found symbol header at line {i}")
                    break
            
            if symbol_line_idx == -1:
                logger.info("No symbol header found")
                return equities
            
            # Look for the actual holdings data
            for i in range(symbol_line_idx + 1, len(lines)):
                line = lines[i].strip()
                
                # Skip empty lines and section headers
                if not line or 'canadian equities' in line.lower() or 'us equities' in line.lower():
                    continue
                
                # Stop if we hit a total line
                if 'total' in line.lower() and '$' in line:
                    logger.info(f"Hit total line at {i}, stopping")
                    break
                
                # Look for lines that match the exact pattern we found
                # Pattern: "Company Name SYMBOL shares shares $price currency $market_value $book_cost"
                
                # First, check if this line has the right structure
                if not re.search(r'\$[\d,]+\.?\d*', line):
                    continue
                
                logger.info(f"Processing line {i}: {line}")
                
                # Look for ticker symbols that are followed by the right pattern
                # We need to find a ticker that is followed by two decimal numbers, then a currency amount
                
                # Find all potential ticker positions
                potential_tickers = []
                for match in re.finditer(r'\b([A-Z]{2,5})\b', line):
                    ticker = match.group(1)
                    ticker_pos = match.start()
                    
                    # Skip common words that aren't tickers
                    if ticker in ['CAD', 'USD', 'ETF', 'INC', 'TRUST', 'TOTAL', 'US']:
                        logger.debug(f"Skipping {ticker} (common word)")
                        continue
                    
                    logger.debug(f"Found potential ticker: {ticker} at position {ticker_pos}")
                    
                    # Check what comes after this ticker
                    after_ticker = line[ticker_pos + len(ticker):]
                    
                    # Look for the pattern: number number $price currency $value $cost
                    pattern = r'^\s*([\d,]+\.?\d*)\s+([\d,]+\.?\d*)\s+\$([\d,]+\.?\d*)\s+([A-Z]{3})\s+\$([\d,]+\.?\d*)\s+\$([\d,]+\.?\d*)'
                    match = re.search(pattern, after_ticker)
                    
                    if match:
                        logger.info(f"Pattern matched for ticker {ticker}")
                        potential_tickers.append({
                            'ticker': ticker,
                            'pos': ticker_pos,
                            'match': match
                        })
                    else:
                        logger.debug(f"Pattern did not match for ticker {ticker}")
                
                # Use the first valid ticker found
                if potential_tickers:
                    ticker_info = potential_tickers[0]
                    ticker = ticker_info['ticker']
                    ticker_pos = ticker_info['pos']
                    match = ticker_info['match']
                    
                    try:
                        # Parse the values
                        shares = Decimal(match.group(1).replace(',', ''))
                        segregated_shares = Decimal(match.group(2).replace(',', ''))
                        price_str = match.group(3).replace(',', '')
                        price = Decimal(price_str)
                        currency = match.group(4)
                        market_value_str = match.group(5).replace(',', '')
                        market_value = Decimal(market_value_str)
                        book_cost_str = match.group(6).replace(',', '')
                        book_cost = Decimal(book_cost_str)
                        
                        # Extract company name (everything before the ticker)
                        company_name = line[:ticker_pos].strip()
                        if company_name.endswith('-'):
                            company_name = company_name[:-1].strip()
                        
                        equity = {
                            'symbol': ticker,
                            'name': company_name,
                            'shares': shares,
                            'price': price,
                            'value': market_value,
                            'book_cost': book_cost,
                            'currency': currency,
                            'type': 'EQUITY'
                        }
                        
                        equities.append(equity)
                        logger.info(f"Found equity: {ticker} - {company_name} - {shares} shares at ${price} {currency}")
                        
                    except (ValueError, IndexError) as e:
                        logger.debug(f"Could not parse line: {line} - {e}")
                        continue
                else:
                    logger.debug(f"No valid tickers found in line: {line}")
                    
        except Exception as e:
            logger.warning(f"Error parsing Wealthsimple specific format: {e}")
        
        logger.info(f"Total equities found: {len(equities)}")
        return equities
    
    def _convert_portfolio_to_transactions(self, portfolio_data: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Convert portfolio equities data to transaction-like format for compatibility"""
        transactions = []
        
        for equity in portfolio_data:
            if equity.get('value', 0) > 0:
                transaction = {
                    'item': f"{equity.get('symbol', '')} - {equity.get('name', '')}",
                    'transaction_date': datetime.now().date(),  # Use current date as fallback
                    'amount': equity.get('value', 0),
                    'direction': 'IN',  # Portfolio holdings are assets
                    'symbol': equity.get('symbol', ''),
                    'shares': equity.get('shares', 0),
                    'price': equity.get('price', 0),
                    'type': 'EQUITY_HOLDING'
                }
                transactions.append(transaction)
        
        return transactions
