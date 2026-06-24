import os
from datetime import datetime
from pathlib import Path


def _log_path() -> Path | None:
    if os.name != "nt":
        return None
    gti = Path(os.environ.get("USERPROFILE", "")) / "GTiSupport"
    gti.mkdir(parents=True, exist_ok=True)
    return gti / "QWX_Log.txt"


def log(message: str) -> None:
    """Registra uma entrada no topo do QWX_Log.txt (mais recente primeiro)."""
    path = _log_path()
    if path is None:
        return
    try:
        timestamp = datetime.now().strftime("%Y/%m/%d %H:%M:%S")
        line = f"{timestamp} - {message}\n"
        existing = path.read_text(encoding="utf-8") if path.exists() else ""
        path.write_text(line + existing, encoding="utf-8")
    except Exception:
        pass
