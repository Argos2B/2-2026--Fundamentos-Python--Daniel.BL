from __future__ import annotations

import secrets
from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, Request, status
from fastapi.responses import HTMLResponse
from sqlalchemy.ext.asyncio import AsyncSession

from ..auth import oauth, create_access_token
from ..crud import create_subscription, create_user, get_current_subscription, get_user_by_email, get_user_by_google_id, get_plan
from ..db import get_db
from ..models import SubscriptionStatus
from ..schemas import AuthenticatedResponse, OAuthUrlResponse, TokenResponse
from ..config import settings

router = APIRouter(prefix="/auth", tags=["auth"])


_token_cache: dict[str, dict[str, Any]] = {}


@router.get("/google/login", response_model=OAuthUrlResponse)
async def google_login(request: Request, state: str = Query(default_factory=lambda: secrets.token_urlsafe(32))):
    redirect_uri = settings.oauth_redirect_uri
    if not settings.google_client_id or not redirect_uri:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Google OAuth no está configurado. Define GOOGLE_CLIENT_ID y OAUTH_REDIRECT_URI.",
        )
    from urllib.parse import urlencode
    params = {
        "client_id": settings.google_client_id,
        "redirect_uri": redirect_uri,
        "response_type": "code",
        "scope": "openid email profile",
        "state": state,
        "access_type": "offline",
        "prompt": "select_account",
    }
    authorization_url = "https://accounts.google.com/o/oauth2/v2/auth?" + urlencode(params)
    _token_cache[state] = {
        "status": "pending",
        "token": None,
        "error": None,
    }
    return {"authorization_url": authorization_url}


@router.get("/google/callback", response_class=HTMLResponse)
async def google_callback(request: Request, state: str | None = None, code: str | None = None, error: str | None = None, db: AsyncSession = Depends(get_db)):
    if error:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=f"Google OAuth error: {error}")
    if not state or not code:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Missing state or code")

    try:
        token = await oauth.google.authorize_access_token(request)
        user_info = await oauth.google.parse_id_token(request, token)
    except Exception as exc:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="No se pudo obtener la información de usuario de Google") from exc

    google_id = user_info.get("sub")
    email = user_info.get("email")
    name = user_info.get("name")
    avatar_url = user_info.get("picture")
    if not google_id or not email:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Google no devolvió información válida del usuario")

    user = await get_user_by_google_id(db, google_id)
    if not user:
        existing = await get_user_by_email(db, email)
        if existing:
            user = existing
            user.google_id = google_id
            db.add(user)
            await db.commit()
            await db.refresh(user)
        else:
            user = await create_user(db, google_id=google_id, email=email, name=name, avatar_url=avatar_url)
            free_plan = await get_plan(db, "FREE")
            if free_plan:
                await create_subscription(db, str(user.id), free_plan.id, SubscriptionStatus.active)

    token = create_access_token({"sub": google_id})

    _token_cache[state] = {
        "status": "complete",
        "token": token,
        "user_id": str(user.id),
    }

    html = """
    <html>
        <head><title>Autenticación completada</title></head>
        <body>
            <h1>Autenticación completada</h1>
            <p>La sesión se ha iniciado correctamente. Puedes volver a la aplicación de escritorio.</p>
        </body>
    </html>
    """
    return HTMLResponse(content=html)


@router.post("/dev-login", response_model=TokenResponse)
async def dev_login(db: AsyncSession = Depends(get_db)) -> TokenResponse:
    dev_email = "dev@localhost"
    user = await get_user_by_email(db, dev_email)
    if not user:
        user = await create_user(
            db,
            google_id=f"dev-{secrets.token_hex(8)}",
            email=dev_email,
            name="Desktop Developer",
            avatar_url=None,
        )
        free_plan = await get_plan(db, "FREE")
        if free_plan:
            await create_subscription(db, str(user.id), free_plan.id, SubscriptionStatus.active)

    token = create_access_token({"sub": user.google_id})
    return {"access_token": token, "token_type": "bearer"}


@router.get("/google/session", response_model=TokenResponse)
async def google_session(state: str = Query(...)) -> TokenResponse:
    result = _token_cache.get(state)
    if not result:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Sesión no encontrada")
    if result["status"] == "pending":
        raise HTTPException(status_code=status.HTTP_202_ACCEPTED, detail="Pendiente")
    if result["status"] == "error":
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=result.get("error", "Error de autenticación"))
    token = result.get("token")
    if not token:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail="Token no disponible")
    return {"access_token": token, "token_type": "bearer"}
