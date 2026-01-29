from datetime import date
import os
import pytest
from credit_card_extraction.parser import parse_ttb_statement

def test_parse_ttb_statement_happy_path():
    # Local-only PDF path for manual runs
    file_path = "test-pdf/ttb_statement_local.pdf"
    if not os.path.exists(file_path):
        pytest.skip(f"Test PDF not found at {file_path}")
    statement = parse_ttb_statement(file_path)
    
    assert statement.bank_name == "TTB"
    assert statement.account_last4 == "1234"
    assert len(statement.transactions) > 0
    assert statement.statement_date == date(2026, 1, 2)
    
    # Golden check for the transaction
    tx = statement.transactions[0]
    assert tx.amount == 1234.56
    assert tx.description == "Sample Transaction"
