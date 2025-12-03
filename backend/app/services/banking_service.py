from sqlalchemy.orm import Session
from typing import List, Optional, Dict, Any
from datetime import datetime, timedelta
from ..models.user import User, Transaction
from ..utils.validators import Validators


class BankingService:
    """
    Banking service with dependency injection
    Handles all banking operations
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.validators = Validators()
        self.min_transfer_amount = 0.01
        self.max_transfer_amount = 1000000.00
        self.daily_transfer_limit = 50000.00
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self.db.query(User).filter(User.username == username).first()
    
    def get_user_by_account(self, account_number: str) -> Optional[User]:
        """Get user by account number"""
        return self.db.query(User).filter(User.account_number == account_number).first()
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def get_balance(self, username: str) -> Dict[str, Any]:
        """Get user's account balance"""
        user = self.get_user_by_username(username)
        
        if not user:
            raise ValueError("User not found")
        
        return {
            "balance": user.balance,
            "account_number": user.account_number,
            "username": user.username,
            "full_name": user.full_name
        }
    
    def deposit_funds(self, username: str, amount: float, description: str = "") -> Dict[str, Any]:
        """
        Deposit funds to user account
        """
        # Validate amount
        amount_error = self.validators.validate_amount(amount)
        if amount_error:
            raise ValueError(amount_error)
        
        # Get user
        user = self.get_user_by_username(username)
        if not user:
            raise ValueError("User not found")
        
        # Update balance
        old_balance = user.balance
        user.balance += amount
        
        # Create transaction record
        transaction = Transaction(
            user_id=user.id,
            transaction_type="credit",
            amount=amount,
            recipient_account=None,
            description=description or f"Deposit to account {user.account_number}"
        )
        
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(user)
        
        return {
            "status": "success",
            "message": f"Successfully deposited ${amount:.2f}",
            "old_balance": old_balance,
            "new_balance": user.balance,
            "transaction_id": transaction.id
        }
    
    def withdraw_funds(self, username: str, amount: float, description: str = "") -> Dict[str, Any]:
        """
        Withdraw funds from user account
        """
        # Validate amount
        amount_error = self.validators.validate_amount(amount)
        if amount_error:
            raise ValueError(amount_error)
        
        # Get user
        user = self.get_user_by_username(username)
        if not user:
            raise ValueError("User not found")
        
        # Check sufficient balance
        if user.balance < amount:
            raise ValueError(f"Insufficient balance. Available: ${user.balance:.2f}")
        
        # Update balance
        old_balance = user.balance
        user.balance -= amount
        
        # Create transaction record
        transaction = Transaction(
            user_id=user.id,
            transaction_type="debit",
            amount=amount,
            recipient_account=None,
            description=description or f"Withdrawal from account {user.account_number}"
        )
        
        self.db.add(transaction)
        self.db.commit()
        self.db.refresh(user)
        
        return {
            "status": "success",
            "message": f"Successfully withdrew ${amount:.2f}",
            "old_balance": old_balance,
            "new_balance": user.balance,
            "transaction_id": transaction.id
        }
    
    def transfer_funds(
        self, 
        username: str, 
        recipient_account: str, 
        amount: float, 
        description: str = ""
    ) -> Dict[str, Any]:
        """Transfer funds to another account"""
        # Validate amount
        amount_error = self.validators.validate_amount(amount)
        if amount_error:
            raise ValueError(amount_error)
        
        # Additional transfer amount validation
        if amount < self.min_transfer_amount:
            raise ValueError(f"Minimum transfer amount is ${self.min_transfer_amount:.2f}")
        
        if amount > self.max_transfer_amount:
            raise ValueError(f"Maximum transfer amount is ${self.max_transfer_amount:.2f}")
        
        # Validate account number format
        account_error = self.validators.validate_account_number(recipient_account)
        if account_error:
            raise ValueError(account_error)
        
        # Get sender
        sender = self.get_user_by_username(username)
        if not sender:
            raise ValueError("Sender not found")
        
        # Get recipient
        recipient = self.get_user_by_account(recipient_account)
        if not recipient:
            raise ValueError(f"Recipient account {recipient_account} not found")
        
        # Check if trying to send to self
        if sender.account_number == recipient_account:
            raise ValueError("Cannot transfer to your own account")
        
        # Check sufficient balance
        if sender.balance < amount:
            raise ValueError(f"Insufficient balance. Available: ${sender.balance:.2f}")
        
        # Check daily transfer limit
        daily_total = self._get_daily_transfer_total(sender.id)
        if daily_total + amount > self.daily_transfer_limit:
            remaining = self.daily_transfer_limit - daily_total
            raise ValueError(f"Daily transfer limit exceeded. Remaining limit: ${remaining:.2f}")
        
        # Perform transfer
        old_sender_balance = sender.balance
        old_recipient_balance = recipient.balance
        
        sender.balance -= amount
        recipient.balance += amount
        
        # Create transaction records
        sender_transaction = Transaction(
            user_id=sender.id,
            transaction_type="debit",
            amount=amount,
            recipient_account=recipient_account,
            description=description or f"Transfer to {recipient.username} ({recipient_account})"
        )
        
        recipient_transaction = Transaction(
            user_id=recipient.id,
            transaction_type="credit",
            amount=amount,
            recipient_account=sender.account_number,
            description=description or f"Transfer from {sender.username} ({sender.account_number})"
        )
        
        self.db.add(sender_transaction)
        self.db.add(recipient_transaction)
        self.db.commit()
        
        return {
            "status": "success",
            "message": f"Successfully transferred ${amount:.2f} to {recipient.username}",
            "sender": {
                "username": sender.username,
                "old_balance": old_sender_balance,
                "new_balance": sender.balance
            },
            "recipient": {
                "username": recipient.username,
                "account_number": recipient_account
            },
            "transaction_id": sender_transaction.id,
            "amount": amount,
            "timestamp": sender_transaction.timestamp
        }
    
    def get_transaction_history(
        self, 
        username: str, 
        limit: int = 50,
        transaction_type: Optional[str] = None,
        start_date: Optional[datetime] = None,
        end_date: Optional[datetime] = None
    ) -> List[Transaction]:
        """
        Get user's transaction history with optional filters
        """
        user = self.get_user_by_username(username)
        
        if not user:
            raise ValueError("User not found")
        
        # Base query
        query = self.db.query(Transaction).filter(Transaction.user_id == user.id)
        
        # Apply filters
        if transaction_type:
            if transaction_type not in ["credit", "debit"]:
                raise ValueError("Invalid transaction type. Must be 'credit' or 'debit'")
            query = query.filter(Transaction.transaction_type == transaction_type)
        
        if start_date:
            query = query.filter(Transaction.timestamp >= start_date)
        
        if end_date:
            query = query.filter(Transaction.timestamp <= end_date)
        
        # Order by most recent and limit
        transactions = query.order_by(Transaction.timestamp.desc()).limit(limit).all()
        
        return transactions
    
    def get_transaction_by_id(self, transaction_id: int, username: str) -> Optional[Transaction]:
        """
        Get specific transaction by ID (only if it belongs to the user)
        """
        user = self.get_user_by_username(username)
        if not user:
            raise ValueError("User not found")
        
        transaction = self.db.query(Transaction).filter(
            Transaction.id == transaction_id,
            Transaction.user_id == user.id
        ).first()
        
        return transaction
    
    def get_transaction_summary(self, username: str, days: int = 30) -> Dict[str, Any]:
        """
        Get transaction summary for specified number of days
        """
        user = self.get_user_by_username(username)
        if not user:
            raise ValueError("User not found")
        
        # Calculate date range
        end_date = datetime.utcnow()
        start_date = end_date - timedelta(days=days)
        
        # Get transactions in date range
        transactions = self.db.query(Transaction).filter(
            Transaction.user_id == user.id,
            Transaction.timestamp >= start_date,
            Transaction.timestamp <= end_date
        ).all()
        
        # Calculate summary
        total_credits = sum(t.amount for t in transactions if t.transaction_type == "credit")
        total_debits = sum(t.amount for t in transactions if t.transaction_type == "debit")
        credit_count = sum(1 for t in transactions if t.transaction_type == "credit")
        debit_count = sum(1 for t in transactions if t.transaction_type == "debit")
        
        return {
            "period_days": days,
            "start_date": start_date,
            "end_date": end_date,
            "total_transactions": len(transactions),
            "credits": {
                "count": credit_count,
                "total_amount": total_credits
            },
            "debits": {
                "count": debit_count,
                "total_amount": total_debits
            },
            "net_change": total_credits - total_debits,
            "current_balance": user.balance
        }
    
    def get_recent_recipients(self, username: str, limit: int = 5) -> List[Dict[str, Any]]:
        """
        Get list of recent transfer recipients
        """
        user = self.get_user_by_username(username)
        if not user:
            raise ValueError("User not found")
        
        # Get recent debit transactions (transfers out)
        recent_transfers = self.db.query(Transaction).filter(
            Transaction.user_id == user.id,
            Transaction.transaction_type == "debit",
            Transaction.recipient_account.isnot(None)
        ).order_by(Transaction.timestamp.desc()).limit(limit * 2).all()
        
        # Extract unique recipients
        recipients = {}
        for txn in recent_transfers:
            if txn.recipient_account and txn.recipient_account not in recipients:
                recipient_user = self.get_user_by_account(txn.recipient_account)
                if recipient_user:
                    recipients[txn.recipient_account] = {
                        "account_number": txn.recipient_account,
                        "username": recipient_user.username,
                        "full_name": recipient_user.full_name,
                        "last_transfer_date": txn.timestamp,
                        "last_transfer_amount": txn.amount
                    }
                if len(recipients) >= limit:
                    break
        
        return list(recipients.values())
    
    def search_transactions(
        self,
        username: str,
        search_term: str,
        limit: int = 20
    ) -> List[Transaction]:
        """
        Search transactions by description or recipient account
        """
        user = self.get_user_by_username(username)
        if not user:
            raise ValueError("User not found")
        
        transactions = self.db.query(Transaction).filter(
            Transaction.user_id == user.id,
            (Transaction.description.ilike(f"%{search_term}%")) |
            (Transaction.recipient_account.ilike(f"%{search_term}%"))
        ).order_by(Transaction.timestamp.desc()).limit(limit).all()
        
        return transactions
    
    def get_account_statement(
        self,
        username: str,
        start_date: datetime,
        end_date: datetime
    ) -> Dict[str, Any]:
        """
        Generate account statement for date range
        """
        user = self.get_user_by_username(username)
        if not user:
            raise ValueError("User not found")
        
        # Get transactions in date range
        transactions = self.db.query(Transaction).filter(
            Transaction.user_id == user.id,
            Transaction.timestamp >= start_date,
            Transaction.timestamp <= end_date
        ).order_by(Transaction.timestamp.asc()).all()
        
        # Calculate opening balance (balance before start_date)
        earlier_transactions = self.db.query(Transaction).filter(
            Transaction.user_id == user.id,
            Transaction.timestamp < start_date
        ).all()
        
        opening_balance = 1000.0  # Initial balance
        for txn in earlier_transactions:
            if txn.transaction_type == "credit":
                opening_balance += txn.amount
            else:
                opening_balance -= txn.amount
        
        # Build statement with running balance
        statement_items = []
        running_balance = opening_balance
        
        for txn in transactions:
            if txn.transaction_type == "credit":
                running_balance += txn.amount
            else:
                running_balance -= txn.amount
            
            statement_items.append({
                "date": txn.timestamp,
                "description": txn.description,
                "type": txn.transaction_type,
                "amount": txn.amount,
                "balance": running_balance,
                "recipient_account": txn.recipient_account
            })
        
        return {
            "account_holder": user.full_name or user.username,
            "account_number": user.account_number,
            "statement_period": {
                "start_date": start_date,
                "end_date": end_date
            },
            "opening_balance": opening_balance,
            "closing_balance": running_balance,
            "transactions": statement_items,
            "total_transactions": len(transactions)
        }
    
    def _get_daily_transfer_total(self, user_id: int) -> float:
        """
        Calculate total amount transferred today
        """
        today_start = datetime.utcnow().replace(hour=0, minute=0, second=0, microsecond=0)
        
        daily_transfers = self.db.query(Transaction).filter(
            Transaction.user_id == user_id,
            Transaction.transaction_type == "debit",
            Transaction.recipient_account.isnot(None),
            Transaction.timestamp >= today_start
        ).all()
        
        return sum(t.amount for t in daily_transfers)
    
    def check_daily_limit_remaining(self, username: str) -> Dict[str, Any]:
        """
        Check remaining daily transfer limit
        """
        user = self.get_user_by_username(username)
        if not user:
            raise ValueError("User not found")
        
        daily_total = self._get_daily_transfer_total(user.id)
        remaining = self.daily_transfer_limit - daily_total
        
        return {
            "daily_limit": self.daily_transfer_limit,
            "used_today": daily_total,
            "remaining": max(0, remaining),
            "percentage_used": (daily_total / self.daily_transfer_limit) * 100
        }


# Dependency function for FastAPI
def get_banking_service(db: Session) -> BankingService:
    """
    Dependency injection function for BankingService
    """
    return BankingService(db)
