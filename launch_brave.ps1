Stop-Process -Name brave -Force -ErrorAction SilentlyContinue
Start-Sleep -Seconds 2
$bravePath = "C:\Program Files\BraveSoftware\Brave-Browser\Application\brave.exe"
$args = "--remote-debugging-port=9222 --remote-allow-origins=* https://flow.google.com/?pli=1&authuser=5"
$fullCmd = "`"$bravePath`" $args"

([wmiclass]"Win32_Process").Create($fullCmd)
Start-Sleep -Seconds 4

try {
    $ver = Invoke-RestMethod -Uri "http://127.0.0.1:9222/json/version" -TimeoutSec 5
    Write-Host "SUCCESS: Brave CDP active on port 9222!"
    Write-Host ($ver | ConvertTo-Json)
} catch {
    Write-Host "FAILED to connect to port 9222: $_"
}
