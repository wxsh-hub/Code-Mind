@echo off
REM ============================================================
REM MCP Gateway 独立测试脚本（Windows）
REM 测试所有模块的单元测试
REM ============================================================

setlocal enabledelayedexpansion

set GREEN=[92m
set RED=[91m
set YELLOW=[93m
set NC=[0m

echo.
echo %YELLOW%==========================================
echo   MCP Gateway 单元测试
echo ==========================================%NC%
echo.

cd /d "%~dp0"

REM 运行所有新测试
echo 运行 RAG Client 测试...
python -m pytest tests/test_rag_client.py -v --tb=short
if errorlevel 1 (
    echo %RED%❌ RAG Client 测试失败%NC%
) else (
    echo %GREEN%✅ RAG Client 测试通过%NC%
)

echo.
echo 运行 RAG Tools 测试...
python -m pytest tests/test_rag_tools.py -v --tb=short
if errorlevel 1 (
    echo %RED%❌ RAG Tools 测试失败%NC%
) else (
    echo %GREEN%✅ RAG Tools 测试通过%NC%
)

echo.
echo 运行 Collector 测试...
python -m pytest tests/test_collector.py -v --tb=short
if errorlevel 1 (
    echo %RED%❌ Collector 测试失败%NC%
) else (
    echo %GREEN%✅ Collector 测试通过%NC%
)

echo.
echo 运行 Conflict 测试...
python -m pytest tests/test_conflict.py -v --tb=short
if errorlevel 1 (
    echo %RED%❌ Conflict 测试失败%NC%
) else (
    echo %GREEN%✅ Conflict 测试通过%NC%
)

echo.
echo %YELLOW%==========================================
echo   运行全部测试
echo ==========================================%NC%
echo.

python -m pytest tests/test_rag_client.py tests/test_rag_tools.py tests/test_collector.py tests/test_conflict.py -v --tb=short

echo.
echo %YELLOW%==========================================
echo   测试完成
echo ==========================================%NC%
echo.

pause
