"""
DataRelay crypto utilities.

Cloudflare delivers secrets base64-encoded to the worker. The worker calls
atob(MASTER_CURRENT) to get the raw key bytes, so the actual AES key is
base64_decode(MASTER_CURRENT). This module replicates that behaviour.
"""

import os
import re
import base64
from cryptography.hazmat.primitives.ciphers.aead import AESGCM


def decode_key(master: str) -> bytes:
    """Derive the AES key bytes from a MASTER_CURRENT secret value."""
    raw = master.strip()
    try:
        key = base64.b64decode(raw)
        if len(key) in (16, 24, 32):
            return key
    except Exception:
        pass
    key = base64.b64decode(base64.b64encode(raw.encode("utf-8")))
    if len(key) in (16, 24, 32):
        return key
    raise ValueError(
        f"Could not derive a valid AES key from MASTER_CURRENT "
        f"(got {len(raw.encode())} bytes — need 16, 24, or 32 after base64 decode)."
    )


def decrypt(master: str, iv_b64: str, ct_b64: str) -> str:
    """Decrypt a single AES-256-GCM ciphertext blob."""
    key = decode_key(master)
    iv = base64.b64decode(iv_b64)
    ct = base64.b64decode(ct_b64)
    return AESGCM(key).decrypt(iv, ct, None).decode()


def _parse_map(value: str) -> dict:
    """Parse Go map string: map[ct:abc iv:xyz] -> {"ct": "abc", "iv": "xyz"}"""
    return dict(re.findall(r'(\w+):([^\s\]]+)', value))


def decrypt_params(master: str | None = None, prefix: str | None = None) -> dict[str, str]:
    """
    Decrypt all env vars with the given prefix using MASTER_CURRENT.

    Reads MASTER_CURRENT and PARAM_PREFIX from env if not provided.
    Overwrites matching env vars with their decrypted plaintext.
    Returns a dict of {param_name: plaintext}.

    Usage:
        from datarelay import decrypt_params
        params = decrypt_params()
        # env vars like DR_MY_KEY are now decrypted in os.environ
    """
    master = master or os.environ.get("MASTER_CURRENT")
    if not master:
        raise ValueError("MASTER_CURRENT is not set")

    prefix = prefix or os.environ.get("PARAM_PREFIX", "DR_")

    params = {k: v for k, v in os.environ.items() if k.startswith(prefix)}
    results = {}

    for var_name, raw_value in sorted(params.items()):
        param_name = var_name[len(prefix):]
        try:
            parsed = _parse_map(raw_value)
            if "iv" not in parsed or "ct" not in parsed:
                continue
            plaintext = decrypt(master, parsed["iv"], parsed["ct"])
            os.environ[var_name] = plaintext
            results[param_name] = plaintext
        except Exception as e:
            raise ValueError(f"Failed to decrypt {var_name}: {e}") from e

    return results
