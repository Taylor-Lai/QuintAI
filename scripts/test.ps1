param([string]$EnvironmentName = "wangtiao-engineering")

$ErrorActionPreference = "Stop"
$RepositoryRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepositoryRoot
conda run -n $EnvironmentName pytest -m "not api_acceptance"
conda run -n $EnvironmentName ruff check backend
