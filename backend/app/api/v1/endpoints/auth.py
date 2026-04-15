from datetime import datetime, timedelta
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session

from app.api.deps import get_db, get_current_user
from app.models.user import User
from app.schemas.auth import (
    RegisterRequest,
    LoginRequest,
    TokenResponse,
    TokenRefreshRequest
)
from app.schemas.user import User as UserSchema
from app.crud.user import (
    get_user_by_email,
    get_user_by_username,
    get_user_by_id,
    create_user,
    update_last_login
)
from app.core.security import (
    verify_password,
    create_token_pair,
    decode_token
)
from app.services.email import generate_otp, send_verification_email

router = APIRouter()


# ---------------------------------------------------------------------------
# Registration
# ---------------------------------------------------------------------------

@router.post("/register", status_code=status.HTTP_201_CREATED)
def register(
        user_data: RegisterRequest,
        db: Session = Depends(get_db)
):
    """Register a new user and send OTP verification email."""
    existing_user = get_user_by_email(db, email=user_data.email)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )

    existing_username = get_user_by_username(db, username=user_data.username)
    if existing_username:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already taken"
        )

    new_user = create_user(db, user=user_data)

    # Generate and store OTP
    code = generate_otp()
    new_user.verification_code = code
    new_user.verification_code_expires_at = datetime.utcnow() + timedelta(minutes=15)
    db.commit()

    send_verification_email(new_user.email, code, new_user.username)

    return {"message": "Registration successful. Check your email for your verification code."}


# ---------------------------------------------------------------------------
# Login
# ---------------------------------------------------------------------------

@router.post("/login", response_model=TokenResponse)
def login(
        login_data: LoginRequest,
        db: Session = Depends(get_db)
):
    user = get_user_by_email(db, email=login_data.email)

    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    if not user.password_hash:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="This account uses Steam login. Please login with Steam."
        )

    if not verify_password(login_data.password, user.password_hash):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect email or password"
        )

    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Account is inactive"
        )

    update_last_login(db, user_id=user.id)
    tokens = create_token_pair(user.id)
    return tokens


# ---------------------------------------------------------------------------
# OTP: Send / Verify
# ---------------------------------------------------------------------------

@router.post("/send-verification-code")
def send_verification_code(
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Send (or resend) a verification OTP to the current user's email."""
    if current_user.email_verified:
        raise HTTPException(status_code=400, detail="Email already verified")

    if not current_user.email or current_user.email.endswith("@steam.placeholder"):
        raise HTTPException(status_code=400, detail="No valid email on account. Please add an email first.")

    # Rate-limit: don't resend if a valid code was issued less than 60 seconds ago
    if (
        current_user.verification_code_expires_at
        and current_user.verification_code_expires_at > datetime.utcnow() + timedelta(minutes=14)
    ):
        raise HTTPException(status_code=429, detail="Please wait before requesting another code")

    code = generate_otp()
    current_user.verification_code = code
    current_user.verification_code_expires_at = datetime.utcnow() + timedelta(minutes=15)
    db.commit()

    sent = send_verification_email(current_user.email, code, current_user.username)
    if not sent:
        raise HTTPException(status_code=500, detail="Failed to send email. Please try again.")

    return {"message": "Verification code sent"}


@router.post("/verify-code")
def verify_code(
        payload: dict,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """Verify the OTP code and mark the user's email as verified."""
    code = payload.get("code", "").strip()

    if current_user.email_verified:
        return {"message": "Already verified"}

    if not current_user.verification_code:
        raise HTTPException(status_code=400, detail="No verification code found. Request a new one.")

    if datetime.utcnow() > current_user.verification_code_expires_at:
        raise HTTPException(status_code=400, detail="Code has expired. Please request a new one.")

    if current_user.verification_code != code:
        raise HTTPException(status_code=400, detail="Incorrect code. Please try again.")

    # Mark verified and clear the code
    current_user.email_verified = True
    current_user.verification_code = None
    current_user.verification_code_expires_at = None
    db.commit()

    # Return fresh tokens so frontend user object updates immediately
    tokens = create_token_pair(current_user.id)
    return {"message": "Email verified", **tokens}


# ---------------------------------------------------------------------------
# Steam users: add email + send OTP
# ---------------------------------------------------------------------------

@router.post("/add-email")
def add_email(
        payload: dict,
        db: Session = Depends(get_db),
        current_user: User = Depends(get_current_user)
):
    """For Steam users — add an email address and trigger OTP send."""
    email = payload.get("email", "").strip().lower()
    if not email or "@" not in email:
        raise HTTPException(status_code=400, detail="Invalid email address")

    existing = get_user_by_email(db, email=email)
    if existing and existing.id != current_user.id:
        raise HTTPException(status_code=400, detail="Email already in use")

    code = generate_otp()
    current_user.email = email
    current_user.email_verified = False
    current_user.verification_code = code
    current_user.verification_code_expires_at = datetime.utcnow() + timedelta(minutes=15)
    db.commit()

    sent = send_verification_email(email, code, current_user.username)
    if not sent:
        raise HTTPException(status_code=500, detail="Failed to send email. Please try again.")

    return {"message": "Email added and verification code sent"}


# ---------------------------------------------------------------------------
# Token refresh / logout
# ---------------------------------------------------------------------------

@router.post("/refresh", response_model=TokenResponse)
def refresh_token(
        refresh_data: TokenRefreshRequest,
        db: Session = Depends(get_db)
):
    payload = decode_token(refresh_data.refresh_token)

    if payload is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    if payload.get("type") != "refresh":
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid token type"
        )

    user_id = payload.get("sub")
    if user_id is None:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid refresh token"
        )

    try:
        user = get_user_by_id(db, user_id=int(user_id))
    except ValueError:
        user = get_user_by_email(db, email=user_id)

    if not user or not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found or inactive"
        )

    tokens = create_token_pair(user.id)
    return tokens


@router.post("/logout")
def logout():
    return {"message": "Successfully logged out. Please delete tokens on client side."}
