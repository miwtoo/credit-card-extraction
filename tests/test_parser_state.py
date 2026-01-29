import pytest
from credit_card_extraction.extractor import StatementParser, NormalizedLine, ParserState

def test_statement_parser_state_transitions():
    parser = StatementParser()
    
    # Simulate a sequence of lines to trigger transitions
    lines = [
        NormalizedLine(text="ttb statement header", page=1, y=10.0),
        NormalizedLine(text="TRANSACTION DETAILS", page=1, y=50.0),
        NormalizedLine(text="SOME REWARD POINTS", page=2, y=10.0),
        NormalizedLine(text="TOTAL AMOUNT DUE", page=2, y=100.0),
    ]
    
    # Test individual transitions via _process_line
    parser._process_line(lines[0])
    assert parser.state == ParserState.HEADER
    
    parser._process_line(lines[1])
    assert parser.state == ParserState.TRANSACTIONS
    
    parser._process_line(lines[2])
    assert parser.state == ParserState.REWARDS
    
    parser._process_line(lines[3])
    assert parser.state == ParserState.FOOTER

def test_parser_run_without_crashing():
    parser = StatementParser()
    lines = [NormalizedLine(text="Hello world", page=1, y=0.0)]
    result = parser.parse(lines)
    assert result is not None
    assert result.header.account_number == "UNKNOWN"
