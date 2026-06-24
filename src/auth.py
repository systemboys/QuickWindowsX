import hashlib
import json
import os
from pathlib import Path

_SALT = "QWXv2:"


def _auth_path() -> Path | None:
    if os.name != "nt":
        return None
    gti = Path(os.environ.get("USERPROFILE", "")) / "GTiSupport"
    gti.mkdir(parents=True, exist_ok=True)
    return gti / "qwx_auth.json"


def _hash(password: str) -> str:
    return hashlib.sha256(f"{_SALT}{password}".encode()).hexdigest()


def get_hash() -> str | None:
    path = _auth_path()
    if path is None or not path.exists():
        return None
    try:
        data = json.loads(path.read_text(encoding="utf-8"))
        h = data.get("senha", "")
        return h if h else None
    except Exception:
        return None


def file_exists() -> bool:
    """Retorna True se o arquivo de autenticacao ja foi criado (independente de ter senha)."""
    path = _auth_path()
    return path is not None and path.exists()


def has_password() -> bool:
    return get_hash() is not None


def verify(password: str) -> bool:
    stored = get_hash()
    if stored is None:
        return True
    return _hash(password) == stored


def save(password: str) -> None:
    path = _auth_path()
    if path is None:
        return
    path.write_text(
        json.dumps({"senha": _hash(password)}, indent=2, ensure_ascii=True),
        encoding="utf-8",
    )


def clear() -> None:
    path = _auth_path()
    if path is None:
        return
    path.write_text(json.dumps({"senha": ""}, indent=2), encoding="utf-8")
