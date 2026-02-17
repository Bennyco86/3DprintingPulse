param(
  [switch]$Force
)

$ErrorActionPreference = "Stop"
Set-StrictMode -Version Latest

$projectRoot = Split-Path -Parent $MyInvocation.MyCommand.Path
$dateStamp = Get-Date -Format "yyyy-MM-dd"
$outDir = Join-Path $projectRoot $dateStamp
$outFile = Join-Path $outDir "README.md"

if (-not (Test-Path -LiteralPath $outDir)) {
  New-Item -Path $outDir -ItemType Directory -Force | Out-Null
}

if ((Test-Path -LiteralPath $outFile) -and -not $Force) {
  Write-Output "Daily README already exists: $outFile"
  exit 0
}

$template = @"
# Quality3Ds Daily 3D Printing News - $dateStamp

## Stories

TODO: Replace this template with curated stories from today's run.
Template (delete this block once filled):
?? Headline here
Hook sentence.
Concrete detail sentence.
Read more ? https://example.com
(Repeat per story; separate stories with one blank line.)
"@

Set-Content -Path $outFile -Value $template -Encoding UTF8
Write-Output "Prepared daily README: $outFile"
