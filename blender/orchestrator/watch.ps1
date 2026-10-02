# Live view of the Devin render job. Run:  powershell -File D:\3DProjects\chasm\blender\orchestrator\watch.ps1
# Ctrl+C to quit. Shows progress log, files Devin touched recently, and whether Devin/Blender are running.
$root = "D:\3DProjects\chasm"
while ($true) {
    Clear-Host
    Write-Host "chasm render job  $(Get-Date -Format 'HH:mm:ss')" -ForegroundColor Cyan
    $devin = Get-Process devin -ErrorAction SilentlyContinue
    $blender = Get-Process blender -ErrorAction SilentlyContinue
    Write-Host ("Devin: " + $(if ($devin) { "running" } else { "not running" }) + "   Blender: " + $(if ($blender) { "rendering/building" } else { "idle" }))
    Write-Host "`n--- PROGRESS.md (latest) ---" -ForegroundColor Yellow
    Get-Content "$root\blender\PROGRESS.md" -Tail 6
    Write-Host "`n--- files changed in last 15 min ---" -ForegroundColor Yellow
    Get-ChildItem "$root\blender", "$root\renders" -Recurse -File -ErrorAction SilentlyContinue |
        Where-Object { $_.LastWriteTime -gt (Get-Date).AddMinutes(-15) -and $_.Name -notlike 'devin-*' } |
        Sort-Object LastWriteTime -Descending | Select-Object -First 15 |
        ForEach-Object { "{0:HH:mm:ss}  {1}" -f $_.LastWriteTime, $_.FullName.Replace("$root\", "") }
    Start-Sleep 10
}
