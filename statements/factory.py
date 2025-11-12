"""
Factory class for creating appropriate statement parsers
"""

from typing import List, Dict, Any, Tuple
import logging

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
from .exceptions import ParserNotFoundError, StatementParsingError

logger = logging.getLogger(__name__)


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
        """
        Get the appropriate parser for the given file.

        Args:
            file_content: Raw file content as bytes
            filename: Name of the file

        Returns:
            Parser instance that can handle the file

        Raises:
            ParserNotFoundError: If no suitable parser is found
        """
        logger.info(f"Attempting to find parser for file: {filename}")

        for parser in self.parsers:
            try:
                if parser.can_parse(file_content, filename):
                    logger.info(f"Selected parser: {parser.__class__.__name__}")
                    return parser
            except Exception as e:
                logger.warning(f"Parser {parser.__class__.__name__} failed to check file: {e}")
                continue

        logger.error(f"No parser found for file: {filename}")
        raise ParserNotFoundError(f"No parser found for file: {filename}")
    
    def parse_statement(self, file_content: bytes, filename: str) -> Tuple[Dict[str, Any], List[Dict[str, Any]]]:
        """
        Parse a statement file using the appropriate parser.

        Args:
            file_content: Raw file content as bytes
            filename: Name of the file

        Returns:
            Tuple of (statement_metadata, transactions_list)

        Raises:
            ParserNotFoundError: If no suitable parser is found
            StatementParsingError: If parsing fails
        """
        try:
            parser = self.get_parser(file_content, filename)
            logger.info(f"Parsing statement with {parser.__class__.__name__}")
            return parser.parse(file_content, filename)
        except ParserNotFoundError:
            raise
        except Exception as e:
            logger.error(f"Error parsing statement: {e}", exc_info=True)
            raise StatementParsingError(f"Failed to parse statement: {str(e)}") from e
