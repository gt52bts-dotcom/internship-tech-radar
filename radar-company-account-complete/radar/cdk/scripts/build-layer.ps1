param(
    [string]$Python = "python"
)

$ErrorActionPreference = "Stop"
$Root = Resolve-Path (Join-Path $PSScriptRoot "..")
$Layer = Join-Path $Root "layer_build"
$PythonDir = Join-Path $Layer "python"

Write-Host "=== Build Lambda layer: anthropic + feedparser ==="
if (Test-Path $Layer) {
    Remove-Item -Recurse -Force $Layer
}
New-Item -ItemType Directory -Force $PythonDir | Out-Null

& $Python -m pip install anthropic feedparser -t $PythonDir

Write-Host "Layer ready at $Layer"
Write-Host "Next: cdk synth, then cdk deploy --all"
