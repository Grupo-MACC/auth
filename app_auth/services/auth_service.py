from datetime import timedelta
from sql import crud
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
                rol=rol_name,
                expires_delta=timedelta(minutes=15),
            )

            refresh_token = create_refresh_token(
                subject=user.username,
                rol=rol_name,
                expires_delta=timedelta(days=7),
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

async def refresh_token_service(refresh_token):
    try:
        payload = decode_token(refresh_token)
    except ValueError:
        raise HTTPException(status_code=401, detail="Refresh token inválido")

    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=401, detail="Refresh token inválido")
    try:
        async for db in get_db():
            user = crud.get_user_by_username(db=db, username=username)
            if not user:
                raise HTTPException(status_code=404, detail="Usuario no encontrado")
    except Exception as exc:
        print(exc)
        raise HTTPException(status_code=404, detail="Usuario no encontrado")

    roles = await crud.get_role(db=db, role_id=user.role_id)
    if not roles:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Rol inválido",
            headers={"WWW-Authenticate": "Basic"},
        )
    rol_name = roles.name
    new_access_token = create_access_token(subject=username, rol=rol_name, expires_delta=timedelta(minutes=15))
    return {"access_token": new_access_token, "token_type": "bearer"}

def get_public_key_service() -> str | None:
    return read_public_key()