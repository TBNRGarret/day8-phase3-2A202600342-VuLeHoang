param(
    [switch]$WithSqlite
)

python -m venv .venv
# Activate the venv for the rest of the script when run in PowerShell
. .venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
if ($WithSqlite) {
    python -m pip install -e ".[sqlite]"
} else {
    python -m pip install -e .
}
