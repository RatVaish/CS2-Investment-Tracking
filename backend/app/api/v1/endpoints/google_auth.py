from fastapi import APIRouter, Depends, HTTPException, status
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
from google.oauth2 import id_token
from google.auth.transport import requests as google_requests
import requests

from app.api.deps import get_db
from app.core.config import settings
from app.crud.user import get_user_by_email, create_user
from app.schemas.user import UserCreate
from app.core.security import create_access_token, create_refresh_token

router = APIRouter()


@router.get("/login")
def google_login():
    """Redirect to Google OAuth login"""
    google_auth_url = (
        f"https://accounts.google.com/o/oauth2/v2/auth?"
        f"client_id={settings.GOOGLE_CLIENT_ID}&"
        f"redirect_uri={settings.GOOGLE_REDIRECT_URI}&"
        f"response_type=code&"
        f"scope=openid%20email%20profile&"
        f"access_type=offline"
    )
    return RedirectResponse(google_auth_url)


@router.get("/callback")
async def google_callback(code: str, db: Session = Depends(get_db)):
    """Handle Google OAuth callback"""
    # Exchange code for tokens
    token_url = "https://oauth2.googleapis.com/token"
    token_data = {
        "code": code,
        "client_id": settings.GOOGLE_CLIENT_ID,
        "client_secret": settings.GOOGLE_CLIENT_SECRET,
        "redirect_uri": settings.GOOGLE_REDIRECT_URI,
        "grant_type": "authorization_code"
    }

    token_response = requests.post(token_url, data=token_data)
    if token_response.status_code != 200:
        raise HTTPException(status_code=400, detail="Failed to get token from Google")

    tokens = token_response.json()
    id_token_str = tokens.get("id_token")

    # Verify and decode ID token
    try:
        user_info = id_token.verify_oauth2_token(
            id_token_str,
            google_requests.Request(),
            settings.GOOGLE_CLIENT_ID
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=f"Invalid token: {str(e)}")

    # Get or create user
    email = user_info.get("email")
    user = get_user_by_email(db, email)

    if not user:
        # Create new user
        username = email.split("@")[0]  # Use email prefix as username
        user_create = UserCreate(
            email=email,
            username=username,
            password="oauth_user_no_password"  # OAuth users don't have passwords
        )
        user = create_user(db, user_create)

    # Create JWT tokens
    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})

    # Redirect to frontend with tokens
    frontend_url = f"{settings.FRONTEND_URL}/auth/callback?access_token={access_token}&refresh_token={refresh_token}"
    return RedirectResponse(frontend_url)
