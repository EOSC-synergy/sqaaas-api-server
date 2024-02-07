# SPDX-FileCopyrightText: Copyright contributors to the Software Quality Assurance as a Service (SQAaaS) project <sqaaas@ibergrid.eu>
# SPDX-FileContributor: Pablo Orviz <orviz@ifca.unican.es>
#
# SPDX-License-Identifier: GPL-3.0-only

import logging
import os

from cryptography.fernet import Fernet

from openapi_server import config

KEY_ENCRYPTION_PATH = config.get("key_encryption_path", fallback=".fernet_key")

logger = logging.getLogger("sqaaas.api.controller")


def encrypt_str(string, to_json=True):
    """Returns the encrypted string.

    :param string: The string to encrypt.
    :param to_json: Whether the string will be stored in a JSON file (it needs to be
        decoded).
    """
    f = _get_fernet_key()
    string_byte = string.encode("utf-8")
    string_encrypted = f.encrypt(string_byte)
    if to_json:
        string_encrypted = string_encrypted.decode("utf-8")

    return string_encrypted


def decrypt_str(string, from_json=True):
    """Returns the text representation of the encrypted string.

    :param string: The string to decrypt.
    :param from_json: Whether the string comes from a JSON file (it needs to be
        encoded).
    """
    f = _get_fernet_key()
    if from_json:
        string = string.encode("utf-8")
    string_decrypted = f.decrypt(string)

    return string_decrypted.decode("utf-8")


def _get_fernet_key():
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
    with open(path, "wb") as fname:
        fname.write(key)

    return Fernet(key)


def _load_fernet_key(path):
    """Load an existing Fernet key.

    Returns the key.

    :param path: Fernet key location
    """
    with open(path, "rb") as fname:
        key = fname.read()

    return Fernet(key)
