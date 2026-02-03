from fastapi import APIRouter, Depends, HTTPException, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session
import requests
from urllib.parse import urlencode

from app.api.deps import get_db
from app.core.config import settings
from app.crud.user import get_user_by_steam_id, create_user
from app.schemas.user import UserCreate
from app.core.security import create_access_token, create_refresh_token

router = APIRouter()

STEAM_OPENID_URL = "https://steamcommunity.com/openid/login"


@router.get("/login")
def steam_login(request: Request):
    """Redirect to Steam OpenID login"""
    params = {
        "openid.ns": "http://specs.openid.net/auth/2.0",
        "openid.mode": "checkid_setup",
        "openid.return_to": settings.STEAM_RETURN_URL,
        "openid.realm": request.base_url._url.rstrip('/'),
        "openid.identity": "http://specs.openid.net/auth/2.0/identifier_select",
        "openid.claimed_id": "http://specs.openid.net/auth/2.0/identifier_select"
    }

    auth_url = f"{STEAM_OPENID_URL}?{urlencode(params)}"
    return RedirectResponse(auth_url)


@router.get("/callback")
async def steam_callback(request: Request, db: Session = Depends(get_db)):
    """Handle Steam OpenID callback"""
    # Verify the response
    params = dict(request.query_params)
    params["openid.mode"] = "check_authentication"

    response = requests.post(STEAM_OPENID_URL, data=params)

    if "is_valid:true" not in response.text:
        raise HTTPException(status_code=400, detail="Invalid Steam authentication")

    # Extract Steam ID from claimed_id
    claimed_id = params.get("openid.claimed_id", "")
    steam_id = claimed_id.split("/")[-1]

    if not steam_id or not steam_id.isdigit():
        raise HTTPException(status_code=400, detail="Invalid Steam ID")

    # Get Steam user info
    steam_api_url = f"http://api.steampowered.com/ISteamUser/GetPlayerSummaries/v0002/?key={settings.STEAM_API_KEY}&steamids={steam_id}"
    steam_response = requests.get(steam_api_url)
    steam_data = steam_response.json()

    if not steam_data.get("response", {}).get("players"):
        raise HTTPException(status_code=400, detail="Could not fetch Steam profile")

    player = steam_data["response"]["players"][0]

    # Get or create user
    user = get_user_by_steam_id(db, steam_id)

    if not user:
        # Create new user with Steam data
        username = player.get("personaname", f"steam_user_{steam_id}")
        email = f"{steam_id}@steam.placeholder"

        user_create = UserCreate(
            email=email,
            username=username,
            password="steam_oauth_user_no_password"
        )
        user = create_user(db, user_create)

        # Update Steam-specific fields directly on the model
        user.steam_id = steam_id
        user.steam_profile_url = player.get("profileurl")
        user.avatar_url = player.get("avatarfull")
        db.commit()
        db.refresh(user)

    # Create JWT tokens
    access_token = create_access_token(data={"sub": user.email})
    refresh_token = create_refresh_token(data={"sub": user.email})

    # Redirect to frontend with tokens
    frontend_url = f"{settings.FRONTEND_URL}/auth/callback?access_token={access_token}&refresh_token={refresh_token}"
    return RedirectResponse(frontend_url)
