from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.banking_service import BankingService
from ..services.otp_service import OTPService
from ..dependencies import get_current_user
from ..models.user import User
from pydantic import BaseModel
from typing import Optional, List
import uuid
from datetime import datetime, timedelta


router = APIRouter(prefix="/api/banking", tags=["Banking Operations"])


class TransferRequest(BaseModel):
    recipient_account: str
    amount: float
    description: Optional[str] = None


class OTPVerification(BaseModel):
    transaction_id: str
    otp: str


class TransferResponse(BaseModel):
    action: str
    message: str
    requires_otp: bool = False
    transaction_id: Optional[str] = None
    data: Optional[dict] = None


# Global OTP service instance
otp_service = OTPService()


@router.get("/balance")
def get_balance(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get current user's account balance"""
    banking_service = BankingService(db)
    balance_info = banking_service.get_balance(current_user.username)
    return balance_info


@router.post("/transfer", response_model=TransferResponse)
def initiate_transfer(
    transfer: TransferRequest,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Initiate a transfer - requires OTP verification
    """
    print(f"\n{'='*60}")
    print(f"💸 Transfer Request from: {current_user.username}")
    print(f"   Amount: ${transfer.amount}")
    print(f"   To: {transfer.recipient_account}")
    print(f"{'='*60}\n")
    
    banking_service = BankingService(db)
    
    # Validate amount
    if transfer.amount <= 0:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transfer amount must be positive"
        )
    
    if transfer.amount > 1000000:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transfer amount exceeds maximum limit of $1,000,000"
        )
    
    # Check if sender has sufficient balance
    try:
        sender_balance = banking_service.get_balance(current_user.username)
        if sender_balance['balance'] < transfer.amount:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Insufficient balance. Available: ${sender_balance['balance']:.2f}"
            )
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    
    # Validate recipient exists
    try:
        recipient_info = banking_service.get_account_info(transfer.recipient_account)
    except ValueError as e:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(e))
    
    # Check not transferring to self
    if current_user.account_number == transfer.recipient_account:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Cannot transfer to your own account"
        )
    
    # Generate transaction ID
    transaction_id = str(uuid.uuid4())
    
    # Generate and send OTP
    otp = otp_service.create_otp(current_user.email, transaction_id)
    email_sent = otp_service.send_otp_email(
        current_user.email,
        otp,
        transfer.amount,
        f"{recipient_info['username']} ({transfer.recipient_account})"
    )
    
    # Store pending transaction
    from ..main import app
    if not hasattr(app.state, 'pending_transactions'):
        app.state.pending_transactions = {}
    
    app.state.pending_transactions[transaction_id] = {
        'sender_username': current_user.username,
        'recipient_account': transfer.recipient_account,
        'amount': transfer.amount,
        'description': transfer.description or f"Transfer to {recipient_info['username']}",
        'transaction_type': 'manual_transfer',
        'expires_at': datetime.now() + timedelta(minutes=5)
    }
    
    print(f"🔐 OTP Generated: {otp}")
    print(f"📧 Email sent: {email_sent}")
    
    otp_message = "OTP sent to your registered email" if email_sent else f"OTP: {otp} (Email not configured)"
    
    return TransferResponse(
        action="transfer_pending",
        message=f"Transfer of ${transfer.amount:.2f} to {recipient_info['username']} requires verification. {otp_message}",
        requires_otp=True,
        transaction_id=transaction_id,
        data={
            "amount": transfer.amount,
            "recipient": recipient_info['username'],
            "recipient_account": transfer.recipient_account,
            "otp_sent": email_sent
        }
    )


@router.post("/verify-transfer")
def verify_and_complete_transfer(
    verification: OTPVerification,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Verify OTP and complete the transfer
    """
    from ..main import app
    
    # Check if transaction exists
    if not hasattr(app.state, 'pending_transactions') or \
       verification.transaction_id not in app.state.pending_transactions:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Transaction not found or expired. Please initiate a new transfer."
        )
    
    pending_tx = app.state.pending_transactions[verification.transaction_id]
    
    # Verify it's the same user
    if pending_tx['sender_username'] != current_user.username:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Unauthorized to verify this transaction"
        )
    
    # Check if expired
    if datetime.now() > pending_tx['expires_at']:
        del app.state.pending_transactions[verification.transaction_id]
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Transaction expired. Please initiate a new transfer."
        )
    
    # Verify OTP
    is_valid, otp_message = otp_service.verify_otp(verification.transaction_id, verification.otp)
    
    if not is_valid:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=otp_message)
    
    # OTP is valid - execute the transfer
    try:
        banking_service = BankingService(db)
        result = banking_service.transfer_funds(
            pending_tx['sender_username'],
            pending_tx['recipient_account'],
            pending_tx['amount'],
            pending_tx['description'] + " [OTP Verified]"
        )
        
        # Remove pending transaction
        del app.state.pending_transactions[verification.transaction_id]
        
        print(f"✅ Transfer completed successfully")
        print(f"   New balance: ${result['sender']['new_balance']:.2f}")
        
        return {
            "action": "transfer_success",
            "message": f"✅ Transfer successful! ${pending_tx['amount']:.2f} sent to {pending_tx['recipient_account']}. Your new balance is ${result['sender']['new_balance']:.2f}",
            "data": result
        }
    
    except ValueError as e:
        # Re-add the transaction back if transfer fails
        pending_tx['expires_at'] = datetime.now() + timedelta(minutes=5)
        app.state.pending_transactions[verification.transaction_id] = pending_tx
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(e))
    except Exception as e:
        print(f"❌ Transfer failed: {str(e)}")
        raise HTTPException(status_code=status.HTTP_500_INTERNAL_SERVER_ERROR, detail="Transfer failed")


@router.get("/transactions")
def get_transactions(
    limit: int = 50,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get user's transaction history"""
    banking_service = BankingService(db)
    transactions = banking_service.get_transaction_history(current_user.username, limit)
    
    return [
        {
            "id": t.id,
            "transaction_type": t.transaction_type,
            "amount": t.amount,
            "description": t.description,
            "timestamp": t.timestamp.isoformat(),
            "balance_after": t.balance_after
        }
        for t in transactions
    ]


@router.get("/recent-recipients")
def get_recent_recipients(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Get list of recent transfer recipients"""
    banking_service = BankingService(db)
    recipients = banking_service.get_recent_recipients(current_user.username)
    return {"recipients": recipients}


@router.get("/search-accounts/{query}")
def search_accounts(
    query: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Search for accounts by username or account number"""
    banking_service = BankingService(db)
    results = banking_service.search_accounts(query, current_user.username)
    return {"results": results}


@router.get("/validate-account/{account_number}")
def validate_account(
    account_number: str,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """Validate if an account number exists"""
    banking_service = BankingService(db)
    try:
        account_info = banking_service.get_account_info(account_number)
        return {
            "valid": True,
            "account_number": account_info["account_number"],
            "username": account_info["username"],
            "full_name": account_info["full_name"]
        }
    except ValueError:
        return {"valid": False, "message": "Account not found"}


@router.get("/all-users")
def get_all_users(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get all users (excluding current user) for testing/admin purposes
    """
    try:
        users = db.query(User).filter(User.id != current_user.id).all()
        
        return {
            "users": [
                {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "full_name": user.full_name,
                    "account_number": user.account_number,
                    "balance": user.balance,
                    "created_at": user.created_at
                }
                for user in users
            ],
            "total": len(users)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
