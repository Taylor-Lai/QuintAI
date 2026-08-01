param(
    [string]$EnvironmentName = "wangtiao-engineering",
    [switch]$SkipWeb,
    [switch]$SkipAndroid
)

$ErrorActionPreference = "Stop"
$env:PYTHONUTF8 = "1"
$env:PYTHONIOENCODING = "utf-8"
$RepositoryRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepositoryRoot

function Invoke-Checked {
    param(
        [Parameter(Mandatory = $true)][string]$FilePath,
        [Parameter(ValueFromRemainingArguments = $true)][string[]]$Arguments
    )
    & $FilePath @Arguments
    if ($LASTEXITCODE -ne 0) {
        throw "Command failed with exit code $LASTEXITCODE`: $FilePath $($Arguments -join ' ')"
    }
}

Invoke-Checked conda run -n $EnvironmentName ruff check backend scripts
Invoke-Checked conda run -n $EnvironmentName mypy
Invoke-Checked conda run -n $EnvironmentName python -m compileall -q backend/src
# Avoid leaving a root-level cache directory that Docker's Windows context
# scanner may be unable to stat even though it is listed in .dockerignore.
Invoke-Checked -FilePath conda -Arguments @(
    "run", "-n", $EnvironmentName,
    "pytest", "backend/tests", "-m", "not api_acceptance", "-p", "no:cacheprovider",
    "--cov=docnexus", "--cov-report=term-missing", "--cov-fail-under=59"
)
Invoke-Checked conda run -n $EnvironmentName python scripts/evaluate_table_engine.py

if (-not $SkipWeb) {
    Push-Location (Join-Path $RepositoryRoot "frontend")
    try {
        Invoke-Checked npm.cmd run lint
        Invoke-Checked npm.cmd test
        Invoke-Checked npm.cmd run build
        Invoke-Checked npm.cmd audit
        Invoke-Checked npm.cmd run test:e2e
    }
    finally {
        Pop-Location
    }
}

if (-not $SkipAndroid) {
    if (-not $env:JAVA_HOME -and -not (Get-Command java -ErrorAction SilentlyContinue)) {
        throw "Android verification requires JAVA_HOME or java on PATH. Use -SkipAndroid only when recording Android as blocked."
    }
    Push-Location (Join-Path $RepositoryRoot "android-app")
    try {
        Invoke-Checked .\gradlew.bat test lint assembleDebug
    }
    finally {
        Pop-Location
    }
}
