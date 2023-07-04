@rem
@echo off

set "_root=%~dp0"
set "_root=%_root:~0,-1%"
cd /d "%_root%"
echo "%_root%"

set "_pyBin=%_root%\toolkit\"
set "_GitBin=%_root%\toolkit\Git\mingw64\bin"
set "PATH=%_pyBin%;%_pyBin%\Scripts;%_GitBin%;%PATH%"
title Python-Git-Program-Launcher
cmd /k