# 自动修复 npm PATH 问题
$npmPath = (npm config get prefix)
$userPath = [Environment]::GetEnvironmentVariable("Path", "User")

if ($userPath -notlike "*$npmPath*") {
    $newPath = if ($userPath) { "$userPath;$npmPath" } else { $npmPath }
    [Environment]::SetEnvironmentVariable("Path", $newPath, "User")
    
    # 同时更新系统级别的 PATH（需要管理员权限）
    if ([Security.Principal.WindowsIdentity]::GetCurrent().Groups -match 'S-1-5-32-544') {
        $machinePath = [Environment]::GetEnvironmentVariable("Path", "Machine")
        if ($machinePath -notlike "*$npmPath*") {
            [Environment]::SetEnvironmentVariable("Path", "$machinePath;$npmPath", "Machine")
        }
    }
    
    Write-Host "✅ npm 路径已永久添加到 PATH" -ForegroundColor Green
    Write-Host "📌 路径: $npmPath" -ForegroundColor Cyan
    Write-Host "⚠️  请重新启动你的 IDE/终端以使更改生效" -ForegroundColor Yellow
} else {
    Write-Host "ℹ️  npm 路径已存在于 PATH 中" -ForegroundColor Blue
}

# 测试 claude 命令
Write-Host "`n正在测试 claude 命令..." -ForegroundColor Magenta
$env:Path = [System.Environment]::GetEnvironmentVariable("Path","Machine") + ";" + [System.Environment]::GetEnvironmentVariable("Path","User")

if (Get-Command claude -ErrorAction SilentlyContinue) {
    Write-Host "✅ claude 命令可用！" -ForegroundColor Green
    claude --version
} else {
    Write-Host "⚠️  claude 命令暂时不可用，请重启终端后再试" -ForegroundColor Yellow
}