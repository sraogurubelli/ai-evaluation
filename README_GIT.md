# Setting Up Git Repository

This repository is initialized and ready to push to a remote.

## Initial Setup

The repository has been initialized with:
- Initial commit with all project files
- Comprehensive .gitignore
- GitHub Actions CI workflow

## Push to Remote

### Option 1: Create new repository on GitHub/GitLab

1. Create a new repository on GitHub/GitLab (e.g., `ai-evolution`)

2. Add remote and push:
```bash
git remote add origin git@github.com:your-username/ai-evolution.git
git branch -M main
git push -u origin main
```

### Option 2: Use existing remote

If you have an existing remote:
```bash
git remote add origin <your-remote-url>
git branch -M main  # or keep as master
git push -u origin main
```

## Repository Structure

```
ai-evolution/
├── src/ai_evolution/     # Main package
├── tests/                # Test suite
├── examples/             # Usage examples
├── docs/                 # Documentation
├── migrations/           # Migration tools
├── .github/workflows/   # CI/CD
├── LICENSE               # MIT License
└── README.md             # Project README
```

## Git Workflow

```bash
# Make changes
git add .
git commit -m "Description of changes"
git push
```

## CI/CD

The repository includes a GitHub Actions workflow that:
- Runs tests on push/PR
- Checks code coverage
- Tests with PostgreSQL

See `.github/workflows/ci.yml` for details.
