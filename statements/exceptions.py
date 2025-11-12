"""
Custom exceptions for the statements app
"""


class StatementParsingError(Exception):
    """Base exception for statement parsing errors"""
    pass


class UnsupportedFileFormatError(StatementParsingError):
    """Raised when file format is not supported"""
    pass


class InvalidStatementDataError(StatementParsingError):
    """Raised when statement data is invalid or corrupted"""
    pass


class ParserNotFoundError(StatementParsingError):
    """Raised when no suitable parser is found for a file"""
    pass


class DateParsingError(StatementParsingError):
    """Raised when date parsing fails"""
    pass


class AmountParsingError(StatementParsingError):
    """Raised when amount parsing fails"""
    pass
