import os
import sys
import json
import subprocess
import webbrowser
from datetime import datetime, timedelta
from pathlib import Path
from src.exceptions import Recarregar
from src import installer

_ROOT = Path(__file__).resolve().parent.parent


# ─── Utilitarios de tela ──────────────────────────────────────────────────────

def _clear():
    os.system("cls" if os.name == "nt" else "clear")


def _cabecalho(titulo):
    print()
    print(f"  === {titulo} ===")
    print()


def _em_desenvolvimento(nome_opcao):
    _clear()
    print()
    print(f"  [{nome_opcao}]")
    print()
    print("  Esta opcao ainda esta em desenvolvimento.")
    print()
    input("  Pressione Enter para voltar...")


def _confirmar(pergunta):
    resp = input(f"  {pergunta} [s/N]: ").strip().lower()
    return resp in ("s", "sim")


# ─── Motor de submenu ─────────────────────────────────────────────────────────

def _submenu(titulo, opcoes, acoes=None):
    """
    Exibe um submenu interativo.
    acoes: dict {int: callable} — se a chave existir, chama o callable;
           caso contrario exibe tela "em desenvolvimento".
    """
    while True:
        _clear()
        _cabecalho(titulo)
        print("   0: Voltar...")
        for i, label in enumerate(opcoes, start=1):
            print(f"  {i:>2}: {label}")
        print()

        entrada = input("  Opcao: ").strip()

        if entrada == "0":
            return

        if not entrada.isdigit():
            _erro_opcao(titulo, opcoes)
            continue

        escolha = int(entrada)

        if 1 <= escolha <= len(opcoes):
            if acoes and escolha in acoes:
                acoes[escolha]()
            else:
                _em_desenvolvimento(opcoes[escolha - 1])
        else:
            _erro_opcao(titulo, opcoes)


def _erro_opcao(titulo, opcoes):
    _clear()
    _cabecalho(titulo)
    print("   0: Voltar...")
    for i, label in enumerate(opcoes, start=1):
        print(f"  {i:>2}: {label}")
    print()
    print("  Opcao invalida. Tente novamente.")
    input("  Pressione Enter para continuar...")


# ─── Execucao PowerShell ──────────────────────────────────────────────────────

def _ps(command):
    if os.name != "nt":
        print()
        print("  [INFO] Este comando so esta disponivel no Windows.")
        return
    subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", command],
        check=False,
    )


# ─── Fabrica de acoes de instalacao ──────────────────────────────────────────

def _instalar(sessao, nome, silent_args=""):
    def _acao():
        installer.executar(sessao, nome, silent_args)
    return _acao


# ─── Acoes da secao Windows ───────────────────────────────────────────────────

def _desligar_windows():
    _clear()
    print()
    print("  === Desligar o Windows ===")
    print()
    if not _confirmar("Deseja realmente desligar o computador agora?"):
        return
    print()
    print("  Desligando...")
    _ps("Stop-Computer -Force")


def _reiniciar_windows():
    _clear()
    print()
    print("  === Reiniciar o Windows ===")
    print()
    if not _confirmar("Deseja realmente reiniciar o computador agora?"):
        return
    print()
    print("  Reiniciando...")
    _ps("Restart-Computer -Force")


def _shutdown_file():
    if os.name != "nt":
        return None
    return Path(os.environ.get("USERPROFILE", "")) / "GTiSupport" / "QWX_Shutdown.json"


def _ler_agendamento():
    arq = _shutdown_file()
    if not arq:
        return None
    try:
        if not arq.exists():
            return None
        data = json.loads(arq.read_text(encoding="utf-8"))
        desliga_em = datetime.fromisoformat(data["desliga_em"])
        if desliga_em <= datetime.now():
            arq.unlink(missing_ok=True)
            return None
        return data
    except Exception:
        return None


def _salvar_agendamento(minutos):
    arq = _shutdown_file()
    if not arq:
        return
    try:
        arq.parent.mkdir(parents=True, exist_ok=True)
        arq.write_text(json.dumps({
            "agendado_em": datetime.now().isoformat(),
            "desliga_em":  (datetime.now() + timedelta(minutes=minutos)).isoformat(),
            "minutos":     minutos,
        }, ensure_ascii=False), encoding="utf-8")
    except Exception:
        pass


def _cancelar_agendamento():
    _ps("shutdown /a")
    arq = _shutdown_file()
    if arq:
        try:
            arq.unlink(missing_ok=True)
        except Exception:
            pass


def _agendar_desligamento():
    _clear()
    print()
    print("  === Agendar Desligamento do Windows ===")
    print()

    agendamento = _ler_agendamento()

    if agendamento:
        desliga_em = datetime.fromisoformat(agendamento["desliga_em"])
        restantes  = max(0, int((desliga_em - datetime.now()).total_seconds() / 60))

        print("  [!] Ja existe um desligamento agendado!")
        print()
        print(f"  Horario do desligamento : {desliga_em.strftime('%d/%m/%Y as %H:%M:%S')}")
        print(f"  Tempo restante          : aprox. {restantes} minuto(s)")
        print()
        print("  O que deseja fazer?")
        print()
        print("   1: Anular o agendamento")
        print("   2: Anular e reagendar")
        print("   0: Voltar")
        print()

        escolha = input("  Opcao: ").strip()

        if escolha == "0":
            return
        elif escolha == "1":
            _cancelar_agendamento()
            print()
            print("  Agendamento cancelado com sucesso.")
            input("  Pressione Enter para continuar...")
            return
        elif escolha == "2":
            _cancelar_agendamento()
            print()
            print("  Agendamento anterior cancelado. Informe o novo horario.")
            print()
        else:
            print()
            print("  Opcao invalida.")
            input("  Pressione Enter para continuar...")
            return

    entrada = input("  Informe em quantos minutos desligar (ex.: 3): ").strip()

    if not entrada.isdigit() or int(entrada) <= 0:
        print()
        print("  Valor invalido. Operacao cancelada.")
        input("  Pressione Enter para voltar...")
        return

    minutos  = int(entrada)
    segundos = minutos * 60

    _ps(f"shutdown /s /t {segundos}")
    _salvar_agendamento(minutos)
    print()
    print(f"  Desligamento agendado para {minutos} minuto(s).")
    input("  Pressione Enter para continuar...")


def _atualizar_windows_softwares():
    _clear()
    print()
    print("  === Atualizar Windows e Softwares ===")
    print()
    print("  Isso pode levar varios minutos. Mantenha o computador ligado.")
    print()
    if not _confirmar("Deseja iniciar as atualizacoes agora?"):
        return
    print()

    ps_script = r"""
        if (-not (Get-Module -ListAvailable -Name PSWindowsUpdate)) {
            Write-Host "  Instalando modulo PSWindowsUpdate..." -ForegroundColor Cyan
            Install-PackageProvider -Name NuGet -MinimumVersion 2.8.5.201 -Force -ErrorAction SilentlyContinue | Out-Null
            Install-Module -Name PSWindowsUpdate -Force -ErrorAction SilentlyContinue
        }
        Write-Host ""
        Write-Host "  Buscando atualizacoes do Windows..." -ForegroundColor Cyan
        try {
            Import-Module PSWindowsUpdate -ErrorAction Stop
            Get-WindowsUpdate -AcceptAll -Install -AutoReboot:$false -IgnoreReboot
        } catch {
            Write-Host "  [AVISO] PSWindowsUpdate indisponivel. Iniciando varredura via UsoClient..." -ForegroundColor Yellow
            Start-Process "UsoClient.exe" -ArgumentList "StartScan" -Wait -ErrorAction SilentlyContinue
        }
        Write-Host ""
        Write-Host "  Atualizando softwares instalados via winget..." -ForegroundColor Cyan
        if (Get-Command winget -ErrorAction SilentlyContinue) {
            winget upgrade --all --silent --accept-source-agreements --accept-package-agreements
        } else {
            Write-Host "  [AVISO] winget nao encontrado. Pulando atualizacao de softwares." -ForegroundColor Yellow
        }
        Write-Host ""
        Write-Host "  Processo de atualizacao concluido." -ForegroundColor Green
    """
    _ps(ps_script)
    print()
    input("  Pressione Enter para continuar...")


def _gerenciar_arquivos_pastas():
    _clear()
    print()
    print("  === Gerenciar Arquivos e Pastas ===")
    print()
    caminho = input("  Informe o caminho a abrir (ex.: C:\\Users): ").strip()
    if not caminho:
        print()
        print("  Caminho invalido. Operacao cancelada.")
        input("  Pressione Enter para voltar...")
        return
    _ps(f'Start-Process "explorer.exe" -ArgumentList "{caminho}"')
    print()
    input("  Pressione Enter para continuar...")


def _informacoes_sistema():
    _clear()
    print()
    print("  === Informacoes do Sistema ===")
    print()
    print("  Coletando informacoes...")
    ps_script = r"""
        function Show-Frame([string]$titulo, [string[]]$linhas) {
            Write-Host ("─" * 70) -ForegroundColor DarkGray
            Write-Host "  $titulo" -ForegroundColor Cyan
            foreach ($l in $linhas) { Write-Host "    $l" }
        }

        $cpu = Get-WmiObject Win32_Processor | Select-Object -First 1
        Show-Frame "Processador" @(
            "Nome     : $($cpu.Name.Trim())",
            "Clock    : $($cpu.MaxClockSpeed) MHz",
            "Nucleos  : $($cpu.NumberOfCores)",
            "Logicos  : $($cpu.NumberOfLogicalProcessors)"
        )

        $ram = (Get-WmiObject Win32_PhysicalMemory | Measure-Object Capacity -Sum).Sum
        Show-Frame "Memoria RAM" @(
            "Total : {0:N2} GB" -f ($ram / 1GB)
        )

        $sys = Get-CimInstance Win32_ComputerSystem
        $os  = Get-CimInstance Win32_OperatingSystem
        Show-Frame "Sistema" @(
            "Fabricante : $($sys.Manufacturer)",
            "Modelo     : $($sys.Model)",
            "SO         : $($os.Caption)",
            "Versao     : $($os.Version)",
            "Arquit.    : $($os.OSArchitecture)"
        )

        Write-Host ("─" * 70) -ForegroundColor DarkGray
        Write-Host ""
    """
    _ps(ps_script)
    input("  Pressione Enter para continuar...")


def _configuracoes():
    def _abrir(cmd, args=""):
        def _acao():
            if args:
                _ps(f'Start-Process "{cmd}" -ArgumentList "{args}"')
            else:
                _ps(f'Start-Process "{cmd}"')
        return _acao

    _submenu("QuickWindowsX / Windows / Configuracoes", [
        "Painel de Controle",
        "Editor de Registro (RegEdit)",
        "Configuracoes do Sistema (MSConfig)",
        "Servicos (services.msc)",
        "Gerenciador de Dispositivos (devmgmt.msc)",
        "Gerenciamento de Discos (diskmgmt.msc)",
        "Explorador de Arquivos do Windows",
        "Configuracoes de Tela (desk.cpl)",
        "Configuracoes avancadas do sistema (sysdm.cpl)",
        "Editar Configuracoes do Plano (powercfg.cpl)",
        "Sobre o Windows (winver)",
        "Gerenciar arquivos e pastas",
        "Configuracoes do Windows (ms-settings)",
        "Gerenciador de Tarefas (taskmgr)",
        "Opcoes de pastas",
        "Informacoes do Sistema",
    ], {
        1:  _abrir("control"),
        2:  _abrir("regedit"),
        3:  _abrir("msconfig"),
        4:  _abrir("services.msc"),
        5:  _abrir("devmgmt.msc"),
        6:  _abrir("diskmgmt.msc"),
        7:  _abrir("explorer"),
        8:  _abrir("desk.cpl"),
        9:  _abrir("sysdm.cpl"),
        10: _abrir("powercfg.cpl"),
        11: _abrir("winver"),
        12: _gerenciar_arquivos_pastas,
        13: _abrir("ms-settings:"),
        14: _abrir("taskmgr"),
        15: _abrir("control", "folders"),
        16: _informacoes_sistema,
    })


def _criar_atalhos():
    _clear()
    print()
    print("  === Criar Atalhos: Desligar e Reiniciar ===")
    print()
    print("  Serao criados dois atalhos na Area de Trabalho:")
    print("    - Desligar computador")
    print("    - Reiniciar computador")
    print()
    if not _confirmar("Deseja criar os atalhos agora?"):
        return
    print()
    print("  Baixando icones e criando atalhos...")

    ps_script = r"""
        $desktopPath = [System.Environment]::GetFolderPath('Desktop')
        $iconDir     = "$env:USERPROFILE\GTiSupport"
        if (-not (Test-Path $iconDir)) { New-Item -ItemType Directory -Path $iconDir -Force | Out-Null }

        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        $wc = New-Object System.Net.WebClient

        $iconDesligar = "$iconDir\button-icon-png-21067-Windows.ico"
        try {
            $wc.DownloadFile(
                "https://raw.githubusercontent.com/systemboys/_GTi_Support_/main/icons/buttons/button-icon-png-21067-Windows.ico",
                $iconDesligar
            )
        } catch { $iconDesligar = ""; Write-Host "  [AVISO] Icone de desligar nao baixado." -ForegroundColor Yellow }

        $shell  = New-Object -ComObject WScript.Shell
        $atalho = $shell.CreateShortcut("$desktopPath\Desligar computador.lnk")
        $atalho.TargetPath  = "powershell.exe"
        $atalho.Arguments   = "-Command `"shutdown /s /t 0`""
        if ($iconDesligar) { $atalho.IconLocation = $iconDesligar }
        $atalho.Description = "Desligar o computador"
        $atalho.Save()
        Write-Host "  [OK] Atalho criado: Desligar computador" -ForegroundColor Green

        $iconReiniciar = "$iconDir\restart-icon-32273-Windows.ico"
        try {
            $wc.DownloadFile(
                "https://raw.githubusercontent.com/systemboys/_GTi_Support_/main/icons/buttons/restart-icon-32273-Windows.ico",
                $iconReiniciar
            )
        } catch { $iconReiniciar = ""; Write-Host "  [AVISO] Icone de reiniciar nao baixado." -ForegroundColor Yellow }

        $atalho2 = $shell.CreateShortcut("$desktopPath\Reiniciar computador.lnk")
        $atalho2.TargetPath  = "powershell.exe"
        $atalho2.Arguments   = "-Command `"shutdown /r /t 0`""
        if ($iconReiniciar) { $atalho2.IconLocation = $iconReiniciar }
        $atalho2.Description = "Reiniciar o computador"
        $atalho2.Save()
        Write-Host "  [OK] Atalho criado: Reiniciar computador" -ForegroundColor Green

        Write-Host ""
        Write-Host "  Atalhos disponiveis na Area de Trabalho." -ForegroundColor Green
    """
    _ps(ps_script)
    print()
    input("  Pressione Enter para continuar...")


def _reiniciar_bios():
    _clear()
    print()
    print("  === Reiniciar e entrar na BIOS ===")
    print()
    print("  O computador sera reiniciado e o firmware UEFI/BIOS sera aberto.")
    print()
    if not _confirmar("Deseja reiniciar agora e entrar na BIOS?"):
        return
    print()
    print("  Reiniciando para a BIOS...")
    _ps("Start-Process 'shutdown' -ArgumentList '/r /fw /t 00'")


_OPCOES_WINDOWS = [
    "Desligar o Windows",
    "Reiniciar o Windows",
    "Agendar desligamento do Windows",
    "Atualizar Windows e Softwares",
    "Acesso rapido as Configuracoes...",
    "Criar atalhos para 'Desligar e Reiniciar'",
    "Reiniciar e iniciar a BIOS da placa-mae",
]

_ACOES_WINDOWS = {
    1: _desligar_windows,
    2: _reiniciar_windows,
    3: _agendar_desligamento,
    4: _atualizar_windows_softwares,
    5: _configuracoes,
    6: _criar_atalhos,
    7: _reiniciar_bios,
}


# ─── Acoes da secao Menu QuickWindowsX ───────────────────────────────────────

def _deletar_quickwindowsx():
    _clear()
    print()
    print("  === Deletar QuickWindowsX ===")
    print()
    print("  ATENCAO: Esta operacao e IRREVERSIVEL!")
    print()
    print("  Sera removido:")
    print("    - %TEMP%\\QuickWindowsX")
    print("    - Atalho 'GTi Support QWX' da Area de Trabalho")
    print()
    print("  Sera preservado:")
    print("    - %USERPROFILE%\\GTiSupport\\ (historico, logs e icones)")
    print()
    if not _confirmar("Tem certeza que deseja deletar o QuickWindowsX?"):
        return

    if os.name != "nt":
        print()
        print("  [INFO] Disponivel apenas no Windows.")
        input("  Pressione Enter para voltar...")
        return

    qwx_dir = Path(os.environ["TEMP"]) / "QuickWindowsX"
    gti_dir = Path(os.environ["USERPROFILE"]) / "GTiSupport"
    cleanup = gti_dir / "QWX_Delete.bat"

    # O QWX roda a partir de dentro de %TEMP%\QuickWindowsX, entao o Windows
    # bloqueia a remocao do diretorio enquanto o processo esta ativo.
    # Solucao: gravar um batch em GTiSupport (fora do diretorio do QWX),
    # lanca-lo como processo independente com delay e fechar o Python.
    gti_dir.mkdir(parents=True, exist_ok=True)
    cleanup.write_text(
        "@echo off\r\n"
        'cd /d "%USERPROFILE%\\GTiSupport"\r\n'
        "timeout /t 5 /nobreak > nul\r\n"
        ":retry\r\n"
        f'rmdir /s /q "{qwx_dir}"\r\n'
        f'if exist "{qwx_dir}" (\r\n'
        "    timeout /t 2 /nobreak > nul\r\n"
        "    goto retry\r\n"
        ")\r\n"
        'powershell -NoProfile -Command "'
        "$d=[Environment]::GetFolderPath(\'Desktop\');"
        " $f=Join-Path $d \'GTi Support QWX.lnk\';"
        " if(Test-Path $f){Remove-Item $f -Force}"
        '"\r\n'
        'del /f /q "%~f0"\r\n',
        encoding="ascii",
    )

    subprocess.Popen(
        ["cmd.exe", "/c", str(cleanup)],
        creationflags=0x08000000,  # CREATE_NO_WINDOW
    )

    print()
    print("  QuickWindowsX sera removido em instantes. Encerrando...")
    sys.exit(0)


def _atualizar_quickwindowsx():
    _clear()
    print()
    print("  === Atualizar QuickWindowsX ===")
    print()
    print("  O QuickWindowsX sera fechado, os arquivos atuais removidos")
    print("  e a versao mais recente sera baixada automaticamente.")
    print()
    if not _confirmar("Deseja atualizar o QuickWindowsX agora?"):
        return

    if os.name != "nt":
        print()
        print("  [INFO] Disponivel apenas no Windows.")
        input("  Pressione Enter para voltar...")
        return

    qwx_dir = Path(os.environ["TEMP"]) / "QuickWindowsX"
    gti_dir = Path(os.environ["USERPROFILE"]) / "GTiSupport"
    update  = gti_dir / "QWX_Update.bat"

    gti_dir.mkdir(parents=True, exist_ok=True)
    update.write_text(
        "@echo off\r\n"
        'cd /d "%USERPROFILE%\\GTiSupport"\r\n'
        "echo Aguardando encerramento do QuickWindowsX...\r\n"
        "timeout /t 5 /nobreak > nul\r\n"
        ":retry\r\n"
        f'rmdir /s /q "{qwx_dir}"\r\n'
        f'if exist "{qwx_dir}" (\r\n'
        "    timeout /t 2 /nobreak > nul\r\n"
        "    goto retry\r\n"
        ")\r\n"
        'powershell.exe -NoProfile -ExecutionPolicy Bypass -Command "irm qwx.gti1.com.br | iex"\r\n'
        'del /f /q "%~f0"\r\n',
        encoding="ascii",
    )

    subprocess.Popen(
        ["cmd.exe", "/c", str(update)],
        creationflags=subprocess.CREATE_NEW_CONSOLE,
    )

    print()
    print("  Atualizando QuickWindowsX em instantes. Encerrando...")
    sys.exit(0)


def _recarregar_quickwindowsx():
    raise Recarregar()


def _documentacao_quickwindowsx():
    _clear()
    print()
    print("  Abrindo documentacao do QuickWindowsX no navegador...")
    url = "https://github.com/systemboys/QuickWindowsX"
    if os.name == "nt":
        _ps(f'Start-Process "{url}"')
    else:
        webbrowser.open(url)
    print()
    input("  Pressione Enter para voltar...")


def _gerenciar_senha():
    from src import auth
    from src.boot import _input_senha, _nova_senha_prompt

    _G = "\033[92m"
    _Y = "\033[93m"
    _R = "\033[91m"
    _X = "\033[0m"
    SEP = "  ─────────────────────────────────────────────"

    while True:
        _clear()
        print()
        print("  === Gerenciar Senha de Acesso ===")
        print()

        if os.name != "nt":
            print("  [INFO] Disponivel apenas no Windows.")
            input("  Pressione Enter para voltar...")
            return

        ativo = auth.has_password()
        status = f"{_G}[ ATIVA ]{_X}" if ativo else f"{_Y}[ DESATIVADA ]{_X}"
        gti_path = Path(os.environ.get("USERPROFILE", "%USERPROFILE%")) / "GTiSupport" / "qwx_auth.json"
        print(f"  Status : {status}")
        print(f"  Arquivo: {gti_path}")
        print()
        print(SEP)

        if ativo:
            print(f"  {_G}1{_X} - Alterar senha")
            print(f"  {_R}2{_X} - Remover protecao por senha")
            print(f"  {_X}0{_X} - Voltar")
        else:
            print(f"  {_G}1{_X} - Ativar protecao por senha (minimo 6 digitos)")
            print(f"  {_X}0{_X} - Voltar")

        print(SEP)
        print()
        op = input("  Opcao: ").strip()

        if op == "0":
            return

        if op == "1" and not ativo:
            # Adicionar nova senha
            print()
            senha = _nova_senha_prompt()
            if senha and auth.save(senha):
                print()
                print(f"  {_G}Senha ativada com sucesso!{_X}")
                print("  O QWX solicitara a senha a cada inicializacao.")
            elif senha:
                print()
                print(f"  {_R}Erro ao salvar senha. Verifique permissoes em GTiSupport.{_X}")
            else:
                print()
                print("  Operacao cancelada.")
            input("  Pressione Enter para continuar...")

        elif op == "1" and ativo:
            # Alterar senha
            print()
            atual = _input_senha("  Senha atual: ")
            if not auth.verify(atual):
                print()
                print(f"  {_R}Senha incorreta. Operacao cancelada.{_X}")
                input("  Pressione Enter para continuar...")
                continue
            print()
            nova = _nova_senha_prompt()
            if nova and auth.save(nova):
                print()
                print(f"  {_G}Senha alterada com sucesso!{_X}")
            elif nova:
                print()
                print(f"  {_R}Erro ao salvar senha. Verifique permissoes em GTiSupport.{_X}")
            else:
                print()
                print("  Operacao cancelada.")
            input("  Pressione Enter para continuar...")

        elif op == "2" and ativo:
            # Remover senha
            print()
            atual = _input_senha("  Digite a senha atual para confirmar a remocao: ")
            if not auth.verify(atual):
                print()
                print(f"  {_R}Senha incorreta. Operacao cancelada.{_X}")
                input("  Pressione Enter para continuar...")
                continue
            auth.clear()
            print()
            print(f"  {_Y}Protecao por senha removida.{_X}")
            print("  O QWX sera iniciado sem solicitar senha.")
            input("  Pressione Enter para continuar...")


_ACOES_MENU_QWX = {
    1: _atualizar_quickwindowsx,
    2: _deletar_quickwindowsx,
    3: _recarregar_quickwindowsx,
    4: _documentacao_quickwindowsx,
    5: _gerenciar_senha,
}


# ─── Acoes especiais: Internet ────────────────────────────────────────────────

def _atalho_pcs_remotos():
    _clear()
    print()
    print("  === Criar Atalho de PC Remoto com AnyDesk ===")
    print()

    anydesk_id = input("  ID do AnyDesk (ex.: 123456789): ").strip()
    if not anydesk_id:
        print("  ID invalido. Operacao cancelada.")
        input("  Pressione Enter para voltar...")
        return

    nome_pc = input("  Nome do computador (ex.: Servidor Principal): ").strip()
    if not nome_pc:
        print("  Nome invalido. Operacao cancelada.")
        input("  Pressione Enter para voltar...")
        return

    tipo = input("  Tipo [d=Desktop / n=Notebook]: ").strip().lower()
    if tipo not in ("d", "n"):
        print("  Tipo invalido. Operacao cancelada.")
        input("  Pressione Enter para voltar...")
        return

    icon_name = "desktop-icon.ico" if tipo == "d" else "laptop-icon.ico"
    icon_url  = (
        f"https://raw.githubusercontent.com/systemboys/_GTi_Support_/main"
        f"/icons/computers/{icon_name}"
    )

    print()
    print(f"  Criando atalho para '{nome_pc}' (ID: {anydesk_id})...")

    ps_script = f"""
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        $wc = New-Object System.Net.WebClient

        $desktopPath = [System.Environment]::GetFolderPath('Desktop')
        $remotosDir  = "$desktopPath\\Remote computers"
        $iconDir     = "$env:USERPROFILE\\GTiSupport"

        if (-not (Test-Path $remotosDir)) {{ New-Item -ItemType Directory -Path $remotosDir -Force | Out-Null }}
        if (-not (Test-Path $iconDir))    {{ New-Item -ItemType Directory -Path $iconDir    -Force | Out-Null }}

        $iconPath = "$iconDir\\{icon_name}"
        try {{
            $wc.DownloadFile("{icon_url}", $iconPath)
        }} catch {{
            $iconPath = ""
            Write-Host "  [AVISO] Icone nao baixado." -ForegroundColor Yellow
        }}

        $anyDeskExe = "$env:ProgramFiles\\AnyDesk\\AnyDesk.exe"
        $regKey = Get-ItemProperty "HKLM:\\SOFTWARE\\Microsoft\\Windows\\CurrentVersion\\Uninstall\\AnyDesk" -ErrorAction SilentlyContinue
        if ($regKey -and $regKey.InstallLocation) {{
            $anyDeskExe = "$($regKey.InstallLocation)\\AnyDesk.exe"
        }}

        $shell  = New-Object -ComObject WScript.Shell
        $atalho = $shell.CreateShortcut("$remotosDir\\{nome_pc}.lnk")
        $atalho.TargetPath  = $anyDeskExe
        $atalho.Arguments   = "{anydesk_id}"
        if ($iconPath) {{ $atalho.IconLocation = $iconPath }}
        $atalho.Description = "Conectar ao {nome_pc} via AnyDesk"
        $atalho.Save()

        Write-Host "  [OK] Atalho '{nome_pc}' criado em Remote computers." -ForegroundColor Green
    """
    _ps(ps_script)
    print()
    input("  Pressione Enter para continuar...")


def _reset_anydesk():
    _clear()
    print()
    print("  === Reset AnyDesk ===")
    print()
    print("  O servico AnyDesk sera parado, configuracoes removidas e reiniciado.")
    print()
    if not _confirmar("Deseja redefinir o AnyDesk agora?"):
        return
    print()
    print("  Redefinindo AnyDesk...")
    ps_script = r"""
        Stop-Service AnyDesk -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 1
        Remove-Item "$env:APPDATA\AnyDesk" -Recurse -Force -ErrorAction SilentlyContinue
        Start-Service AnyDesk -ErrorAction SilentlyContinue
        Write-Host ""
        Write-Host "  [OK] AnyDesk redefinido com sucesso." -ForegroundColor Green
    """
    _ps(ps_script)
    print()
    input("  Pressione Enter para continuar...")


def _baixar_url():
    _clear()
    print()
    print("  === Baixar URL ===")
    print()
    url = input("  Informe a URL para download: ").strip()
    if not url:
        print()
        print("  URL invalida. Operacao cancelada.")
        input("  Pressione Enter para voltar...")
        return

    if os.name != "nt":
        print()
        print(f"  [INFO] Download disponivel apenas no Windows.")
        print(f"  URL: {url}")
        input("  Pressione Enter para voltar...")
        return

    print()
    subprocess.run(
        ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
         "-File", str(_ROOT / "src" / "run_package.ps1"),
         "-Url", url],
        check=False,
    )


# ─── Acoes especiais: Utilitarios ────────────────────────────────────────────

def _backup_zip():
    _clear()
    print()
    print("  === Compressao / Backup Automatico (.zip) ===")
    print()
    origem = input("  Pasta de origem (ex.: C:\\Documentos): ").strip()
    if not origem:
        print()
        print("  Caminho invalido. Operacao cancelada.")
        input("  Pressione Enter para voltar...")
        return

    destino = input("  Pasta de destino para o .zip (ex.: D:\\Backups): ").strip()
    if not destino:
        print()
        print("  Caminho invalido. Operacao cancelada.")
        input("  Pressione Enter para voltar...")
        return

    print()
    print(f"  Compactando '{origem}' em '{destino}'...")

    ps_script = f"""
        $origem  = "{origem}"
        $destino = "{destino}"
        $stamp   = Get-Date -Format "yyyyMMdd_HHmmss"
        $zipPath = Join-Path $destino "Backup_$stamp.zip"

        if (-not (Test-Path $destino)) {{
            New-Item -ItemType Directory -Path $destino -Force | Out-Null
        }}
        try {{
            Compress-Archive -Path $origem -DestinationPath $zipPath -Force
            Write-Host ""
            Write-Host "  [OK] Backup criado: $zipPath" -ForegroundColor Green
        }} catch {{
            Write-Host ""
            Write-Host "  [ERRO] Falha ao criar backup: $_" -ForegroundColor Red
        }}
    """
    _ps(ps_script)
    print()
    input("  Pressione Enter para continuar...")


def _limpar_spooler():
    _clear()
    print()
    print("  === Limpar Spooler de Impressao ===")
    print()
    print("  O servico Spooler sera parado, arquivos pendentes removidos e reiniciado.")
    print()
    if not _confirmar("Deseja limpar o spooler agora?"):
        return
    print()
    ps_script = r"""
        $spoolDir = "$env:SystemRoot\System32\spool\PRINTERS"

        Write-Host "  Parando servico Spooler..." -ForegroundColor Cyan
        Stop-Service Spooler -Force -ErrorAction SilentlyContinue

        $arquivos = Get-ChildItem -Path $spoolDir -Include "*.SHD","*.SPL" -Recurse -ErrorAction SilentlyContinue
        if ($arquivos) {
            foreach ($arq in $arquivos) {
                try {
                    Remove-Item $arq.FullName -Force -ErrorAction Stop
                    Write-Host "  [OK] Removido: $($arq.FullName)" -ForegroundColor Green
                } catch {
                    Write-Host "  [AVISO] Nao removido: $($arq.FullName)" -ForegroundColor Yellow
                }
            }
        } else {
            Write-Host "  Nenhum arquivo de impressao pendente encontrado." -ForegroundColor DarkGray
        }

        Write-Host ""
        Write-Host "  Reiniciando servico Spooler..." -ForegroundColor Cyan
        Start-Service Spooler -ErrorAction SilentlyContinue
        Write-Host ""
        Write-Host "  [OK] Spooler de impressao limpo e reiniciado." -ForegroundColor Green
    """
    _ps(ps_script)
    print()
    input("  Pressione Enter para continuar...")


def _limpar_temporarios():
    _clear()
    print()
    print("  === Limpar Arquivos Temporarios ===")
    print()
    print("  Serao removidos arquivos de %TEMP% e C:\\Windows\\Temp.")
    print("  O diretorio QuickWindowsX sera preservado.")
    print()
    if not _confirmar("Deseja limpar os arquivos temporarios agora?"):
        return
    print()
    ps_script = r"""
        $deletados = 0
        $erros     = 0
        $qwxPath   = "$env:TEMP\QuickWindowsX"

        Write-Host "  Limpando C:\Windows\Temp..." -ForegroundColor Cyan
        Get-ChildItem -Path "$env:SystemRoot\Temp" -ErrorAction SilentlyContinue | ForEach-Object {
            try {
                Remove-Item $_.FullName -Force -Recurse -ErrorAction Stop
                Write-Host "  Removido: $($_.FullName)"
                $deletados++
            } catch {
                Write-Host "  [AVISO] $($_.Name): $($_.Exception.Message)" -ForegroundColor Yellow
                $erros++
            }
        }

        Write-Host ""
        Write-Host "  Limpando $env:TEMP..." -ForegroundColor Cyan
        Get-ChildItem -Path $env:TEMP -ErrorAction SilentlyContinue |
            Where-Object { $_.FullName -ne $qwxPath } |
            ForEach-Object {
                try {
                    Remove-Item $_.FullName -Force -Recurse -ErrorAction Stop
                    Write-Host "  Removido: $($_.FullName)"
                    $deletados++
                } catch {
                    Write-Host "  [AVISO] $($_.Name): $($_.Exception.Message)" -ForegroundColor Yellow
                    $erros++
                }
            }

        Write-Host ""
        Write-Host "  [OK] Concluido: $deletados item(ns) removido(s), $erros nao puderam ser removidos." -ForegroundColor Green
    """
    _ps(ps_script)
    print()
    input("  Pressione Enter para continuar...")


def _battery_report():
    _clear()
    print()
    print("  === Battery Report ===")
    print()
    print("  Gera um relatorio detalhado sobre a bateria do dispositivo.")
    print()
    print("  Gerando relatorio...")
    ps_script = r"""
        $gtiDir = "$env:USERPROFILE\GTiSupport"
        if (-not (Test-Path $gtiDir)) { New-Item -ItemType Directory -Path $gtiDir -Force | Out-Null }
        $relatorio = "$gtiDir\battery-report.html"
        powercfg /batteryreport /output "$relatorio" | Out-Null
        if (Test-Path $relatorio) {
            Write-Host ""
            Write-Host "  [OK] Relatorio gerado: $relatorio" -ForegroundColor Green
            Start-Process $relatorio
        } else {
            Write-Host ""
            Write-Host "  [AVISO] Relatorio nao disponivel neste dispositivo." -ForegroundColor Yellow
        }
    """
    _ps(ps_script)
    print()
    input("  Pressione Enter para continuar...")


# ─── Acoes especiais: Escritorio ─────────────────────────────────────────────

def _atalhos_office_2021():
    _clear()
    print()
    print("  === Criar Atalhos para Apps do Office 2021 ===")
    print()
    print("  Serao criados atalhos na Area de Trabalho para os principais apps do Office.")
    print()
    if not _confirmar("Deseja criar os atalhos agora?"):
        return
    print()
    print("  Criando atalhos...")
    ps_script = r"""
        $desktopPath = [System.Environment]::GetFolderPath('Desktop')
        $shell  = New-Object -ComObject WScript.Shell
        $criados = 0

        $apps = @(
            @{ Nome = "Word 2021";       Exe = "WINWORD.EXE"  },
            @{ Nome = "Excel 2021";      Exe = "EXCEL.EXE"    },
            @{ Nome = "PowerPoint 2021"; Exe = "POWERPNT.EXE" },
            @{ Nome = "Outlook 2021";    Exe = "OUTLOOK.EXE"  },
            @{ Nome = "Access 2021";     Exe = "MSACCESS.EXE" },
            @{ Nome = "OneNote 2021";    Exe = "ONENOTE.EXE"  }
        )

        $officePaths = @(
            "$env:ProgramFiles\Microsoft Office\root\Office16",
            "$env:ProgramFiles\Microsoft Office\Office16",
            "${env:ProgramFiles(x86)}\Microsoft Office\root\Office16",
            "${env:ProgramFiles(x86)}\Microsoft Office\Office16"
        )

        foreach ($app in $apps) {
            $exePath = $null
            foreach ($dir in $officePaths) {
                $c = Join-Path $dir $app.Exe
                if (Test-Path $c) { $exePath = $c; break }
            }
            if (-not $exePath) {
                Write-Host "  [AVISO] $($app.Nome) nao encontrado." -ForegroundColor Yellow
                continue
            }
            $atalho = $shell.CreateShortcut("$desktopPath\$($app.Nome).lnk")
            $atalho.TargetPath = $exePath
            $atalho.Save()
            Write-Host "  [OK] Atalho criado: $($app.Nome)" -ForegroundColor Green
            $criados++
        }

        Write-Host ""
        Write-Host "  $criados atalho(s) criado(s) na Area de Trabalho." -ForegroundColor Green
    """
    _ps(ps_script)
    print()
    input("  Pressione Enter para continuar...")


# ─── Acoes especiais: Redes ───────────────────────────────────────────────────

def _obter_ip_publico():
    _clear()
    print()
    print("  === Obter IP Publico ===")
    print()
    print("  Consultando IP publico via api.ipify.org...")
    ps_script = r"""
        try {
            $ip = Invoke-RestMethod -Uri "https://api.ipify.org?format=json" | Select-Object -ExpandProperty ip
            Write-Host ""
            Write-Host "  IP Publico: $ip" -ForegroundColor Green
        } catch {
            Write-Host ""
            Write-Host "  [ERRO] Nao foi possivel obter o IP publico: $_" -ForegroundColor Red
        }
    """
    _ps(ps_script)
    print()
    input("  Pressione Enter para continuar...")


def _obter_ip_local():
    _clear()
    print()
    print("  === Obter IP Local ===")
    print()
    print("  Interfaces de rede detectadas:")
    print()
    ps_script = r"""
        $adapters = Get-NetIPAddress -AddressFamily IPv4 |
                    Where-Object { $_.IPAddress -ne "127.0.0.1" } |
                    Select-Object InterfaceAlias, IPAddress, PrefixLength

        if ($adapters) {
            foreach ($a in $adapters) {
                Write-Host "  $($a.InterfaceAlias): $($a.IPAddress)/$($a.PrefixLength)" -ForegroundColor Green
            }
        } else {
            Write-Host "  [AVISO] Nenhuma interface com IP encontrada." -ForegroundColor Yellow
        }

        Write-Host ""
        Write-Host "  ----- ipconfig -----" -ForegroundColor DarkGray
        ipconfig
    """
    _ps(ps_script)
    print()
    input("  Pressione Enter para continuar...")


def _rota_conexao():
    _clear()
    print()
    print("  === Obter Rota de Conexao (Traceroute) ===")
    print()
    dominio = input("  Informe o dominio (ex.: google.com): ").strip()
    if not dominio:
        print()
        print("  Dominio invalido. Operacao cancelada.")
        input("  Pressione Enter para voltar...")
        return
    print()
    print(f"  Rastreando rota ate '{dominio}'... (pode levar alguns segundos)")

    ps_script = f"""
        try {{
            $ip = [System.Net.Dns]::GetHostAddresses("{dominio}") |
                  Select-Object -First 1 -ExpandProperty IPAddressToString
            Write-Host ""
            Write-Host "  Dominio : {dominio}" -ForegroundColor Cyan
            Write-Host "  IP      : $ip" -ForegroundColor Cyan
            Write-Host ""
            Write-Host "  Rota:" -ForegroundColor DarkGray
            $result = Test-NetConnection -TraceRoute -ComputerName $ip -ErrorAction Stop
            $hops = $result | Select-Object -ExpandProperty TraceRoute
            $i = 1
            foreach ($hop in $hops) {{
                Write-Host "    $i. $hop"
                $i++
            }}
            Write-Host ""
            Write-Host "  Destino alcancado: $($result.TcpTestSucceeded -or $result.PingSucceeded)" -ForegroundColor Green
        }} catch {{
            Write-Host ""
            Write-Host "  [ERRO] Falha ao rastrear rota: $_" -ForegroundColor Red
        }}
    """
    _ps(ps_script)
    print()
    input("  Pressione Enter para continuar...")


# ─── Secoes do menu principal ─────────────────────────────────────────────────

def menu_quickwindows():
    _submenu("QuickWindowsX / Menu", [
        "Atualizar QuickWindows",
        "Deletar QuickWindows",
        "Recarregar QuickWindows",
        "Documentacao do QuickWindows",
        "Gerenciar Senha de Acesso",
    ], _ACOES_MENU_QWX)


def windows():
    _submenu("QuickWindowsX / Windows", _OPCOES_WINDOWS, _ACOES_WINDOWS)


def internet():
    _submenu("QuickWindowsX / Internet", [
        "AnyDesk",
        "RustDesk",
        "HopToDesk",
        "Criar atalho de PCs remotos com AnyDesk",
        "Reset AnyDesk",
        "Microsoft Edge",
        "Google Chrome",
        "Google Earth Pro",
        "Skype",
        "Opera",
        "Mozilla Firefox",
        "Real VNC Viewer",
        "Transmission",
        "IDM - Internet Download Manager",
        "Baixar URL",
    ], {
        1:  _instalar("Internet", "AnyDesk"),
        2:  _instalar("Internet", "RustDesk"),
        3:  _instalar("Internet", "HopToDesk"),
        4:  _atalho_pcs_remotos,
        5:  _reset_anydesk,
        6:  _instalar("Internet", "Microsoft Edge"),
        7:  _instalar("Internet", "Google Chrome"),
        8:  _instalar("Internet", "Google Earth Pro"),
        9:  _instalar("Internet", "Skype"),
        10: _instalar("Internet", "Opera"),
        11: _instalar("Internet", "Mozilla Firefox"),
        12: _instalar("Internet", "Real VNC Viewer"),
        13: _instalar("Internet", "Transmission"),
        14: _instalar("Internet", "IDM - Internet Download Manager"),
        15: _baixar_url,
    })


def utilitarios():
    _submenu("QuickWindowsX / Utilitarios para Windows", [
        "Revo Uninstaller",
        "Revo Uninstaller Portable",
        "WinRAR",
        "WinZip",
        "7-Zip",
        "Acrobat Reader DC",
        "Foxit PDF Reader",
        "VLC Media Player",
        "Deep Freeze Standard",
        "Shadow Defender",
        "Compressao de arquivos - PowerShell Backup Automatico (.zip)",
        "Cobian Backup",
        "MiniTool Partition Wizard v12 Instalacao",
        "MiniTool Partition Wizard v12 32bit Portable",
        "MiniTool Partition Wizard v12 64bit Portable",
        "WinToHDD",
        "Hasleo WinToHDD Free",
        "Rufus",
        "DriverMax",
        "Driver Booster Free",
        "CPU-Z",
        "CPU-Z Portable",
        "Crystal Disk Info",
        "Crystal Disk Info Portable",
        "Limpar Spooler de Impressao",
        "Limpar Arquivos Temporarios",
        "Windows Update Activation",
        "SiberiaProg-CH341A",
        "SiberiaProg-CH341A Portable",
        "Open Hardware Monitor",
        "Moo0 System Monitor",
        "WizTree",
        "WizTree64",
        "Battery Report",
    ], {
        1:  _instalar("UtilitiesForWindows", "Revo Uninstaller"),
        2:  _instalar("UtilitiesForWindows", "Revo Uninstaller Portable"),
        3:  _instalar("UtilitiesForWindows", "WinRAR"),
        4:  _instalar("UtilitiesForWindows", "WinZip"),
        5:  _instalar("UtilitiesForWindows", "7-Zip"),
        6:  _instalar("UtilitiesForWindows", "Acrobat Reader DC"),
        7:  _instalar("UtilitiesForWindows", "Foxit PDF Reader"),
        8:  _instalar("UtilitiesForWindows", "VLC Media Player"),
        9:  _instalar("UtilitiesForWindows", "Deep Freeze Standard"),
        10: _instalar("UtilitiesForWindows", "Shadow Defender"),
        11: _backup_zip,
        12: _instalar("UtilitiesForWindows", "Cobian Backup"),
        13: _instalar("UtilitiesForWindows", "MiniTool Partition Wizard v12 Instalacao"),
        14: _instalar("UtilitiesForWindows", "MiniTool Partition Wizard v12 32bit Portable"),
        15: _instalar("UtilitiesForWindows", "MiniTool Partition Wizard v12 64bit Portable"),
        16: _instalar("UtilitiesForWindows", "WinToHDD"),
        17: _instalar("UtilitiesForWindows", "Hasleo WinToHDD Free"),
        18: _instalar("UtilitiesForWindows", "Rufus"),
        19: _instalar("UtilitiesForWindows", "DriverMax"),
        20: _instalar("UtilitiesForWindows", "Driver Booster Free"),
        21: _instalar("UtilitiesForWindows", "CPU-Z"),
        22: _instalar("UtilitiesForWindows", "CPU-Z Portable"),
        23: _instalar("UtilitiesForWindows", "Crystal Disk Info"),
        24: _instalar("UtilitiesForWindows", "Crystal Disk Info Portable"),
        25: _limpar_spooler,
        26: _limpar_temporarios,
        27: _instalar("UtilitiesForWindows", "Windows Update Activation"),
        28: _instalar("UtilitiesForWindows", "SiberiaProg-CH341A"),
        29: _instalar("UtilitiesForWindows", "SiberiaProg-CH341A Portable"),
        30: _instalar("UtilitiesForWindows", "Open Hardware Monitor"),
        31: _instalar("UtilitiesForWindows", "Moo0 System Monitor"),
        32: _instalar("UtilitiesForWindows", "WizTree"),
        33: _instalar("UtilitiesForWindows", "WizTree64"),
        34: _battery_report,
    })


def escritorio():
    _submenu("QuickWindowsX / Softwares para Escritorio", [
        "Microsoft Office 365",
        "Microsoft Office 2016 a 2019",
        "Microsoft Office 2019 a 2021",
        "Criar atalhos para Apps do Office 2021",
    ], {
        1: _instalar("OfficeSoftware", "Microsoft Office 365"),
        2: _instalar("OfficeSoftware", "Microsoft Office 2016 a 2019"),
        3: _instalar("OfficeSoftware", "Microsoft Office 2019 a 2021"),
        4: _atalhos_office_2021,
    })


def sistemas_operacionais():
    _submenu("QuickWindowsX / Sistemas Operacionais Microsoft", [
        "Windows 10 22H2 Portugues x32",
        "Windows 10 22H2 Portugues x64",
        "Windows 11 24H2 Portugues x64",
    ], {
        1: _instalar("MicrosoftOperatingSystems", "Windows 10 22H2 Portugues x32"),
        2: _instalar("MicrosoftOperatingSystems", "Windows 10 22H2 Portugues x64"),
        3: _instalar("MicrosoftOperatingSystems", "Windows 11 24H2 Portugues x64"),
    })


# ─── Secoes ainda sem submenu ─────────────────────────────────────────────────

def _show(name):
    _clear()
    print()
    print(f"  [{name}]")
    print()
    print("  Esta secao ainda esta em desenvolvimento.")
    print()
    input("  Pressione Enter para voltar ao menu principal...")


def _executar_comando_ps():
    _clear()
    print()
    print("  === Execucao de Comandos no PowerShell ===")
    print()
    print("  Cada comando sera executado em uma nova janela do PowerShell.")
    print("  A janela permanece aberta para voce ver o resultado.")
    print("  Digite '0' para voltar ao menu.")
    print()

    while True:
        cmd = input("  Comando: ").strip()

        if cmd == "0":
            return

        if not cmd:
            continue

        if os.name != "nt":
            print()
            print(f"  [INFO] Execucao disponivel apenas no Windows.")
            print(f"  Comando: {cmd}")
            print()
            continue

        subprocess.Popen(
            ["powershell", "-NoProfile", "-ExecutionPolicy", "Bypass",
             "-NoExit", "-Command", cmd],
            creationflags=subprocess.CREATE_NEW_CONSOLE,
        )

        print()
        print("  Comando enviado para nova janela do PowerShell.")
        print()


def redes():
    _submenu("QuickWindowsX / Redes", [
        "Obter IP publico",
        "Obter IP local",
        "Obter IPs de uma determinada rota",
    ], {
        1: _obter_ip_publico,
        2: _obter_ip_local,
        3: _rota_conexao,
    })


def powershell():
    _executar_comando_ps()


def rotinas():
    _G  = "\033[92m"   # verde
    _R  = "\033[91m"   # vermelho
    _C  = "\033[96m"   # ciano
    _N  = "\033[2m"    # dim
    _X  = "\033[0m"    # reset
    SEP = "  " + "─" * 76

    def _linha(num, label, ok=True, indent=0):
        esp    = " " * indent
        cor    = _G if ok else _R
        status = "[ ok ]" if ok else "[null]"
        txt    = f"  {esp}{num} = {label}"
        pad    = max(1, 74 - len(txt))
        print(f"{cor}{txt}{' ' * pad}{status}{_X}")

    def _abrir(cmd, args=""):
        if args:
            _ps(f'Start-Process "{cmd}" -ArgumentList "{args}"')
        else:
            _ps(f'Start-Process "{cmd}"')

    _MAPA = {
        # ── 1x: Menu QuickWindowsX ───────────────────────────────────────────
        "11": ("Atualizar QuickWindowsX",                         _atualizar_quickwindowsx),
        "13": ("Recarregar QuickWindowsX",                        _recarregar_quickwindowsx),
        "14": ("Documentacao do QuickWindowsX",                   _documentacao_quickwindowsx),
        "15": ("Gerenciar Senha de Acesso",                       _gerenciar_senha),
        # ── 2x: Windows ──────────────────────────────────────────────────────
        "21": ("Desligar o Windows",                              _desligar_windows),
        "22": ("Reiniciar o Windows",                             _reiniciar_windows),
        "23": ("Agendar desligamento do Windows",                 _agendar_desligamento),
        "24": ("Atualizar Windows e Softwares",                   _atualizar_windows_softwares),
        "251":  ("Painel de Controle",                            lambda: _abrir("control")),
        "252":  ("Editor de Registro (RegEdit)",                  lambda: _abrir("regedit")),
        "253":  ("Configuracoes do Sistema (MSConfig)",           lambda: _abrir("msconfig")),
        "254":  ("Servicos (services.msc)",                       lambda: _abrir("services.msc")),
        "255":  ("Gerenciador de Dispositivos (devmgmt.msc)",     lambda: _abrir("devmgmt.msc")),
        "256":  ("Gerenciamento de Discos (diskmgmt.msc)",        lambda: _abrir("diskmgmt.msc")),
        "257":  ("Explorador de Arquivos do Windows",             lambda: _abrir("explorer")),
        "258":  ("Configuracoes de Tela (desk.cpl)",              lambda: _abrir("desk.cpl")),
        "259":  ("Configuracoes avancadas do sistema (sysdm.cpl)",lambda: _abrir("sysdm.cpl")),
        "2510": ("Configuracoes do Plano (powercfg.cpl)",         lambda: _abrir("powercfg.cpl")),
        "2511": ("Sobre o Windows (winver)",                      lambda: _abrir("winver")),
        "2512": ("Gerenciar arquivos e pastas",                   _gerenciar_arquivos_pastas),
        "2513": ("Configuracoes do Windows (ms-settings)",        lambda: _abrir("ms-settings:")),
        "2514": ("Gerenciador de Tarefas (taskmgr)",              lambda: _abrir("taskmgr")),
        "2515": ("Opcoes de pastas",                              lambda: _abrir("control", "folders")),
        "2516": ("Informacoes do Sistema",                        _informacoes_sistema),
        "26":   ("Criar atalhos Desligar e Reiniciar",            _criar_atalhos),
        "27":   ("Reiniciar e entrar na BIOS",                    _reiniciar_bios),
        # ── 3x: Internet ─────────────────────────────────────────────────────
        "31":  ("AnyDesk",                                        _instalar("Internet", "AnyDesk")),
        "32":  ("RustDesk",                                       _instalar("Internet", "RustDesk")),
        "33":  ("HopToDesk",                                      _instalar("Internet", "HopToDesk")),
        "34":  ("Criar atalho de PCs remotos com AnyDesk",        _atalho_pcs_remotos),
        "35":  ("Reset AnyDesk",                                  _reset_anydesk),
        "36":  ("Microsoft Edge",                                 _instalar("Internet", "Microsoft Edge")),
        "37":  ("Google Chrome",                                  _instalar("Internet", "Google Chrome")),
        "38":  ("Google Earth Pro",                               _instalar("Internet", "Google Earth Pro")),
        "39":  ("Skype",                                          _instalar("Internet", "Skype")),
        "310": ("Opera",                                          _instalar("Internet", "Opera")),
        "311": ("Mozilla Firefox",                                _instalar("Internet", "Mozilla Firefox")),
        "312": ("Real VNC Viewer",                                _instalar("Internet", "Real VNC Viewer")),
        "313": ("Transmission",                                   _instalar("Internet", "Transmission")),
        "314": ("IDM - Internet Download Manager",                _instalar("Internet", "IDM - Internet Download Manager")),
        "315": ("Baixar URL",                                     _baixar_url),
        # ── 4x: Redes ────────────────────────────────────────────────────────
        "41":  ("Obter IP publico",                               _obter_ip_publico),
        "42":  ("Obter IP local",                                 _obter_ip_local),
        "43":  ("Obter IPs de uma determinada rota",              _rota_conexao),
        # ── 6x: Utilitarios para Windows ─────────────────────────────────────
        "61":  ("Revo Uninstaller",                               _instalar("UtilitiesForWindows", "Revo Uninstaller")),
        "62":  ("Revo Uninstaller Portable",                      _instalar("UtilitiesForWindows", "Revo Uninstaller Portable")),
        "63":  ("WinRAR",                                         _instalar("UtilitiesForWindows", "WinRAR")),
        "64":  ("WinZip",                                         _instalar("UtilitiesForWindows", "WinZip")),
        "65":  ("7-Zip",                                          _instalar("UtilitiesForWindows", "7-Zip")),
        "66":  ("Acrobat Reader DC",                              _instalar("UtilitiesForWindows", "Acrobat Reader DC")),
        "67":  ("Foxit PDF Reader",                               _instalar("UtilitiesForWindows", "Foxit PDF Reader")),
        "68":  ("VLC Media Player",                               _instalar("UtilitiesForWindows", "VLC Media Player")),
        "69":  ("Deep Freeze Standard",                           _instalar("UtilitiesForWindows", "Deep Freeze Standard")),
        "610": ("Shadow Defender",                                _instalar("UtilitiesForWindows", "Shadow Defender")),
        "611": ("Backup Automatico (.zip)",                       _backup_zip),
        "612": ("Cobian Backup",                                  _instalar("UtilitiesForWindows", "Cobian Backup")),
        "613": ("MiniTool Partition Wizard v12 Instalacao",       _instalar("UtilitiesForWindows", "MiniTool Partition Wizard v12 Instalacao")),
        "614": ("MiniTool Partition Wizard v12 32bit Portable",   _instalar("UtilitiesForWindows", "MiniTool Partition Wizard v12 32bit Portable")),
        "615": ("MiniTool Partition Wizard v12 64bit Portable",   _instalar("UtilitiesForWindows", "MiniTool Partition Wizard v12 64bit Portable")),
        "616": ("WinToHDD",                                       _instalar("UtilitiesForWindows", "WinToHDD")),
        "617": ("Hasleo WinToHDD Free",                           _instalar("UtilitiesForWindows", "Hasleo WinToHDD Free")),
        "618": ("Rufus",                                          _instalar("UtilitiesForWindows", "Rufus")),
        "619": ("DriverMax",                                      _instalar("UtilitiesForWindows", "DriverMax")),
        "620": ("Driver Booster Free",                            _instalar("UtilitiesForWindows", "Driver Booster Free")),
        "621": ("CPU-Z",                                          _instalar("UtilitiesForWindows", "CPU-Z")),
        "622": ("CPU-Z Portable",                                 _instalar("UtilitiesForWindows", "CPU-Z Portable")),
        "623": ("Crystal Disk Info",                              _instalar("UtilitiesForWindows", "Crystal Disk Info")),
        "624": ("Crystal Disk Info Portable",                     _instalar("UtilitiesForWindows", "Crystal Disk Info Portable")),
        "625": ("Limpar Spooler de Impressao",                    _limpar_spooler),
        "626": ("Limpar Arquivos Temporarios",                    _limpar_temporarios),
        "627": ("Windows Update Activation",                      _instalar("UtilitiesForWindows", "Windows Update Activation")),
        "628": ("SiberiaProg-CH341A",                             _instalar("UtilitiesForWindows", "SiberiaProg-CH341A")),
        "629": ("SiberiaProg-CH341A Portable",                    _instalar("UtilitiesForWindows", "SiberiaProg-CH341A Portable")),
        "630": ("Open Hardware Monitor",                          _instalar("UtilitiesForWindows", "Open Hardware Monitor")),
        "631": ("Moo0 System Monitor",                            _instalar("UtilitiesForWindows", "Moo0 System Monitor")),
        "632": ("WizTree",                                        _instalar("UtilitiesForWindows", "WizTree")),
        "633": ("WizTree64",                                      _instalar("UtilitiesForWindows", "WizTree64")),
        "634": ("Battery Report",                                 _battery_report),
        # ── 7x: Softwares para Escritorio ────────────────────────────────────
        "71":  ("Microsoft Office 365",                           _instalar("OfficeSoftware", "Microsoft Office 365")),
        "72":  ("Microsoft Office 2016 a 2019",                   _instalar("OfficeSoftware", "Microsoft Office 2016 a 2019")),
        "73":  ("Microsoft Office 2019 a 2021",                   _instalar("OfficeSoftware", "Microsoft Office 2019 a 2021")),
        "74":  ("Criar atalhos para Apps do Office 2021",         _atalhos_office_2021),
        # ── 8x: Sistemas Operacionais Microsoft ──────────────────────────────
        "81":  ("Windows 10 22H2 Portugues x32",                  _instalar("MicrosoftOperatingSystems", "Windows 10 22H2 Portugues x32")),
        "82":  ("Windows 10 22H2 Portugues x64",                  _instalar("MicrosoftOperatingSystems", "Windows 10 22H2 Portugues x64")),
        "83":  ("Windows 11 24H2 Portugues x64",                  _instalar("MicrosoftOperatingSystems", "Windows 11 24H2 Portugues x64")),
    }

    while True:
        _clear()
        print()
        print(f"  {_C}=== QuickWindowsX / Executar Rotinas ==={_X}")
        print()
        print(f"{_G}    0 = Voltar{_X}")
        print(SEP)

        # ── Sessao 1 ──────────────────────────────────────────────────────────
        print(f"{_C}    1 = Menu QuickWindowsX{_X}")
        _linha("11", "Atualizar QuickWindowsX",                         ok=True,  indent=4)
        _linha("12", "Deletar QuickWindowsX",                           ok=False, indent=4)
        _linha("13", "Recarregar QuickWindowsX",                        ok=True,  indent=4)
        _linha("14", "Documentacao do QuickWindowsX",                   ok=True,  indent=4)
        _linha("15", "Gerenciar Senha de Acesso",                       ok=True,  indent=4)
        print(SEP)

        # ── Sessao 2 ──────────────────────────────────────────────────────────
        print(f"{_C}    2 = Windows{_X}")
        _linha("21", "Desligar o Windows",                              ok=True,  indent=4)
        _linha("22", "Reiniciar o Windows",                             ok=True,  indent=4)
        _linha("23", "Agendar desligamento do Windows",                 ok=True,  indent=4)
        _linha("24", "Atualizar Windows e Softwares",                   ok=True,  indent=4)
        print(f"{_N}        25 = Acesso rapido as Configuracoes{_X}")
        _linha("251",  "Painel de Controle",                            ok=True,  indent=8)
        _linha("252",  "Editor de Registro (RegEdit)",                  ok=True,  indent=8)
        _linha("253",  "Configuracoes do Sistema (MSConfig)",           ok=True,  indent=8)
        _linha("254",  "Servicos (services.msc)",                       ok=True,  indent=8)
        _linha("255",  "Gerenciador de Dispositivos (devmgmt.msc)",     ok=True,  indent=8)
        _linha("256",  "Gerenciamento de Discos (diskmgmt.msc)",        ok=True,  indent=8)
        _linha("257",  "Explorador de Arquivos do Windows",             ok=True,  indent=8)
        _linha("258",  "Configuracoes de Tela (desk.cpl)",              ok=True,  indent=8)
        _linha("259",  "Configuracoes avancadas do sistema (sysdm.cpl)",ok=True,  indent=8)
        _linha("2510", "Configuracoes do Plano (powercfg.cpl)",         ok=True,  indent=8)
        _linha("2511", "Sobre o Windows (winver)",                      ok=True,  indent=8)
        _linha("2512", "Gerenciar arquivos e pastas",                   ok=True,  indent=8)
        _linha("2513", "Configuracoes do Windows (ms-settings)",        ok=True,  indent=8)
        _linha("2514", "Gerenciador de Tarefas (taskmgr)",              ok=True,  indent=8)
        _linha("2515", "Opcoes de pastas",                              ok=True,  indent=8)
        _linha("2516", "Informacoes do Sistema",                        ok=True,  indent=8)
        _linha("26",   "Criar atalhos Desligar e Reiniciar",            ok=True,  indent=4)
        _linha("27",   "Reiniciar e entrar na BIOS",                    ok=True,  indent=4)
        print(SEP)

        # ── Sessao 3 ──────────────────────────────────────────────────────────
        print(f"{_C}    3 = Internet{_X}")
        _linha("31",  "AnyDesk",                                        ok=True,  indent=4)
        _linha("32",  "RustDesk",                                       ok=True,  indent=4)
        _linha("33",  "HopToDesk",                                      ok=True,  indent=4)
        _linha("34",  "Criar atalho de PCs remotos com AnyDesk",        ok=True,  indent=4)
        _linha("35",  "Reset AnyDesk",                                  ok=True,  indent=4)
        _linha("36",  "Microsoft Edge",                                 ok=True,  indent=4)
        _linha("37",  "Google Chrome",                                  ok=True,  indent=4)
        _linha("38",  "Google Earth Pro",                               ok=True,  indent=4)
        _linha("39",  "Skype",                                          ok=True,  indent=4)
        _linha("310", "Opera",                                          ok=True,  indent=4)
        _linha("311", "Mozilla Firefox",                                ok=True,  indent=4)
        _linha("312", "Real VNC Viewer",                                ok=True,  indent=4)
        _linha("313", "Transmission",                                   ok=True,  indent=4)
        _linha("314", "IDM - Internet Download Manager",                ok=True,  indent=4)
        _linha("315", "Baixar URL",                                     ok=True,  indent=4)
        print(SEP)

        # ── Sessao 4 ──────────────────────────────────────────────────────────
        print(f"{_C}    4 = Redes{_X}")
        _linha("41", "Obter IP publico",                                ok=True,  indent=4)
        _linha("42", "Obter IP local",                                  ok=True,  indent=4)
        _linha("43", "Obter IPs de uma determinada rota",               ok=True,  indent=4)
        print(SEP)

        # ── Sessao 5 ──────────────────────────────────────────────────────────
        _linha("5", "Execucao de Comandos no PowerShell",               ok=False, indent=0)
        print(SEP)

        # ── Sessao 6 ──────────────────────────────────────────────────────────
        print(f"{_C}    6 = Utilitarios para Windows{_X}")
        _linha("61",  "Revo Uninstaller",                               ok=True,  indent=4)
        _linha("62",  "Revo Uninstaller Portable",                      ok=True,  indent=4)
        _linha("63",  "WinRAR",                                         ok=True,  indent=4)
        _linha("64",  "WinZip",                                         ok=True,  indent=4)
        _linha("65",  "7-Zip",                                          ok=True,  indent=4)
        _linha("66",  "Acrobat Reader DC",                              ok=True,  indent=4)
        _linha("67",  "Foxit PDF Reader",                               ok=True,  indent=4)
        _linha("68",  "VLC Media Player",                               ok=True,  indent=4)
        _linha("69",  "Deep Freeze Standard",                           ok=True,  indent=4)
        _linha("610", "Shadow Defender",                                ok=True,  indent=4)
        _linha("611", "Backup Automatico (.zip)",                       ok=True,  indent=4)
        _linha("612", "Cobian Backup",                                  ok=True,  indent=4)
        _linha("613", "MiniTool Partition Wizard v12 Instalacao",       ok=True,  indent=4)
        _linha("614", "MiniTool Partition Wizard v12 32bit Portable",   ok=True,  indent=4)
        _linha("615", "MiniTool Partition Wizard v12 64bit Portable",   ok=True,  indent=4)
        _linha("616", "WinToHDD",                                       ok=True,  indent=4)
        _linha("617", "Hasleo WinToHDD Free",                           ok=True,  indent=4)
        _linha("618", "Rufus",                                          ok=True,  indent=4)
        _linha("619", "DriverMax",                                      ok=True,  indent=4)
        _linha("620", "Driver Booster Free",                            ok=True,  indent=4)
        _linha("621", "CPU-Z",                                          ok=True,  indent=4)
        _linha("622", "CPU-Z Portable",                                 ok=True,  indent=4)
        _linha("623", "Crystal Disk Info",                              ok=True,  indent=4)
        _linha("624", "Crystal Disk Info Portable",                     ok=True,  indent=4)
        _linha("625", "Limpar Spooler de Impressao",                    ok=True,  indent=4)
        _linha("626", "Limpar Arquivos Temporarios",                    ok=True,  indent=4)
        _linha("627", "Windows Update Activation",                      ok=True,  indent=4)
        _linha("628", "SiberiaProg-CH341A",                             ok=True,  indent=4)
        _linha("629", "SiberiaProg-CH341A Portable",                    ok=True,  indent=4)
        _linha("630", "Open Hardware Monitor",                          ok=True,  indent=4)
        _linha("631", "Moo0 System Monitor",                            ok=True,  indent=4)
        _linha("632", "WizTree",                                        ok=True,  indent=4)
        _linha("633", "WizTree64",                                      ok=True,  indent=4)
        _linha("634", "Battery Report",                                 ok=True,  indent=4)
        print(SEP)

        # ── Sessao 7 ──────────────────────────────────────────────────────────
        print(f"{_C}    7 = Softwares para Escritorio{_X}")
        _linha("71", "Microsoft Office 365",                            ok=True,  indent=4)
        _linha("72", "Microsoft Office 2016 a 2019",                    ok=True,  indent=4)
        _linha("73", "Microsoft Office 2019 a 2021",                    ok=True,  indent=4)
        _linha("74", "Criar atalhos para Apps do Office 2021",          ok=True,  indent=4)
        print(SEP)

        # ── Sessao 8 ──────────────────────────────────────────────────────────
        print(f"{_C}    8 = Sistemas Operacionais Microsoft{_X}")
        _linha("81", "Windows 10 22H2 Portugues x32",                   ok=True,  indent=4)
        _linha("82", "Windows 10 22H2 Portugues x64",                   ok=True,  indent=4)
        _linha("83", "Windows 11 24H2 Portugues x64",                   ok=True,  indent=4)
        print(SEP)
        print()
        print("  Exemplo: 37, 63, 65, 623")
        print("  Digite 0 para voltar.")
        print()

        entrada = input("  Rotinas: ").strip()

        if entrada == "0":
            return

        if not entrada:
            continue

        numeros  = [x.strip() for x in entrada.split(",")]
        validos  = [n for n in numeros if n in _MAPA]
        invalidos = [n for n in numeros if n and n not in _MAPA]

        if invalidos:
            print()
            print(f"  {_R}[!] Rotinas nao reconhecidas: {', '.join(invalidos)}{_X}")
            if not validos:
                input("  Pressione Enter para continuar...")
                continue
            input("  Pressione Enter para executar as validas...")

        if not validos:
            continue

        _clear()
        print()
        print(f"  {_C}Executando {len(validos)} rotina(s): {', '.join(validos)}{_X}")
        print()
        for i, num in enumerate(validos, 1):
            label, fn = _MAPA[num]
            print(f"  [{i}/{len(validos)}] {num} = {label}")
            print()
            fn()

        print()
        print(f"  {_G}Rotinas concluidas: {', '.join(validos)}{_X}")
        input("  Pressione Enter para continuar...")
