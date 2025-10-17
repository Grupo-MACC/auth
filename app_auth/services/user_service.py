from sql import crud, schemas
from dependencies import get_db
from fastapi import status, HTTPException
from core.security import get_password_hash

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