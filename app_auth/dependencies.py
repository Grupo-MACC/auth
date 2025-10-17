# -*- coding: utf-8 -*-
"""Application dependency injector."""
import logging
from fastapi import Depends, HTTPException, status
from fastapi.security import HTTPAuthorizationCredentials, HTTPBearer
from sqlalchemy.orm import Session
from core.security import decode_token
from sql.models import User
from sql import crud

auth_scheme = HTTPBearer()

logger = logging.getLogger(__name__)


# Database #########################################################################################
async def get_db():
    """Generates database sessions and closes them when finished."""
    from sql.database import SessionLocal  # pylint: disable=import-outside-toplevel
    logger.debug("Getting database SessionLocal")
    db = SessionLocal()
    try:
        yield db
        await db.commit()
    except:
        await db.rollback()
    finally:
        await db.close()

async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(auth_scheme),
    db: Session = Depends(get_db),
) -> User:
    """
    Decodifica el JWT y obtiene el usuario actual desde la base de datos.
    """
    token = credentials.credentials

    try:
        payload = decode_token(token) 
    except ValueError:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")

    username = payload.get("sub")
    if not username:
        raise HTTPException(status_code=status.HTTP_401_UNAUTHORIZED, detail="Token inválido")

    user = await crud.get_user_by_username(db=db, username=username)
    if not user:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Usuario no encontrado")

    return user
