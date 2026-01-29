import re
from datetime import datetime
from typing import List, Tuple, Dict, Optional
import fitz  # PyMuPDF
from .models import RawLine, NormalizedLine, ExtractionResult, StatementHeader, ParserState, Transaction

class StatementParser:
    # TTB specific patterns
    DATE_PATTERN = re.compile(r"(\d{2}/\d{2}/\d{4})")
    AMOUNT_PATTERN = re.compile(r"(-?[\d,]+\.\d{2})")
    FX_PATTERN = re.compile(r"^([A-Z]{3})\s+([\d,]+\.\d{2})$")

    def __init__(self):
        self.state = ParserState.START
        self.result = ExtractionResult(
            header=StatementHeader(account_number="UNKNOWN"),
            transactions=[],
            validation=[]
        )
        self.current_transaction: Optional[Transaction] = None
        self.pending_fx: Optional[Tuple[str, float]] = None

    def parse(self, lines: List[NormalizedLine]) -> ExtractionResult:
        """
        Main parsing loop using a state machine.
        """
        for line in lines:
            self._process_line(line)
        
        # Flush last transaction
        self._flush_current()
            
        return self.result

    def _process_line(self, line: NormalizedLine):
        """
        TTB-specific parsing logic.
        """
        text = line.text.strip()
        
        # Global state transitions
        lower_text = text.lower()
        if "transaction date" in lower_text or "วันที่ใช้บัตร" in text or "transaction details" in lower_text:
            self.state = ParserState.TRANSACTIONS
            return
        elif "reward" in lower_text or "point" in lower_text:
            self._flush_current()
            self.state = ParserState.REWARDS
            return
        elif "sub total balance" in lower_text or "grand total" in lower_text or "total amount due" in lower_text:
            self._flush_current()
            self.state = ParserState.FOOTER
            return

        if self.state == ParserState.START:
            self.state = ParserState.HEADER

        if self.state == ParserState.HEADER:
            self._parse_header_line(text)

        if self.state == ParserState.TRANSACTIONS:
            self._parse_transaction_line(text)

    def _parse_header_line(self, text: str):
        # Extract Card Number: XXXX-XXXX-XXXX-2989
        card_match = re.search(r"(\d{4}-[\dXx-]{7,}-\d{4})", text)
        if card_match:
            self.result.header.account_number = card_match.group(1)
        
        # Extract Statement Date (usually near the top)
        # TTB often has "Date: 02 Jan 2026" or similar
        # For now, look for any date if account is already found
        if self.result.header.statement_date is None:
            # Look for 02Jan2026 or 02/01/2026
            date_match = self.DATE_PATTERN.search(text)
            if date_match:
                self.result.header.statement_date = datetime.strptime(date_match.group(1), "%d/%m/%Y").date()

    def _flush_current(self):
        if self.current_transaction:
            self.result.transactions.append(self.current_transaction)
            self.current_transaction = None

    def _parse_transaction_line(self, text: str):
        # 1. Check for FX line (prefix to transaction) 
        # e.g. "JPY 2,580.00"
        fx_match = self.FX_PATTERN.match(text)
        if fx_match:
            curr, amt_str = fx_match.groups()
            self.pending_fx = (curr, float(amt_str.replace(",", "")))
            return

        # 2. Check for main transaction line
        # e.g. "08/12/2025 11/12/2025 KINSHO STORE MATSUBARA JP 393.71"
        dates = self.DATE_PATTERN.findall(text)
        if len(dates) >= 1:
            # We found a potential new transaction
            self._flush_current()
            
            # Extract dates
            trans_date_str = dates[0]
            post_date_str = dates[1] if len(dates) > 1 else trans_date_str
            
            # Extract amount (usually the last number)
            amounts = self.AMOUNT_PATTERN.findall(text)
            amount = 0.0
            if amounts:
                amount = float(amounts[-1].replace(",", ""))
                
            # Better description extraction:
            # TTB layout: TransDate PostDate Description Amount
            # We can strip dates from start
            desc_part = text
            for d in dates:
                desc_part = desc_part.replace(d, "", 1).strip()
            # Strip amount from end
            if amounts:
                desc_part = desc_part.rsplit(amounts[-1], 1)[0].strip()
            
            try:
                self.current_transaction = Transaction(
                    transaction_date=datetime.strptime(trans_date_str, "%d/%m/%Y").date(),
                    post_date=datetime.strptime(post_date_str, "%d/%m/%Y").date(),
                    description=desc_part,
                    amount=amount
                )
                
                if self.pending_fx:
                    self.current_transaction.foreign_currency = self.pending_fx[0]
                    self.current_transaction.foreign_amount = self.pending_fx[1]
                    self.pending_fx = None
            except ValueError:
                # Handle potential date parsing issues
                pass
        
        elif self.current_transaction:
            # Likely a description continuation
            if not text.lower().startswith("page"):
                # Clean up repeated info if any (some statements repeat column headers on overflow)
                if "transaction date" not in text.lower():
                    self.current_transaction.description += " " + text

def extract_text_with_coords(file_path: str) -> List[RawLine]:
    """
    Extracts text blocks from a PDF file along with their bounding box coordinates.
    """
    doc = fitz.open(file_path)
    raw_lines = []
    
    for page_num, page in enumerate(doc):
        # Using "blocks" to get text grouped by blocks with their rectangles
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
            if abs(line.bbox[1] - prev_line.bbox[1]) <= y_tolerance:
                current_row.append(line)
            else:
                rows.append(current_row)
                current_row = [line]
        rows.append(current_row)
        
        # Process each row: sort by x and join text
        for row in rows:
            sorted_row = sorted(row, key=lambda l: l.bbox[0])
            text = " ".join(item.text for item in sorted_row)
            y_coord = min(item.bbox[1] for item in sorted_row)
            
            normalized_lines.append(NormalizedLine(
                text=text,
                page=page_num,
                y=y_coord
            ))
            
    return normalized_lines
