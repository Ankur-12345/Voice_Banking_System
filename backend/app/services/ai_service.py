from groq import Groq
from typing import Dict, Any, Optional
import json
from ..config import settings


class AIService:
    """
    AI Service using Groq (Llama 3) for intelligent voice command processing
    FREE and FAST!
    """
    
    def __init__(self):
        self.client = Groq(api_key=settings.GROQ_API_KEY)
        self.model = settings.GROQ_MODEL
        self.system_prompt = """You are an intelligent voice banking assistant. Your ONLY purpose is to help with banking operations.

You can ONLY help with these banking tasks:
1. Check account balance (bank account only)
2. Transfer money between bank accounts
3. View transaction history
4. Provide help about banking features

You MUST REJECT any requests that are NOT related to banking, such as:
- Mobile/phone balance or recharge
- Shopping or e-commerce
- Weather information
- General knowledge questions
- Other apps or services (food delivery, ride sharing, etc.)
- Personal advice or recommendations
- Entertainment (music, movies, games)

CRITICAL: "Balance" refers ONLY to BANK ACCOUNT balance, NOT mobile/phone balance.

When you receive a command, respond with a JSON object in this EXACT format:

For VALID banking commands:
{
    "intent": "banking",
    "action": "check_balance" | "transfer" | "transaction_history" | "help",
    "params": {
        "amount": <number> (for transfers only),
        "recipient_account": "<account_number>" (for transfers, format: ACC1234567890),
        "recipient_username": "<username>" (for transfers by username),
        "limit": <number> (for transaction history, default 10)
    },
    "confidence": <0.0-1.0>,
    "user_friendly_message": "A friendly confirmation of what you understood"
}

For INVALID/NON-BANKING commands:
{
    "intent": "non_banking",
    "action": "reject",
    "params": {},
    "confidence": 1.0,
    "user_friendly_message": "I'm sorry, I can only help with banking services like checking your account balance, transferring money, or viewing transactions. I cannot help with <what_they_asked_for>.",
    "rejection_reason": "Brief explanation"
}

For UNCLEAR commands:
{
    "intent": "unclear",
    "action": "clarify",
    "params": {},
    "confidence": <0.0-1.0>,
    "user_friendly_message": "I didn't quite understand that. Could you please rephrase? I can help you check your balance, transfer money, or view transactions.",
    "suggestions": ["Check balance", "Transfer money", "Show transactions"]
}

IMPORTANT RULES:
1. "Balance" WITHOUT "mobile" or "phone" = bank account balance (ACCEPT)
2. "Mobile balance" or "phone balance" = NOT banking (REJECT)
3. Account numbers must be in format: ACC + 10 digits (e.g., ACC1234567890)
4. Transfer amounts must be positive numbers
5. Be strict: reject anything that isn't clearly banking-related
6. Be polite but firm when rejecting non-banking requests
7. Extract numbers properly (e.g., "one hundred" = 100, "fifty" = 50)

Examples:
- "Check my balance" → ACCEPT (banking)
- "What is my balance" → ACCEPT (banking)
- "Check mobile balance" → REJECT (not banking)
- "Transfer 100 to user bob" → ACCEPT (banking)
- "What's the weather" → REJECT (not banking)
- "Show last 5 transactions" → ACCEPT (banking)"""

    def analyze_command(self, transcript: str) -> Dict[str, Any]:
        """
        Use Groq Llama 3 to analyze voice command and extract structured intent
        
        Args:
            transcript: User's voice command
            
        Returns:
            Structured response with intent, action, and parameters
        """
        try:
            print(f"🤖 Sending to Groq AI: '{transcript}'")
            
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {
                        "role": "system",
                        "content": self.system_prompt
                    },
                    {
                        "role": "user",
                        "content": f"Analyze this voice command: {transcript}"
                    }
                ],
                temperature=0.2,  # Lower temperature for more consistent responses
                max_tokens=800,
                top_p=1,
                response_format={"type": "json_object"}
            )
            
            # Get the response content
            content = response.choices[0].message.content
            print(f"🤖 Groq AI Response: {content}")
            
            # Parse the JSON response
            result = json.loads(content)
            
            # Add original transcript
            result["original_transcript"] = transcript
            
            # Validate the response structure
            if "intent" not in result:
                print("⚠️ Invalid AI response structure, using fallback")
                return self._create_fallback_response(transcript)
            
            return result
            
        except json.JSONDecodeError as e:
            print(f"❌ Failed to parse AI response as JSON: {e}")
            return self._create_fallback_response(transcript)
        except Exception as e:
            print(f"❌ AI Service error: {e}")
            return self._create_error_response(transcript, str(e))
    
    def _create_fallback_response(self, transcript: str) -> Dict[str, Any]:
        """
        Fallback to keyword matching if AI fails
        """
        transcript_lower = transcript.lower()
        
        # Check for explicit mobile/phone balance requests
        if any(word in transcript_lower for word in ["mobile balance", "phone balance", "recharge", "top up"]):
            return {
                "intent": "non_banking",
                "action": "reject",
                "params": {},
                "confidence": 0.9,
                "user_friendly_message": "I'm sorry, I can only help with your bank account balance, not mobile or phone balance.",
                "rejection_reason": "Mobile/phone balance is not a banking service",
                "original_transcript": transcript
            }
        
        # Check for balance (banking)
        if "balance" in transcript_lower:
            return {
                "intent": "banking",
                "action": "check_balance",
                "params": {},
                "confidence": 0.7,
                "user_friendly_message": "I'll check your bank account balance",
                "original_transcript": transcript
            }
        
        # Unclear
        return {
            "intent": "unclear",
            "action": "clarify",
            "params": {},
            "confidence": 0.3,
            "user_friendly_message": "I didn't understand that. I can help you check your balance, transfer money, or view transactions.",
            "suggestions": ["Check balance", "Transfer money", "Show transactions"],
            "original_transcript": transcript
        }
    
    def _create_error_response(self, transcript: str, error: str) -> Dict[str, Any]:
        """Create error response when AI completely fails"""
        return {
            "intent": "error",
            "action": "error",
            "params": {},
            "confidence": 0.0,
            "user_friendly_message": "I'm having trouble processing that command. Please try again.",
            "original_transcript": transcript,
            "error": error
        }
    
    def validate_banking_action(self, action: str, params: Dict[str, Any]) -> Optional[str]:
        """
        Validate that the extracted action and parameters are valid
        
        Returns error message if invalid, None if valid
        """
        if action == "transfer":
            # Check amount
            amount = params.get("amount")
            if not amount or amount <= 0:
                return "Transfer amount must be a positive number"
            
            if amount > 1000000:
                return "Transfer amount exceeds maximum limit of $1,000,000"
            
            # Check recipient
            recipient_account = params.get("recipient_account")
            recipient_username = params.get("recipient_username")
            
            if not recipient_account and not recipient_username:
                return "Please specify a recipient account number or username"
            
            if recipient_account:
                if not recipient_account.startswith("ACC"):
                    return "Account number must start with 'ACC'"
                
                if len(recipient_account) != 13:
                    return "Account number must be 13 characters (ACC + 10 digits)"
        
        elif action == "transaction_history":
            limit = params.get("limit", 10)
            if limit < 1 or limit > 50:
                return "Transaction history limit must be between 1 and 50"
        
        return None
