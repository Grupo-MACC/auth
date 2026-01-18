import logging
from fastapi import APIRouter, Depends, HTTPException
from dependencies import get_current_user
from sql import schemas, models
from services import user_service
from typing import List

logger = logging.getLogger(__name__)
router = APIRouter(
    prefix="/user",
    tags=["Users"],
    responses={404: {"description": "No encontrado"}},
)

@router.get("/health", include_in_schema=False)
async def health() -> dict:
    """ Healthcheck LIVENESS (para Consul / balanceadores). """
    return {"detail": "OK"}

@router.post("", response_model=schemas.UserResponse, summary="Registrar nuevo usuario (solo admin)")
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

@router.get("", response_model=List[schemas.UserResponse])
async def read_users(
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role_id != 1:
        raise HTTPException(status_code=403, detail="No autorizado. Se requiere rol admin.")
    
    return await user_service.get_user_list_service()

@router.get("/{user_id}", response_model=List[schemas.UserResponse])
async def read_user(
    user_id: int,
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role_id != 1:
        raise HTTPException(status_code=403, detail="No autorizado. Se requiere rol admin.")
    
    return await user_service.get_user_service(user_id=user_id)

@router.put("/{user_id}", response_model=schemas.UserResponse)
async def update_user(
    user_id: int,
    user: schemas.UserUpdate,
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role_id != 1:
        raise HTTPException(status_code=403, detail="No autorizado. Se requiere rol admin.")
    
    return await user_service.update_user_service(user_id=user_id, user=user)

@router.delete("/{user_id}", response_model=schemas.UserResponse)
async def update_user(
    user_id: int,
    current_user: models.User = Depends(get_current_user)
):
    if current_user.role_id != 1:
        raise HTTPException(status_code=403, detail="No autorizado. Se requiere rol admin.")
    
    return await user_service.delete_user_service(user_id=user_id)