# Docker Volume Management

This project uses Docker Compose for PostgreSQL and pgAdmin. Here's how to manage volumes.

## Available Tasks

### Stop Database (Keep Volumes)
```bash
task db-down
```
Stops the PostgreSQL container but keeps the data volumes intact.

### Stop Database and Remove Volumes
```bash
task db-down-volumes
```
Stops the PostgreSQL container and removes all associated volumes (⚠️ **deletes data**).

### Stop All Services and Remove Volumes
```bash
task db-stop-all
```
Stops all Docker Compose services (postgres, pgadmin) and removes all volumes.

### Complete Docker Cleanup
```bash
task db-cleanup
```
Stops all services, removes containers, volumes, networks, and orphaned containers.

### Clean Docker Resources
```bash
task clean-docker
```
Same as `db-cleanup` - removes all Docker resources.

## Volume Information

The project uses these Docker volumes:
- `postgres_data`: PostgreSQL database files
- `pgadmin_data`: pgAdmin configuration and data

## Manual Commands

### List volumes
```bash
docker volume ls | grep ai-evolution
```

### Inspect a volume
```bash
docker volume inspect ai-evolution_postgres_data
```

### Remove a specific volume
```bash
docker volume rm ai-evolution_postgres_data
```

### Remove all project volumes
```bash
docker-compose down -v
```

## Fresh Start (Removes Everything)

To completely start fresh, including removing volumes:
```bash
task fresh
```

This will:
1. Clean Python artifacts
2. Remove virtual environment
3. Stop and remove database volumes
4. Create new virtual environment
5. Install dependencies
6. Start database
7. Run migrations

## Warning

⚠️ **Removing volumes will delete all database data permanently!**

Always backup important data before removing volumes:
```bash
# Backup database before removing volumes
docker-compose exec postgres pg_dump -U ai_evolution ai_evolution > backup.sql

# Then remove volumes if needed
task db-down-volumes
```
