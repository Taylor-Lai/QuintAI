param(
    [string]$EnvironmentName = "wangtiao-engineering",
    [string]$CondaExecutable = "conda"
)

$ErrorActionPreference = "Stop"
$RepositoryRoot = Split-Path -Parent $PSScriptRoot

& $CondaExecutable create -n $EnvironmentName python=3.11 pip -y
& $CondaExecutable run -n $EnvironmentName python -m pip install -r "$RepositoryRoot\requirements\dev.txt"
& $CondaExecutable run -n $EnvironmentName python -m pip install --no-deps -e "$RepositoryRoot\backend"
