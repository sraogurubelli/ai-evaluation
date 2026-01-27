# Installing Docker for AI Evolution

The project uses Docker Compose to run PostgreSQL. You need Docker installed to use database-related tasks.

## macOS Installation

### Option 1: Docker Desktop (Recommended)
1. Download from: https://www.docker.com/products/docker-desktop/
2. Install the `.dmg` file
3. Open Docker Desktop and wait for it to start
4. Restart your terminal

### Option 2: Homebrew
```bash
brew install --cask docker
```

Then open Docker Desktop from Applications.

## Verify Installation

After installing, verify Docker works:

```bash
# Check Docker is installed
docker --version

# Check Docker Compose (newer syntax)
docker compose version

# Or check old docker-compose (if installed)
docker-compose --version
```

## After Installation

Once Docker is installed, you can use database tasks:

```bash
# Start database
task db-up

# Or run full setup
task fresh
```

## Troubleshooting

### "docker-compose: command not found"
- Docker Desktop includes `docker compose` (newer syntax)
- The Taskfile automatically detects which version you have
- Make sure Docker Desktop is running

### Docker Desktop not starting
- Check System Preferences -> Security & Privacy
- Allow Docker Desktop if prompted
- Restart your Mac if needed

### Permission denied
- Make sure your user is in the `docker` group (usually automatic on macOS)
- Restart terminal after installation

## Alternative: Use External PostgreSQL

If you don't want to use Docker, you can:
1. Install PostgreSQL locally: `brew install postgresql@15`
2. Update `.env` with your PostgreSQL connection string
3. Skip `task db-up` and run `task db-migrate` directly
