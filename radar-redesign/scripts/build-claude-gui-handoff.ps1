param(
    [string]$Destination = (Join-Path $PSScriptRoot "..\claude-gui-handoff")
)

$ErrorActionPreference = "Stop"
$RadarRoot = (Resolve-Path (Join-Path $PSScriptRoot "..")).Path
$Destination = [System.IO.Path]::GetFullPath($Destination)
if (-not $Destination.StartsWith($RadarRoot, [System.StringComparison]::OrdinalIgnoreCase)) {
    throw "Destination must stay inside radar-redesign."
}
if (Test-Path -LiteralPath $Destination) {
    Remove-Item -LiteralPath $Destination -Recurse -Force
}
New-Item -ItemType Directory -Path $Destination | Out-Null

$directories = @("agentic_cloud_radar", "web_api", "web", "web-demo-cdk", "docs")
foreach ($directory in $directories) {
    Copy-Item -LiteralPath (Join-Path $RadarRoot $directory) -Destination (Join-Path $Destination $directory) -Recurse
}
Get-ChildItem -LiteralPath $Destination -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force
$generatedWebFiles = @(
    (Join-Path $Destination "web-demo-cdk\cdk.out"),
    (Join-Path $Destination "web-demo-cdk\synth.log")
)
foreach ($generatedFile in $generatedWebFiles) {
    if (Test-Path -LiteralPath $generatedFile) {
        Remove-Item -LiteralPath $generatedFile -Recurse -Force
    }
}
Copy-Item -LiteralPath (Join-Path $RadarRoot "design-baseline.md") -Destination $Destination
Copy-Item -LiteralPath (Join-Path $RadarRoot "README.md") -Destination $Destination
Copy-Item -LiteralPath (Join-Path $RadarRoot "CLAUDE_GUI_HANDOFF.md") -Destination $Destination
Copy-Item -LiteralPath (Join-Path $RadarRoot "web_demo_local.py") -Destination $Destination

$ProjectRoot = Split-Path $RadarRoot -Parent
$pocSource = Join-Path $ProjectRoot "poc"
$pocDestination = Join-Path $Destination "poc"
New-Item -ItemType Directory -Path $pocDestination | Out-Null
$registeredRecipes = @("s3-files-cdk-poc", "lambda-self-managed-storage-cdk-poc")
foreach ($recipe in $registeredRecipes) {
    $recipeSource = Join-Path $pocSource $recipe
    Get-ChildItem -LiteralPath $recipeSource -Recurse -File |
        Where-Object { $_.FullName -notmatch "\\cdk\.out|\\evidence" } |
        ForEach-Object {
            $relativePath = $_.FullName.Substring($pocSource.Length).TrimStart("\\")
            $target = Join-Path $pocDestination $relativePath
            New-Item -ItemType Directory -Path (Split-Path $target -Parent) -Force | Out-Null
            Copy-Item -LiteralPath $_.FullName -Destination $target
        }
}
$sampleDestination = Join-Path $Destination "sample-artifacts\lambda-self-managed-code-storage"
New-Item -ItemType Directory -Path $sampleDestination -Force | Out-Null
$sampleSource = Join-Path $RadarRoot "out\lambda-self-managed-code-storage-s4-20260729"
Get-ChildItem -LiteralPath $sampleSource -File | Copy-Item -Destination $sampleDestination
Get-ChildItem -LiteralPath $Destination -Recurse -Directory -Filter "__pycache__" | Remove-Item -Recurse -Force

@'
# Agentic Cloud Radar GUI Handoff

This folder is self-contained: it includes the current S1-S5 core, a deployable AWS web demo, two controlled S4 PoC recipes, real redacted artifact examples, and the GUI contract for Claude.

Start with `CLAUDE_GUI_HANDOFF.md`. Run `python web_demo_local.py` for a local GUI, or deploy from `web-demo-cdk/README.md`.

Do not add a browser action that bypasses the S4 approval and cleanup flow.
'@ | Set-Content -LiteralPath (Join-Path $Destination "README.md") -Encoding utf8

Write-Host "Claude GUI handoff created at: $Destination"
