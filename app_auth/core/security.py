import os
import time
import fcntl
from datetime import datetime, timedelta, timezone
import jwt
from passlib.context import CryptContext
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from core.config import settings
import secrets


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def ensure_rsa_keys():
    private_path = settings.PRIVATE_KEY_PATH
    public_path = settings.PUBLIC_KEY_PATH
    
    # Crear directorio keys si no existe
    keys_dir = os.path.dirname(private_path)
    if keys_dir and not os.path.exists(keys_dir):
        os.makedirs(keys_dir, exist_ok=True)
    
    lock_file = os.path.join(keys_dir if keys_dir else ".", ".keys.lock")
    
    # Usar file locking para evitar race conditions entre réplicas
    with open(lock_file, "w") as lock:
        fcntl.flock(lock.fileno(), fcntl.LOCK_EX)
        try:
            # Verificar de nuevo después de obtener el lock
            if os.path.exists(private_path) and os.path.exists(public_path):
                time.sleep(0.1)  # Esperar a que los archivos estén completamente escritos
                with open(private_path, "rb") as f:
                    private_pem = f.read()
                with open(public_path, "rb") as f:
                    public_pem = f.read()
                print("=== USING EXISTING RSA KEYS ===")
                return private_pem, public_pem

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
        finally:
            fcntl.flock(lock.fileno(), fcntl.LOCK_UN)


PRIVATE_PEM, PUBLIC_PEM = ensure_rsa_keys()


def create_access_token(subject: str, user_id: str, rol: str, expires_delta: timedelta | None = None) -> str:
    now = datetime.now(timezone.utc)
    if expires_delta is None:
        expires_delta = timedelta(minutes=settings.JWT_EXP_MINUTES)

    payload = {
        "sub": subject,
        "user_id": user_id,
        "rol": rol,
        "iat": now,
        "exp": now + expires_delta,
    }

    token = jwt.encode(payload, PRIVATE_PEM, algorithm=settings.ALGORITHM)
    return token


def create_refresh_token():
    return secrets.token_urlsafe(64)
        
def decode_token(token: str) -> dict:
    try:
        payload = jwt.decode(token, PUBLIC_PEM, algorithms=[settings.ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise ValueError("Token expired")
    except jwt.InvalidSignatureError:
        raise ValueError("Invalid signature – check your RSA keys")
    except jwt.InvalidAlgorithmError:
        raise ValueError("Algorithm mismatch – check settings.ALGORITHM")
    except jwt.DecodeError:
        raise ValueError("Malformed token")
    except Exception as e:
        raise ValueError(f"Unexpected error decoding token: {str(e)}")

def read_public_key() -> str | None:
    return PUBLIC_PEM