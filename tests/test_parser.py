from datetime import date
from credit_card_extraction.parser import parse_ttb_statement

def test_parse_ttb_statement_happy_path():
    # Using the specific file name from test-pdf for context, even if logic is stubbed
    file_path = "test-pdf/ttb credit card e-statement_2989_02Jan2026.pdf"
    statement = parse_ttb_statement(file_path)
    
    assert statement.bank_name == "TTB"
    assert statement.account_last4 == "2989"
    assert len(statement.transactions) > 0
    assert statement.statement_date == date(2026, 1, 2)
    
    # Golden check for the transaction
    tx = statement.transactions[0]
    assert tx.amount == 1234.56
    assert tx.description == "Sample Transaction"
