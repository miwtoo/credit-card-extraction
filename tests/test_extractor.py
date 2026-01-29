import pytest
import os
from credit_card_extraction.extractor import extract_text_with_coords, normalize_lines
from credit_card_extraction.models import RawLine

def test_extract_text_with_coords_real_pdf():
    # Use the known TTB test PDF
    pdf_path = "test-pdf/ttb_statement_local.pdf"
    
    # Ensure file exists
    if not os.path.exists(pdf_path):
        pytest.skip(f"Test PDF not found at {pdf_path}")
        
    lines = extract_text_with_coords(pdf_path)
    
    assert len(lines) > 0
    # Check if we can find some expected text (like "ttb" or "Credit Card")
    found_ttb = any("ttb" in line.text.lower() for line in lines)
    assert found_ttb, "Should find 'ttb' in the extracted text"
    
    # Check structure of the first line
    first_line = lines[0]
    assert hasattr(first_line, "text")
    assert hasattr(first_line, "page")
    assert hasattr(first_line, "bbox")
    assert len(first_line.bbox) == 4

def test_normalize_lines_mock_data():
    # Mock data with lines that should be grouped into rows
    # Row 1: y=10, x=50 and x=150
    # Row 2: y=30, x=50 and x=150
    raw = [
        RawLine(text="Left 1", page=1, bbox=(50, 10, 100, 20)),
        RawLine(text="Right 1", page=1, bbox=(150, 10.5, 200, 20.5)), # 0.5 diff
        RawLine(text="Left 2", page=1, bbox=(50, 30, 100, 40)),
        RawLine(text="Right 2", page=1, bbox=(150, 31, 200, 41)), # 1.0 diff
    ]
    
    normalized = normalize_lines(raw, y_tolerance=2.0)
    
    assert len(normalized) == 2
    assert normalized[0].text == "Left 1 Right 1"
    assert normalized[1].text == "Left 2 Right 2"
    assert normalized[0].page == 1
    assert normalized[1].page == 1

def test_normalize_lines_with_real_pdf():
    pdf_path = "test-pdf/ttb_statement_local.pdf"
    if not os.path.exists(pdf_path):
        pytest.skip(f"Test PDF not found at {pdf_path}")
        
    raw_lines = extract_text_with_coords(pdf_path)
    normalized = normalize_lines(raw_lines)
    
    assert len(normalized) > 0
    # Verify we still find ttb
    found_ttb = any("ttb" in line.text.lower() for line in normalized)
    assert found_ttb
    
    # Check if we have fewer normalized lines than raw lines (due to grouping)
    assert len(normalized) <= len(raw_lines)
