import re
from datetime import datetime
from typing import List, Tuple, Dict, Optional
import fitz  # PyMuPDF
from .models import (
    RawLine, 
    NormalizedLine, 
    ExtractionResult, 
    StatementHeader, 
    ParserState, 
    Transaction, 
    ValidationResult,
    RewardBalance
)

class StatementParser:
    # TTB specific patterns
    DATE_PATTERN = re.compile(r"(\d{2}/\d{2}/\d{4})")
    AMOUNT_PATTERN = re.compile(r"(-?[\d,]+\.\d{2})")
    FX_PATTERN = re.compile(r"^([A-Z]{3})\s+([\d,]+\.\d{2})$")
    TXN_TWO_DATES_PATTERN = re.compile(
        r"(?P<trans>\d{2}/\d{2}/\d{4})\s+"
        r"(?P<post>\d{2}/\d{2}/\d{4})\s+"
        r"(?P<desc>.+?)\s+"
        r"(?P<amount>-?[\d,]+\.\d{2})"
        r"(?=\s+\d{2}/\d{2}/\d{4}|\s*$)"
    )
    TXN_ONE_DATE_PATTERN = re.compile(
        r"(?P<trans>\d{2}/\d{2}/\d{4})\s+"
        r"(?P<desc>.+?)\s+"
        r"(?P<amount>-?[\d,]+\.\d{2})"
        r"(?=\s+\d{2}/\d{2}/\d{4}|\s*$)"
    )
    CONTROL_CHARS = re.compile(r"[\x00-\x1F\x7F-\x9F]")
    MULTISPACE_PATTERN = re.compile(r"\s+")
    
    # Complex Header Patterns
    # Line with Card + Statement Date + Due Date
    HEADER_DATES_ROW = re.compile(r"(\d{4}-[\dXx-]{7,}-\d{4}).*?(\d{2}/\d{2}/\d{4})\s+(\d{2}/\d{2}/\d{4})")
    # Direct Debit Line for Outstanding Balance: Account ... Balance
    DIRECT_DEBIT_ROW = re.compile(r"\d{3}-\d-\d{5}-\d\s+([\d,]+\.\d{2})")
    # Credit Info Row: Limit ... MinPay ... PastDue ... TotalMin
    # Heuristic: 4 numbers, last 3 having decimals
    CREDIT_INFO_ROW = re.compile(r"([0-9,]+)\s+([0-9,]+\.\d{2})\s+([0-9,]+\.\d{2})\s+([0-9,]+\.\d{2})")
    
    # Header summary patterns (Single key-value fallback)
    HEADER_SUMMARY_PATTERNS = {
        "payment_due_date": re.compile(r"Payment Due Date\s*[:\s]\s*(\d{2}/\d{2}/\d{4})", re.IGNORECASE),
        "credit_limit": re.compile(r"Credit Limit\(Baht\)\s*[:\s]\s*([\d,]+\.\d{2}|[\d,]+)", re.IGNORECASE),
        "min_payment": re.compile(r"Min\. Payment Amount\s*[:\s]\s*([\d,]+\.\d{2}|[\d,]+)", re.IGNORECASE),
        "past_due_amount": re.compile(r"Past Due Amount\s*[:\s]\s*([\d,]+\.\d{2}|[\d,]+)", re.IGNORECASE),
        "total_min_payment": re.compile(r"Total Min\. Payment Amount\s*[:\s]\s*([\d,]+\.\d{2}|[\d,]+)", re.IGNORECASE),
        "outstanding_balance": re.compile(r"Outstanding Balance\s*[:\s]\s*([\d,]+\.\d{2}|[\d,]+)", re.IGNORECASE),
        "previous_balance": re.compile(r"(?:Previous|Prev)\s*Balance\s*[:\s]?\s*([\d,]+\.\d{2}|[\d,]+)", re.IGNORECASE),
        "new_balance": re.compile(r"(?:New Balance|Total Amount Due)\s*[:\s]?\s*([\d,]+\.\d{2}|[\d,]+)", re.IGNORECASE),
    }
    
    FOOTER_KEYWORDS = [
        "sub total balance", "grand total",
        "bank's copy", "pay-in-slip", "ส่วนสำาหรับธนาคาร",
        "service code", "cardholder name", "ชื่อผู้ถือบัตร",
        "scan to", "สแกนเพื่อ", "www.ttbbank.com",
        "amount in words", "จำนวนเงินเป็นตัวหนังสือ"
    ]

    def __init__(self):
        self.state = ParserState.START
        self.result = ExtractionResult(
            statement=StatementHeader(account_last4="UNKNOWN"),
            transactions=[],
            validation=ValidationResult()
        )
        self.current_transaction: Optional[Transaction] = None
        # self.pending_fx removed as FX follows transaction

    def parse(self, lines: List[NormalizedLine]) -> ExtractionResult:
        """
        Main parsing loop using a state machine.
        """
        for line in lines:
            self._process_line(line)
        
        # Flush last transaction
        self._flush_current()
        
        # Final cleanup / fallback logic
        if self.result.statement.outstanding_balance == 0.0 and self.result.statement.new_balance > 0:
            self.result.statement.outstanding_balance = self.result.statement.new_balance
        if self.result.statement.new_balance == 0.0 and self.result.statement.outstanding_balance > 0:
            self.result.statement.new_balance = self.result.statement.outstanding_balance
            
        return self.result

    def _sanitize_text(self, text: str) -> str:
        cleaned = self.CONTROL_CHARS.sub(" ", text)
        cleaned = cleaned.replace("\u00a0", " ")
        cleaned = self.MULTISPACE_PATTERN.sub(" ", cleaned)
        return cleaned.strip()

    def _find_footer_index(self, lower_text: str) -> Optional[int]:
        hits = [lower_text.find(k) for k in self.FOOTER_KEYWORDS if k in lower_text]
        return min(hits) if hits else None

    def _looks_like_noise(self, text: str) -> bool:
        if "B^^^B" in text:
            return True
        if len(text) < 12:
            return False
        alnum_count = sum(1 for ch in text if ch.isalnum())
        return (alnum_count / max(len(text), 1)) < 0.3

    def _clean_description(self, text: str) -> str:
        cleaned = self._sanitize_text(text)
        footer_index = self._find_footer_index(cleaned.lower())
        if footer_index is not None:
            cleaned = cleaned[:footer_index].strip()
        return cleaned

    def _process_line(self, line: NormalizedLine):
        """
        TTB-specific parsing logic.
        """
        text = self._sanitize_text(line.text)
        if not text:
            return
        
        # Global state transitions
        lower_text = text.lower()
        if "transaction date" in lower_text or "วันที่ใช้บัตร" in text or "transaction details" in lower_text:
            self.state = ParserState.TRANSACTIONS
            return
        elif "reward" in lower_text or "point" in lower_text:
            self._flush_current()
            self.state = ParserState.REWARDS
            return
            
        # Footer detection logic (with transaction-safe trimming)
        footer_pending = False
        footer_index = self._find_footer_index(lower_text)
        if footer_index is not None:
            if self.state == ParserState.TRANSACTIONS:
                footer_pending = True
                text = text[:footer_index].strip()
                if not text:
                    self._flush_current()
                    self.state = ParserState.FOOTER
                    return
                lower_text = text.lower()
            else:
                self._flush_current()
                self.state = ParserState.FOOTER
                return
        elif "total amount due" in lower_text:
            # Only treat as footer if we've already started transactions/rewards
            # otherwise it might be the 'New Balance' line in the header
            if self.state in (ParserState.TRANSACTIONS, ParserState.REWARDS):
                self._flush_current()
                self.state = ParserState.FOOTER
                return
        elif "แบบฟอร์ม" in text: # Check raw text for Thai forms
            self._flush_current()
            self.state = ParserState.FOOTER
            return

        if self.state == ParserState.START:
            self.state = ParserState.HEADER

        if self.state == ParserState.HEADER:
            self._parse_header_line(text)

        if self.state == ParserState.TRANSACTIONS:
            # Extra safeguard against noise lines if we are already in transactions
            # e.g. "B^^^B" or lines with widely different structure
            if self._looks_like_noise(text):
                if footer_pending:
                    self._flush_current()
                    self.state = ParserState.FOOTER
                return
            
            # Check for PREVIOUS BALANCE (which acts like a header line inside txn section)
            if "previous balance" in lower_text:
                 match = self.HEADER_SUMMARY_PATTERNS["previous_balance"].search(text)
                 if match:
                     try:
                        self.result.statement.previous_balance = float(match.group(1).replace(",", ""))
                     except ValueError:
                        pass
                 return
            
            self._parse_transaction_line(text)
            if footer_pending:
                self._flush_current()
                self.state = ParserState.FOOTER

    def _parse_header_line(self, text: str):
        # 1. Try Complex Multi-Value Lines first
        
        # Date Row: Card + Statement + Due
        dates_row_match = self.HEADER_DATES_ROW.search(text)
        if dates_row_match:
            self.result.statement.account_last4 = dates_row_match.group(1)
            try:
                self.result.statement.statement_date = datetime.strptime(dates_row_match.group(2), "%d/%m/%Y").date()
                self.result.statement.payment_due_date = datetime.strptime(dates_row_match.group(3), "%d/%m/%Y").date()
            except ValueError:
                pass
            return # Consumed this line

        # Direct Debit Row for Outstanding Balance
        dd_match = self.DIRECT_DEBIT_ROW.search(text)
        if dd_match:
            try:
                self.result.statement.outstanding_balance = float(dd_match.group(1).replace(",", ""))
            except ValueError:
                pass
            return
            
        # Credit Info Row
        credit_match = self.CREDIT_INFO_ROW.search(text)
        if credit_match:
            try:
                self.result.statement.credit_limit = float(credit_match.group(1).replace(",", ""))
                self.result.statement.min_payment = float(credit_match.group(2).replace(",", ""))
                self.result.statement.past_due_amount = float(credit_match.group(3).replace(",", ""))
                # group(4) is total min payment
                self.result.statement.total_min_payment = float(credit_match.group(4).replace(",", ""))
            except ValueError:
                pass
            return

        # 2. Standard single field extraction
        # Extract Card Number: XXXX-XXXX-XXXX-1234
        card_match = re.search(r"(\d{4}-[\dXx-]{7,}-\d{4})", text)
        if card_match and "THE PRIMA" in text: # Avoid re-matching if already caught
             pass
        elif card_match and self.result.statement.account_last4 == "UNKNOWN":
             self.result.statement.account_last4 = card_match.group(1)
        
        # Extract Statement Date (fallback)
        if self.result.statement.statement_date is None:
            date_match = self.DATE_PATTERN.search(text)
            if date_match and "Date" in text:
                 try:
                    self.result.statement.statement_date = datetime.strptime(date_match.group(1), "%d/%m/%Y").date()
                 except ValueError:
                    pass

        # Extract summary fields
        for field, pattern in self.HEADER_SUMMARY_PATTERNS.items():
            match = pattern.search(text)
            if match:
                val = match.group(1)
                if "date" in field:
                    try:
                        setattr(self.result.statement, field, datetime.strptime(val, "%d/%m/%Y").date())
                    except ValueError:
                        pass
                else:
                    try:
                        setattr(self.result.statement, field, float(val.replace(",", "")))
                    except ValueError:
                        pass

    def _flush_current(self):
        if self.current_transaction:
            self.result.transactions.append(self.current_transaction)
            self.current_transaction = None

    def _parse_transaction_line(self, text: str):
        # 1. Check for FX line (POST-Fix: FX follows transaction) 
        # e.g. "JPY 2,580.00"
        fx_match = self.FX_PATTERN.match(text)
        if fx_match:
            curr, amt_str = fx_match.groups()
            if self.current_transaction:
                self.current_transaction.foreign_currency = curr
                self.current_transaction.foreign_amount = float(amt_str.replace(",", ""))
            return

        matches = list(self.TXN_TWO_DATES_PATTERN.finditer(text))
        if not matches:
            matches = list(self.TXN_ONE_DATE_PATTERN.finditer(text))

        if matches:
            self._flush_current()
            transactions = []
            for match in matches:
                trans_date_str = match.group("trans")
                post_date_str = match.groupdict().get("post") or trans_date_str
                desc_part = self._clean_description(match.group("desc"))
                if not desc_part:
                    continue
                amount = float(match.group("amount").replace(",", ""))
                try:
                    transactions.append(Transaction(
                        date=datetime.strptime(trans_date_str, "%d/%m/%Y").date(),
                        post_date=datetime.strptime(post_date_str, "%d/%m/%Y").date(),
                        description=desc_part,
                        amount=amount
                    ))
                except ValueError:
                    continue
            for idx, transaction in enumerate(transactions):
                if idx < len(transactions) - 1:
                    self.result.transactions.append(transaction)
                else:
                    self.current_transaction = transaction
            return

        # 2. Check for main transaction line
        # e.g. "08/12/2025 11/12/2025 KINSHO STORE MATSUBARA JP 393.71"
        dates = self.DATE_PATTERN.findall(text)
        if len(dates) >= 1:
            dates = dates[:2]
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
            desc_part = self._clean_description(desc_part)
            
            try:
                self.current_transaction = Transaction(
                    date=datetime.strptime(trans_date_str, "%d/%m/%Y").date(),
                    post_date=datetime.strptime(post_date_str, "%d/%m/%Y").date(),
                    description=desc_part,
                    amount=amount
                )
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
