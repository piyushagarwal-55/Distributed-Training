@echo off
echo ============================================================
echo   COMPLETE SYSTEM VERIFICATION
echo ============================================================
echo.

echo [1/3] Checking Backend API (Port 8000)...
curl -s http://localhost:8000/health
if %errorlevel% == 0 (
    echo [OK] Backend is running
) else (
    echo [FAIL] Backend not responding
)
echo.

echo [2/3] Checking Frontend (Port 3000)...
curl -s http://localhost:3000 ^>nul
if %errorlevel% == 0 (
    echo [OK] Frontend is running
) else (
    echo [FAIL] Frontend not responding
)
echo.

echo [3/3] Checking Blockchain (Port 8546)...
curl -s -X POST -H "Content-Type: application/json" --data "{\"jsonrpc\":\"2.0\",\"method\":\"eth_blockNumber\",\"params\":[],\"id\":1}" http://localhost:8546 ^>nul
if %errorlevel% == 0 (
    echo [OK] Blockchain is running
) else (
    echo [FAIL] Blockchain not responding
)
echo.

echo ============================================================
echo   SYSTEM STATUS SUMMARY
echo ============================================================
curl -s http://localhost:8000/api/status
echo.
echo.

echo ============================================================
echo   ACCESS URLS:
echo ============================================================
echo   Frontend:    http://localhost:3000
echo   Backend API: http://localhost:8000/docs
echo   Blockchain:  http://localhost:8546
echo ============================================================
