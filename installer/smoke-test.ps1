<#
.SYNOPSIS
    Runs the *built* converter.exe on real files, the way Explorer does.

.DESCRIPTION
    Unit tests run from source; this catches what only breaks after
    freezing: modules or binaries PyInstaller didn't bundle (FFmpeg,
    PyMuPDF, pillow-heif, pdf2docx/OpenCV, fonts...).
    All conversions are started at once, which also exercises the
    multi-select job queue. Used by build.ps1 and by CI after a silent install.
#>
param([Parameter(Mandatory)] [string]$Exe)

$ErrorActionPreference = "Stop"
$samples = Join-Path $PSScriptRoot "..\Test"
$work = Join-Path ([IO.Path]::GetTempPath()) ("pc-smoke-" + [guid]::NewGuid().ToString("N").Substring(0, 8))
New-Item -ItemType Directory $work | Out-Null

# Keep the test away from the real user profile and the notification area
$savedEnv = @{ LOCALAPPDATA = $env:LOCALAPPDATA; POCKETCONVERTER_NO_TOAST = $env:POCKETCONVERTER_NO_TOAST }
$env:LOCALAPPDATA = Join-Path $work "appdata"
$env:POCKETCONVERTER_NO_TOAST = "1"
try {

Copy-Item "$samples\sample.png", "$samples\sample.txt", "$samples\sample.json", "$samples\sample.md", "$samples\sample.csv" $work
Set-Content -Encoding utf8 "$work\vector.svg" '<svg xmlns="http://www.w3.org/2000/svg" width="64" height="32"><rect width="64" height="32" fill="red"/></svg>'
New-Item -ItemType Directory "$work\Album" | Out-Null
Copy-Item "$samples\sample.jpg" "$work\Album\IMG_1.JPG"
Copy-Item "$samples\sample.png" "$work\Album\IMG_2.png"

# Make a short video with the FFmpeg that PyInstaller bundled — proves it's there
$ffmpeg = Get-ChildItem (Split-Path $Exe) -Recurse -Filter "ffmpeg*.exe" | Select-Object -First 1
if (-not $ffmpeg) { throw "Bundled FFmpeg not found next to $Exe" }
& $ffmpeg.FullName -hide_banner -loglevel error -f lavfi -i "testsrc=size=64x48:rate=10:duration=1" `
    -f lavfi -i "sine=duration=1" -shortest -pix_fmt yuv420p "$work\clip.mp4"

$jobs = @(
    @("sample.png", "jpg", "sample.jpg"),
    @("sample.png", "ico", "sample.ico"),
    @("vector.svg", "png", "vector.png"),
    @("sample.txt", "pdf", "sample.pdf"),
    @("sample.txt", "docx", "sample.docx"),
    @("sample.md", "html", "sample.html"),
    @("sample.json", "yaml", "sample.yaml"),
    @("sample.csv", "xml", "sample.xml"),
    @("clip.mp4", "mp3", "clip.mp3"),
    @("clip.mp4", "gif", "clip.gif"),
    @("Album", "folderpdf", "Album.pdf")
)

$procs = foreach ($j in $jobs) {
    Start-Process -FilePath $Exe -ArgumentList "`"$work\$($j[0])`"", $j[1] -PassThru
}
$procs | Wait-Process -Timeout 300

# pdf2docx (OpenCV, fonttools...) is the heaviest import chain: test it on the PDF made above
Start-Process -FilePath $Exe -ArgumentList "`"$work\sample.pdf`"", "docx" -Wait
$jobs += , @("sample.pdf", "docx", "sample(1).docx")

$failed = @($jobs | Where-Object { -not (Test-Path (Join-Path $work $_[2])) })
foreach ($j in $jobs) {
    $ok = Test-Path (Join-Path $work $j[2])
    Write-Host ("  {0,-4} {1,-12} -> {2}" -f $(if ($ok) { "OK" } else { "FAIL" }), $j[0], $j[1]) -ForegroundColor $(if ($ok) { "Green" } else { "Red" })
}

$log = Join-Path $env:LOCALAPPDATA "PocketConverter\PocketConverter_log.txt"
if ($failed.Count -gt 0) {
    if (Test-Path $log) { Write-Host "`n--- error log ---"; Get-Content $log }
    throw "$($failed.Count) smoke test conversion(s) failed"
}
Remove-Item -Recurse -Force $work -ErrorAction SilentlyContinue
Write-Host "Smoke test passed ($($jobs.Count) conversions)" -ForegroundColor Green
$global:LASTEXITCODE = 0
}
finally {
    $env:LOCALAPPDATA = $savedEnv.LOCALAPPDATA
    $env:POCKETCONVERTER_NO_TOAST = $savedEnv.POCKETCONVERTER_NO_TOAST
}
