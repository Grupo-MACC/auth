# sql/init_db.py
import logging
from sqlalchemy.future import select
from sqlalchemy.ext.asyncio import AsyncSession
from core.security import get_password_hash
from core.config import settings
from sql import models

logger = logging.getLogger(__name__)

async def init_db(session: AsyncSession):
    """Crea roles base y usuario admin si no existen."""
    logger.info("🔧 Inicializando datos base...")

    # --- Crear roles base ---
    for role_name in ["admin", "user"]:
        result = await session.execute(select(models.Role).where(models.Role.name == role_name))
        role = result.scalar_one_or_none()
        if not role:
            role = models.Role(name=role_name, description=f"Rol {role_name}")
            session.add(role)
            logger.info(f"✅ Rol '{role_name}' creado.")

    await session.commit()

    # --- Crear usuario admin ---
    result = await session.execute(
        select(models.User).where(models.User.username == settings.ADMIN_USERNAME)
    )
    admin_user = result.scalar_one_or_none()

    if not admin_user:
        result = await session.execute(select(models.Role).where(models.Role.name == "admin"))
        admin_role = result.scalar_one_or_none()

        if not admin_role:
            logger.warning("Rol 'admin' no encontrado. Creándolo...")
            admin_role = models.Role(name="admin", description="Superusuario")
            session.add(admin_role)
            await session.commit()

        hashed_pw = get_password_hash(settings.ADMIN_PASSWORD)
        admin_user = models.User(
            username=settings.ADMIN_USERNAME,
            hashed_password=hashed_pw,
            role_id=admin_role.id,
        )
        session.add(admin_user)
        await session.commit()
        logger.info(f"👑 Usuario admin '{settings.ADMIN_USERNAME}' creado.")
    else:
        logger.info("👑 Usuario admin ya existente.")
