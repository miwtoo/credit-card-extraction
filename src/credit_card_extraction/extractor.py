from typing import List, Tuple
from pydantic import BaseModel
import fitz  # PyMuPDF

class RawLine(BaseModel):
    text: str
    page: int
    bbox: Tuple[float, float, float, float]  # (x0, y0, x1, y1)

def extract_text_with_coords(file_path: str) -> List[RawLine]:
    """
    Extracts text blocks from a PDF file along with their bounding box coordinates.
    """
    doc = fitz.open(file_path)
    raw_lines = []
    
    for page_num, page in enumerate(doc):
        # Using "blocks" to get text grouped by blocks with their rectangles
        # Each block: (x0, y0, x1, y1, "text", block_no, block_type)
        blocks = page.get_text("blocks")
        for b in blocks:
            text = b[4].strip()
            if text:
                raw_lines.append(RawLine(
                    text=text,
                    page=page_num + 1,
                    bbox=(b[0], b[1], b[2], b[3])
                ))
    
    doc.close()
    return raw_lines
