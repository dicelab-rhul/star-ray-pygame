@echo off
REM Run unit tests
echo Running unit tests...
python -m unittest discover -s test

REM Check if tests passed
IF %ERRORLEVEL% NEQ 0 (
    echo Unit tests failed. Aborting build.
    EXIT /B 1
)

REM Build the package
echo Building package...
python -m build --wheel

REM Check if the build was successful
IF %ERRORLEVEL% NEQ 0 (
    echo Build failed.
    EXIT /B 1
)

echo Build successful.
