import os
import json
from pathlib import Path
from src import screens
from src.boot import get_update_info

_YELLOW = "\033[93m"
_RESET  = "\033[0m"

_OPCOES = [
    ( 0, "Sair"),
    ( 1, "Menu QuickWindows..."),
    ( 2, "Windows..."),
    ( 3, "Internet..."),
    ( 4, "Redes..."),
    ( 5, "Execucao de Comandos no PowerShell"),
    ( 6, "Utilitarios para Windows..."),
    ( 7, "Softwares para Escritorio..."),
    ( 8, "Sistemas Operacionais Microsoft..."),
    ( 9, "Executar Rotinas..."),
]

_ACOES = {
    1: screens.menu_quickwindows,
    2: screens.windows,
    3: screens.internet,
    4: screens.redes,
    5: screens.powershell,
    6: screens.utilitarios,
    7: screens.escritorio,
    8: screens.sistemas_operacionais,
    9: screens.rotinas,
}


def _versao():
    try:
        root = Path(__file__).resolve().parent.parent
        dados = json.loads((root / "version.json").read_text(encoding="utf-8"))
        return dados.get("version", "?")
    except Exception:
        return "?"


def _limpar():
    os.system("cls" if os.name == "nt" else "clear")


def _cabecalho(versao, aviso=None):
    print()
    print("  ========================================")
    print("          QuickWindowsX")
    print(f"          Versao: {versao}")
    if aviso:
        print(f"  {aviso}")
    print("  ========================================")
    print()


def _opcoes():
    for num, label in _OPCOES:
        print(f"  {num:>2} - {label}")
    print()


def rodar():
    versao = _versao()

    local_ver, remote_ver = get_update_info()
    aviso = None
    if remote_ver and remote_ver != local_ver:
        aviso = f"{_YELLOW}[ NOVO ] v{remote_ver} disponivel! Use '1 > 1' para atualizar.{_RESET}"

    while True:
        _limpar()
        _cabecalho(versao, aviso)
        _opcoes()

        entrada = input("  Opcao: ").strip()

        # ── Atalho direto: [sessao:op,...;sessao:sub:op,...] ─────────────────
        if ":" in entrada:
            chunks = [c.strip() for c in entrada.split(";") if c.strip()]
            for chunk in chunks:
                partes = chunk.split(":", 2)   # max 3 partes: sessao:sub:opcoes
                if len(partes) < 2:
                    continue
                sessao_str = partes[0].strip()
                if not sessao_str.isdigit():
                    continue
                sessao = int(sessao_str)
                if sessao not in _ACOES:
                    print(f"  Sessao {sessao} nao existe.")
                    input("  Pressione Enter para continuar...")
                    continue

                if len(partes) == 3:
                    # formato: sessao:sub_opcao:opcoes_internas  (drill-down)
                    sub_str, opcoes_str = partes[1].strip(), partes[2].strip()
                    sub_opcao = int(sub_str) if sub_str.isdigit() else None
                    sub_nums = [int(n.strip()) for n in opcoes_str.split(",")
                                if n.strip().isdigit()]
                    if sub_opcao and sub_nums:
                        _ACOES[sessao](preset=[(sub_opcao, sub_nums)])
                    continue

                # formato: sessao:op1,op2  (opcoes diretas)
                resto = partes[1].strip()
                if sessao == 9:
                    screens.rotinas(preset=resto)
                elif sessao == 5:
                    _ACOES[sessao]()
                else:
                    nums = [int(n.strip()) for n in resto.split(",")
                            if n.strip().isdigit()]
                    if nums:
                        _ACOES[sessao](preset=nums)
            continue

        if not entrada.isdigit():
            _limpar()
            _cabecalho(versao, aviso)
            _opcoes()
            print("  Opcao invalida. Tente novamente.")
            input("  Pressione Enter para continuar...")
            continue

        escolha = int(entrada)

        if escolha == 0:
            _limpar()
            print()
            print("  Encerrando QuickWindowsX. Ate logo!")
            print()
            break

        if escolha not in _ACOES:
            _limpar()
            _cabecalho(versao, aviso)
            _opcoes()
            print("  Opcao invalida. Tente novamente.")
            input("  Pressione Enter para continuar...")
            continue

        _ACOES[escolha]()
