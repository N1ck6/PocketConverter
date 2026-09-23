<#
.SYNOPSIS
    Builds PocketConverter: tests -> PyInstaller -> smoke test -> Setup.exe.

.DESCRIPTION
    Output: installer\output\PocketConverterSetup-<version>.exe (+ .sha256).
    The same script runs locally and in GitHub Actions (.github\workflows).

    Requires: Python 3.10+ with requirements-dev.txt installed, Inno Setup 6.
    Signing is optional: pass -CertThumbprint (or set
    POCKETCONVERTER_CERT_THUMBPRINT) and have signtool.exe on PATH.

.EXAMPLE
    .\build.ps1                                   # unsigned build, version from converter_app\__init__.py
    .\build.ps1 -Python .\.venv\Scripts\python.exe
    .\build.ps1 -CertThumbprint AABBCCDD...       # signed release build
#>

param(
    [string]$Version,
    [string]$Python = "python",
    [string]$CertThumbprint = $env:POCKETCONVERTER_CERT_THUMBPRINT,
    [string]$TimestampUrl = "http://timestamp.digicert.com",
    [switch]$SkipTests
)

$ErrorActionPreference = "Stop"
$root = $PSScriptRoot
Set-Location $root

function Step($title) { Write-Host "`n== $title ==" -ForegroundColor Cyan }

# Native tools (python, ISCC, signtool) log to stderr; Windows PowerShell 5.1
# would turn that into a terminating error under "Stop". Judge them by exit code.
function Invoke-Native([string]$what, [scriptblock]$command) {
    $previous = $ErrorActionPreference
    $ErrorActionPreference = "Continue"
    try { & $command 2>&1 | ForEach-Object { Write-Host "$_" } }
    finally { $ErrorActionPreference = $previous }
    if ($LASTEXITCODE -ne 0) { throw "$what failed (exit code $LASTEXITCODE)" }
}

# ── Version ───────────────────────────────────────────────────────────
$sourceVersion = ([regex]::Match((Get-Content "converter_app\__init__.py" -Raw), '__version__\s*=\s*"([^"]+)"')).Groups[1].Value
if (-not $Version) { $Version = $sourceVersion }
if ($Version -ne $sourceVersion) {
    throw "Version '$Version' doesn't match converter_app\__init__.py ('$sourceVersion'). Bump __version__ first."
}
$numeric = (($Version -split '[-+]')[0].Split('.') + @('0', '0', '0', '0')) | Select-Object -First 4
Write-Host "Building PocketConverter $Version" -ForegroundColor Green

# ── Tools ─────────────────────────────────────────────────────────────
Step "1) Checking tools"
Invoke-Native "Python" { & $Python --version }
Invoke-Native "PyInstaller (pip install -r requirements-dev.txt)" { & $Python -m PyInstaller --version }

$iscc = (Get-Command "ISCC.exe" -ErrorAction SilentlyContinue).Source
if (-not $iscc) {
    $iscc = @("${env:ProgramFiles(x86)}\Inno Setup 6\ISCC.exe", "$env:ProgramFiles\Inno Setup 6\ISCC.exe",
              "$env:LOCALAPPDATA\Programs\Inno Setup 6\ISCC.exe") | Where-Object { Test-Path $_ } | Select-Object -First 1
}
if (-not $iscc) { throw "ISCC.exe not found. Install Inno Setup 6 (winget install JRSoftware.InnoSetup)." }
Write-Host "Inno Setup: $iscc"

$sign = [bool]$CertThumbprint
if ($sign -and -not (Get-Command signtool -ErrorAction SilentlyContinue)) {
    throw "A certificate was given but signtool.exe isn't on PATH (install the Windows SDK)."
}

# ── Tests ─────────────────────────────────────────────────────────────
if (-not $SkipTests) {
    Step "2) Running unit tests"
    Invoke-Native "Unit tests" { & $Python -m pytest Test -q -p no:warnings }
}

# ── Freeze ────────────────────────────────────────────────────────────
Step "3) Building dist\converter with PyInstaller"
Remove-Item -Recurse -Force ".\build", ".\dist", ".\installer\output" -ErrorAction SilentlyContinue
New-Item -ItemType Directory -Force ".\build" | Out-Null

# Version resource: shows up in the exe's Properties > Details
$v = $numeric -join ', '
@"
VSVersionInfo(
  ffi=FixedFileInfo(filevers=($v), prodvers=($v), mask=0x3f, flags=0x0, OS=0x40004, fileType=0x1, subtype=0x0, date=(0, 0)),
  kids=[
    StringFileInfo([StringTable('040904B0', [
      StringStruct('CompanyName', 'N1ck6'),
      StringStruct('FileDescription', 'PocketConverter'),
      StringStruct('FileVersion', '$Version'),
      StringStruct('InternalName', 'converter'),
      StringStruct('LegalCopyright', 'MIT License'),
      StringStruct('OriginalFilename', 'converter.exe'),
      StringStruct('ProductName', 'PocketConverter'),
      StringStruct('ProductVersion', '$Version')])]),
    VarFileInfo([VarStruct('Translation', [1033, 1200])])
  ]
)
"@ | Out-File -Encoding utf8 ".\build\version_info.txt"

# --onedir + --noupx: self-extracting one-file exes and UPX packing are the
# most common antivirus false-positive triggers for PyInstaller apps, and
# onedir starts much faster (no 170 MB unpack on every right-click).
Invoke-Native "PyInstaller" {
    & $Python -m PyInstaller --noconfirm --clean --onedir --noconsole --noupx --log-level WARN `
        --name converter `
        --specpath build `
        --icon "$root\small.ico" `
        --version-file "$root\build\version_info.txt" `
        --add-data "$root\logo.ico;." `
        --add-data "$root\DejaVuSansCondensed.ttf;." `
        --collect-binaries imageio_ffmpeg `
        --exclude-module tkinter `
        converter.py
}

$exe = ".\dist\converter\converter.exe"
if ($sign) {
    Step "3b) Signing converter.exe"
    Invoke-Native "Signing converter.exe" { signtool sign /sha1 $CertThumbprint /fd sha256 /tr $TimestampUrl /td sha256 $exe }
}

Step "4) Smoke-testing the frozen exe"
& "$root\installer\smoke-test.ps1" -Exe (Resolve-Path $exe)

# ── Installer ─────────────────────────────────────────────────────────
Step "5) Generating registry entries from converter_app\formats.py"
Invoke-Native "Registry generation" { & $Python .\installer\generate_registry_iss.py .\installer\registry_generated.iss }

Step "6) Compiling installer with Inno Setup"
$isccArgs = @("/Qp", "/DMyAppVersion=$Version")
if ($sign) {
    # $f is replaced by Inno with the quoted path of each file it signs
    $isccArgs += @("/Ssigntoolcli=signtool sign /sha1 $CertThumbprint /fd sha256 /tr $TimestampUrl /td sha256 `$f", "/DSIGN")
}
Invoke-Native "Inno Setup" { & $iscc @isccArgs ".\installer\installer.iss" }

$setup = Get-Item ".\installer\output\PocketConverterSetup-$Version.exe"
$hash = (Get-FileHash $setup -Algorithm SHA256).Hash.ToLower()
"$hash  $($setup.Name)" | Out-File -Encoding ascii "$($setup.FullName).sha256"

Write-Host "`nDone: $($setup.FullName) ($([math]::Round($setup.Length / 1MB, 1)) MB)" -ForegroundColor Green
Write-Host "SHA256: $hash"
if (-not $sign) { Write-Host "Note: unsigned build - Windows SmartScreen will warn users on first run." -ForegroundColor Yellow }
