import os
import sys
import time
import json
import random
import urllib.request
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

_version_cache: dict = {}


def get_update_info():
    """Retorna (local_ver, remote_ver) da verificação feita no boot."""
    return _version_cache.get("local"), _version_cache.get("remote")


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
    print(f"         Starting {msg}...")
    time.sleep(random.uniform(0.08, 0.18))


def _check_version():
    """Retorna (local_ver, remote_ver). remote_ver é None se a verificação falhar."""
    try:
        local = json.loads((ROOT / "version.json").read_text(encoding="utf-8")).get("version", "")
    except Exception:
        return None, None
    try:
        url = "https://raw.githubusercontent.com/systemboys/QuickWindowsX/main/version.json"
        with urllib.request.urlopen(url, timeout=4) as resp:
            remote = json.loads(resp.read().decode("utf-8")).get("version", "")
        return local, remote
    except Exception:
        return local, None


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
    local_ver, remote_ver = _check_version()
    _version_cache["local"]  = local_ver
    _version_cache["remote"] = remote_ver
    if remote_ver and remote_ver != local_ver:
        print(f"[ {_YELLOW}NOVO{_RESET} ] v{remote_ver} disponivel! (instalada: v{local_ver}) — use '1 > 1' para atualizar.")
        time.sleep(random.uniform(0.07, 0.22))
    else:
        _ok(f"Versao {local_ver} — atualizada." if remote_ver else "QuickWindowsX iniciado.")

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
    _check_file("src/__init__.py",    "src/__init__.py")
    _check_file("src/app.py",         "src/app.py")
    _check_file("src/menu.py",        "src/menu.py")
    _check_file("src/screens.py",     "src/screens.py")
    _check_file("src/boot.py",        "src/boot.py")
    _check_file("src/auth.py",        "src/auth.py")
    _check_file("src/logger.py",      "src/logger.py")
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

    # ── Registro de inicializacao ─────────────────────────────────────────────
    from src import logger
    logger.log(f"QuickWindowsX v{local_ver or '?'} iniciado")

    # ── Autenticacao ──────────────────────────────────────────────────────────
    _handle_auth()


def _input_senha(prompt: str) -> str:
    """Lê senha sem eco. Usa getpass (padrão Python) com fallback para input()."""
    import getpass
    try:
        return getpass.getpass(prompt)
    except Exception:
        return input(prompt)


def _nova_senha_prompt() -> str | None:
    """Solicita e confirma nova senha (minimo 6 caracteres). Retorna a senha ou None se cancelado."""
    while True:
        p1 = _input_senha("  Nova senha (minimo 6 caracteres): ")
        if not p1:
            return None
        if len(p1) < 6:
            _warn(f"Senha muito curta. Minimo 6 caracteres. Voce digitou {len(p1)}.")
            continue
        p2 = _input_senha("  Confirmar senha: ")
        if p1 != p2:
            _warn("As senhas nao coincidem. Tente novamente.")
            continue
        return p1


def _handle_auth():
    """Gerencia autenticacao no boot: setup na primeira vez, prompt nas seguintes."""
    if os.name != "nt":
        return

    from src import auth
    from src import logger

    if not auth.file_exists():
        # Primeira execucao: perguntar uma unica vez sobre senha
        print("  ─────────────────────────────────────────────")
        print("  Deseja proteger o QWX com senha?")
        print("  (minimo 6 caracteres — opcional, Enter para pular)")
        print("  ─────────────────────────────────────────────")
        resp = input("  Ativar protecao por senha? (s/N): ").strip().lower()
        if resp == "s":
            senha = _nova_senha_prompt()
            if senha and auth.save(senha):
                logger.log("Senha de protecao configurada")
                _ok("Senha configurada! O QWX solicitara a senha no proximo acesso.")
            elif senha:
                _fail("Nao foi possivel salvar a senha. Verifique permissoes em GTiSupport.")
                auth.clear()
            else:
                auth.clear()  # cria o arquivo vazio para nao perguntar de novo
                _warn("Configuracao de senha cancelada.")
        else:
            auth.clear()  # cria o arquivo vazio para nao perguntar de novo
        print()
        return

    if not auth.has_password():
        return  # Arquivo existe mas sem senha — acesso direto, sem perguntar

    # Senha ativa: solicitar acesso
    print()
    print("  ─────────────────────────────────────────────")
    print("  QuickWindowsX esta protegido por senha.")
    print("  ─────────────────────────────────────────────")
    for tentativa in range(1, 4):
        senha = _input_senha(f"  Senha ({tentativa}/3): ")
        if auth.verify(senha):
            logger.log("Acesso autorizado")
            _ok("Acesso autorizado.")
            print()
            return
        restantes = 3 - tentativa
        if restantes > 0:
            logger.log(f"Tentativa de acesso com senha incorreta ({tentativa}/3)")
            _warn(f"Senha incorreta. Tentativas restantes: {restantes}")
        else:
            logger.log("Acesso negado apos 3 tentativas com senha incorreta")
            print()
            _fail("Acesso negado. Encerrando o QuickWindowsX.")
            print()
            sys.exit(1)
