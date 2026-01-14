$ErrorActionPreference = "Stop"

$projectRoot = $PSScriptRoot
$dateStamp = Get-Date -Format "yyyy-MM-dd"
$outDir = Join-Path $projectRoot $dateStamp
$outFile = Join-Path $outDir "README.md"

if (-not (Test-Path $outDir)) {
  New-Item -Path $outDir -ItemType Directory | Out-Null
}

if (Test-Path $outFile) {
  Write-Host "Daily README already exists: $outFile"
  exit 0
}

$content = @(
  "# Quality3Ds Daily 3D Printing News - $dateStamp",
  "",
  "## Stories",
  "",
  "TODO: Replace this section with 4-8 verified stories per README requirements.",
  "",
  "Template (delete this block once filled):",
  "?? Headline here",
  "Hook sentence.",
  "Concrete detail sentence.",
  "Read more ? https://example.com",
  "",
  "(Repeat per story; separate stories with one blank line.)"
)

Set-Content -Path $outFile -Value $content -Encoding UTF8
Write-Host "Wrote $outFile"
