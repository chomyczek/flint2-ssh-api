@echo off
setlocal EnableDelayedExpansion

set ERRORS=0
set RUFF_LINT=OK
set RUFF_FORMAT=OK
set MYPY=OK
set DEPTRY=OK

echo [1/4] Ruff lint...
uv run ruff check .
if %ERRORLEVEL% neq 0 (set RUFF_LINT=FAIL& set /a ERRORS+=1)

echo [2/4] Ruff format...
uv run ruff format --check .
if %ERRORLEVEL% neq 0 (set RUFF_FORMAT=FAIL& set /a ERRORS+=1)

echo [3/4] Mypy...
uv run mypy app/
if %ERRORLEVEL% neq 0 (set MYPY=FAIL& set /a ERRORS+=1)

echo [4/4] Deptry...
uv run deptry .
if %ERRORLEVEL% neq 0 (set DEPTRY=FAIL& set /a ERRORS+=1)

echo.
echo ================================
echo  SUMMARY
echo ================================
echo  Ruff lint:    !RUFF_LINT!
echo  Ruff format:  !RUFF_FORMAT!
echo  Mypy:         !MYPY!
echo  Deptry:       !DEPTRY!
echo ================================

if !ERRORS! == 0 (
    echo  Result: ALL CHECKS PASSED
    echo ================================
    exit 0)
echo  Result: !ERRORS! check(s) FAILED
echo ================================
exit 1
