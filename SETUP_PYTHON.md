# Python Version Setup

This project requires **Python >=3.11**.

## Check Your Python Version

```bash
python3 --version
python3.11 --version  # Should show 3.11.x or higher
```

## If Python 3.11+ is Not Available

### macOS (using Homebrew)
```bash
brew install python@3.11
# or
brew install python@3.12
```

### Using pyenv (Recommended)
```bash
# Install pyenv if not already installed
brew install pyenv

# Install Python 3.11
pyenv install 3.11.14

# Set local version for this project
pyenv local 3.11.14
```

### Using conda/miniconda
```bash
conda create -n ai-evolution python=3.11
conda activate ai-evolution
```

## Verify Setup

After installing Python 3.11+, verify it's available:
```bash
python3.11 --version  # Should show Python 3.11.x
which python3.11      # Should show path to Python 3.11
```

## Recreate Virtual Environment

If you already created a venv with Python 3.9, remove it and recreate:

```bash
rm -rf .venv
task venv
```

Or manually:
```bash
rm -rf .venv
python3.11 -m venv .venv
source .venv/bin/activate
pip install --upgrade pip setuptools wheel
pip install -e ".[dev]"
```

## Troubleshooting

### Taskfile uses python3.11 by default
The Taskfile has been updated to use `python3.11` by default. If you need to use a different Python 3.11+ version, you can override it:

```bash
PYTHON=python3.12 task venv
```

### Check which Python versions are available
```bash
which -a python3 python3.11 python3.12 python3.13
ls -la /usr/local/bin/python3*
```
