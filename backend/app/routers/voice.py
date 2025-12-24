from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.voice_service import VoiceService
from ..services.banking_service import BankingService
from ..services.ai_service import AIService
from ..services.otp_service import OTPService
from ..dependencies import get_current_user
from ..models.user import User
from pydantic import BaseModel
from typing import Optional
import uuid
from datetime import datetime, timedelta


router = APIRouter(prefix="/api/voice", tags=["Voice Commands"])


class VoiceCommand(BaseModel):
    transcript: str


class VoiceResponse(BaseModel):
    action: str
    data: Optional[dict] = None
    message: Optional[str] = None
    confidence: Optional[float] = None
    suggestions: Optional[list] = None
    intent: Optional[str] = None
    requires_otp: Optional[bool] = False
    transaction_id: Optional[str] = None


class OTPVerification(BaseModel):
    transaction_id: str
    otp: str


# Global OTP service instance
otp_service = OTPService()


@router.post("/process", response_model=VoiceResponse)
def process_voice_command(
    command: VoiceCommand,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Process voice command using AI with OTP security for transfers
    """
    print(f"\n{'='*60}")
    print(f"🎤 Voice Command from: {current_user.username}")
    print(f"📝 Transcript: '{command.transcript}'")
    print(f"{'='*60}\n")
    
    # Initialize services
    ai_service = AIService()
    voice_service = VoiceService(db)
    
    # Use AI to analyze the command
    ai_result = ai_service.analyze_command(command.transcript)
    
    print(f"🤖 AI Analysis:")
    print(f"   Intent: {ai_result.get('intent')}")
    print(f"   Action: {ai_result.get('action')}")
    print(f"   Confidence: {ai_result.get('confidence')}")
    
    intent = ai_result.get("intent")
    action = ai_result.get("action")
    params = ai_result.get("params", {})
    confidence = ai_result.get("confidence", 0.0)
    message = ai_result.get("user_friendly_message", "")
    
    # Handle non-banking requests
    if intent == "non_banking":
        return {
            "action": "rejected",
            "intent": "non_banking",
            "message": message,
            "confidence": confidence
        }
    
    # Handle unclear requests
    if intent == "unclear":
        return {
            "action": "clarify",
            "intent": "unclear",
            "message": message,
            "suggestions": ai_result.get("suggestions", []),
            "confidence": confidence
        }
    
    # Handle errors
    if intent == "error":
        return {
            "action": "error",
            "intent": "error",
            "message": message,
            "confidence": 0.0
        }
    
    # Handle valid banking commands
    if intent == "banking":
        validation_error = ai_service.validate_banking_action(action, params)
        if validation_error:
            return {
                "action": "error",
                "message": validation_error,
                "confidence": confidence
            }
        
        try:
            if action == "check_balance":
                banking_service = BankingService(db)
                result = banking_service.get_balance(current_user.username)
                return {
                    "action": "check_balance",
                    "intent": "banking",
                    "data": result,
                    "message": f"Your current account balance is ${result['balance']:.2f}",
                    "confidence": confidence
                }
            
            elif action == "transfer":
                # SECURITY: Require OTP for voice transfers
                print(f"🔐 Transfer detected - OTP verification required")
                
                # Handle transfer by username
                if params.get("recipient_username") and not params.get("recipient_account"):
                    user_info = voice_service.lookup_user_by_username(params["recipient_username"])
                    if not user_info:
                        return {
                            "action": "error",
                            "message": f"User '{params['recipient_username']}' not found.",
                            "confidence": confidence
                        }
                    params["recipient_account"] = user_info["account_number"]
                    recipient_display = f"user {params['recipient_username']}"
                else:
                    recipient_display = params["recipient_account"]
                
                # Generate transaction ID
                transaction_id = str(uuid.uuid4())
                
                # Generate and send OTP
                otp = otp_service.create_otp(current_user.email, transaction_id)
                email_sent = otp_service.send_otp_email(
                    current_user.email,
                    otp,
                    params["amount"],
                    recipient_display
                )
                
                # Store pending transaction in session/cache (simplified)
                # In production, store in database
                from ..main import app
                if not hasattr(app.state, 'pending_transactions'):
                    app.state.pending_transactions = {}
                
                app.state.pending_transactions[transaction_id] = {
                    'sender_username': current_user.username,
                    'recipient_account': params["recipient_account"],
                    'amount': params["amount"],
                    'description': f"Voice transfer: {command.transcript}",
                    'expires_at': datetime.now() + timedelta(minutes=5)
                }
                
                otp_message = f"OTP sent to your email ({current_user.email})" if email_sent else f"OTP: {otp} (SMTP not configured - for testing only)"
                
                return {
                    "action": "transfer_pending",
                    "intent": "banking",
                    "message": f"Transfer of ${params['amount']:.2f} to {recipient_display} requires verification. {otp_message}. Please provide the OTP to complete the transaction.",
                    "requires_otp": True,
                    "transaction_id": transaction_id,
                    "data": {
                        "amount": params["amount"],
                        "recipient": recipient_display,
                        "otp_sent": email_sent
                    },
                    "confidence": confidence
                }
            
            elif action == "transaction_history":
                banking_service = BankingService(db)
                limit = params.get("limit", 10)
                result = banking_service.get_transaction_history(current_user.username, limit)
                
                transactions_data = [
                    {
                        "id": t.id,
                        "type": t.transaction_type,
                        "amount": t.amount,
                        "description": t.description,
                        "timestamp": t.timestamp.isoformat()
                    }
                    for t in result
                ]
                
                return {
                    "action": "transaction_history",
                    "intent": "banking",
                    "data": {"transactions": transactions_data},
                    "message": f"Here are your last {len(result)} transactions",
                    "confidence": confidence
                }
            
            elif action == "help":
                commands = voice_service.get_available_commands()
                return {
                    "action": "help",
                    "intent": "banking",
                    "data": {"commands": commands},
                    "message": "I can help you with checking balance, transferring money, and viewing transactions.",
                    "confidence": confidence
                }
        
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            raise HTTPException(status_code=500, detail=str(e))
    
    return {
        "action": "unknown",
        "message": "I couldn't understand that command.",
        "confidence": 0.0
    }


@router.post("/verify-otp")
def verify_transfer_otp(
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
        raise HTTPException(status_code=404, detail="Transaction not found or expired")
    
    pending_tx = app.state.pending_transactions[verification.transaction_id]
    
    # Check if expired
    if datetime.now() > pending_tx['expires_at']:
        del app.state.pending_transactions[verification.transaction_id]
        raise HTTPException(status_code=400, detail="Transaction expired. Please initiate a new transfer.")
    
    # Verify OTP
    is_valid, otp_message = otp_service.verify_otp(verification.transaction_id, verification.otp)
    
    if not is_valid:
        raise HTTPException(status_code=400, detail=otp_message)
    
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
        
        return {
            "action": "transfer",
            "message": f"✅ Transfer successful! ${pending_tx['amount']:.2f} sent. New balance: ${result['sender']['new_balance']:.2f}",
            "data": result
        }
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Transfer failed: {str(e)}")
