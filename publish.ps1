param(
  [switch]$Force,
  [switch]$SkipGit,
  [switch]$SkipPush,
  [int]$StartupDelaySeconds = 120
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$logsDir = Join-Path $projectRoot "logs"
$logFile = Join-Path $logsDir "publish.log"
$lastRunFile = Join-Path $projectRoot "last_run.txt"
$lastSuccessFile = Join-Path $projectRoot "last_success.txt"

if (-not (Test-Path -LiteralPath $logsDir)) {
  New-Item -Path $logsDir -ItemType Directory -Force | Out-Null
}

Set-Location -Path $projectRoot

function Write-Log {
  param([string]$Message)
  $stamp = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
  Add-Content -Path $logFile -Value "[$stamp] $Message" -Encoding UTF8
}

function Get-LastSuccessDate {
  param([string]$Path)
  if (-not (Test-Path -LiteralPath $Path)) {
    return $null
  }

  $raw = (Get-Content -LiteralPath $Path -Raw -ErrorAction Stop).Trim()
  if (-not $raw) {
    return $null
  }

  if ($raw -match "Last success:\s*(\d{4}-\d{2}-\d{2})\s") {
    return $matches[1]
  }
  return $null
}

function Resolve-PythonExecutable {
  $pyCmd = Get-Command py -ErrorAction SilentlyContinue
  if ($pyCmd) {
    $pyPath = $null
    try {
      $pyList = & $pyCmd.Source -0p 2>$null
      if ($pyList) {
        $pyPath = ($pyList | Select-Object -First 1).Split()[-1]
      }
    } catch {
      $pyPath = $null
    }

    if ($pyPath -and (Test-Path -LiteralPath $pyPath)) {
      return $pyPath
    }
    return $pyCmd.Source
  }

  $pythonCandidates = @()
  try {
    $pythonCandidates = & where.exe python 2>$null
  } catch {
    $pythonCandidates = @()
  }

  $fallback = $pythonCandidates |
    Where-Object { $_ -and ($_ -notmatch "WindowsApps") } |
    Select-Object -First 1

  if ($fallback) {
    return $fallback
  }

  throw "Python not found. Install Python or add it to PATH."
}

function Invoke-PythonScript {
  param(
    [string]$PythonExe,
    [string]$ScriptName,
    [string[]]$Args = @()
  )

  $scriptPath = Join-Path $projectRoot $ScriptName
  if (-not (Test-Path -LiteralPath $scriptPath)) {
    throw "$ScriptName is missing at $scriptPath"
  }

  & $PythonExe $scriptPath @Args
  if ($LASTEXITCODE -ne 0) {
    throw "$ScriptName failed with exit code $LASTEXITCODE."
  }
  Write-Log "OK $ScriptName completed."
}

function Invoke-Git {
  param(
    [string[]]$GitArgs,
    [string]$FailureMessage
  )

  & git -C $projectRoot @GitArgs
  if ($LASTEXITCODE -ne 0) {
    throw $FailureMessage
  }
}

try {
  $today = Get-Date -Format "yyyy-MM-dd"
  $startedAt = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
  Set-Content -Path $lastRunFile -Value "Last run start: $startedAt" -Encoding UTF8

  $lastSuccessDate = Get-LastSuccessDate -Path $lastSuccessFile
  if (-not $Force -and $lastSuccessDate -eq $today) {
    Write-Log "Skipping: already succeeded today ($today). Use -Force to rerun."
    exit 0
  }

  Write-Log "START publish.ps1 (user=$env:USERNAME machine=$env:COMPUTERNAME)"

  if ($StartupDelaySeconds -gt 0) {
    Start-Sleep -Seconds $StartupDelaySeconds
  }

  $runDailyPath = Join-Path $projectRoot "run_daily.ps1"
  if (-not (Test-Path -LiteralPath $runDailyPath)) {
    throw "run_daily.ps1 is missing at $runDailyPath"
  }

  $runDailyArgs = @()
  if ($Force) {
    $runDailyArgs += "-Force"
  }

  & $runDailyPath @runDailyArgs
  if (-not $?) {
    throw "run_daily.ps1 failed."
  }
  Write-Log "OK run_daily.ps1 completed."

  $pythonExe = Resolve-PythonExecutable
  Write-Log "OK Python resolved: $pythonExe"

  $autoDailyArgs = @()
  if ($Force) {
    $autoDailyArgs += "--force"
  }

  Invoke-PythonScript -PythonExe $pythonExe -ScriptName "auto_daily.py" -Args $autoDailyArgs
  Invoke-PythonScript -PythonExe $pythonExe -ScriptName "generate_rss.py"
  Invoke-PythonScript -PythonExe $pythonExe -ScriptName "prepare_linkedin_draft.py"

  if ($SkipGit) {
    Write-Log "OK git steps skipped (-SkipGit)."
  } else {
    Invoke-Git -GitArgs @("add", "-A") -FailureMessage "Git add failed."
    $statusLines = & git -C $projectRoot status --porcelain
    if ($LASTEXITCODE -ne 0) {
      throw "Git status failed."
    }

    $commitDate = Get-Date -Format "yyyy-MM-dd"
    $hasChanges = -not [string]::IsNullOrWhiteSpace(($statusLines | Out-String))

    if ($hasChanges) {
      Invoke-Git -GitArgs @("commit", "-m", "Daily content update: $commitDate") -FailureMessage "Git commit failed."
      Write-Log "OK git commit completed (date=$commitDate)."
    } else {
      Write-Log "OK git commit skipped (no changes)."
    }

    if ($SkipPush) {
      Write-Log "OK git push skipped (-SkipPush)."
    } else {
      & git -C $projectRoot push origin master
      if ($LASTEXITCODE -ne 0) {
        & git -C $projectRoot push origin main
        if ($LASTEXITCODE -ne 0) {
          throw "Git push failed. Check network access or credentials."
        }
      }
      Write-Log "OK git push completed."
    }
  }

  $successAt = Get-Date -Format "yyyy-MM-dd HH:mm:ss"
  Set-Content -Path $lastSuccessFile -Value "Last success: $successAt" -Encoding UTF8
  Write-Log "SUCCESS publish.ps1"
  exit 0
} catch {
  Write-Log "ERROR $($_.Exception.Message)"
  Write-Error $_
  exit 1
}
