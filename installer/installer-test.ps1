<#
.SYNOPSIS
    End-to-end test of the Setup.exe: install, upgrade cleanup, per-user
    mode, opting out of the context menu, and uninstall.

.DESCRIPTION
    Changes the machine it runs on (installs software, writes registry),
    so only run it on a throwaway machine: a CI runner or Windows Sandbox.
    Needs to run elevated.
#>
param(
    [Parameter(Mandatory)] [string]$Setup,
    [string]$Report
)

$ErrorActionPreference = "Stop"
$failures = [System.Collections.Generic.List[string]]::new()
function Log($msg) { Write-Host $msg; if ($Report) { Add-Content -Path $Report -Value $msg -Encoding utf8 } }
function Check([bool]$condition, [string]$what) {
    if ($condition) { Log "  PASS  $what" } else { Log "  FAIL  $what"; $failures.Add($what) }
}
function Run-Setup([string[]]$extraArgs) {
    $log = Join-Path $env:TEMP ("setup-" + [guid]::NewGuid().ToString("N").Substring(0, 6) + ".log")
    $p = Start-Process $Setup -ArgumentList (@("/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART", "/LOG=`"$log`"") + $extraArgs) -Wait -PassThru
    if ($p.ExitCode -ne 0) { Get-Content $log -Tail 30 | ForEach-Object { Log $_ } }
    return $p.ExitCode
}
function Uninstall([string]$dir) {
    $p = Start-Process (Join-Path $dir "unins000.exe") -ArgumentList "/VERYSILENT", "/SUPPRESSMSGBOXES", "/NORESTART" -Wait -PassThru
    Start-Sleep -Seconds 2  # the uninstaller finishes deleting itself from a temp copy
    return $p.ExitCode
}

$machineDir = "$env:ProgramFiles\PocketConverter"
$userDir = "$env:LOCALAPPDATA\Programs\PocketConverter"
$pngKey = "Software\Classes\SystemFileAssociations\.png\shell\PocketConverter"
$dirKey = "Software\Classes\Directory\shell\PocketConverter"

# ── 1. All-users install over a simulated 1.x install ─────────────────
Log "`n[1] All-users install (upgrading from 1.x leftovers)"
New-Item -Force "HKCU:\$pngKey\shell\sub_one_0\command" | Out-Null  # what Pocket.reg / 1.x created
Check ((Run-Setup @("/ALLUSERS")) -eq 0) "setup exit code 0"
Check (Test-Path "$machineDir\converter.exe") "converter.exe installed to Program Files"
Check (Test-Path "$machineDir\_internal") "runtime folder installed"
Check (Test-Path "HKLM:\$pngKey\shell\item_00\command") ".png menu registered (HKLM)"
Check ((Get-ItemProperty "HKLM:\$pngKey").MultiSelectModel -eq "Player") "menu shown for multi-selection"
$cmd = (Get-ItemProperty "HKLM:\$pngKey\shell\item_00\command").'(default)'
Check ($cmd -eq "`"$machineDir\converter.exe`" `"%1`" jpg") "command line is quoted correctly ($cmd)"
Check (Test-Path "HKLM:\$dirKey\shell\item_01\command") "folder menu registered"
Check (-not (Test-Path "HKCU:\$pngKey")) "legacy 1.x per-user menu removed (no duplicates)"
Check (Test-Path "HKLM:\Software\Classes\AppUserModelId\N1ck6.PocketConverter") "notification identity registered"
Check (Test-Path "$env:ProgramData\Microsoft\Windows\Start Menu\Programs\PocketConverter.lnk") "Start menu shortcut"

Log "`n[2] Installed exe works (smoke test)"
try { & "$PSScriptRoot\smoke-test.ps1" -Exe "$machineDir\converter.exe" *>&1 | ForEach-Object { Log "    $_" }; Check $true "smoke test" }
catch { Log "    $_"; Check $false "smoke test" }

Log "`n[3] Re-running setup with the context menu unticked removes it"
Check ((Run-Setup @("/ALLUSERS", "/MERGETASKS=`"!contextmenu`"")) -eq 0) "setup exit code 0"
Check (-not (Test-Path "HKLM:\$pngKey")) ".png menu removed"
Check (-not (Test-Path "HKLM:\$dirKey")) "folder menu removed"

Log "`n[4] Uninstall"
Check ((Run-Setup @("/ALLUSERS")) -eq 0) "reinstall with menu"
Check ((Uninstall $machineDir) -eq 0) "uninstaller exit code 0"
Check (-not (Test-Path "$machineDir\converter.exe")) "files removed"
Check (-not (Test-Path "HKLM:\$pngKey")) "menu removed"
Check (-not (Test-Path "HKLM:\Software\Classes\AppUserModelId\N1ck6.PocketConverter")) "notification identity removed"

# ── 5. Per-user install (no admin needed) ─────────────────────────────
Log "`n[5] Per-user install"
Check ((Run-Setup @("/CURRENTUSER")) -eq 0) "setup exit code 0"
Check (Test-Path "$userDir\converter.exe") "installed to %LOCALAPPDATA%\Programs"
Check (Test-Path "HKCU:\$pngKey\shell\item_00\command") ".png menu registered (HKCU)"
Check (-not (Test-Path "HKLM:\$pngKey")) "nothing written to HKLM"
Check ((Uninstall $userDir) -eq 0) "uninstaller exit code 0"
Check (-not (Test-Path "HKCU:\$pngKey")) "menu removed"

Log ""
if ($failures.Count) { Log "INSTALLER TEST FAILED: $($failures.Count) check(s)"; exit 1 }
Log "INSTALLER TEST PASSED"
exit 0
