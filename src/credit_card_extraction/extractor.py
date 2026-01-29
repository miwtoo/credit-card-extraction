from typing import List, Tuple, Dict
import fitz  # PyMuPDF
from .models import RawLine, NormalizedLine, ExtractionResult, StatementHeader, ParserState

class StatementParser:
    def __init__(self):
        self.state = ParserState.START
        self.result = ExtractionResult(
            header=StatementHeader(account_number="UNKNOWN"),
            transactions=[],
            validation=[]
        )
        
    def parse(self, lines: List[NormalizedLine]) -> ExtractionResult:
        """
        Main parsing loop using a state machine.
        """
        for line in lines:
            self._process_line(line)
        return self.result

    def _process_line(self, line: NormalizedLine):
        """
        Simple state transitions for the skeleton.
        In Issue #6, these will be replaced with TTB-specific rules.
        """
        text = line.text.lower()
        
        if self.state == ParserState.START:
            self.state = ParserState.HEADER
            
        if "transaction" in text or "activity" in text:
            self.state = ParserState.TRANSACTIONS
        elif "reward" in text or "point" in text:
            self.state = ParserState.REWARDS
        elif "footer" in text or "total" in text:
            self.state = ParserState.FOOTER

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

def normalize_lines(raw_lines: List[RawLine], y_tolerance: float = 3.0) -> List[NormalizedLine]:
    """
    Groups raw lines by page and Y-coordinate (with tolerance) to reconstruct rows.
    Rows are sorted by X-coordinate within each grouped Y-coordinate.
    """
    if not raw_lines:
        return []

    # Sort primarily by page, then by y0, then by x0
    sorted_raw = sorted(raw_lines, key=lambda l: (l.page, l.bbox[1], l.bbox[0]))
    
    normalized_lines = []
    
    # Group by page
    pages: Dict[int, List[RawLine]] = {}
    for l in sorted_raw:
        pages.setdefault(l.page, []).append(l)
        
    for page_num in sorted(pages.keys()):
        page_lines = pages[page_num]
        if not page_lines:
            continue
            
        rows = []
        current_row: List[RawLine] = [page_lines[0]]
        
        for i in range(1, len(page_lines)):
            line = page_lines[i]
            prev_line = current_row[-1]
            
            # Check if this line is on the same row as the previous one (within tolerance)
            # We use y0 (top of the box) for alignment
            if abs(line.bbox[1] - prev_line.bbox[1]) <= y_tolerance:
                current_row.append(line)
            else:
                rows.append(current_row)
                current_row = [line]
        rows.append(current_row)
        
        # Process each row: sort by x and join text
        for row in rows:
            # Sort row by x0
            sorted_row = sorted(row, key=lambda l: l.bbox[0])
            text = " ".join(item.text for item in sorted_row)
            # Use the min y0 as the representative Y for the row
            y_coord = min(item.bbox[1] for item in sorted_row)
            
            normalized_lines.append(NormalizedLine(
                text=text,
                page=page_num,
                y=y_coord
            ))
            
    return normalized_lines
