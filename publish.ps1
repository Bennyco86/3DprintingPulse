param(
  [switch]$Force,
  [switch]$SkipGit,
  [switch]$SkipPush,
  [int]$StartupDelaySeconds = 120,
  [int]$StepTimeoutSeconds = 900,
  [int]$GitTimeoutSeconds = 300
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

function Write-CommandOutput {
  param(
    [string]$StepName,
    [string]$Stream,
    [string]$Text
  )

  if ([string]::IsNullOrWhiteSpace($Text)) {
    return
  }

  $normalized = $Text -replace "`r", ""
  $lines = $normalized -split "`n"
  foreach ($line in $lines) {
    if ([string]::IsNullOrWhiteSpace($line)) {
      continue
    }
    Write-Log "[$StepName][$Stream] $line"
  }
}

function Invoke-CommandWithTimeout {
  param(
    [string]$FilePath,
    [string[]]$Arguments = @(),
    [int]$TimeoutSeconds = 900,
    [string]$StepName = "Command"
  )

  if ($TimeoutSeconds -lt 1) {
    throw "Invalid timeout for $StepName. TimeoutSeconds must be at least 1."
  }

  $escapedArgs = @()
  foreach ($arg in $Arguments) {
    if ($null -eq $arg) {
      $escapedArgs += '""'
      continue
    }
    if ($arg -match '[\s"]') {
      $quoted = $arg -replace '(\\*)"', '$1$1\"'
      $quoted = $quoted -replace '(\\+)$', '$1$1'
      $escapedArgs += '"' + $quoted + '"'
    } else {
      $escapedArgs += $arg
    }
  }
  $argumentString = $escapedArgs -join " "

  $startInfo = New-Object System.Diagnostics.ProcessStartInfo
  $startInfo.FileName = $FilePath
  $startInfo.Arguments = $argumentString
  $startInfo.WorkingDirectory = $projectRoot
  $startInfo.UseShellExecute = $false
  $startInfo.CreateNoWindow = $true
  $startInfo.RedirectStandardOutput = $true
  $startInfo.RedirectStandardError = $true

  $process = New-Object System.Diagnostics.Process
  $process.StartInfo = $startInfo

  if (-not $process.Start()) {
    throw "Failed to start $StepName."
  }

  $completed = $process.WaitForExit($TimeoutSeconds * 1000)
  if (-not $completed) {
    try {
      $process.Kill()
    } catch {
    }
    $process.WaitForExit()
    throw "$StepName timed out after $TimeoutSeconds seconds."
  }

  $stdoutText = $process.StandardOutput.ReadToEnd()
  $stderrText = $process.StandardError.ReadToEnd()

  return [pscustomobject]@{
    ExitCode = $process.ExitCode
    StdOut = $stdoutText
    StdErr = $stderrText
  }
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
    [string[]]$Args = @(),
    [int]$TimeoutSeconds = 900
  )

  $scriptPath = Join-Path $projectRoot $ScriptName
  if (-not (Test-Path -LiteralPath $scriptPath)) {
    throw "$ScriptName is missing at $scriptPath"
  }

  $result = Invoke-CommandWithTimeout `
    -FilePath $PythonExe `
    -Arguments @($scriptPath) + $Args `
    -TimeoutSeconds $TimeoutSeconds `
    -StepName $ScriptName

  Write-CommandOutput -StepName $ScriptName -Stream "stdout" -Text $result.StdOut
  Write-CommandOutput -StepName $ScriptName -Stream "stderr" -Text $result.StdErr

  if ($result.ExitCode -ne 0) {
    throw "$ScriptName failed with exit code $($result.ExitCode)."
  }
  Write-Log "OK $ScriptName completed."
}

function Invoke-Git {
  param(
    [string[]]$GitArgs,
    [string]$FailureMessage,
    [int]$TimeoutSeconds = 300
  )

  $stepName = "git " + ($GitArgs -join " ")
  $previousErrorActionPreference = $ErrorActionPreference
  $output = @()
  $exitCode = 1
  try {
    $ErrorActionPreference = "Continue"
    $output = & git -C $projectRoot @GitArgs 2>&1
    $exitCode = $LASTEXITCODE
  } finally {
    $ErrorActionPreference = $previousErrorActionPreference
  }

  if ($output) {
    Write-CommandOutput -StepName $stepName -Stream "stdout" -Text (($output | ForEach-Object { "$_" }) -join "`n")
  }

  if ($exitCode -ne 0) {
    throw $FailureMessage
  }

  return [pscustomobject]@{
    ExitCode = $exitCode
    StdOut = (($output | ForEach-Object { "$_" }) -join "`n")
    StdErr = ""
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

  $powerShellExe = (Get-Command powershell.exe -ErrorAction Stop).Source
  $runDailyResult = Invoke-CommandWithTimeout `
    -FilePath $powerShellExe `
    -Arguments @("-NoProfile", "-ExecutionPolicy", "Bypass", "-File", $runDailyPath) + $runDailyArgs `
    -TimeoutSeconds $StepTimeoutSeconds `
    -StepName "run_daily.ps1"
  Write-CommandOutput -StepName "run_daily.ps1" -Stream "stdout" -Text $runDailyResult.StdOut
  Write-CommandOutput -StepName "run_daily.ps1" -Stream "stderr" -Text $runDailyResult.StdErr
  if ($runDailyResult.ExitCode -ne 0) {
    throw "run_daily.ps1 failed with exit code $($runDailyResult.ExitCode)."
  }
  Write-Log "OK run_daily.ps1 completed."

  $pythonExe = Resolve-PythonExecutable
  Write-Log "OK Python resolved: $pythonExe"

  $autoDailyArgs = @()
  if ($Force) {
    $autoDailyArgs += "--force"
  }

  Invoke-PythonScript -PythonExe $pythonExe -ScriptName "auto_daily.py" -Args $autoDailyArgs -TimeoutSeconds $StepTimeoutSeconds
  Invoke-PythonScript -PythonExe $pythonExe -ScriptName "generate_rss.py" -TimeoutSeconds $StepTimeoutSeconds
  Invoke-PythonScript -PythonExe $pythonExe -ScriptName "prepare_linkedin_draft.py" -TimeoutSeconds $StepTimeoutSeconds

  if ($SkipGit) {
    Write-Log "OK git steps skipped (-SkipGit)."
  } else {
    Invoke-Git -GitArgs @("add", "-A") -FailureMessage "Git add failed." -TimeoutSeconds $GitTimeoutSeconds | Out-Null
    $statusResult = Invoke-Git -GitArgs @("status", "--porcelain") -FailureMessage "Git status failed." -TimeoutSeconds $GitTimeoutSeconds

    $statusLines = @()
    if (-not [string]::IsNullOrWhiteSpace($statusResult.StdOut)) {
      $statusLines = $statusResult.StdOut -split "(`r`n|`n|`r)" | Where-Object { -not [string]::IsNullOrWhiteSpace($_) }
    }
    if ($statusResult.ExitCode -ne 0) {
      throw "Git status failed."
    }

    $commitDate = Get-Date -Format "yyyy-MM-dd"
    $hasChanges = -not [string]::IsNullOrWhiteSpace(($statusLines | Out-String))

    if ($hasChanges) {
      Invoke-Git -GitArgs @("commit", "-m", "Daily content update: $commitDate") -FailureMessage "Git commit failed." -TimeoutSeconds $GitTimeoutSeconds | Out-Null
      Write-Log "OK git commit completed (date=$commitDate)."
    } else {
      Write-Log "OK git commit skipped (no changes)."
    }

    if ($SkipPush) {
      Write-Log "OK git push skipped (-SkipPush)."
    } else {
      $pushMasterFailed = $false
      try {
        Invoke-Git -GitArgs @("push", "origin", "master") -FailureMessage "Git push master failed." -TimeoutSeconds $GitTimeoutSeconds | Out-Null
      } catch {
        $pushMasterFailed = $true
        Write-Log "WARN git push origin master failed. Trying main."
      }

      if ($pushMasterFailed) {
        try {
          Invoke-Git -GitArgs @("push", "origin", "main") -FailureMessage "Git push main failed." -TimeoutSeconds $GitTimeoutSeconds | Out-Null
        } catch {
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
