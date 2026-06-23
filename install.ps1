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
# v1.0.1 2026-06-23, Marcos Aurélio:
#   - Correção do lançamento final: powershell.exe -Verb runAs -File setup.ps1,
#     espelhando o padrão do QuickWindows que garante processo filho elevado.
#   - try/catch em BackgroundColor e TLS para compatibilidade com PS7/WT.
#   - -UseBasicParsing em todos os Invoke-WebRequest (PS5 sem IE configurado).
#   - try/catch global mantém janela aberta em caso de erro.
# v1.1.0 2026-06-23, Marcos Aurélio:
#   - Atalho "GTi Support QWX" criado na Área de Trabalho após instalação.
#   - Removida a animação de boot estilo GRUB do Linux.
# v1.1.1 2026-06-23, Marcos Aurélio:
#   - Removida a definição de fundo preto (deixa o padrão do terminal).
#   - URL do ícone corrigida: usa QuickWindows/raw enquanto QWX não tem ícone publicado.
# v1.1.2 2026-06-23, Marcos Aurélio:
#   - Remoção defensiva de $qwxDir antes do Rename-Item evita erro "arquivo já existente"
#     quando o diretório antigo não foi removido completamente pelo instalador anterior.
# v1.1.3 2026-06-23, Marcos Aurélio:
#   - QWX agora abre em janela cmd.exe compacta via Start-Process, em vez de herdar
#     a janela grande do Windows PowerShell onde o instalador foi executado.
#
# Licença: GPL.

clear

# Comando de execução (salvo no atalho da Área de Trabalho)
$QWXCommand = "irm qwx.gti1.com.br | iex"

# Verifica se o Windows PowerShell está sendo executado como administrador
if (-not ([Security.Principal.WindowsPrincipal][Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "This script needs to be run as administrator."
    Start-Process powershell -Verb RunAs -ArgumentList '-NoProfile', '-ExecutionPolicy', 'Bypass', '-Command', $QWXCommand
    exit
}

# TLS 1.2 para downloads seguros
try { [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12 } catch {}

# Ativar a execução de scripts no PowerShell (somente se não houver política por GPO)
try {
    $policies = Get-ExecutionPolicy -List
    $hasGpoPolicy = ($policies | Where-Object { $_.Scope -in @('MachinePolicy','UserPolicy') -and $_.ExecutionPolicy -ne 'Undefined' }).Count -gt 0
    if (-not $hasGpoPolicy) {
        Set-ExecutionPolicy -Scope CurrentUser -ExecutionPolicy RemoteSigned -Force -ErrorAction Stop
    }
} catch {}

# Define o nome e caminho do diretório utilizado pelo QuickWindowsX
$dirName  = "GTiSupport"
$fullPath = Join-Path -Path $env:USERPROFILE -ChildPath $dirName

# Garantir que o diretório exista
if (-not (Test-Path -Path $fullPath)) {
    try {
        New-Item -Path $fullPath -ItemType Directory -Force | Out-Null
        Write-Host "Directory created successfully: $fullPath"
    } catch {
        Write-Host "An error occurred while creating the directory: $_"
        exit
    }
}

# Função de log inline
function Write-QWXLog([string]$msg) {
    $ts = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path "$fullPath\QWX_Log.txt" -Value "$ts | $msg" -ErrorAction SilentlyContinue
}

Write-QWXLog "QuickWindowsX: instalador iniciado."
clear

# Corpo principal — try/catch global mantém janela aberta se algo falhar
try {

    # ── Atalho na Área de Trabalho ────────────────────────────────────────────
    $desktopPath  = [System.Environment]::GetFolderPath([System.Environment+SpecialFolder]::DesktopDirectory)
    $shortcutName = "GTi Support QWX"
    $shortcutPath = Join-Path -Path $desktopPath -ChildPath "$shortcutName.lnk"
    $iconUrl      = "https://github.com/systemboys/QuickWindows/raw/main/Images/QuickWindows.ico"
    $iconPath     = "$fullPath\QuickWindowsX.ico"

    try {
        Invoke-WebRequest -Uri $iconUrl -OutFile $iconPath -UseBasicParsing -ErrorAction Stop
    } catch {
        Write-Host "Icon download failed: $_"
    }

    $shell            = New-Object -ComObject WScript.Shell
    $shortcut         = $shell.CreateShortcut($shortcutPath)
    $shortcut.TargetPath  = "powershell.exe"
    $shortcut.Arguments   = "-NoProfile -ExecutionPolicy Bypass -Command $QWXCommand"
    if (Test-Path $iconPath) { $shortcut.IconLocation = $iconPath }
    $shortcut.Description = "QuickWindowsX - Facilitate installations and routines on Windows"
    $shortcut.Save()

    Write-Host "Atalho criado em: $shortcutPath"
    Write-QWXLog "Atalho criado na Area de Trabalho."

    # ── Verificar / baixar QuickWindowsX ──────────────────────────────────────
    $qwxDir  = "$env:TEMP\QuickWindowsX"
    $qwxZip  = "$env:TEMP\QuickWindowsX.zip"
    $qwxTemp = "$env:TEMP\QuickWindowsX-main"

    if (Test-Path "$qwxDir\main.py") {
        Write-Host "Starting QuickWindowsX..."
        Set-Location -Path $qwxDir
    } else {
        # Limpar restos de instalação anterior
        foreach ($p in @($qwxDir, $qwxTemp, $qwxZip)) {
            if (Test-Path $p) { Remove-Item -Recurse -Force $p -ErrorAction SilentlyContinue }
        }

        Write-Host ""
        Write-Host "Downloading QuickWindowsX..."
        Write-QWXLog "Iniciando download do QuickWindowsX."

        $zipUrl     = "https://github.com/systemboys/QuickWindowsX/archive/refs/heads/main.zip"
        $downloaded = $false

        try {
            Start-BitsTransfer -Source $zipUrl -Destination $qwxZip -ErrorAction Stop
            $downloaded = $true
        } catch {
            try {
                Invoke-WebRequest -Uri $zipUrl -OutFile $qwxZip -UseBasicParsing -ErrorAction Stop
                $downloaded = $true
            } catch {
                throw "Failed to download QuickWindowsX: $_"
            }
        }

        if ($downloaded) {
            Write-Host "Extracting..."
            Expand-Archive -Path $qwxZip -DestinationPath $env:TEMP -Force
            Remove-Item -Path $qwxZip -Force -ErrorAction SilentlyContinue

            if (Test-Path $qwxTemp) {
                if (Test-Path $qwxDir) { Remove-Item -Recurse -Force $qwxDir -ErrorAction SilentlyContinue }
                Rename-Item -Path $qwxTemp -NewName "QuickWindowsX"
                Write-Host "QuickWindowsX installed at: $qwxDir"
                Write-QWXLog "QuickWindowsX extraido em: $qwxDir."
                Set-Location -Path $qwxDir
            } else {
                throw "Extraction failed — directory '$qwxTemp' not found."
            }
        }
    }

    # ── Iniciar QuickWindowsX em janela cmd.exe (compacta, sem herdar PS grande) ──
    Write-QWXLog "Iniciando QuickWindowsX via cmd.exe + setup.ps1."
    Start-Process cmd.exe -ArgumentList "/c powershell.exe -NoProfile -ExecutionPolicy Bypass -File `"$qwxDir\setup.ps1`""

} catch {
    Write-Host ""
    Write-Host "  [ERRO] $($_.Exception.Message)" -ForegroundColor Red
    Write-QWXLog "ERRO: $($_.Exception.Message)"
    Write-Host ""
    Write-Host "  Pressione Enter para fechar..."
    $null = Read-Host
    exit 1
}
