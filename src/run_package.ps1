# run_package.ps1 - Executor generico de pacotes para QuickWindowsX
#
# Autor: Marcos Aurelio R. da Silva <systemboys@hotmail.com>
#
# Uso:
#   powershell -File run_package.ps1 -Url "<url>" -Nome "<nome>" [-SilentArgs "<args>"]
#
# Comportamento:
#   .exe / .msi  -> download para %TEMP%, executa o instalador, remove o arquivo
#   .zip         -> download para %TEMP%, extrai, executa o maior .exe encontrado,
#                   remove o zip e a pasta extraida
#
# Logs gravados em: %USERPROFILE%\GTiSupport\QWX_Log.txt

param(
    [Parameter(Mandatory = $true)]
    [string]$Url,

    [string]$Nome = "",

    # Argumentos extras para o instalador (ex.: "/S" ou "/quiet"). Deixe vazio
    # para abrir o instalador normalmente (com UI).
    [string]$SilentArgs = ""
)

$ErrorActionPreference = "Stop"
[Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12

# ─── Configuracoes (config.json) ──────────────────────────────────────────────

$_configPath = Join-Path (Split-Path $PSScriptRoot -Parent) "config.json"
if (Test-Path $_configPath) {
    try { $_config = Get-Content $_configPath -Raw | ConvertFrom-Json } catch { $_config = $null }
}
$_windowTitle  = if ($_config -and $_config.promptWindowTitle) { $_config.promptWindowTitle } else { "GTi - QuickWindowsX" }
$_beepsCount   = if ($_config -and $_config.beepsOnDownloads)  { [int]$_config.beepsOnDownloads } else { 3 }

$Host.UI.RawUI.WindowTitle = "$_windowTitle - Instalador"

# ─── Helpers ─────────────────────────────────────────────────────────────────

$_gtiDir = "$env:USERPROFILE\GTiSupport"
if (-not (Test-Path $_gtiDir)) {
    New-Item -ItemType Directory -Path $_gtiDir -Force | Out-Null
}

function Write-Log([string]$msg) {
    $stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
    Add-Content -Path "$_gtiDir\QWX_Log.txt" -Value "$stamp | $msg" -ErrorAction SilentlyContinue
}

function Remove-Safe([string]$path) {
    if (Test-Path $path) {
        Remove-Item -Path $path -Recurse -Force -ErrorAction SilentlyContinue
    }
}

# ─── Derivar nomes a partir da URL ───────────────────────────────────────────

$_cleanUrl  = ($Url -split '\?')[0]          # remove query string para pegar o nome
$_fileName  = [System.IO.Path]::GetFileName($_cleanUrl)
$_ext       = [System.IO.Path]::GetExtension($_fileName).ToLower()
$_baseName  = [System.IO.Path]::GetFileNameWithoutExtension($_fileName)
$_label     = if ($Nome) { $Nome } else { $_baseName }

$_tempZip   = Join-Path $env:TEMP "QWX_$_fileName"          # destino do download
$_extractTo = Join-Path $env:TEMP "QWX_$_baseName"          # pasta de extracao (zip)

# ─── Interface inicial ────────────────────────────────────────────────────────

$Host.UI.RawUI.BackgroundColor = "Black"
Clear-Host

Write-Host ""
Write-Host "  ========================================" -ForegroundColor DarkGray
Write-Host "    QuickWindowsX - Executor de Pacotes" -ForegroundColor Cyan
Write-Host "  ========================================" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  Pacote  : $_label" -ForegroundColor White
Write-Host "  Arquivo : $_fileName" -ForegroundColor Gray
Write-Host "  Tipo    : $($_ext.TrimStart('.'))" -ForegroundColor Gray
Write-Host ""

# ─── Download ─────────────────────────────────────────────────────────────────

Write-Host "  [1/3] Baixando..." -ForegroundColor Cyan
Write-Log "Inicio | $_label | $Url"

try {
    $wc = New-Object System.Net.WebClient
    $wc.DownloadFile($Url, $_tempZip)
} catch {
    Write-Host ""
    Write-Host "  [ERRO] Falha no download." -ForegroundColor Red
    Write-Host "  $_" -ForegroundColor DarkGray
    Write-Log "ERRO download | $_label | $_"
    Write-Host ""
    Write-Host "  Pressione Enter para fechar..."
    $null = Read-Host
    exit 1
}

$_sizeMB = [math]::Round((Get-Item $_tempZip).Length / 1MB, 2)
Write-Host "  [OK] Download concluido. ($_sizeMB MB)" -ForegroundColor Green
Write-Log "Download OK | $_label | $_sizeMB MB"

for ($i = 0; $i -lt $_beepsCount; $i++) {
    [Console]::Beep(500, 300)
    Start-Sleep -Milliseconds 200
}

# ─── Instalar ou Executar ─────────────────────────────────────────────────────

if ($_ext -eq ".zip") {

    # ── ZIP: extrair e executar o portable ───────────────────────────────────
    Write-Host ""
    Write-Host "  [2/3] Extraindo $_fileName..." -ForegroundColor Cyan

    try {
        Remove-Safe $_extractTo
        Expand-Archive -Path $_tempZip -DestinationPath $_extractTo -Force
    } catch {
        Write-Host "  [ERRO] Falha na extracao: $_" -ForegroundColor Red
        Write-Log "ERRO extracao | $_label | $_"
        Remove-Safe $_tempZip
        Write-Host "  Pressione Enter para fechar..."
        $null = Read-Host
        exit 1
    }

    # Encontrar o exe principal: exclui nomes com "uninstall"/"uninst",
    # depois escolhe o de maior tamanho (tipicamente o executavel principal).
    $candidates = Get-ChildItem -Path $_extractTo -Filter "*.exe" -Recurse |
                  Where-Object { $_.Name -notmatch "(?i)uninst" } |
                  Sort-Object Length -Descending

    if (-not $candidates) {
        Write-Host "  [ERRO] Nenhum executavel encontrado no arquivo compactado." -ForegroundColor Red
        Write-Log "ERRO sem exe | $_label"
        Remove-Safe $_tempZip
        Remove-Safe $_extractTo
        Write-Host "  Pressione Enter para fechar..."
        $null = Read-Host
        exit 1
    }

    $_exeFile = $candidates[0].FullName
    Write-Host "  [OK] Extraido. Executando: $($candidates[0].Name)" -ForegroundColor Green
    Write-Host ""
    Write-Host "  [3/3] Executando..." -ForegroundColor Cyan
    Write-Log "Executando portable | $_label | $_exeFile"

    Start-Process -FilePath $_exeFile -Wait

} elseif ($_ext -eq ".msi") {

    # ── MSI: msiexec ─────────────────────────────────────────────────────────
    Write-Host ""
    Write-Host "  [2/3] Instalando (msiexec)..." -ForegroundColor Cyan
    Write-Log "Instalando MSI | $_label | SilentArgs: $SilentArgs"

    $msiArgs = "/i `"$_tempZip`""
    if ($SilentArgs) { $msiArgs += " $SilentArgs" }

    Start-Process "msiexec.exe" -ArgumentList $msiArgs -Wait
    Write-Host "  [OK] Instalacao concluida." -ForegroundColor Green

} elseif ($_ext -eq ".exe") {

    # ── EXE: executar diretamente ─────────────────────────────────────────────
    Write-Host ""
    Write-Host "  [2/3] Executando instalador..." -ForegroundColor Cyan
    Write-Log "Executando EXE | $_label | SilentArgs: $SilentArgs"

    if ($SilentArgs) {
        Start-Process -FilePath $_tempZip -ArgumentList $SilentArgs -Wait
    } else {
        Start-Process -FilePath $_tempZip -Wait
    }
    Write-Host "  [OK] Instalacao concluida." -ForegroundColor Green

} else {
    Write-Host "  [AVISO] Extensao nao suportada: $_ext" -ForegroundColor Yellow
    Write-Log "AVISO extensao | $_label | $_ext"
}

# ─── Limpeza ──────────────────────────────────────────────────────────────────

Write-Host ""
Write-Host "  [3/3] Removendo arquivos temporarios..." -ForegroundColor Cyan

Remove-Safe $_tempZip
Remove-Safe $_extractTo

Write-Host "  [OK] Limpeza concluida." -ForegroundColor Green
Write-Log "Limpeza OK | $_label"

Write-Host ""
Write-Host "  ========================================" -ForegroundColor DarkGray
Write-Host "  Concluido: $_label" -ForegroundColor Green
Write-Host "  ========================================" -ForegroundColor DarkGray
Write-Host ""
Write-Host "  Pressione Enter para continuar..."
$null = Read-Host
