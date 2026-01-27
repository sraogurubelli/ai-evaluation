# Quick Fix: Ruff Not Found Error

## Problem
```
"ruff": executable file not found in $PATH
```

## Root Cause
1. Virtual environment was created with Python 3.9.5 (project requires 3.11+)
2. Dev dependencies (ruff, pytest, mypy) are not installed

## Solution

### Option 1: Fresh Start (Recommended)
```bash
# Remove old venv and start fresh
rm -rf .venv
task fresh
```

### Option 2: Manual Fix
```bash
# 1. Remove old venv
rm -rf .venv

# 2. Create new venv with Python 3.11
python3.11 -m venv .venv

# 3. Activate venv
source .venv/bin/activate

# 4. Upgrade pip and install dependencies
pip install --upgrade pip setuptools wheel
pip install -e ".[dev]"

# 5. Verify ruff is installed
ruff --version
```

### Option 3: Just Install Dev Dependencies (if venv is Python 3.11+)
```bash
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -e ".[dev]"
```

## Verify Fix
```bash
# Check Python version
source .venv/bin/activate
python --version  # Should show 3.11.x

# Check ruff is installed
ruff --version

# Run dev task
task dev
```

## What Changed
- Taskfile now shows helpful error messages when tools are missing
- Tasks guide you to run `task setup` or `task install-dev` when dependencies are missing
