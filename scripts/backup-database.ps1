[CmdletBinding()]
param(
    [string]$OutputDirectory = "backups"
)

$ErrorActionPreference = "Stop"
$repositoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
$backupDirectory = Join-Path $repositoryRoot $OutputDirectory
New-Item -ItemType Directory -Path $backupDirectory -Force | Out-Null
$timestamp = Get-Date -Format "yyyyMMdd-HHmmss"
$containerPath = "/tmp/huiwenrongtong-$timestamp.dump"
$targetPath = Join-Path $backupDirectory "huiwenrongtong-$timestamp.dump"

docker compose -f (Join-Path $repositoryRoot "compose.yaml") exec -T postgres `
    pg_dump -U huiwenrongtong -d huiwenrongtong -Fc -f $containerPath
if ($LASTEXITCODE -ne 0) { throw "数据库备份失败" }

docker compose -f (Join-Path $repositoryRoot "compose.yaml") cp `
    "postgres:$containerPath" $targetPath
if ($LASTEXITCODE -ne 0) { throw "备份文件复制失败" }

docker compose -f (Join-Path $repositoryRoot "compose.yaml") exec -T postgres rm -f $containerPath
Write-Output "数据库备份已生成：$targetPath"
