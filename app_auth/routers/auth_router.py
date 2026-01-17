import logging
import socket
import os
from fastapi.security import HTTPBasic, HTTPBasicCredentials
from fastapi import APIRouter, Depends
from dependencies import get_current_user
from sql import schemas, models
from services import auth_service
from fastapi.responses import PlainTextResponse

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/auth",
    tags=["Auth"],
    responses={404: {"description": "No encontrado"}},
)
security = HTTPBasic()

@router.get("/health", include_in_schema=False)
async def health() -> dict:
    """ Healthcheck LIVENESS (para Consul / balanceadores). """
    return {"detail": "OK"}

@router.post("/login", summary="Login con Basic Auth", response_model=dict)
async def login(credentials: HTTPBasicCredentials = Depends(security)):
    """
    Login con usuario y contraseña.
    Devuelve access_token + refresh_token.
    """
    return await auth_service.login_service(credentials.username, credentials.password)

@router.post("/refresh", summary="Renovar access token con refresh token")
async def refresh_token(refresh_token: schemas.RefreshRequest):
    """
    Recibe un refresh token válido y devuelve un nuevo access token.
    """

    return await auth_service.refresh_token_service(refresh_token_request=refresh_token)

@router.get("/public-key", summary="Obtener la clave pública actual", response_class=PlainTextResponse)
def get_public_key():
    return auth_service.get_public_key_service()