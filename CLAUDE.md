# Claude Code — Project Instructions

## Shell / Platform

The working directory lives inside WSL (`\\wsl$\Ubuntu\home\paolo\claude-eve-gate-logger`).
The shell is **PowerShell on Windows**, but SSH keys and the git remote are configured inside WSL.

### Git — use Windows PowerShell directly

The remote is HTTPS and credentials are stored in Windows Credential Manager,
so all git operations work from PowerShell in the UNC path:

```powershell
cd "\\wsl$\Ubuntu\home\paolo\claude-eve-gate-logger"
git status
git add file.py
git commit -m "message"
git push
git pull
```

For multi-line commit messages use a PowerShell here-string:

```powershell
cd "\\wsl$\Ubuntu\home\paolo\claude-eve-gate-logger"
git commit -m "$(cat <<'EOF'
Subject line

Body paragraph here.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>
EOF
)"
git push
```

### Linux commands — use WSL

For bash scripts or Linux-only tools still use WSL:

```powershell
wsl -e bash -c "cd ~/claude-eve-gate-logger && <command>"
```

## Building the exe

PyInstaller runs on Windows (Python is Windows-native):

```powershell
cd "\\wsl$\Ubuntu\home\paolo\claude-eve-gate-logger"
C:\Users\paolo\AppData\Local\Programs\Python\Python314\Scripts\pyinstaller.exe build.spec --clean
# output: dist\eve-gate-logger.exe
```

## File editing

Use the `Edit` / `Write` / `Read` tools with the UNC path
`\\wsl$\Ubuntu\home\paolo\claude-eve-gate-logger\<file>` — these work fine
from Windows even though git does not.
