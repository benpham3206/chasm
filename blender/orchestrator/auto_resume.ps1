# Waits for the current Devin run (pid 8156) to exit, then resumes the session with resume-02.md. Logs to auto_resume.log.
$log = "D:\3DProjects\chasm\blender\orchestrator\auto_resume.log"
"$(Get-Date -Format s) waiting for devin pid 8156" | Out-File $log -Append -Encoding utf8
while (Get-Process -Id 8156 -ErrorAction SilentlyContinue) { Start-Sleep 30 }
"$(Get-Date -Format s) pid 8156 exited; resuming with resume-02.md" | Out-File $log -Append -Encoding utf8
$p = Start-Process -FilePath "C:\Users\hotdo\AppData\Local\devin\cli\bin\devin.exe" -WorkingDirectory "D:\3DProjects\chasm" `
  -ArgumentList @('-r','lucky-idea','--prompt-file','blender/orchestrator/resume-02.md','-p','--model','fusion-claude-opus-5-5-high-sidekick-swe-2-high','--permission-mode','dangerous','--respect-workspace-trust','false','--export','blender/devin-session-v1.md') `
  -RedirectStandardOutput "D:\3DProjects\chasm\blender\devin-stdout-2.log" -RedirectStandardError "D:\3DProjects\chasm\blender\devin-stderr-2.log" -WindowStyle Hidden -PassThru
"$(Get-Date -Format s) started resumed devin pid $($p.Id)" | Out-File $log -Append -Encoding utf8
