# Docker Setup for Money Tracking App

Simple Docker Compose setup with Django app and PostgreSQL database.

## Quick Start

### 1. Prerequisites
- Docker installed
- Docker Compose installed

### 2. Run the App
```bash
# Make the script executable (if not already)
chmod +x docker-deploy.sh

# Run the deployment script
./docker-deploy.sh
```

### 3. Access the App
- **App**: http://localhost:8000
- **Database**: localhost:5432
- **Database credentials**: postgres/postgres

## Manual Commands

### Start services
```bash
docker-compose up -d
```

### Build and start
```bash
docker-compose up --build -d
```

### Run migrations
```bash
docker-compose exec web python manage.py migrate
```

### Create superuser
```bash
docker-compose exec web python manage.py createsuperuser
```

### View logs
```bash
docker-compose logs -f
```

### Stop services
```bash
docker-compose down
```

### Shell access
```bash
docker-compose exec web bash
```

## Services

### Web App (Django)
- **Port**: 8000
- **Environment**: Development (DEBUG=1)
- **Database**: PostgreSQL
- **Static files**: Collected automatically

### Database (PostgreSQL)
- **Port**: 5432
- **Database**: money_tracking
- **User**: postgres
- **Password**: postgres
- **Data**: Persisted in Docker volume

## File Structure
```
moneyTracking/
├── docker-compose.yml    # Main compose file
├── Dockerfile           # App container definition
├── docker-deploy.sh     # Deployment script
└── DOCKER_README.md     # This file
```

## Troubleshooting

### Port already in use
```bash
# Check what's using the port
lsof -i :8000
lsof -i :5432

# Stop conflicting services or change ports in docker-compose.yml
```

### Database connection issues
```bash
# Check if database is ready
docker-compose exec db pg_isready -U postgres

# View database logs
docker-compose logs db
```

### Reset everything
```bash
# Stop and remove everything
docker-compose down -v

# Remove all containers and volumes
docker system prune -a --volumes

# Start fresh
./docker-deploy.sh
```

## Development

### Hot reload
The app is configured for development with volume mounting, so changes to your code will be reflected immediately.

### Database access
```bash
# Connect to PostgreSQL
docker-compose exec db psql -U postgres -d money_tracking

# Or from outside Docker
psql -h localhost -p 5432 -U postgres -d money_tracking
```

### Static files
Static files are automatically collected and served by WhiteNoise.

## Production Notes

This setup is for development. For production:
1. Change database password
2. Set DEBUG=False
3. Use proper secret key
4. Configure proper ALLOWED_HOSTS
5. Use external database service
6. Set up proper logging
7. Use reverse proxy (nginx)
