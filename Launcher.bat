::[Bat To Exe Converter]
::
::YAwzoRdxOk+EWAnk
::fBw5plQjdG8=
::YAwzuBVtJxjWCl3EqQJgSA==
::ZR4luwNxJguZRRnk
::Yhs/ulQjdF+5
::cxAkpRVqdFKZSDk=
::cBs/ulQjdF+5
::ZR41oxFsdFKZSDk=
::eBoioBt6dFKZSDk=
::cRo6pxp7LAbNWATEpCI=
::egkzugNsPRvcWATEpCI=
::dAsiuh18IRvcCxnZtBJQ
::cRYluBh/LU+EWAnk
::YxY4rhs+aU+JeA==
::cxY6rQJ7JhzQF1fEqQJQ
::ZQ05rAF9IBncCkqN+0xwdVs0
::ZQ05rAF9IAHYFVzEqQJQ
::eg0/rx1wNQPfEVWB+kM9LVsJDGQ=
::fBEirQZwNQPfEVWB+kM9LVsJDGQ=
::cRolqwZ3JBvQF1fEqQJQ
::dhA7uBVwLU+EWDk=
::YQ03rBFzNR3SWATElA==
::dhAmsQZ3MwfNWATElA==
::ZQ0/vhVqMQ3MEVWAtB9wSA==
::Zg8zqx1/OA3MEVWAtB9wSA==
::dhA7pRFwIByZRRnk
::Zh4grVQjdCuDJGmW+0UiKRYUaAWWPVesFbYT7O3H+++UtnEaUewscIbV5b2DMOEQ/nrlZoUkxW5blt8zBRVLahOnYgomln5XtGiMJM+jpV+vGHSO40UjE2x6uGrdnCo4dOxpidAKwDS/8lnAlqsDxXnzUqwcKnP0w6BhK8E/61r6OnXvs5IVZvf7Zb7hBiSGJnEa7A==
::YB416Ek+ZW8=
::
::
::978f952a14a936cc963da21a135fa983
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
python -m main

echo The program is over. This may be due to an error or an active end.
cmd /k