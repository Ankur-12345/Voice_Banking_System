from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from ..database import get_db
from ..services.voice_service import VoiceService
from ..services.banking_service import BankingService
from ..dependencies import get_current_user
from ..models.user import User
from pydantic import BaseModel
from typing import Optional


router = APIRouter(prefix="/api/voice", tags=["Voice Commands"])


class VoiceCommand(BaseModel):
    transcript: str


class VoiceResponse(BaseModel):
    action: str
    data: Optional[dict] = None
    message: Optional[str] = None
    confidence: Optional[float] = None
    suggestions: Optional[list] = None


@router.post("/process", response_model=VoiceResponse)
def process_voice_command(
    command: VoiceCommand,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Process voice command and execute corresponding action
    
    Supports:
    - Balance check
    - Fund transfer
    - Transaction history
    - Help commands
    """
    voice_service = VoiceService(db)
    banking_service = BankingService(db)
    
    # Parse the voice command
    parsed = voice_service.parse_voice_command(command.transcript)
    action = parsed["action"]
    params = parsed["params"]
    
    # Handle help command
    if action == "help":
        available_commands = voice_service.get_available_commands()
        return {
            "action": "help",
            "data": {"commands": available_commands},
            "message": "Here are the available voice commands",
            "confidence": parsed.get("confidence")
        }
    
    # Handle unknown command
    if action == "unknown":
        return {
            "action": "unknown",
            "message": parsed["message"],
            "suggestions": parsed.get("suggestions", []),
            "confidence": parsed.get("confidence")
        }
    
    # Validate command parameters
    validation_error = voice_service.validate_command_params(action, params)
    if validation_error:
        raise HTTPException(status_code=400, detail=validation_error)
    
    # Execute command based on action
    try:
        if action == "check_balance":
            result = banking_service.get_balance(current_user.username)
            return {
                "action": "check_balance",
                "data": result,
                "message": f"Your current balance is ${result['balance']:.2f}",
                "confidence": parsed.get("confidence")
            }
        
        elif action == "transfer":
            result = banking_service.transfer_funds(
                current_user.username,
                params["recipient_account"],
                params["amount"]
            )
            return {
                "action": "transfer",
                "data": result,
                "message": result["message"],
                "confidence": parsed.get("confidence")
            }
        
        elif action == "transaction_history":
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
                "data": {"transactions": transactions_data},
                "message": f"Showing {len(result)} recent transactions",
                "confidence": parsed.get("confidence")
            }
        
        else:
            raise HTTPException(status_code=400, detail="Invalid action")
    
    except ValueError as e:
        raise HTTPException(status_code=400, detail=str(e))
    except Exception as e:
        raise HTTPException(status_code=500, detail="Failed to process command")


@router.get("/commands")
def get_available_commands(db: Session = Depends(get_db)):
    """
    Get list of all available voice commands with examples
    """
    voice_service = VoiceService(db)
    commands = voice_service.get_available_commands()
    return {
        "commands": commands,
        "total": len(commands)
    }


@router.post("/validate")
def validate_command(
    command: VoiceCommand,
    db: Session = Depends(get_db)
):
    """
    Validate and parse voice command without executing it
    
    Useful for testing voice recognition
    """
    voice_service = VoiceService(db)
    parsed = voice_service.parse_voice_command(command.transcript)
    
    if parsed["action"] != "unknown":
        validation_error = voice_service.validate_command_params(
            parsed["action"], 
            parsed["params"]
        )
        
        return {
            "valid": validation_error is None,
            "parsed": parsed,
            "error": validation_error
        }
    
    return {
        "valid": False,
        "parsed": parsed,
        "error": "Command not recognized"
    }
