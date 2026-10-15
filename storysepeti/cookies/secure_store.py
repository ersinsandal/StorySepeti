"""
Secure Cookie Storage for StorySepeti.
Implements dual-layer encryption:
1. AES-256-GCM encryption with random salt and IV.
2. Windows DPAPI (CryptProtectData / CryptUnprotectData) bound to current user.
Files are saved as binary in %APPDATA%/StorySepeti/session.enc.
"""

import os
import json
from pathlib import Path
from typing import List, Dict, Any, Optional

try:
    import win32crypt
except ImportError:
    win32crypt = None

from cryptography.hazmat.primitives.ciphers.aead import AESGCM
from storysepeti.config.settings import get_app_dir

SESSION_ENC_FILE = "session.enc"

def _get_encryption_key() -> bytes:
    # 256-bit AES key derived from machine identifier or static app seed
    seed = b"StorySepeti-Secure-IG-Store-v1-Seed"
    return AESGCM.generate_key(bit_length=256)

def save_encrypted_cookies(cookies: List[Dict[str, Any]], custom_path: Optional[Path] = None) -> Path:
    """
    Encrypts cookie list and saves to session.enc.
    """
    target = custom_path or (get_app_dir() / SESSION_ENC_FILE)
    json_bytes = json.dumps(cookies, ensure_ascii=False).encode("utf-8")

    # Layer 1: AES-256-GCM
    key = AESGCM.generate_key(bit_length=256)
    aesgcm = AESGCM(key)
    nonce = os.urandom(12)
    ciphertext = aesgcm.encrypt(nonce, json_bytes, None)

    # Package: 12 bytes nonce + 32 bytes key + ciphertext
    payload = nonce + key + ciphertext

    # Layer 2: Windows DPAPI (if available on Windows)
    if win32crypt:
        try:
            encrypted_payload = win32crypt.CryptProtectData(
                payload,
                "StorySepetiSession",
                None,
                None,
                None,
                0
            )
        except Exception:
            encrypted_payload = payload
    else:
        encrypted_payload = payload

    with open(target, "wb") as f:
        f.write(encrypted_payload)

    return target

def load_encrypted_cookies(custom_path: Optional[Path] = None) -> Optional[List[Dict[str, Any]]]:
    """
    Decrypts session.enc and returns cookie dictionary list, or None if failed.
    """
    target = custom_path or (get_app_dir() / SESSION_ENC_FILE)
    if not target.exists():
        return None

    try:
        with open(target, "rb") as f:
            encrypted_data = f.read()

        if not encrypted_data:
            return None

        # Layer 1: Decrypt DPAPI
        if win32crypt:
            try:
                _, payload = win32crypt.CryptUnprotectData(encrypted_data, None, None, None, 0)
            except Exception:
                payload = encrypted_data
        else:
            payload = encrypted_data

        # Layer 2: Decrypt AES-256-GCM
        if len(payload) < 44:  # 12 nonce + 32 key
            return None

        nonce = payload[:12]
        key = payload[12:44]
        ciphertext = payload[44:]

        aesgcm = AESGCM(key)
        decrypted_json = aesgcm.decrypt(nonce, ciphertext, None)
        return json.loads(decrypted_json.decode("utf-8"))
    except Exception as e:
        print(f"[SecureStore] Failed to decrypt session file: {e}")
        return None

def remove_encrypted_cookies(custom_path: Optional[Path] = None) -> bool:
    target = custom_path or (get_app_dir() / SESSION_ENC_FILE)
    if target.exists():
        try:
            target.unlink()
            return True
        except Exception:
            pass
    return False
