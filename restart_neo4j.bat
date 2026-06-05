@echo off
REM Stop Neo4j
echo Stopping Neo4j...
cd neo4j-community-2026.05.0-windows\neo4j-community-2026.05.0\bin
call neo4j.bat stop

REM Wait for graceful shutdown
timeout /t 5 /nobreak

REM Start Neo4j
echo Starting Neo4j...
call neo4j.bat start

echo.
echo Neo4j is restarting. Please wait 10-15 seconds for it to fully start.
echo.
pause
