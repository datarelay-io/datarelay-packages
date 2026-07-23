# datarelay-packages

Client packages for [DataRelay](https://github.com/hsuk/datarelay).

## Packages

| Directory | Language | Install |
|-----------|----------|---------|
| `python/` | Python 3.10+ | `pip install "git+https://github.com/datarelay-io/datarelay-packages.git#subdirectory=python"` |

---

## Python

### Install

```bash
python3 -m venv .venv
source .venv/bin/activate
pip install "git+https://github.com/datarelay-io/datarelay-packages.git#subdirectory=python"
```

### Usage

#### Decrypt all params at startup

```python
from datarelay import decrypt_params

# Reads MASTER_CURRENT and PARAM_PREFIX from env.
# Decrypts all DR_* env vars and overwrites them with plaintext.
params = decrypt_params()
# os.environ["DR_MY_KEY"] is now the plaintext value
```

#### Decrypt a single value

```python
from datarelay import decrypt

plaintext = decrypt(master="your-master-current", iv_b64="...", ct_b64="...")
```

#### Decode the AES key

```python
from datarelay import decode_key

key_bytes = decode_key(os.environ["MASTER_CURRENT"])
```

### API

#### `decrypt_params(master=None, prefix=None) -> dict[str, str]`

Decrypts all env vars with the given prefix. Falls back to `MASTER_CURRENT` and `PARAM_PREFIX` env vars if not provided. Overwrites matching env vars in `os.environ` with plaintext. Returns `{param_name: plaintext}`.

#### `decrypt(master, iv_b64, ct_b64) -> str`

Decrypts a single AES-256-GCM blob. `master` is the raw `MASTER_CURRENT` secret value.

#### `decode_key(master) -> bytes`

Derives the AES key bytes from a `MASTER_CURRENT` secret value, replicating the Cloudflare Worker's base64 handling.
