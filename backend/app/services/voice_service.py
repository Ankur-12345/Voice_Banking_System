from typing import Dict, Any, Optional
import re
from sqlalchemy.orm import Session


class VoiceService:
    """
    Voice command processing service with dependency injection
    Handles voice command parsing and interpretation
    """
    
    def __init__(self, db: Session):
        self.db = db
        self.command_patterns = self._initialize_command_patterns()
    
    def _initialize_command_patterns(self) -> Dict[str, Any]:
        """Initialize command patterns for voice recognition"""
        return {
            "balance": {
                "keywords": ["balance", "check balance", "my balance", "account balance", "show balance"],
                "action": "check_balance"
            },
            "transfer": {
                "patterns": [
                    r"transfer\s+(\d+\.?\d*)\s+(?:to|into)\s+(\w+)",
                    r"send\s+(\d+\.?\d*)\s+(?:to|into)\s+(\w+)",
                    r"pay\s+(\d+\.?\d*)\s+(?:to|into)\s+(\w+)",
                    r"give\s+(\d+\.?\d*)\s+(?:to|into)\s+(\w+)"
                ],
                "action": "transfer"
            },
            "history": {
                "keywords": ["history", "transactions", "statement", "transaction history", "show transactions"],
                "action": "transaction_history"
            },
            "help": {
                "keywords": ["help", "what can you do", "commands", "show commands"],
                "action": "help"
            }
        }
    
    def parse_voice_command(self, transcript: str) -> Dict[str, Any]:
        """
        Parse voice command transcript and extract action and parameters
        
        Args:
            transcript: Voice command text
            
        Returns:
            Dictionary with action and parameters
        """
        # Normalize transcript
        transcript = self._normalize_transcript(transcript)
        
        # Try to parse balance command
        balance_result = self._parse_balance_command(transcript)
        if balance_result:
            return balance_result
        
        # Try to parse transfer command
        transfer_result = self._parse_transfer_command(transcript)
        if transfer_result:
            return transfer_result
        
        # Try to parse history command
        history_result = self._parse_history_command(transcript)
        if history_result:
            return history_result
        
        # Try to parse help command
        help_result = self._parse_help_command(transcript)
        if help_result:
            return help_result
        
        # Command not recognized
        return self._create_unknown_response(transcript)
    
    def _normalize_transcript(self, transcript: str) -> str:
        """Normalize transcript for processing"""
        # Convert to lowercase and strip whitespace
        normalized = transcript.lower().strip()
        
        # Remove extra whitespace
        normalized = re.sub(r'\s+', ' ', normalized)
        
        # Remove punctuation at the end
        normalized = normalized.rstrip('.,!?')
        
        return normalized
    
    def _parse_balance_command(self, transcript: str) -> Optional[Dict[str, Any]]:
        """Parse balance check commands"""
        keywords = self.command_patterns["balance"]["keywords"]
        
        for keyword in keywords:
            if keyword in transcript:
                return {
                    "action": "check_balance",
                    "params": {},
                    "confidence": self._calculate_confidence(transcript, keyword)
                }
        
        return None
    
    def _parse_transfer_command(self, transcript: str) -> Optional[Dict[str, Any]]:
        """Parse fund transfer commands"""
        patterns = self.command_patterns["transfer"]["patterns"]
        
        for pattern in patterns:
            match = re.search(pattern, transcript)
            if match:
                try:
                    amount = float(match.group(1))
                    recipient = match.group(2).upper()
                    
                    # Ensure recipient has correct format
                    if not recipient.startswith("ACC"):
                        recipient = f"ACC{recipient}"
                    
                    return {
                        "action": "transfer",
                        "params": {
                            "amount": amount,
                            "recipient_account": recipient
                        },
                        "confidence": self._calculate_confidence(transcript, "transfer")
                    }
                except (ValueError, IndexError):
                    continue
        
        return None
    
    def _parse_history_command(self, transcript: str) -> Optional[Dict[str, Any]]:
        """Parse transaction history commands"""
        keywords = self.command_patterns["history"]["keywords"]
        
        for keyword in keywords:
            if keyword in transcript:
                # Check if user wants limited results
                limit_match = re.search(r'(\d+)\s+(?:transactions|last)', transcript)
                limit = int(limit_match.group(1)) if limit_match else 10
                
                return {
                    "action": "transaction_history",
                    "params": {"limit": min(limit, 50)},  # Max 50
                    "confidence": self._calculate_confidence(transcript, keyword)
                }
        
        return None
    
    def _parse_help_command(self, transcript: str) -> Optional[Dict[str, Any]]:
        """Parse help commands"""
        keywords = self.command_patterns["help"]["keywords"]
        
        for keyword in keywords:
            if keyword in transcript:
                return {
                    "action": "help",
                    "params": {},
                    "confidence": self._calculate_confidence(transcript, keyword)
                }
        
        return None
    
    def _calculate_confidence(self, transcript: str, keyword: str) -> float:
        """
        Calculate confidence score for command recognition
        
        Returns value between 0.0 and 1.0
        """
        # Simple confidence calculation based on keyword match
        word_count = len(transcript.split())
        keyword_count = len(keyword.split())
        
        if word_count == 0:
            return 0.0
        
        # Higher confidence for exact matches
        if transcript == keyword:
            return 1.0
        
        # Calculate based on keyword length vs transcript length
        confidence = min(keyword_count / word_count, 1.0)
        
        return round(confidence, 2)
    
    def _create_unknown_response(self, transcript: str) -> Dict[str, Any]:
        """Create response for unrecognized commands"""
        suggestions = self._get_command_suggestions(transcript)
        
        return {
            "action": "unknown",
            "params": {},
            "confidence": 0.0,
            "message": "Command not recognized",
            "suggestions": suggestions,
            "original_transcript": transcript
        }
    
    def _get_command_suggestions(self, transcript: str) -> list:
        """Get command suggestions based on transcript"""
        suggestions = []
        
        # Check for partial matches
        if any(word in transcript for word in ["money", "account", "check"]):
            suggestions.append("Try: 'Check balance'")
        
        if any(word in transcript for word in ["send", "pay", "give"]):
            suggestions.append("Try: 'Transfer 100 to ACC1234567890'")
        
        if any(word in transcript for word in ["show", "list", "see"]):
            suggestions.append("Try: 'Show transaction history'")
        
        if not suggestions:
            suggestions = [
                "Check balance",
                "Transfer [amount] to [account]",
                "Show transaction history"
            ]
        
        return suggestions
    
    def get_available_commands(self) -> list:
        """Get list of all available voice commands"""
        return [
            {
                "command": "Check Balance",
                "examples": [
                    "Check balance",
                    "What is my balance",
                    "Show my account balance"
                ],
                "action": "check_balance"
            },
            {
                "command": "Transfer Funds",
                "examples": [
                    "Transfer 100 to ACC1234567890",
                    "Send 50 to ACC9876543210",
                    "Pay 25 to ACC5555555555"
                ],
                "action": "transfer"
            },
            {
                "command": "Transaction History",
                "examples": [
                    "Show transaction history",
                    "Show my transactions",
                    "Last 10 transactions"
                ],
                "action": "transaction_history"
            },
            {
                "command": "Help",
                "examples": [
                    "Help",
                    "What can you do",
                    "Show commands"
                ],
                "action": "help"
            }
        ]
    
    def validate_command_params(self, action: str, params: dict) -> Optional[str]:
        """
        Validate command parameters
        
        Returns error message if invalid, None if valid
        """
        if action == "transfer":
            amount = params.get("amount", 0)
            recipient = params.get("recipient_account", "")
            
            if amount <= 0:
                return "Transfer amount must be greater than zero"
            
            if amount > 1000000:
                return "Transfer amount exceeds maximum limit of $1,000,000"
            
            if not recipient.startswith("ACC"):
                return "Invalid recipient account format. Must start with 'ACC'"
            
            if len(recipient) != 13:
                return "Invalid account number length. Must be 13 characters"
        
        elif action == "transaction_history":
            limit = params.get("limit", 10)
            
            if limit < 1 or limit > 50:
                return "Transaction limit must be between 1 and 50"
        
        return None


# Dependency function for FastAPI
def get_voice_service(db: Session) -> VoiceService:
    """
    Dependency injection function for VoiceService
    """
    return VoiceService(db)
