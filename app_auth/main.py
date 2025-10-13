import os
from pydantic import BaseSettings


class Settings(BaseSettings):
    # Base de datos
    DATABASE_URL: str = os.getenv("DATABASE_URL", "sqlite:///./auth.db")


    # JWT y seguridad
    JWT_EXP_MINUTES: int = int(os.getenv("JWT_EXP_MINUTES", 60))
    PRIVATE_KEY_PATH: str = os.getenv("PRIVATE_KEY_PATH", "private.pem")
    PUBLIC_KEY_PATH: str = os.getenv("PUBLIC_KEY_PATH", "public.pem")


    # Usuario administrador inicial
    ADMIN_USERNAME: str = os.getenv("ADMIN_USERNAME", "admin")
    ADMIN_PASSWORD: str = os.getenv("ADMIN_PASSWORD", "adminpass")


class Config:
    env_file = ".env"
    env_file_encoding = "utf-8"


settings = Settings()