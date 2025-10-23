from datetime import timedelta, timezone, datetime
from sql import crud, schemas
from dependencies import get_db
from fastapi import status, HTTPException
from core.security import (
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
    read_public_key
)

async def login_service(username: str, password: str):
    try:
        async for db in get_db():
            # Buscar usuario por nombre
            user = await crud.get_user_by_username(db=db, username=username)
            if not user or not verify_password(password, user.hashed_password):
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Credenciales inválidas",
                    headers={"WWW-Authenticate": "Basic"},
                )

            # Buscar rol del usuario
            roles = await crud.get_role(db=db, role_id=user.role_id)
            if not roles:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Rol inválido",
                    headers={"WWW-Authenticate": "Basic"},
                )

            rol_name = roles.name

            # Crear tokens
            access_token = create_access_token(
                subject=user.username,
                user_id=user.id,
                rol=rol_name,
                expires_delta=timedelta(minutes=15),
            )

            refresh_token = create_refresh_token()
            
            db_refresh_token = await crud.create_refresh_token_from_schema(
                db=db, refresh_token=schemas.RefreshTokenCreate(
                    user_id=user.id,
                    token=refresh_token,
                    expires_at=datetime.now(timezone.utc) + timedelta(days=7)
                )
            )
            
            if not db_refresh_token:
                raise HTTPException(
                status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                detail="Error interno en el servicio de login",
                headers={"WWW-Authenticate": "Basic"},
                )

            # Devolvemos aquí dentro para evitar que se cierre la sesión antes
            return {
                "access_token": access_token,
                "refresh_token": refresh_token,
                "token_type": "bearer"
            }

    except HTTPException:
        # Propagar los errores HTTP específicos sin modificarlos
        raise
    except Exception as exc:
        print(f"Error en login_service: {exc}")
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail="Error interno en el servicio de login",
            headers={"WWW-Authenticate": "Basic"},
        )

async def refresh_token_service(refresh_token_request: schemas.RefreshRequest):
    try:
        async for db in get_db():
            db_token = await crud.get_refresh_token(db=db, token_str=refresh_token_request.refresh_token_str)
            if not db_token:
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token inválido")
            if db_token.revoked or db_token.expires_at.replace(tzinfo=timezone.utc) < datetime.now(timezone.utc):
                raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Refresh token expirado o revocado")
            user = await crud.get_user(db=db, user_id=db_token.user_id)
            if not user:
                raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")
            role = await crud.get_role(db=db, role_id=user.role_id)
            if not role:
                raise HTTPException(
                    status_code=status.HTTP_401_UNAUTHORIZED,
                    detail="Rol inválido",
                    headers={"WWW-Authenticate": "Basic"},
                )

            new_access_token = create_access_token(
                subject=user.username,
                user_id=user.id,
                rol=role.name,
                expires_delta=timedelta(minutes=15)
            )
    except Exception as exc:
        print(exc)
        raise HTTPException(status_code=500, detail="Error interno en el servicio de refresh")

    return {"access_token": new_access_token, "token_type": "bearer"}

def get_public_key_service() -> str | None:
    return read_public_key()