import pytest
from datetime import date
from credit_card_extraction.models import NormalizedLine
from credit_card_extraction.extractor import StatementParser

def test_parse_header_summary_fields():
    parser = StatementParser()
    lines = [
        NormalizedLine(text="Card Number: 1234-XXXX-XXXX-5678", page=1, y=10.0),
        NormalizedLine(text="Statement Date: 01/01/2026", page=1, y=20.0),
        NormalizedLine(text="Payment Due Date: 20/01/2026", page=1, y=30.0),
        NormalizedLine(text="Credit Limit(Baht): 100,000", page=1, y=40.0),
        NormalizedLine(text="Min. Payment Amount: 1,000.00", page=1, y=50.0),
        NormalizedLine(text="Past Due Amount: 0.00", page=1, y=60.0),
        NormalizedLine(text="Total Min. Payment Amount: 1,000.00", page=1, y=70.0),
        NormalizedLine(text="Outstanding Balance: 5,432.10", page=1, y=80.0),
        NormalizedLine(text="Transaction Date Transaction Details Amount", page=1, y=100.0), # Trigger state change
    ]
    
    result = parser.parse(lines)
    
    assert result.statement.account_last4 == "1234-XXXX-XXXX-5678"
    assert result.statement.statement_date == date(2026, 1, 1)
    assert result.statement.payment_due_date == date(2026, 1, 20)
    assert result.statement.credit_limit == 100000.0
    assert result.statement.min_payment == 1000.0
    assert result.statement.past_due_amount == 0.0
    assert result.statement.total_min_payment == 1000.0
    assert result.statement.outstanding_balance == 5432.1

def test_parse_header_summary_variations():
    """Test with different spacing/punctuation as per requirements"""
    parser = StatementParser()
    lines = [
        NormalizedLine(text="Payment Due Date 20/01/2026", page=1, y=30.0),
        NormalizedLine(text="Credit Limit(Baht) 100000", page=1, y=40.0),
        NormalizedLine(text="Outstanding Balance:5432.10", page=1, y=80.0),
        NormalizedLine(text="Transaction Date", page=1, y=100.0),
    ]
    
    result = parser.parse(lines)
    
    assert result.statement.payment_due_date == date(2026, 1, 20)
    assert result.statement.credit_limit == 100000.0
    assert result.statement.outstanding_balance == 5432.1
