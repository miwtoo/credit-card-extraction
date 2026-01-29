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
    provider: str = "ttb"
    account_last4: str = Field(..., description="Anonymized or last 4 digits of the card")
    statement_date: Optional[date] = None
    period_start: Optional[date] = None
    period_end: Optional[date] = None
    previous_balance: float = 0.0
    new_balance: float = 0.0

class Transaction(BaseModel):
    date: date
    post_date: Optional[date] = None
    description: str
    amount: float
    currency: str = "THB"
    foreign_amount: Optional[float] = None
    foreign_currency: Optional[str] = None
    conversion_rate: Optional[float] = None
    notes: Optional[str] = None

class RewardBalance(BaseModel):
    points_previous_balance: int = 0
    points_earned: int = 0
    points_redeemed: int = 0
    points_balance: int = 0

class ValidationResult(BaseModel):
    errors: List[str] = []
    warnings: List[str] = []

class ExtractionResult(BaseModel):
    statement: StatementHeader
    transactions: List[Transaction] = []
    rewards: Optional[RewardBalance] = None
    validation: ValidationResult = Field(default_factory=ValidationResult)

class ParserStateOutput(BaseModel):
    """Container for intermediate parser states if needed"""
    pass
