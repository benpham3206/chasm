# Waits for the current Devin run (pid 25016) to exit, then resumes the session with resume-03.md. Logs to auto_resume.log.
$log = "D:\3DProjects\chasm\blender\orchestrator\auto_resume.log"
"$(Get-Date -Format s) waiting for devin pid 25016" | Out-File $log -Append -Encoding utf8
while (Get-Process -Id 25016 -ErrorAction SilentlyContinue) { Start-Sleep 30 }
"$(Get-Date -Format s) pid 25016 exited; resuming with resume-03.md" | Out-File $log -Append -Encoding utf8
$p = Start-Process -FilePath "C:\Users\hotdo\AppData\Local\devin\cli\bin\devin.exe" -WorkingDirectory "D:\3DProjects\chasm" `
  -ArgumentList @('-r','lucky-idea','--prompt-file','blender/orchestrator/resume-03.md','-p','--model','fusion-claude-opus-5-5-high-sidekick-swe-2-high','--permission-mode','dangerous','--respect-workspace-trust','false','--export','blender/devin-session-v1.md') `
  -RedirectStandardOutput "D:\3DProjects\chasm\blender\devin-stdout-3.log" -RedirectStandardError "D:\3DProjects\chasm\blender\devin-stderr-3.log" -WindowStyle Hidden -PassThru
"$(Get-Date -Format s) started resumed devin pid $($p.Id)" | Out-File $log -Append -Encoding utf8
