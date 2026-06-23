# install.ps1 - Instalador e iniciador do QuickWindowsX
#
# Autor: Marcos Aurélio R. da Silva <systemboys@hotmail.com>
# Manutenção: Marcos Aurélio R. da Silva <systemboys@hotmail.com>
#
# ──────────────────────────────────────────────────────────────────────────────
# Este script instala o QuickWindowsX no diretório Temp do usuário,
# cria um atalho na Área de Trabalho e inicia o menu interativo.
# ──────────────────────────────────────────────────────────────────────────────
# Histórico:
# v1.0.0 2026-06-23 às 00h00, Marcos Aurélio:
#   - Versão inicial do instalador/iniciador do QuickWindowsX.
#
# Licença: GPL.

Clear-Host

# ─── Comando de execução (salvo no atalho da Área de Trabalho) ────────────────
$QWXCommand = "irm qwx.gti1.com.br | iex"

# ─── Verificar administrador ──────────────────────────────────────────────────
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "Reiniciando como administrador..."
    Start-Process powershell -Verb RunAs -ArgumentList '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', $QWXCommand
    exit
}

# ─── Configuracao do terminal ─────────────────────────────────────────────────
$Host.UI.RawUI.BackgroundColor = "Black"
Clear-Host
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

# ─── ExecutionPolicy ─────────────────────────────────────────────────────────
try {
    $restricted = Get-ExecutionPolicy -List |
                  Where-Object { $_.Scope -in @('MachinePolicy', 'UserPolicy') -and $_.ExecutionPolicy -ne 'Undefined' }
    if (-not $restricted) {
        Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned -Force -ErrorAction SilentlyContinue
    }
} catch {}

# ─── Diretório GTiSupport ─────────────────────────────────────────────────────
$gtiDir = Join-Path $env:USERPROFILE "GTiSupport"
if (-not (Test-Path $gtiDir)) {
    New-Item -ItemType Directory -Path $gtiDir -Force | Out-Null
    Write-Host "Diretorio criado: $gtiDir"
}

# ─── Funcao de log ────────────────────────────────────────────────────────────
function Write-QWXLog([string]$msg) {
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path "$gtiDir\QWX_Log.txt" -Value "$ts | $msg" -ErrorAction SilentlyContinue
}

Write-QWXLog "QuickWindowsX: instalador iniciado."

# ─── Atalho na Área de Trabalho ──────────────────────────────────────────────
$desktopPath  = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::DesktopDirectory)
$shortcutPath = Join-Path $desktopPath "GTi Support QWX.lnk"
$iconUrl      = "https://raw.githubusercontent.com/systemboys/QuickWindowsX/main/Images/QuickWindowsX.ico"
$iconPath     = Join-Path $gtiDir "QuickWindowsX.ico"

try {
    Invoke-WebRequest -Uri $iconUrl -OutFile $iconPath -ErrorAction Stop
} catch {
    $iconPath = ""
    Write-Host "Icone nao disponivel — atalho sera criado sem icone personalizado."
}

$shell             = New-Object -ComObject WScript.Shell
$shortcut          = $shell.CreateShortcut($shortcutPath)
$shortcut.TargetPath  = "powershell.exe"
$shortcut.Arguments   = "-NoProfile -ExecutionPolicy Bypass -Command `"$QWXCommand`""
if ($iconPath -and (Test-Path $iconPath)) { $shortcut.IconLocation = $iconPath }
$shortcut.Description = "QuickWindowsX - Menu interativo para manutencao e instalacoes no Windows"
$shortcut.Save()

Write-Host "Atalho criado: $shortcutPath"
Write-QWXLog "Atalho criado na Area de Trabalho."

# ─── Verificar / baixar QuickWindowsX ────────────────────────────────────────
$qwxDir  = "$env:TEMP\QuickWindowsX"
$qwxZip  = "$env:TEMP\QuickWindowsX.zip"
$qwxTemp = "$env:TEMP\QuickWindowsX-main"

if (Test-Path "$qwxDir\main.py") {
    Write-Host ""
    Write-Host "QuickWindowsX localizado em: $qwxDir"
} else {
    # Limpar restos de instalacao anterior
    foreach ($p in @($qwxDir, $qwxTemp, $qwxZip)) {
        if (Test-Path $p) { Remove-Item -Recurse -Force $p -ErrorAction SilentlyContinue }
    }

    Write-Host ""
    Write-Host "Baixando QuickWindowsX..."
    Write-QWXLog "Iniciando download do QuickWindowsX."

    $zipUrl     = "https://github.com/systemboys/QuickWindowsX/archive/refs/heads/main.zip"
    $downloaded = $false

    try {
        Start-BitsTransfer -Source $zipUrl -Destination $qwxZip -ErrorAction Stop
        $downloaded = $true
    } catch {
        try {
            Invoke-WebRequest -Uri $zipUrl -OutFile $qwxZip -ErrorAction Stop
            $downloaded = $true
        } catch {
            Write-Host ""
            Write-Host "  [ERRO] Falha ao baixar QuickWindowsX:" -ForegroundColor Red
            Write-Host "  $_" -ForegroundColor DarkGray
            Write-QWXLog "ERRO: falha ao baixar — $_"
            Write-Host ""
            Write-Host "  Pressione Enter para fechar..."
            $null = Read-Host
            exit 1
        }
    }

    if ($downloaded) {
        Write-Host "Extraindo..."
        Expand-Archive -Path $qwxZip -DestinationPath $env:TEMP -Force
        Remove-Item -Path $qwxZip -Force -ErrorAction SilentlyContinue

        if (Test-Path $qwxTemp) {
            Rename-Item -Path $qwxTemp -NewName "QuickWindowsX"
            Write-Host "QuickWindowsX instalado em: $qwxDir"
            Write-QWXLog "QuickWindowsX extraido em: $qwxDir."
        } else {
            Write-Host ""
            Write-Host "  [ERRO] Extracao falhou — diretorio nao encontrado." -ForegroundColor Red
            Write-QWXLog "ERRO: extracao falhou."
            Write-Host ""
            Write-Host "  Pressione Enter para fechar..."
            $null = Read-Host
            exit 1
        }
    }
}

# ─── Animacao de inicializacao ────────────────────────────────────────────────
function Show-QWXBoot {
    function Show-OkLine([string]$msg) {
        Write-Host "[ " -NoNewline
        Write-Host "OK" -NoNewline -ForegroundColor Green
        Write-Host " ] $msg"
        Start-Sleep -Milliseconds (Get-Random -InputObject @(80, 150, 280, 400))
    }

    $lines = @(
        "Started LSB: Record successful boot for GRUB.",
        "Reached target Host and Network Name Lookups.",
        "Started Thermal Daemon Service.",
        "Started WPA supplicant.",
        "Finished Remove Stale Online ext4 Metadata Check Snapshots.",
        "Started Network Manager.",
        "Started Avahi mDNS/DNS-SD Stack.",
        "Started Switcheroo Control Proxy service.",
        "Reached target Network.",
        "Starting Network Manager Wait Online...",
        "Started Make remote CUPS printers available locally.",
        "Starting OpenVPN service...",
        "Started Service for snap application... canonical-livepatch.",
        "Started Dispatcher daemon for systemd-networkd.",
        "Finished Permit User Sessions.",
        "Starting GNOME Display Manager...",
        "Starting Hold until boot process finishes up...",
        "Started Authorization Manager.",
        "Starting Modem Manager...",
        "Finished Set console scheme.",
        "Started GNOME Display Manager.",
        "Started Accounts Service.",
        "Started Disk Manager.",
        "Started Login Service.",
        "Started User Manager for UID 1000.",
        "QuickWindowsX ready."
    )

    foreach ($line in $lines) { Show-OkLine $line }
}

Clear-Host
Show-QWXBoot

# ─── Iniciar QuickWindowsX ────────────────────────────────────────────────────
Write-QWXLog "Iniciando QuickWindowsX via run.cmd."
Start-Process -FilePath "cmd.exe" -ArgumentList "/c `"`"$qwxDir\run.cmd`"`""
exit
