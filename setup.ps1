# setup.ps1 - Verifica Python, instala se necessario, executa main.py
# Autor: Marcos Aurelio R. da Silva <systemboys@hotmail.com>
# Elevacao ja garantida pelo run.cmd — este script nao faz auto-elevacao.

$root = Split-Path -Parent $MyInvocation.MyCommand.Definition

# ─── Funcoes ─────────────────────────────────────────────────────────────────

function Find-Python {
    # Testa candidatos ignorando o alias falso da Microsoft Store
    foreach ($cmd in @("python", "py")) {
        try {
            $out = & $cmd -c "import sys; print(sys.executable)" 2>$null
            if ($LASTEXITCODE -eq 0 -and $out -and ($out -notmatch "WindowsApps")) {
                return $out.Trim()   # retorna o caminho completo do executavel
            }
        } catch { }
    }

    # Busca direta em caminhos conhecidos (cobre versoes 3.8 a 3.13)
    $bases = @(
        "$env:ProgramFiles\Python3",
        "$env:LOCALAPPDATA\Programs\Python\Python3"
    )
    foreach ($base in $bases) {
        foreach ($minor in @(13,12,11,10,9,8)) {
            $exe = "${base}${minor}\python.exe"
            if (Test-Path $exe) { return $exe }
        }
    }

    # py launcher (C:\Windows\py.exe) instalado pelo proprio Python
    $py = "$env:SystemRoot\py.exe"
    if (Test-Path $py) { return $py }

    return $null
}

function Install-Python {
    $arch    = if ([Environment]::Is64BitOperatingSystem) { "amd64" } else { "win32" }
    $version = "3.12.9"
    $url     = "https://www.python.org/ftp/python/$version/python-$version-$arch.exe"
    $dest    = Join-Path $env:TEMP "python_setup.exe"

    Write-Host ""
    Write-Host "  Baixando Python $version ($arch)..." -ForegroundColor Cyan
    Write-Host "  Isso pode levar alguns minutos dependendo da sua conexao." -ForegroundColor DarkGray

    try {
        [Net.ServicePointManager]::SecurityProtocol = [Net.SecurityProtocolType]::Tls12
        $wc = New-Object System.Net.WebClient
        $wc.DownloadFile($url, $dest)
    } catch {
        Write-Host ""
        Write-Host "  [ERRO] Falha no download." -ForegroundColor Red
        Write-Host "  Detalhe: $_" -ForegroundColor DarkGray
        return $false
    }

    if (-not (Test-Path $dest)) {
        Write-Host "  [ERRO] Instalador nao encontrado apos download." -ForegroundColor Red
        return $false
    }

    Write-Host "  Instalando Python silenciosamente..." -ForegroundColor Cyan

    $args = "/quiet InstallAllUsers=1 PrependPath=1 Include_launcher=1 Include_test=0"
    $proc = Start-Process -FilePath $dest -ArgumentList $args -Wait -PassThru

    Remove-Item $dest -Force -ErrorAction SilentlyContinue

    if ($proc.ExitCode -ne 0) {
        Write-Host "  [ERRO] Instalador terminou com codigo $($proc.ExitCode)." -ForegroundColor Red
        return $false
    }

    Write-Host "  Python instalado com sucesso!" -ForegroundColor Green
    return $true
}

function Refresh-Path {
    $machine = [Environment]::GetEnvironmentVariable("PATH", "Machine")
    $user    = [Environment]::GetEnvironmentVariable("PATH", "User")
    if ($machine -or $user) {
        $env:PATH = "$machine;$user"
    }
}

# ─── Principal ───────────────────────────────────────────────────────────────

$ocorreuErro = $false

try {

    $python = Find-Python

    if (-not $python) {
        Write-Host ""
        Write-Host "  Python nao encontrado. Iniciando instalacao automatica..." -ForegroundColor Yellow

        $ok = Install-Python

        if (-not $ok) {
            Write-Host ""
            Write-Host "  Nao foi possivel instalar o Python." -ForegroundColor Red
            Write-Host "  Instale manualmente em: https://www.python.org/downloads/" -ForegroundColor Yellow
            $ocorreuErro = $true
        } else {
            # Atualizar PATH da sessao atual com os caminhos recem-registrados
            Refresh-Path

            $python = Find-Python

            if (-not $python) {
                Write-Host ""
                Write-Host "  Python instalado, mas o terminal precisa ser reiniciado." -ForegroundColor Yellow
                Write-Host "  Feche esta janela e execute run.cmd novamente." -ForegroundColor Cyan
                $ocorreuErro = $true
            }
        }
    }

    if (-not $ocorreuErro -and $python) {
        Write-Host ""
        Write-Host "  Python encontrado: $python" -ForegroundColor DarkGray
        Write-Host ""

        Set-Location $root
        & $python main.py

        if ($LASTEXITCODE -ne 0) {
            Write-Host ""
            Write-Host "  [ERRO] main.py terminou com codigo $LASTEXITCODE." -ForegroundColor Red
            $ocorreuErro = $true
        }
    }

} catch {
    Write-Host ""
    Write-Host "  [ERRO INESPERADO]" -ForegroundColor Red
    Write-Host "  $_" -ForegroundColor Red
    $ocorreuErro = $true
}

# Manter janela aberta somente se houve erro
if ($ocorreuErro) {
    Write-Host ""
    Read-Host "  Pressione Enter para fechar"
}
