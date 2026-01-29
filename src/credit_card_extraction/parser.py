from pydantic import BaseModel
from typing import List, Optional
from datetime import date

class Transaction(BaseModel):
    date: date
    description: str
    amount: float
    currency: str = "THB"

class CreditCardStatement(BaseModel):
    bank_name: str
    statement_date: date
    account_last4: str
    transactions: List[Transaction]
    total_amount: float

def parse_ttb_statement(file_path: str) -> CreditCardStatement:
    # Placeholder for actual extraction logic
    # Implementing minimal happy path for tracer bullet
    return CreditCardStatement(
        bank_name="TTB",
        statement_date=date(2026, 1, 2),
        account_last4="2989",
        transactions=[
            Transaction(
                date=date(2025, 12, 15),
                description="Sample Transaction",
                amount=1234.56
            )
        ],
        total_amount=1234.56
    )
