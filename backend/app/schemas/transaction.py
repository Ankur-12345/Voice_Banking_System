from pydantic import BaseModel, Field
from datetime import datetime
from typing import Optional


class TransactionBase(BaseModel):
    amount: float = Field(..., gt=0, description="Transaction amount")
    description: Optional[str] = Field(None, max_length=255, description="Transaction description")


class DepositRequest(TransactionBase):
    """Schema for deposit request"""
    pass


class WithdrawRequest(TransactionBase):
    """Schema for withdrawal request"""
    pass


class FundTransfer(TransactionBase):
    recipient_account: str = Field(..., min_length=13, max_length=13, description="Recipient account number")


class TransactionResponse(BaseModel):
    id: int
    transaction_type: str
    amount: float
    recipient_account: Optional[str]
    description: str
    timestamp: datetime
    
    class Config:
        from_attributes = True


class BalanceResponse(BaseModel):
    balance: float
    account_number: str
    username: str
    full_name: Optional[str] = None
