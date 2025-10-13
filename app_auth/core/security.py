"""
core/security.py
Módulo de seguridad para el Auth Service.
Incluye:
- Generación y carga de claves RSA (private/public)
- Creación y validación de tokens JWT (RS256)
- Hashing y verificación de contraseñas con bcrypt
"""

import os
import jwt
from datetime import datetime, timedelta
from passlib.context import CryptContext
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from core.config import settings


# ---------------------- Hashing ----------------------
pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")


def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)


def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)


# ---------------------- Claves RSA ----------------------
def ensure_rsa_keys():
    private_path = settings.PRIVATE_KEY_PATH
    public_path = settings.PUBLIC_KEY_PATH

    if os.path.exists(private_path) and os.path.exists(public_path):
        with open(private_path, "rb") as f:
            private_pem = f.read()
        with open(public_path, "rb") as f:
            public_pem = f.read()
        return private_pem, public_pem

    # Generar nuevo par de claves
    key = rsa.generate_private_key(public_exponent=65537, key_size=2048)
    private_pem = key.private_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PrivateFormat.TraditionalOpenSSL,
        encryption_algorithm=serialization.NoEncryption(),
    )
    public_pem = key.public_key().public_bytes(
        encoding=serialization.Encoding.PEM,
        format=serialization.PublicFormat.SubjectPublicKeyInfo,
    )

    with open(private_path, "wb") as f:
        f.write(private_pem)
    with open(public_path, "wb") as f:
        f.write(public_pem)

    # Notificación simple
    digest = hashes.Hash(hashes.SHA256())
    digest.update(public_pem)
    fingerprint = digest.finalize().hex()
    print("=== NEW CERTIFICATE GENERATED ===")
    print(f"Public key saved to: {public_path}")
    print(f"Fingerprint: {fingerprint}")

    return private_pem, public_pem


PRIVATE_PEM, PUBLIC_PEM = ensure_rsa_keys()


# ---------------------- JWT helpers ----------------------
def create_access_token(subject: str, roles: list[str], expires_delta: timedelta | None = None) -> str:
    now = datetime.now()
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.JWT_EXP_MINUTES)

    payload = {
        "sub": subject,
        "roles": roles,
        "iat": now,
        "exp": now + expires_delta,
    }

    token = jwt.encode(payload, PRIVATE_PEM, algorithm=settings.ALGORITHM)
    return token


def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, PUBLIC_PEM, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token expired")
    except jwt.PyJWTError:
        raise ValueError("Invalid token")
