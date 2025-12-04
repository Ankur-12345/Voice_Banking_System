from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from typing import List, Optional
from datetime import datetime
from ..database import get_db
from ..schemas.transaction import (
    FundTransfer, 
    TransactionResponse, 
    BalanceResponse,
    DepositRequest,
    WithdrawRequest
)
from ..services.banking_service import BankingService
from ..dependencies import get_current_user
from ..models.user import User
from pydantic import BaseModel


router = APIRouter(prefix="/api/banking", tags=["Banking Operations"])


class TransactionSearch(BaseModel):
    search_term: str


@router.get("/balance", response_model=BalanceResponse)
def check_balance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current account balance and account information"""
    banking_service = BankingService(db)
    try:
        return banking_service.get_balance(current_user.username)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/deposit")
def deposit_funds(
    deposit: DepositRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Deposit funds to your account"""
    banking_service = BankingService(db)
    try:
        result = banking_service.deposit_funds(
            current_user.username,
            deposit.amount,
            deposit.description or ""
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/withdraw")
def withdraw_funds(
    withdraw: WithdrawRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Withdraw funds from your account"""
    banking_service = BankingService(db)
    try:
        result = banking_service.withdraw_funds(
            current_user.username,
            withdraw.amount,
            withdraw.description or ""
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.post("/transfer", status_code=status.HTTP_200_OK)
def transfer_funds(
    transfer: FundTransfer,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Transfer funds to another account"""
    banking_service = BankingService(db)
    try:
        result = banking_service.transfer_funds(
            current_user.username,
            transfer.recipient_account,
            transfer.amount,
            transfer.description or ""
        )
        return result
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))


@router.get("/transactions", response_model=List[TransactionResponse])
def get_transactions(
    limit: int = Query(50, ge=1, le=100, description="Number of transactions to retrieve"),
    transaction_type: Optional[str] = Query(None, regex="^(credit|debit)$", description="Filter by transaction type"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get transaction history"""
    banking_service = BankingService(db)
    try:
        return banking_service.get_transaction_history(
            current_user.username, 
            limit,
            transaction_type
        )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/transactions/{transaction_id}", response_model=TransactionResponse)
def get_transaction_by_id(
    transaction_id: int,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get specific transaction details by ID"""
    banking_service = BankingService(db)
    try:
        transaction = banking_service.get_transaction_by_id(transaction_id, current_user.username)
        if not transaction:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail="Transaction not found"
            )
        return transaction
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/summary")
def get_transaction_summary(
    days: int = Query(30, ge=1, le=365, description="Number of days to summarize"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get transaction summary for specified period"""
    banking_service = BankingService(db)
    try:
        return banking_service.get_transaction_summary(current_user.username, days)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/recent-recipients")
def get_recent_recipients(
    limit: int = Query(5, ge=1, le=10, description="Number of recipients to retrieve"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of recent transfer recipients"""
    banking_service = BankingService(db)
    try:
        return banking_service.get_recent_recipients(current_user.username, limit)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.post("/transactions/search")
def search_transactions(
    search_data: TransactionSearch,
    limit: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search transactions by description or recipient account"""
    banking_service = BankingService(db)
    try:
        results = banking_service.search_transactions(
            current_user.username,
            search_data.search_term,
            limit
        )
        return {
            "search_term": search_data.search_term,
            "results_count": len(results),
            "transactions": results
        }
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/statement")
def get_account_statement(
    start_date: datetime = Query(..., description="Start date for statement"),
    end_date: datetime = Query(..., description="End date for statement"),
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Generate account statement for date range"""
    banking_service = BankingService(db)
    try:
        if end_date < start_date:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="End date must be after start date"
            )
        
        statement = banking_service.get_account_statement(
            current_user.username,
            start_date,
            end_date
        )
        return statement
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/daily-limit")
def check_daily_limit(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Check remaining daily transfer limit"""
    banking_service = BankingService(db)
    try:
        return banking_service.check_daily_limit_remaining(current_user.username)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))


@router.get("/account-info")
def get_account_info(
    current_user: User = Depends(get_current_user)
):
    """Get comprehensive account information"""
    return {
        "username": current_user.username,
        "full_name": current_user.full_name,
        "email": current_user.email,
        "account_number": current_user.account_number,
        "balance": current_user.balance,
        "account_created": current_user.created_at
    }

@router.get("/search-accounts/{query}")
def search_accounts(
    query: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Search for accounts by username or account number
    """
    banking_service = BankingService(db)
    
    try:
        # Search by username or account number
        users = db.query(User).filter(
            (User.username.ilike(f"%{query}%")) |
            (User.account_number.ilike(f"%{query}%"))
        ).filter(
            User.id != current_user.id  # Exclude current user
        ).limit(10).all()
        
        results = [
            {
                "username": user.username,
                "full_name": user.full_name,
                "account_number": user.account_number
            }
            for user in users
        ]
        
        return {
            "query": query,
            "results": results,
            "count": len(results)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/validate-account/{account_number}")
def validate_account(
    account_number: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Validate if an account number exists and get account details
    """
    banking_service = BankingService(db)
    
    try:
        recipient = banking_service.get_user_by_account(account_number)
        
        if not recipient:
            return {
                "valid": False,
                "message": "Account not found"
            }
        
        if recipient.id == current_user.id:
            return {
                "valid": False,
                "message": "Cannot transfer to your own account"
            }
        
        return {
            "valid": True,
            "account_number": recipient.account_number,
            "username": recipient.username,
            "full_name": recipient.full_name,
            "message": "Account found"
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
