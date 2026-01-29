import pytest
import os
from credit_card_extraction.extractor import extract_text_with_coords

def test_extract_text_with_coords_real_pdf():
    # Use the known TTB test PDF
    pdf_path = "test-pdf/ttb credit card e-statement_2989_02Jan2026.pdf"
    
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
