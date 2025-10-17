# -*- coding: utf-8 -*-
"""Functions that interact with the database."""
import logging
from datetime import datetime
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.future import select
from . import models, schemas

logger = logging.getLogger(__name__)

async def create_user_from_schema(db: AsyncSession, user: schemas.UserCreate):
    db_user = models.User(
        username=user.username,
        hashed_password=user.password,
        role_id=user.role_id
    )
    db.add(db_user)
    await db.commit()
    await db.refresh(db_user)
    return db_user

async def get_user(db: AsyncSession, user_id):
    return await get_element_by_id(db, models.User, user_id)

async def get_user_by_username(db: AsyncSession, username):
    result = await db.execute(select(models.User).where(models.User.username == username))
    user = result.scalar_one_or_none()
    return user

async def get_role(db: AsyncSession, role_id):
    return await get_element_by_id(db, models.Role, role_id)

# Generic functions ################################################################################
# READ
async def get_list(db: AsyncSession, model):
    """Retrieve a list of elements from database"""
    result = await db.execute(select(model))
    item_list = result.unique().scalars().all()
    return item_list


async def get_list_statement_result(db: AsyncSession, stmt):
    """Execute given statement and return list of items."""
    result = await db.execute(stmt)
    item_list = result.unique().scalars().all()
    return item_list


async def get_element_statement_result(db: AsyncSession, stmt):
    """Execute statement and return a single items"""
    result = await db.execute(stmt)
    item = result.scalar()
    return item


async def get_element_by_id(db: AsyncSession, model, element_id):
    """Retrieve any DB element by id."""
    if element_id is None:
        return None

    element = await db.get(model, element_id)
    return element


# DELETE
async def delete_element_by_id(db: AsyncSession, model, element_id):
    """Delete any DB element by id."""
    element = await get_element_by_id(db, model, element_id)
    if element is not None:
        await db.delete(element)
        await db.commit()
    return element