import logging
import os

from cryptography.fernet import Fernet
from openapi_server import config


KEY_ENCRYPTION_PATH = config.get('key_encryption_path')

logger = logging.getLogger('sqaaas.api.controller')


def get_fernet_key():
    """Generates and stores a Fernet key for encryption."""
    if not os.path.exists(KEY_ENCRYPTION_PATH):
        f = _generate_fernet_key(KEY_ENCRYPTION_PATH)
    else:
        f = _load_fernet_key(KEY_ENCRYPTION_PATH)

    return f


def _generate_fernet_key(path):
    """Generates and stores a Fernet key for encryption.

    Returns the key.

    :param path: Fernet key location
    """
    key = Fernet.generate_key()
    with open(path, 'wb') as fname:
        fname.write(key)

    return Fernet(key)


def _load_fernet_key(path):
    """Load an existing Fernet key.
    
    Returns the key.

    :param path: Fernet key location
    """
    with open(path, 'rb') as fname:
        key = fname.read()

    return Fernet(key)
