from sqlalchemy.orm import Session
from sqlalchemy import or_, desc
from ..models.user import User
from ..models.transaction import Transaction
from datetime import datetime, timedelta
from typing import List, Dict


class BankingService:
    """
    Service for handling banking operations
    """
    
    def __init__(self, db: Session):
        self.db = db
    
    def get_balance(self, username: str) -> dict:
        """Get user's current balance"""
        user = self.db.query(User).filter(User.username == username).first()
        
        if not user:
            raise ValueError(f"User {username} not found")
        
        return {
            "balance": user.balance,
            "account_number": user.account_number,
            "username": user.username
        }
    
    def get_account_info(self, account_number: str) -> dict:
        """Get account information by account number"""
        user = self.db.query(User).filter(User.account_number == account_number).first()
        
        if not user:
            print(f"❌ Account not found: {account_number}")
            raise ValueError(f"Account {account_number} not found")
        
        print(f"✅ Account found: {user.username} ({account_number})")
        
        return {
            "account_number": user.account_number,
            "username": user.username,
            "full_name": user.full_name,
            "email": user.email
        }
    
    def transfer_funds(
        self, 
        sender_username: str, 
        recipient_account: str, 
        amount: float, 
        description: str = None
    ) -> dict:
        """Transfer funds between accounts"""
        # Get sender
        sender = self.db.query(User).filter(User.username == sender_username).first()
        if not sender:
            raise ValueError("Sender account not found")
        
        # Get recipient
        recipient = self.db.query(User).filter(User.account_number == recipient_account).first()
        if not recipient:
            raise ValueError("Recipient account not found")
        
        # Validate amount
        if amount <= 0:
            raise ValueError("Transfer amount must be positive")
        
        if amount > 1000000:
            raise ValueError("Transfer amount exceeds limit")
        
        # Check sufficient balance
        if sender.balance < amount:
            raise ValueError(f"Insufficient funds. Available: ${sender.balance:.2f}")
        
        # Prevent self-transfer
        if sender.account_number == recipient.account_number:
            raise ValueError("Cannot transfer to your own account")
        
        # Perform transfer
        try:
            # Update balances
            sender.balance -= amount
            recipient.balance += amount
            
            # Create debit transaction for sender
            sender_transaction = Transaction(
                user_id=sender.id,
                transaction_type='debit',
                amount=amount,
                description=description or f"Transfer to {recipient.username}",
                balance_after=sender.balance,
                recipient_account=recipient.account_number
            )
            
            # Create credit transaction for recipient
            recipient_transaction = Transaction(
                user_id=recipient.id,
                transaction_type='credit',
                amount=amount,
                description=description or f"Transfer from {sender.username}",
                balance_after=recipient.balance,
                recipient_account=sender.account_number
            )
            
            # Add transactions to database
            self.db.add(sender_transaction)
            self.db.add(recipient_transaction)
            
            # Commit all changes
            self.db.commit()
            self.db.refresh(sender)
            self.db.refresh(recipient)
            
            print(f"✅ Transfer successful: ${amount:.2f} from {sender.username} to {recipient.username}")
            print(f"   Sender new balance: ${sender.balance:.2f}")
            print(f"   Recipient new balance: ${recipient.balance:.2f}")
            
            return {
                "success": True,
                "sender": {
                    "username": sender.username,
                    "new_balance": sender.balance
                },
                "recipient": {
                    "username": recipient.username,
                    "new_balance": recipient.balance
                },
                "transaction": {
                    "amount": amount,
                    "description": description,
                    "timestamp": sender_transaction.timestamp.isoformat()
                }
            }
            
        except Exception as e:
            self.db.rollback()
            print(f"❌ Transfer failed: {str(e)}")
            raise ValueError(f"Transfer failed: {str(e)}")
    
    def get_transaction_history(self, username: str, limit: int = 50) -> List[Transaction]:
        """Get user's transaction history"""
        user = self.db.query(User).filter(User.username == username).first()
        
        if not user:
            raise ValueError(f"User {username} not found")
        
        transactions = self.db.query(Transaction).filter(
            Transaction.user_id == user.id
        ).order_by(desc(Transaction.timestamp)).limit(limit).all()
        
        print(f"📋 Retrieved {len(transactions)} transactions for {username}")
        
        return transactions
    
    def get_recent_recipients(self, username: str, limit: int = 5) -> List[dict]:
        """Get list of recent transfer recipients"""
        user = self.db.query(User).filter(User.username == username).first()
        
        if not user:
            return []
        
        # Get recent debit transactions with recipients
        recent_transactions = self.db.query(Transaction).filter(
            Transaction.user_id == user.id,
            Transaction.transaction_type == 'debit',
            Transaction.recipient_account.isnot(None)
        ).order_by(desc(Transaction.timestamp)).limit(20).all()
        
        # Get unique recipients
        seen_accounts = set()
        recipients = []
        
        for transaction in recent_transactions:
            if transaction.recipient_account not in seen_accounts:
                recipient_user = self.db.query(User).filter(
                    User.account_number == transaction.recipient_account
                ).first()
                
                if recipient_user:
                    recipients.append({
                        "account_number": recipient_user.account_number,
                        "username": recipient_user.username,
                        "full_name": recipient_user.full_name
                    })
                    seen_accounts.add(transaction.recipient_account)
                    
                    if len(recipients) >= limit:
                        break
        
        return recipients
    
    def search_accounts(self, query: str, exclude_username: str = None) -> List[dict]:
        """Search for accounts by username or account number"""
        search_filter = or_(
            User.username.ilike(f"%{query}%"),
            User.account_number.ilike(f"%{query}%"),
            User.full_name.ilike(f"%{query}%")
        )
        
        if exclude_username:
            search_filter = search_filter & (User.username != exclude_username)
        
        users = self.db.query(User).filter(search_filter).limit(10).all()
        
        return [
            {
                "account_number": user.account_number,
                "username": user.username,
                "full_name": user.full_name
            }
            for user in users
        ]
