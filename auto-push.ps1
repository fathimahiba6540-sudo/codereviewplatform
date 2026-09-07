# ============================================================
#  Auto Git Push - File Watcher for codereviewplatform
#  Watches for file changes and automatically commits + pushes
#  to GitHub whenever you save a file.
#
#  HOW TO RUN:
#    Right-click this file -> "Run with PowerShell"
#    OR in terminal: powershell -ExecutionPolicy Bypass -File auto-push.ps1
# ============================================================

$GIT = "C:\Program Files\Git\cmd\git.exe"
$REPO = $PSScriptRoot
$DEBOUNCE_SECONDS = 5   # Wait 5s after last change before pushing (avoids rapid-fire commits)

Write-Host ""
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Auto Git Push - Watching for changes  " -ForegroundColor Cyan
Write-Host "========================================" -ForegroundColor Cyan
Write-Host "  Repo   : $REPO" -ForegroundColor Gray
Write-Host "  Remote : GitHub (fathimahiba6540-sudo)" -ForegroundColor Gray
Write-Host "  Delay  : $DEBOUNCE_SECONDS seconds after last save" -ForegroundColor Gray
Write-Host ""
Write-Host "  Press Ctrl+C to stop watching." -ForegroundColor Yellow
Write-Host "========================================" -ForegroundColor Cyan
Write-Host ""

# --- Setup FileSystemWatcher ---
$watcher = New-Object System.IO.FileSystemWatcher
$watcher.Path = $REPO
$watcher.IncludeSubdirectories = $true
$watcher.EnableRaisingEvents = $true
$watcher.NotifyFilter = [System.IO.NotifyFilters]::LastWrite -bor [System.IO.NotifyFilters]::FileName

# Ignore patterns (git internals, python cache, IDE files)
$ignorePatterns = @(
    '\.git\\', '__pycache__', '\.pyc$', '\.pyo$',
    'node_modules\\', '\.dart_tool\\', '\.pub\\',
    '\.vscode\\', '\.idea\\', '\.DS_Store',
    'Thumbs\.db', '\.env$'
)

$lastPushTime = [DateTime]::MinValue
$pendingChanges = $false
$changedFiles = [System.Collections.Generic.List[string]]::new()
$lock = [object]::new()

$action = {
    $path = $Event.SourceEventArgs.FullPath
    $changeType = $Event.SourceEventArgs.ChangeType

    # Check ignore patterns
    foreach ($pattern in $ignorePatterns) {
        if ($path -match $pattern) { return }
    }

    $timestamp = Get-Date -Format "HH:mm:ss"
    Write-Host "[$timestamp] " -NoNewline -ForegroundColor DarkGray
    Write-Host "$changeType" -NoNewline -ForegroundColor Yellow
    Write-Host " : $($path.Replace($REPO + '\', ''))" -ForegroundColor White

    [System.Threading.Monitor]::Enter($lock)
    try {
        $script:pendingChanges = $true
        $script:lastChangeTime = [DateTime]::Now
        if (-not $script:changedFiles.Contains($path)) {
            $script:changedFiles.Add($path)
        }
    }
    finally {
        [System.Threading.Monitor]::Exit($lock)
    }
}

# Register events
Register-ObjectEvent $watcher "Changed" -Action $action | Out-Null
Register-ObjectEvent $watcher "Created" -Action $action | Out-Null
Register-ObjectEvent $watcher "Deleted" -Action $action | Out-Null
Register-ObjectEvent $watcher "Renamed" -Action $action | Out-Null

$script:lastChangeTime = [DateTime]::MinValue
$script:pendingChanges = $false
$script:changedFiles = [System.Collections.Generic.List[string]]::new()

# --- Main loop: debounce and push ---
try {
    while ($true) {
        Start-Sleep -Milliseconds 500

        # Process any pending events
        Get-Event -ErrorAction SilentlyContinue | ForEach-Object { $_ | Remove-Event }

        $shouldPush = $false
        [System.Threading.Monitor]::Enter($lock)
        try {
            if ($script:pendingChanges) {
                $elapsed = ([DateTime]::Now - $script:lastChangeTime).TotalSeconds
                if ($elapsed -ge $DEBOUNCE_SECONDS) {
                    $shouldPush = $true
                    $script:pendingChanges = $false
                    $script:changedFiles.Clear()
                }
            }
        }
        finally {
            [System.Threading.Monitor]::Exit($lock)
        }

        if ($shouldPush) {
            $timestamp = Get-Date -Format "HH:mm:ss"
            $commitMsg = "Auto-save: $(Get-Date -Format 'yyyy-MM-dd HH:mm:ss')"

            Write-Host ""
            Write-Host "[$timestamp] " -NoNewline -ForegroundColor DarkGray
            Write-Host "Changes detected — committing & pushing..." -ForegroundColor Cyan

            Set-Location $REPO

            # Stage all changes
            & $GIT add . 2>&1 | Out-Null

            # Check if there's anything to commit
            $status = & $GIT status --porcelain 2>&1
            if ($status) {
                # Commit
                $commitOut = & $GIT commit -m $commitMsg 2>&1
                Write-Host "[$timestamp] " -NoNewline -ForegroundColor DarkGray
                Write-Host "Committed: $commitMsg" -ForegroundColor Green

                # Push
                $pushOut = & $GIT push origin main 2>&1
                if ($LASTEXITCODE -eq 0) {
                    Write-Host "[$timestamp] " -NoNewline -ForegroundColor DarkGray
                    Write-Host "✅ Pushed to GitHub successfully!" -ForegroundColor Green
                } else {
                    Write-Host "[$timestamp] " -NoNewline -ForegroundColor DarkGray
                    Write-Host "❌ Push failed: $pushOut" -ForegroundColor Red
                }
            } else {
                Write-Host "[$timestamp] " -NoNewline -ForegroundColor DarkGray
                Write-Host "No changes to commit (files may be gitignored)." -ForegroundColor DarkGray
            }
            Write-Host ""
        }
    }
}
finally {
    # Cleanup
    $watcher.EnableRaisingEvents = $false
    $watcher.Dispose()
    Get-EventSubscriber | Unregister-Event
    Write-Host ""
    Write-Host "Watcher stopped." -ForegroundColor Yellow
}
