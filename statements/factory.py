"""
Factory class for creating appropriate statement parsers
"""

from typing import List, Dict, Any, Tuple

from .base import BaseStatementParser
from .amex_parser import AmexCreditCardParser
from .td_parser import TDChequeAccountParser
from .td_credit_parser import TDCreditCardParser
from .csv_parser import CSVStatementParser
from .excel_parser import ExcelStatementParser
from .text_parser import TextStatementParser
from .wealthsimple_parser import WealthsimpleRRSPParser
from .rbc_business_parser import RBCBusinessParser
from .eq_joint_parser import EQJointParser
from .bmo_parser import BMOBankParser


class StatementParserFactory:
    """Factory class for creating appropriate parsers"""
    
    def __init__(self):
        self.parsers = [
            WealthsimpleRRSPParser(),  # Add Wealthsimple parser first for PDF priority
            AmexCreditCardParser(),    # Add Amex parser second for priority
            TDChequeAccountParser(),   # Add TD parser third for priority
            TDCreditCardParser(),      # Add TD credit card parser fourth for priority
            RBCBusinessParser(),       # Add RBC Business parser for specific CSV format
            EQJointParser(),           # Add EQ Joint parser for specific CSV format
            BMOBankParser(),           # Add BMO Bank parser for specific CSV format
            CSVStatementParser(),
            ExcelStatementParser(),
            TextStatementParser(),
        ]
    
    def get_parser(self, file_content: bytes, filename: str) -> BaseStatementParser:
        """Get the appropriate parser for the given file"""
        for parser in self.parsers:
            if parser.can_parse(file_content, filename):
                return parser
        
        raise ValueError(f"No parser found for file: {filename}")
    
    def parse_statement(self, file_content: bytes, filename: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """Parse a statement file using the appropriate parser"""
        parser = self.get_parser(file_content, filename)
        return parser.parse(file_content, filename)
