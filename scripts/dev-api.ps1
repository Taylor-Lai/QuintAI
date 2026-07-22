param([string]$EnvironmentName = "wangtiao-engineering")

$ErrorActionPreference = "Stop"
$RepositoryRoot = Split-Path -Parent $PSScriptRoot
Set-Location $RepositoryRoot
conda run -n $EnvironmentName uvicorn docnexus.main:app --host 127.0.0.1 --port 8000 --reload
