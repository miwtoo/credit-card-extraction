from typing import List, Optional, Tuple
from pydantic import BaseModel, Field
from datetime import date
from enum import Enum, auto

class ParserState(Enum):
    START = auto()
    HEADER = auto()
    TRANSACTIONS = auto()
    REWARDS = auto()
    FOOTER = auto()
    END = auto()

class RawLine(BaseModel):
    text: str
    page: int
    bbox: Tuple[float, float, float, float]  # (x0, y0, x1, y1)

class NormalizedLine(BaseModel):
    text: str
    page: int
    y: float

class StatementHeader(BaseModel):
    account_number: str = Field(..., description="Anonymized or last 4 digits of the card")
    statement_date: Optional[date] = None
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    bank_name: str = "TTB"  # Default for MVP

class Transaction(BaseModel):
    transaction_date: date
    post_date: Optional[date] = None
    description: str
    amount: float
    currency: str = "THB"
    foreign_amount: Optional[float] = None
    foreign_currency: Optional[str] = None
    conversion_rate: Optional[float] = None

class RewardBalance(BaseModel):
    previous_balance: int = 0
    earned: int = 0
    redeemed: int = 0
    current_balance: int = 0

class ValidationIssue(BaseModel):
    level: str  # "warning" or "error"
    message: str
    line_number: Optional[int] = None

class ExtractionResult(BaseModel):
    header: StatementHeader
    transactions: List[Transaction] = []
    rewards: Optional[RewardBalance] = None
    validation: List[ValidationIssue] = []

class ParserStateOutput(BaseModel):
    """Container for intermediate parser states if needed"""
    pass
