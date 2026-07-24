[CmdletBinding()]
param(
    [Parameter(Mandatory = $true)]
    [string]$BackupPath,
    [switch]$ConfirmRestore
)

$ErrorActionPreference = "Stop"
if (-not $ConfirmRestore) {
    throw "恢复操作会覆盖当前数据库。确认目标无误后添加 -ConfirmRestore。"
}

$repositoryRoot = (Resolve-Path -LiteralPath (Join-Path $PSScriptRoot "..")).Path
$resolvedBackup = (Resolve-Path -LiteralPath $BackupPath).Path
if (-not $resolvedBackup.StartsWith($repositoryRoot + [IO.Path]::DirectorySeparatorChar)) {
    throw "备份文件必须位于项目目录内"
}

$containerPath = "/tmp/quintai-restore.dump"
docker compose -f (Join-Path $repositoryRoot "compose.yaml") cp `
    $resolvedBackup "postgres:$containerPath"
if ($LASTEXITCODE -ne 0) { throw "备份文件复制失败" }

docker compose -f (Join-Path $repositoryRoot "compose.yaml") exec -T postgres `
    pg_restore -U quintai -d quintai --clean --if-exists --no-owner $containerPath
if ($LASTEXITCODE -ne 0) { throw "数据库恢复失败" }

docker compose -f (Join-Path $repositoryRoot "compose.yaml") exec -T postgres rm -f $containerPath
Write-Output "数据库恢复完成，请重新启动 app 和 worker 服务。"
