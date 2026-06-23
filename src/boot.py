import os
import sys
import time
import json
import random
from pathlib import Path

# Habilitar ANSI no Windows (suportado no Windows 10+)
if os.name == "nt":
    try:
        import ctypes
        kernel32 = ctypes.windll.kernel32
        kernel32.SetConsoleMode(kernel32.GetStdHandle(-11), 7)
    except Exception:
        pass

_GREEN  = "\033[92m"
_RED    = "\033[91m"
_YELLOW = "\033[93m"
_RESET  = "\033[0m"
_DIM    = "\033[2m"

ROOT = Path(__file__).resolve().parent.parent


def _ok(msg):
    print(f"[ {_GREEN}OK{_RESET} ] {msg}")
    time.sleep(random.uniform(0.07, 0.22))


def _fail(msg):
    print(f"[ {_RED}FAIL{_RESET} ] {msg}")
    time.sleep(random.uniform(0.07, 0.15))


def _warn(msg):
    print(f"[ {_YELLOW}WARN{_RESET} ] {msg}")
    time.sleep(random.uniform(0.07, 0.15))


def _starting(msg):
    print(f"{_DIM}         Starting {msg}...{_RESET}")
    time.sleep(random.uniform(0.08, 0.18))


def _check_file(rel_path, label=None):
    label = label or rel_path
    if (ROOT / rel_path).exists():
        _ok(f"Localizado {label}")
        return True
    _fail(f"Nao encontrado: {label}")
    return False


def executar():
    os.system("cls" if os.name == "nt" else "clear")
    print()

    # ── Inicializacao do sistema ──────────────────────────────────────────────
    _starting("QuickWindowsX")
    _ok("Iniciado QuickWindowsX.")

    # ── Arquivos principais ───────────────────────────────────────────────────
    _starting("verificacao de arquivos principais")
    _check_file("main.py",      "main.py")
    _check_file("run.cmd",      "run.cmd")
    _check_file("setup.ps1",    "setup.ps1")
    _check_file("version.json", "version.json")
    _check_file("urls.json",    "urls.json")
    _check_file("config.json",  "config.json")

    # ── Modulos do sistema ────────────────────────────────────────────────────
    _starting("carregamento de modulos")
    _check_file("src/__init__.py", "src/__init__.py")
    _check_file("src/app.py",      "src/app.py")
    _check_file("src/menu.py",     "src/menu.py")
    _check_file("src/screens.py",  "src/screens.py")
    _check_file("src/boot.py",       "src/boot.py")
    _check_file("src/exceptions.py",  "src/exceptions.py")
    _check_file("src/installer.py",   "src/installer.py")
    _check_file("src/run_package.ps1","src/run_package.ps1")

    # ── Configuracao e versao ─────────────────────────────────────────────────
    _starting("leitura de configuracoes")
    try:
        data = json.loads((ROOT / "version.json").read_text(encoding="utf-8"))
        ver   = data.get("version", "?")
        stage = data.get("stage", "?")
        _ok(f"Versao {ver} ({stage}) carregada.")
    except Exception as e:
        _fail(f"Falha ao ler version.json: {e}")

    try:
        cfg   = json.loads((ROOT / "config.json").read_text(encoding="utf-8"))
        title = cfg.get("promptWindowTitle", "GTi - QuickWindowsX")
        if os.name == "nt":
            import ctypes
            ctypes.windll.kernel32.SetConsoleTitleW(title)
        _ok(f"Titulo da janela: {title}")
    except Exception as e:
        _fail(f"Falha ao ler config.json: {e}")

    # ── Ambiente Python ───────────────────────────────────────────────────────
    _starting("verificacao de ambiente Python")
    py_ver = f"{sys.version_info.major}.{sys.version_info.minor}.{sys.version_info.micro}"
    _ok(f"Python {py_ver} detectado.")

    plat = "Windows" if os.name == "nt" else sys.platform
    _ok(f"Plataforma: {plat}.")

    # ── Pronto ────────────────────────────────────────────────────────────────
    _ok("Todos os servicos iniciados.")
    print()
    time.sleep(0.3)
