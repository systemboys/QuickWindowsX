import os
import json
import subprocess
from pathlib import Path

_ROOT      = Path(__file__).resolve().parent.parent
_PS_SCRIPT = _ROOT / "src" / "run_package.ps1"
_URLS_FILE = _ROOT / "urls.json"


def _carregar_urls():
    try:
        return json.loads(_URLS_FILE.read_text(encoding="utf-8"))
    except Exception as e:
        return None


def executar(sessao, nome, silent_args=""):
    """
    Busca a URL de urls.json[sessao][nome] e executa run_package.ps1.

    Parametros
    ----------
    sessao      : chave de primeiro nivel em urls.json
                  (ex.: "Internet", "UtilitiesForWindows")
    nome        : nome exato da opcao dentro da sessao
                  (ex.: "AnyDesk", "CPU-Z Portable")
    silent_args : argumentos extras para o instalador (ex.: "/S").
                  Deixe em branco para abrir o instalador com UI.
    """
    if os.name != "nt":
        print()
        print(f"  [INFO] Execucao de instaladores disponivel apenas no Windows.")
        _mostrar_url(sessao, nome)
        input("  Pressione Enter para voltar...")
        return

    urls = _carregar_urls()
    if not urls:
        print()
        print("  [ERRO] Nao foi possivel ler urls.json.")
        input("  Pressione Enter para voltar...")
        return

    if sessao not in urls:
        print()
        print(f"  [ERRO] Sessao '{sessao}' nao encontrada em urls.json.")
        input("  Pressione Enter para voltar...")
        return

    if nome not in urls[sessao]:
        print()
        print(f"  [ERRO] '{nome}' nao encontrado em urls.json['{sessao}'].")
        input("  Pressione Enter para voltar...")
        return

    url = urls[sessao][nome]

    cmd = [
        "powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
        "-File", str(_PS_SCRIPT),
        "-Url", url,
        "-Nome", nome,
    ]
    if silent_args:
        cmd += ["-SilentArgs", silent_args]

    subprocess.run(cmd, check=False)


def _mostrar_url(sessao, nome):
    """Exibe a URL correspondente (util fora do Windows para debug/preview)."""
    urls = _carregar_urls()
    if urls and sessao in urls and nome in urls[sessao]:
        print(f"  URL: {urls[sessao][nome]}")
    print()
