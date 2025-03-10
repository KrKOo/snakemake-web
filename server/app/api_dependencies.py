from fastapi import HTTPException, Request

from .auth import AccessToken, AuthClient
from .config import config


async def get_authenticated_user(request: Request) -> str:
    username = request.headers.get("X-Forwarded-Preferred-Username")
    if not username:
        raise HTTPException(status_code=401, detail="User not authenticated")
    return username

async def get_valid_access_token(request: Request) -> AccessToken:
    token_value = request.headers.get("X-Forwarded-Access-Token")
    if not token_value:
        raise HTTPException(status_code=401, detail="No access token provided")
    auth_client = AuthClient(
		config.app.oidc_url,
        config.app.oidc_client_id,
        config.app.oidc_client_secret
    )
    token = AccessToken(token_value, auth_client)
    if token.is_expired() or not token.is_valid():
        raise HTTPException(status_code=401, detail="Invalid access token")
    return token
