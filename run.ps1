$ErrorActionPreference = "Stop"

$pythonBase = "D:\Python312\python.exe"
$venvDir = ".venv"
$venvPython = Join-Path $venvDir "Scripts\python.exe"

if (-not (Test-Path $venvPython)) {
    & $pythonBase -m venv $venvDir
}

& $venvPython -m pip install --upgrade pip
& $venvPython -m pip install --upgrade -r requirements.txt

& $venvPython main.py
