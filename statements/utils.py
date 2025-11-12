"""
Utility functions for the statements app
"""

from typing import Dict, List, Any
from decimal import Decimal
from .constants import (
    TRANSFER_KEYWORDS,
    INVESTMENT_KEYWORDS,
    PAYMENT_KEYWORDS,
    DIRECTION_IN,
    DIRECTION_OUT
)


def categorize_transaction(transaction) -> str:
    """
    Categorize a bank transaction based on its properties.

    Args:
        transaction: StatementDetail instance

    Returns:
        Category string: 'transfer', 'investment', 'spending', 'income', or 'other'
    """
    item_upper = transaction.item.upper()

    # Check if it's a transfer (only OUT direction)
    if transaction.direction == DIRECTION_OUT:
        for keyword in TRANSFER_KEYWORDS:
            if keyword in item_upper:
                return 'transfer'

    # Check if it's an investment transaction (only OUT direction)
    if transaction.direction == DIRECTION_OUT:
        for keyword in INVESTMENT_KEYWORDS:
            if keyword in item_upper:
                return 'investment'

    # Check if it's spending (outgoing but not investment or transfer)
    if transaction.direction == DIRECTION_OUT:
        is_investment = any(keyword in item_upper for keyword in INVESTMENT_KEYWORDS)
        is_transfer = any(keyword in item_upper for keyword in TRANSFER_KEYWORDS)
        if not is_investment and not is_transfer:
            return 'spending'

    # Check if it's income (IN direction, excluding GIC)
    if transaction.direction == DIRECTION_IN and 'GIC' not in item_upper:
        return 'income'

    return 'other'


def aggregate_transactions_by_category(transactions) -> Dict[str, Any]:
    """
    Aggregate transactions by category.

    Args:
        transactions: QuerySet of StatementDetail instances

    Returns:
        Dictionary with categorized amounts and transaction lists
    """
    result = {
        'income': Decimal('0.00'),
        'spending': Decimal('0.00'),
        'investments': Decimal('0.00'),
        'transfers': Decimal('0.00'),
        'income_transactions': [],
        'spending_transactions': [],
        'investment_transactions': [],
        'transfer_transactions': [],
    }

    for transaction in transactions:
        category = categorize_transaction(transaction)

        transaction_data = {
            'id': transaction.id,
            'item': transaction.item,
            'amount': float(transaction.amount),
            'date': transaction.transaction_date.strftime('%Y-%m-%d'),
            'direction': transaction.direction
        }

        if category == 'transfer':
            result['transfers'] += transaction.amount
            result['transfer_transactions'].append(transaction_data)
        elif category == 'investment':
            result['investments'] += transaction.amount
            result['investment_transactions'].append(transaction_data)
        elif category == 'spending':
            result['spending'] += transaction.amount
            result['spending_transactions'].append(transaction_data)
        elif category == 'income':
            result['income'] += transaction.amount
            result['income_transactions'].append(transaction_data)

    result['net_amount'] = result['income'] - result['spending'] - result['transfers']
    return result


def is_payment_transaction(item: str) -> bool:
    """
    Check if a transaction is a payment.

    Args:
        item: Transaction description

    Returns:
        True if it's a payment transaction
    """
    item_upper = item.upper()
    return any(keyword in item_upper for keyword in PAYMENT_KEYWORDS)
