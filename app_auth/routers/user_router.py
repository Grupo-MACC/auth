import logging
from fastapi import APIRouter, Depends, HTTPException
from dependencies import get_current_user
from sql import schemas, models
from services import user_service

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/user",
    tags=["Users"],
    responses={404: {"description": "No encontrado"}},
)

@router.get(
    "/health",
    summary="Health check endpoint",
    response_model=schemas.Message,
)
async def health_check():
    """Endpoint to check if everything started correctly."""
    logger.debug("GET '/user/health' endpoint called.")
    return {
        "detail": "OK"
    }

@router.post("/user", response_model=schemas.UserResponse, summary="Registrar nuevo usuario (solo admin)")
async def register_user(
    new_user: schemas.UserCreate,
    current_user: models.User = Depends(get_current_user),
):
    """
    Registrar un nuevo usuario (solo admins pueden hacerlo).
    """
    # Verificar rol admin
    if current_user.role_id != 1:
        raise HTTPException(status_code=403, detail="No autorizado. Se requiere rol admin.")

    return await user_service.register_user_service(new_user=new_user)