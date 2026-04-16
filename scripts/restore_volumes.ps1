#!/usr/bin/env pwsh
<#
.SYNOPSIS
    恢复 QuantScope Docker 数据卷

.DESCRIPTION
    此脚本用于从备份恢复 MongoDB 和 Redis 数据卷

.PARAMETER BackupPath
    备份目录路径（例如：backups/20250117_143000）

.EXAMPLE
    .\scripts\restore_volumes.ps1 -BackupPath "backups/20250117_143000"
#>

param(
    [Parameter(Mandatory=$false)]
    [string]$BackupPath
)

# 设置错误处理
$ErrorActionPreference = "Stop"

# 获取脚本所在目录的父目录（项目根目录）
$ProjectRoot = Split-Path -Parent $PSScriptRoot

# 如果未指定备份路径，列出可用备份并让用户选择
if (-not $BackupPath) {
    $BackupDir = Join-Path $ProjectRoot "backups"
    
    if (-not (Test-Path $BackupDir)) {
        Write-Host "❌ 备份目录不存在: $BackupDir" -ForegroundColor Red
        exit 1
    }
    
    $AvailableBackups = Get-ChildItem -Path $BackupDir -Directory | Sort-Object Name -Descending
    
    if ($AvailableBackups.Count -eq 0) {
        Write-Host "❌ 没有可用的备份" -ForegroundColor Red
        exit 1
    }
    
    Write-Host ""
    Write-Host "📦 可用的备份:" -ForegroundColor Cyan
    Write-Host ""
    
    for ($i = 0; $i -lt $AvailableBackups.Count; $i++) {
        $Backup = $AvailableBackups[$i]
        $MetadataFile = Join-Path $Backup.FullName "metadata.json"
        
        if (Test-Path $MetadataFile) {
            $Metadata = Get-Content $MetadataFile | ConvertFrom-Json
            Write-Host "   [$($i + 1)] $($Backup.Name) - $($Metadata.date)" -ForegroundColor White
        } else {
            Write-Host "   [$($i + 1)] $($Backup.Name)" -ForegroundColor White
        }
    }
    
    Write-Host ""
    $Selection = Read-Host "请选择要恢复的备份 (1-$($AvailableBackups.Count))"
    
    try {
        $Index = [int]$Selection - 1
        if ($Index -lt 0 -or $Index -ge $AvailableBackups.Count) {
            Write-Host "❌ 无效的选择" -ForegroundColor Red
            exit 1
        }
        $BackupPath = $AvailableBackups[$Index].FullName
    } catch {
        Write-Host "❌ 无效的输入" -ForegroundColor Red
        exit 1
    }
}

# 验证备份路径
if (-not (Test-Path $BackupPath)) {
    Write-Host "❌ 备份路径不存在: $BackupPath" -ForegroundColor Red
    exit 1
}

Write-Host ""
Write-Host "=" * 70 -ForegroundColor Yellow
Write-Host "⚠️  警告：恢复数据卷将覆盖现有数据！" -ForegroundColor Yellow
Write-Host "=" * 70 -ForegroundColor Yellow
Write-Host ""
Write-Host "📁 备份路径: $BackupPath" -ForegroundColor Cyan
Write-Host ""

# 读取备份元数据
$MetadataFile = Join-Path $BackupPath "metadata.json"
if (Test-Path $MetadataFile) {
    $Metadata = Get-Content $MetadataFile | ConvertFrom-Json
    Write-Host "📝 备份信息:" -ForegroundColor Cyan
    Write-Host "   - 时间: $($Metadata.date)" -ForegroundColor White
    Write-Host "   - 主机: $($Metadata.host)" -ForegroundColor White
    Write-Host ""
}

$Confirmation = Read-Host "确认恢复？(yes/no)"
if ($Confirmation -ne "yes") {
    Write-Host "❌ 已取消恢复" -ForegroundColor Yellow
    exit 0
}

Write-Host ""
Write-Host "🔄 开始恢复数据卷..." -ForegroundColor Green
Write-Host ""

# 数据卷配置
$Volumes = @(
    @{
        Name = "tradingagents_mongodb_data"
        Container = "tradingagents-mongodb"
        BackupFile = "mongodb_backup.tar"
        Description = "MongoDB 数据"
    },
    @{
        Name = "tradingagents_redis_data"
        Container = "tradingagents-redis"
        BackupFile = "redis_backup.tar"
        Description = "Redis 数据"
    }
)

# 停止相关容器
Write-Host "🛑 停止相关容器..." -ForegroundColor Cyan
foreach ($Volume in $Volumes) {
    $ContainerName = $Volume.Container
    $IsRunning = docker ps --format "{{.Names}}" | Select-String -Pattern "^$ContainerName$"
    
    if ($IsRunning) {
        Write-Host "   停止容器: $ContainerName" -ForegroundColor Gray
        docker stop $ContainerName | Out-Null
    }
}

Write-Host ""

# 恢复每个数据卷
foreach ($Volume in $Volumes) {
    $VolumeName = $Volume.Name
    $ContainerName = $Volume.Container
    $BackupFile = Join-Path $BackupPath $Volume.BackupFile
    $Description = $Volume.Description
    
    if (-not (Test-Path $BackupFile)) {
        Write-Host "⚠️  备份文件不存在，跳过: $BackupFile" -ForegroundColor Yellow
        continue
    }
    
    Write-Host "📦 恢复 $Description ($VolumeName)..." -ForegroundColor Cyan
    
    try {
        # 检查数据卷是否存在
        $VolumeExists = docker volume ls --format "{{.Name}}" | Select-String -Pattern "^$VolumeName$"
        
        if ($VolumeExists) {
            Write-Host "   🗑️  删除现有数据卷..." -ForegroundColor Gray
            docker volume rm $VolumeName | Out-Null
        }
        
        # 创建新数据卷
        Write-Host "   📁 创建新数据卷..." -ForegroundColor Gray
        docker volume create $VolumeName | Out-Null
        
        # 使用临时容器恢复数据
        Write-Host "   🔄 恢复数据..." -ForegroundColor Gray
        
        docker run --rm `
            -v ${VolumeName}:/data `
            -v ${BackupPath}:/backup `
            alpine `
            sh -c "cd /data && tar xzf /backup/$($Volume.BackupFile)"
        
        if ($LASTEXITCODE -eq 0) {
            Write-Host "   ✅ 恢复成功" -ForegroundColor Green
        } else {
            Write-Host "   ❌ 恢复失败" -ForegroundColor Red
        }
        
    } catch {
        Write-Host "   ❌ 恢复失败: $_" -ForegroundColor Red
    }
    
    Write-Host ""
}

# 重启容器
Write-Host "🚀 重启容器..." -ForegroundColor Cyan
foreach ($Volume in $Volumes) {
    $ContainerName = $Volume.Container
    $ContainerExists = docker ps -a --format "{{.Names}}" | Select-String -Pattern "^$ContainerName$"
    
    if ($ContainerExists) {
        Write-Host "   启动容器: $ContainerName" -ForegroundColor Gray
        docker start $ContainerName | Out-Null
    }
}

Write-Host ""
Write-Host "=" * 70 -ForegroundColor Green
Write-Host "✅ 恢复完成！" -ForegroundColor Green
Write-Host "=" * 70 -ForegroundColor Green
Write-Host ""
Write-Host "💡 提示:" -ForegroundColor Yellow
Write-Host "   - 请检查容器日志确认服务正常运行" -ForegroundColor Gray
Write-Host "   - 使用 'docker logs <container_name>' 查看日志" -ForegroundColor Gray
Write-Host ""

