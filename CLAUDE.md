# Claude Code — Project Instructions

## Shell / Platform

The working directory lives inside WSL (`\\wsl$\Ubuntu\home\paolo\claude-eve-gate-logger`).
The shell is **PowerShell on Windows**, but SSH keys and the git remote are configured inside WSL.

### Rule: always use WSL for git and Linux commands

**Never** run `git` directly in PowerShell for this repo — the UNC path
(`\\wsl$\...`) triggers a "dubious ownership" error and SSH host-key checks fail
because the Windows SSH agent cannot reach the WSL key.

**Always** delegate git and Linux commands to WSL via:**

```powershell
# One-off command
wsl -e bash -c "cd ~/claude-eve-gate-logger && <command>"

# Multi-step pipeline
wsl -e bash -c "cd ~/claude-eve-gate-logger && git add -p && git commit -m '...' && git push"
```

The `~/claude-eve-gate-logger` path inside WSL is the same directory as
`\\wsl$\Ubuntu\home\paolo\claude-eve-gate-logger` on Windows.

### Common patterns

| Task | Command |
|------|---------|
| `git status` | `wsl -e bash -c "cd ~/claude-eve-gate-logger && git status"` |
| `git add` + `git commit` | `wsl -e bash -c "cd ~/claude-eve-gate-logger && git add FILE && git commit -m 'msg'"` |
| `git push` | `wsl -e bash -c "cd ~/claude-eve-gate-logger && git push"` |
| `git pull` | `wsl -e bash -c "cd ~/claude-eve-gate-logger && git pull"` |
| `git log` | `wsl -e bash -c "cd ~/claude-eve-gate-logger && git log --oneline -10"` |
| Run any bash script | `wsl -e bash -c "cd ~/claude-eve-gate-logger && bash script.sh"` |

### Commit message with newlines (PowerShell here-string → WSL)

```powershell
wsl -e bash -c @'
cd ~/claude-eve-gate-logger
git add file.py
git commit -m "Subject line

Body paragraph here.

Co-Authored-By: Claude Sonnet 4.6 <noreply@anthropic.com>"
git push
'@
```

> **Note:** the `@'...'@` PowerShell here-string passes the block verbatim to
> `bash -c`, so newlines and `$` signs are preserved without escaping.

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
