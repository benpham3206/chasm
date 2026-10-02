# Hourly (Task Scheduler "ChasmDevinResume"): when Devin's quota is back, resume the chasm render session once with resume-04.md, then stand down.
$dir  = "D:\3DProjects\chasm\blender\orchestrator"
$log  = "$dir\devin_cron.log"
$done = "$dir\devin_cron.launched"
function L($m) { "$(Get-Date -Format s) $m" | Out-File $log -Append -Encoding utf8 }
if (Test-Path $done) { exit }                                   # already launched once
if (Get-CimInstance Win32_Process -Filter "Name='devin.exe'" | Where-Object { $_.CommandLine -match 'lucky-idea' }) { L "session busy, skip"; exit }
$devin = "C:\Users\hotdo\AppData\Local\devin\cli\bin\devin.exe"
$probe = & $devin -p "Reply with just OK" --model fusion-claude-opus-5-5-high-sidekick-swe-2-high --respect-workspace-trust false 2>&1 | Out-String
if ($probe -match 'quota|resource_exhausted') { L "quota still exhausted"; exit }
if ($probe -notmatch 'OK') { L "probe unexpected: $($probe.Substring(0, [Math]::Min(200, $probe.Length)))"; exit }
$p = Start-Process -FilePath $devin -WorkingDirectory "D:\3DProjects\chasm" `
  -ArgumentList @('-r','lucky-idea','--prompt-file','blender/orchestrator/resume-04.md','-p','--model','fusion-claude-opus-5-5-high-sidekick-swe-2-high','--permission-mode','dangerous','--respect-workspace-trust','false','--export','blender/devin-session-v1.md') `
  -RedirectStandardOutput "D:\3DProjects\chasm\blender\devin-stdout-4.log" -RedirectStandardError "D:\3DProjects\chasm\blender\devin-stderr-4.log" -WindowStyle Hidden -PassThru
"pid $($p.Id)" | Out-File $done -Encoding utf8
L "quota back - resumed devin with resume-04.md, pid $($p.Id)"
