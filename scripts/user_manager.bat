@echo off
chcp 65001 >nul
setlocal enabledelayedexpansion

echo 🔧 QuantScope 用户密码管理工具
echo ================================================

REM 检查Python是否可用
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ 错误: 未找到Python，请确保Python已安装并添加到PATH
    pause
    exit /b 1
)

REM 获取脚本目录
set "SCRIPT_DIR=%~dp0"
set "MANAGER_SCRIPT=%SCRIPT_DIR%user_password_manager.py"

REM 检查管理脚本是否存在
if not exist "%MANAGER_SCRIPT%" (
    echo ❌ 错误: 找不到用户管理脚本 %MANAGER_SCRIPT%
    pause
    exit /b 1
)

REM 如果没有参数，显示帮助
if "%~1"=="" (
    echo.
    echo 使用方法:
    echo   %~nx0 list                              - 列出所有用户
    echo   %~nx0 change-password [用户名] [新密码]   - 修改用户密码
    echo   %~nx0 create-user [用户名] [密码] [角色]   - 创建新用户
    echo   %~nx0 delete-user [用户名]               - 删除用户
    echo   %~nx0 reset                             - 重置为默认配置
    echo.
    echo 示例:
    echo   %~nx0 list
    echo   %~nx0 change-password admin newpass123
    echo   %~nx0 create-user testuser pass123 user
    echo   %~nx0 delete-user testuser
    echo   %~nx0 reset
    echo.
    pause
    exit /b 0
)

REM 执行Python脚本
python "%MANAGER_SCRIPT%" %*

REM 如果有错误，暂停显示
if errorlevel 1 (
    echo.
    echo 按任意键继续...
    pause >nul
)