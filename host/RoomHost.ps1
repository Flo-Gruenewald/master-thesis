# Room Host on/off (15.10.2026). Double-click the desktop icon "Room Host" (→ RoomHost.bat → this script):
#   host not running → starts it in its own window with the live log (closing that window stops the host)
#   host running     → stops it
# The window's log is also written to host.log (UTF-8, new for every start).
$here = Split-Path -Parent $MyInvocation.MyCommand.Path
$running = @()                                   # (a list: adding two single ids would sum them)
$running += @(Get-NetTCPConnection -State Listen -LocalPort 8080 -ErrorAction SilentlyContinue | ForEach-Object { $_.OwningProcess })  # web page
$running += @(Get-NetUDPEndpoint -LocalPort 7010 -ErrorAction SilentlyContinue | ForEach-Object { $_.OwningProcess })               # table mic (also while starting)
$running = @($running | Where-Object { $_ -and (Get-Process -Id $_ -ErrorAction SilentlyContinue) } | Select-Object -Unique)

if ($running) {
    $running | ForEach-Object { Stop-Process -Id $_ -Force }
    Write-Host "Room Host stopped." -ForegroundColor Yellow
    Start-Sleep -Seconds 2
} else {
    $cmd = "`$host.UI.RawUI.WindowTitle = 'Room Host - close this window to stop'; " +
           "Set-Location '$here'; `$env:PYTHONUNBUFFERED = '1'; Set-Content host.log '' -Encoding UTF8; " +
           "python main.py 2>&1 | ForEach-Object { `$l = `"`$_`"; `$l; Add-Content host.log `$l -Encoding UTF8 }; " +
           "Write-Host ''; Write-Host 'Room Host has stopped. Press Enter to close.' -ForegroundColor Yellow; Read-Host"
    Start-Process powershell -ArgumentList "-NoProfile", "-ExecutionPolicy", "Bypass", "-Command", $cmd
    Write-Host "Room Host starting: web page http://localhost:8080" -ForegroundColor Green
    Start-Sleep -Seconds 2
}
