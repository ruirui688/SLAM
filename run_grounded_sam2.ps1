param(
    [Parameter(ValueFromRemainingArguments = $true)]
    [string[]]$PythonArgs
)

$ErrorActionPreference = "Stop"
$python = "D:\miniconda3\envs\grounded-sam2\python.exe"

if (-not (Test-Path -LiteralPath $python)) {
    Write-Error "Python executable not found: $python"
}

Push-Location $PSScriptRoot
try {
    if (-not $PythonArgs -or $PythonArgs.Count -eq 0) {
        Write-Host "Project root: $PSScriptRoot"
        Write-Host "Python: $python"
        Write-Host ""
        Write-Host "Usage:"
        Write-Host "  .\run_grounded_sam2.ps1 script.py [args]"
        Write-Host "  .\run_grounded_sam2.ps1 -m module [args]"
        Write-Host "  .\run_grounded_sam2.ps1 -c `"code`""
        exit 0
    }

    & $python @PythonArgs
    exit $LASTEXITCODE
}
finally {
    Pop-Location
}
