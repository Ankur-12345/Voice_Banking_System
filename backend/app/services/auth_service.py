from sqlalchemy.orm import Session
from typing import Optional
from ..models.user import User
from ..schemas.user import UserCreate
from ..utils.security import get_password_hash, verify_password, create_access_token
from ..utils.validators import Validators
from ..utils.email import EmailService
from datetime import timedelta
from ..config import settings
import secrets


class AuthService:
    """
    Authentication service with dependency injection
    Handles all authentication-related business logic
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.email_service = EmailService()
        self.validators = Validators()
    
    def get_user_by_username(self, username: str) -> Optional[User]:
        """Get user by username"""
        return self.db.query(User).filter(User.username == username).first()
    
    def get_user_by_email(self, email: str) -> Optional[User]:
        """Get user by email"""
        return self.db.query(User).filter(User.email == email).first()
    
    def get_user_by_id(self, user_id: int) -> Optional[User]:
        """Get user by ID"""
        return self.db.query(User).filter(User.id == user_id).first()
    
    def username_exists(self, username: str) -> bool:
        """Check if username already exists"""
        return self.get_user_by_username(username) is not None
    
    def email_exists(self, email: str) -> bool:
        """Check if email already exists"""
        return self.get_user_by_email(email) is not None
    
    def validate_user_data(self, user: UserCreate) -> Optional[str]:
        """
        Validate user registration data
        Returns error message if invalid, None if valid
        """
        # Validate username
        if len(user.username) < 3:
            return "Username must be at least 3 characters long"
        
        if len(user.username) > 50:
            return "Username must not exceed 50 characters"
        
        # Check for valid username characters
        if not user.username.replace('_', '').replace('.', '').isalnum():
            return "Username can only contain letters, numbers, underscores, and periods"
        
        if self.username_exists(user.username):
            return "Username already registered"
        
        # Validate email
        if self.email_exists(user.email):
            return "Email already registered"
        
        # Validate email format
        if not self._is_valid_email(user.email):
            return "Invalid email format"
        
        # Validate password
        password_error = self.validators.validate_password(user.password)
        if password_error:
            return password_error
        
        # Validate full name if provided
        if user.full_name and len(user.full_name) > 100:
            return "Full name must not exceed 100 characters"
        
        return None
    
    def create_user(self, user: UserCreate) -> User:
        """Create a new user with validated data"""
        # Generate unique account number
        account_number = self._generate_account_number()
        
        # Hash the password
        hashed_password = get_password_hash(user.password)
        
        # Create user instance
        db_user = User(
            email=user.email,
            username=user.username,
            hashed_password=hashed_password,
            full_name=user.full_name,
            account_number=account_number,
            balance=1000.0  # Initial balance
        )
        
        # Add to database
        self.db.add(db_user)
        self.db.commit()
        self.db.refresh(db_user)
        
        return db_user
    
    def authenticate_user(self, username: str, password: str) -> Optional[User]:
        """Authenticate user with username and password"""
        user = self.get_user_by_username(username)
        
        if not user:
            return None
        
        if not verify_password(password, user.hashed_password):
            return None
        
        return user
    
    def create_token_for_user(self, user: User) -> str:
        """Create JWT access token for user"""
        access_token_expires = timedelta(minutes=settings.ACCESS_TOKEN_EXPIRE_MINUTES)
        
        token_data = {
            "sub": user.username,
            "user_id": user.id,
            "email": user.email
        }
        
        access_token = create_access_token(
            data=token_data,
            expires_delta=access_token_expires
        )
        
        return access_token
    
    def initiate_password_reset(self, email: str) -> Optional[dict]:
        """Initiate password reset process"""
        user = self.get_user_by_email(email)
        
        if not user:
            return None
        
        reset_token = self.create_token_for_user(user)
        
        return {
            "token": reset_token,
            "email": email,
            "username": user.username
        }
    
    def reset_password(self, email: str, new_password: str) -> bool:
        """Reset user password"""
        password_error = self.validators.validate_password(new_password)
        if password_error:
            raise ValueError(password_error)
        
        user = self.get_user_by_email(email)
        if not user:
            return False
        
        user.hashed_password = get_password_hash(new_password)
        self.db.commit()
        
        return True
    
    def change_password(self, username: str, old_password: str, new_password: str) -> bool:
        """Change user password with old password verification"""
        user = self.authenticate_user(username, old_password)
        if not user:
            raise ValueError("Current password is incorrect")
        
        password_error = self.validators.validate_password(new_password)
        if password_error:
            raise ValueError(password_error)
        
        if verify_password(new_password, user.hashed_password):
            raise ValueError("New password must be different from current password")
        
        user.hashed_password = get_password_hash(new_password)
        self.db.commit()
        
        return True
    
    def update_user_profile(self, username: str, full_name: Optional[str] = None) -> User:
        """Update user profile information"""
        user = self.get_user_by_username(username)
        
        if not user:
            raise ValueError("User not found")
        
        if full_name is not None:
            if len(full_name) > 100:
                raise ValueError("Full name must not exceed 100 characters")
            user.full_name = full_name
        
        self.db.commit()
        self.db.refresh(user)
        
        return user
    
    def delete_user_account(self, username: str, password: str) -> bool:
        """Delete user account"""
        user = self.authenticate_user(username, password)
        if not user:
            raise ValueError("Invalid password")
        
        if user.balance > 0:
            raise ValueError("Cannot delete account with remaining balance. Please withdraw all funds first.")
        
        self.db.delete(user)
        self.db.commit()
        
        return True
    
    def _generate_account_number(self) -> str:
        """Generate unique account number"""
        max_attempts = 10
        attempts = 0
        
        while attempts < max_attempts:
            account_number = f"ACC{secrets.randbelow(9000000000) + 1000000000}"
            
            existing = self.db.query(User).filter(
                User.account_number == account_number
            ).first()
            
            if not existing:
                return account_number
            
            attempts += 1
        
        raise RuntimeError("Failed to generate unique account number")
    
    def _is_valid_email(self, email: str) -> bool:
        """Validate email format"""
        import re
        email_pattern = r'^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$'
        return re.match(email_pattern, email) is not None
      
    def get_user_statistics(self, username: str) -> dict:
        """Get user account statistics"""
        user = self.get_user_by_username(username)
        
        if not user:
            raise ValueError("User not found")
        
        from ..models.user import Transaction
        transaction_count = self.db.query(Transaction).filter(
            Transaction.user_id == user.id
        ).count()
        
        transactions = self.db.query(Transaction).filter(
            Transaction.user_id == user.id
        ).all()
        
        total_credits = sum(t.amount for t in transactions if t.transaction_type == "credit")
        total_debits = sum(t.amount for t in transactions if t.transaction_type == "debit")
        
        return {
            "username": user.username,
            "account_number": user.account_number,
            "current_balance": user.balance,
            "transaction_count": transaction_count,
            "total_credits": total_credits,
            "total_debits": total_debits,
            "account_created": user.created_at
        }
