from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from ..database import get_db
from ..schemas.user import UserCreate, UserLogin, UserResponse, Token, PasswordReset
from ..services.auth_service import AuthService
from ..dependencies import get_current_user
from ..models.user import User
from pydantic import BaseModel
from typing import Optional


router = APIRouter(prefix="/api/auth", tags=["Authentication"])


class PasswordChange(BaseModel):
    old_password: str
    new_password: str


class ProfileUpdate(BaseModel):
    full_name: Optional[str] = None


class AccountDelete(BaseModel):
    password: str


# FIXED: Create service instance in each route
@router.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED)
def register(
    user: UserCreate, 
    db: Session = Depends(get_db)
):
    """
    Register a new user
    """
    auth_service = AuthService(db)
    
    # Validate user data
    validation_error = auth_service.validate_user_data(user)
    if validation_error:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail=validation_error
        )
    
    # Create user
    try:
        new_user = auth_service.create_user(user)
        return new_user
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Failed to create user. Please try again."
        )


@router.post("/login", response_model=Token)
def login(
    credentials: UserLogin, 
    db: Session = Depends(get_db)
):
    """
    Login with username and password
    """
    auth_service = AuthService(db)
    
    # Authenticate user
    user = auth_service.authenticate_user(credentials.username, credentials.password)
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    # Create access token
    access_token = auth_service.create_token_for_user(user)
    
    return {
        "access_token": access_token, 
        "token_type": "bearer"
    }


@router.post("/forgot-password")
def forgot_password(
    data: PasswordReset, 
    db: Session = Depends(get_db)
):
    """
    Request password reset
    """
    auth_service = AuthService(db)
    
    reset_data = auth_service.initiate_password_reset(data.email)
    
    if not reset_data:
        return {
            "message": "If the email exists, reset instructions will be sent"
        }
    
    return {
        "message": "Reset token generated",
        "token": reset_data["token"],
        "email": reset_data["email"]
    }


@router.post("/reset-password")
def reset_password(
    email: str, 
    new_password: str, 
    db: Session = Depends(get_db)
):
    """
    Reset user password with new password
    """
    auth_service = AuthService(db)
    
    try:
        success = auth_service.reset_password(email, new_password)
        
        if not success:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND, 
                detail="User not found"
            )
        
        return {"message": "Password reset successful"}
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/change-password")
def change_password(
    password_data: PasswordChange,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Change password for authenticated user
    """
    auth_service = AuthService(db)
    
    try:
        success = auth_service.change_password(
            current_user.username,
            password_data.old_password,
            password_data.new_password
        )
        
        if success:
            return {"message": "Password changed successfully"}
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/check-username/{username}")
def check_username_availability(
    username: str,
    db: Session = Depends(get_db)
):
    """
    Check if username is available for registration
    """
    auth_service = AuthService(db)
    is_taken = auth_service.username_exists(username)
    
    return {
        "username": username,
        "available": not is_taken,
        "message": "Username is already taken" if is_taken else "Username is available"
    }


@router.get("/check-email/{email}")
def check_email_availability(
    email: str,
    db: Session = Depends(get_db)
):
    """
    Check if email is available for registration
    """
    auth_service = AuthService(db)
    is_taken = auth_service.email_exists(email)
    
    return {
        "email": email,
        "available": not is_taken,
        "message": "Email is already registered" if is_taken else "Email is available"
    }


@router.get("/profile", response_model=UserResponse)
def get_profile(
    current_user: User = Depends(get_current_user)
):
    """
    Get current user's profile information
    """
    return current_user


@router.put("/profile", response_model=UserResponse)
def update_profile(
    profile_data: ProfileUpdate,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Update user profile information
    """
    auth_service = AuthService(db)
    
    try:
        updated_user = auth_service.update_user_profile(
            current_user.username,
            full_name=profile_data.full_name
        )
        return updated_user
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.get("/statistics")
def get_user_statistics(
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Get user account statistics
    """
    auth_service = AuthService(db)
    
    try:
        stats = auth_service.get_user_statistics(current_user.username)
        return stats
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=str(e)
        )


@router.delete("/account")
def delete_account(
    delete_data: AccountDelete,
    current_user: User = Depends(get_current_user),
    db: Session = Depends(get_db)
):
    """
    Delete user account
    """
    auth_service = AuthService(db)
    
    try:
        success = auth_service.delete_user_account(
            current_user.username,
            delete_data.password
        )
        
        if success:
            return {
                "message": "Account deleted successfully",
                "username": current_user.username
            }
    
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.post("/logout")
def logout(current_user: User = Depends(get_current_user)):
    """
    Logout current user
    """
    return {
        "message": "Logged out successfully",
        "username": current_user.username
    }


@router.get("/verify-token")
def verify_token(current_user: User = Depends(get_current_user)):
    """
    Verify if the current token is valid
    """
    return {
        "valid": True,
        "username": current_user.username,
        "email": current_user.email
    }
