import os
from datetime import datetime, timedelta, timezone
import jwt
from passlib.context import CryptContext
from cryptography.hazmat.primitives import serialization, hashes
from cryptography.hazmat.primitives.asymmetric import rsa
from core.config import settings
from microservice_chassis_grupo2.core.secrets import SecretsManager
import secrets


pwd_context = CryptContext(schemes=["bcrypt"], deprecated="auto")

# Nombres de los secretos en AWS Secrets Manager
PRIVATE_KEY_SECRET_NAME = os.getenv("JWT_PRIVATE_KEY_SECRET", "auth/jwt/private-key")
PUBLIC_KEY_SECRET_NAME = os.getenv("JWT_PUBLIC_KEY_SECRET", "auth/jwt/public-key")

def verify_password(plain_password: str, hashed_password: str) -> bool:
    return pwd_context.verify(plain_password, hashed_password)

def get_password_hash(password: str) -> str:
    return pwd_context.hash(password)

def save_public_key_to_container(public_pem: bytes):
    """
    Guarda la public key en el contenedor para que otros servicios puedan acceder a ella.
    """
    public_path = settings.PUBLIC_KEY_PATH
    keys_dir = os.path.dirname(public_path)
    
    if keys_dir and not os.path.exists(keys_dir):
        os.makedirs(keys_dir, exist_ok=True)
    
    with open(public_path, "wb") as f:
        f.write(public_pem)
    
    print(f"Public key saved to container: {public_path}")


def ensure_rsa_keys():
    """
    Obtiene las claves RSA desde AWS Secrets Manager.
    Si no existen, las genera y las guarda en Secrets Manager.
    También guarda la public key en el contenedor.
    """
    secrets_manager = SecretsManager()
    
    try:
        # Intentar obtener las claves existentes de Secrets Manager
        private_pem = secrets_manager.get_secret(PRIVATE_KEY_SECRET_NAME).encode()
        public_pem = secrets_manager.get_secret(PUBLIC_KEY_SECRET_NAME).encode()
        print("=== USING EXISTING RSA KEYS FROM SECRETS MANAGER ===")
        
        # Guardar public key en el contenedor
        save_public_key_to_container(public_pem)
        
        return private_pem, public_pem
    except Exception as e:
        print(f"Keys not found in Secrets Manager, generating new ones: {e}")
    
    # Generar nuevas claves RSA
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
    
    # Guardar las claves en Secrets Manager
    try:
        secrets_manager.create_secret(
            name=PRIVATE_KEY_SECRET_NAME,
            secret_value=private_pem.decode(),
            description="JWT Private Key for Auth Service",
            overwrite=True
        )
        secrets_manager.create_secret(
            name=PUBLIC_KEY_SECRET_NAME,
            secret_value=public_pem.decode(),
            description="JWT Public Key for Auth Service",
            overwrite=True
        )
        
        # Notificación
        digest = hashes.Hash(hashes.SHA256())
        digest.update(public_pem)
        fingerprint = digest.finalize().hex()
        print("=== NEW CERTIFICATE GENERATED AND SAVED TO SECRETS MANAGER ===")
        print(f"Fingerprint: {fingerprint}")
    except Exception as e:
        print(f"Warning: Could not save keys to Secrets Manager: {e}")
    
    # Guardar public key en el contenedor
    save_public_key_to_container(public_pem)
    
    return private_pem, public_pem


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