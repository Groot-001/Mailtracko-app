
from cryptography.fernet import Fernet

from src.core.config.settings import config

_fernet = Fernet(config.SECRET_ENCRYPTION_KEY.encode())


def encrypt(plain_text: str) -> str:
    if not plain_text:
        return ""
    return _fernet.encrypt(plain_text.encode()).decode()


def decrypt(cipher_text: str) -> str:
    if not cipher_text:
        return ""
    return _fernet.decrypt(cipher_text.encode()).decode()