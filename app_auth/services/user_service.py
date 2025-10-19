from sql import crud, schemas, models
from dependencies import get_db
from fastapi import status, HTTPException
from core.security import get_password_hash
from typing import List

async def register_user_service(new_user: schemas.UserCreate) -> schemas.UserResponse:
    try:
        async for db in get_db():
            existing = await crud.get_user_by_username(db=db, username=new_user.username)
            if existing:
                raise HTTPException(status_code=400, detail="El nombre de usuario ya existe.")
            hashed_pw = get_password_hash(new_user.password)
            new_user.password = hashed_pw
            db_user = await crud.create_user_from_schema(db=db, user=new_user)
            user_response = schemas.UserResponse(
                username=db_user.username,
                id=db_user.id,
                role_id=db_user.role_id
            )
            return user_response
    except Exception as exc:
        print(exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno en el servicio de creación del usuario",
            headers={"WWW-Authenticate": "Basic"},
        )

async def get_user_list_service() -> List[schemas.UserResponse]:
    try:
        async for db in get_db():
            user_list = await crud.get_list(db=db, model=models.User)
            return [
                schemas.UserResponse(
                    id=user.id,
                    username=user.username,
                    role_id=user.role_id
                )
                for user in user_list
            ]
    except Exception as exc:
        print(exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno en el servicio al extraer los usuarios",
            headers={"WWW-Authenticate": "Basic"},
        )

async def get_user_service(user_id) -> schemas.UserResponse:
    try:
        async for db in get_db():
            db_user = await crud.get_user(db=db, user_id=user_id)
            if not db_user:
                return None
            return schemas.UserResponse(
                id=db_user.id,
                username=db_user.username,
                role_id=db_user.role_id
            )
    except Exception as exc:
        print(exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno en el servicio al extraer el usuario",
            headers={"WWW-Authenticate": "Basic"},
        )

async def update_user_service(user_id, user: schemas.UserUpdate):
    try:
        async for db in get_db():
            db_user = await crud.update_user(db=db, user_id=user_id, user_update=user)
            if not db_user:
                raise HTTPException(status_code=400, detail="El usuario no existe.")
            return db_user
    except Exception as exc:
        print(exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno en el servicio al editar el usuario",
            headers={"WWW-Authenticate": "Basic"},
        )   

async def delete_user_service(user_id):
    try:
        async for db in get_db():
            db_user = await crud.delete_element_by_id(db=db, model=models.User, element_id=user_id)
            if not db_user:
                raise HTTPException(status_code=400, detail="El usuario no existe.")
            return db_user
    except Exception as exc:
        print(exc)
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno en el servicio al editar el usuario",
            headers={"WWW-Authenticate": "Basic"},
        )      