import re
from typing import Optional

class Validators:
    @staticmethod
    def validate_password(password: str) -> Optional[str]:
        """
        Validate password strength
        Returns error message if invalid, None if valid
        """
        if len(password) < 8:
            return "Password must be at least 8 characters long"
        
        if not re.search(r"[A-Za-z]", password):
            return "Password must contain at least one letter"
        
        if not re.search(r"\d", password):
            return "Password must contain at least one number"
        
        return None
    
    @staticmethod
    def validate_amount(amount: float) -> Optional[str]:
        """
        Validate transaction amount
        """
        if amount <= 0:
            return "Amount must be greater than zero"
        
        if amount > 1000000:
            return "Amount exceeds maximum limit"
        
        return None
    
    @staticmethod
    def validate_account_number(account_number: str) -> Optional[str]:
        """
        Validate account number format
        """
        if not account_number.startswith("ACC"):
            return "Invalid account number format"
        
        if len(account_number) != 13:
            return "Account number must be 13 characters"
        
        return None
