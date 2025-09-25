#!/bin/bash

# Simple Docker Compose deployment script for Money Tracking app

echo "🚀 Starting Docker Compose deployment..."

# Check if Docker is running
if ! docker info > /dev/null 2>&1; then
    echo "❌ Docker is not running. Please start Docker first."
    exit 1
fi

# Check if Docker Compose is available
if ! command -v docker-compose &> /dev/null; then
    echo "❌ Docker Compose is not installed. Please install it first."
    exit 1
fi

echo "📦 Building and starting services..."
docker-compose up --build -d

echo "⏳ Waiting for database to be ready..."
sleep 10

echo "🔧 Running database migrations..."
docker-compose exec web python manage.py migrate

echo "👤 Creating superuser (optional)..."
echo "Do you want to create a superuser? (y/n)"
read -r response
if [[ "$response" =~ ^([yY][eE][sS]|[yY])$ ]]; then
    docker-compose exec web python manage.py createsuperuser
fi

echo "✅ Deployment completed!"
echo "🌐 Your app is available at: http://localhost:8000"
echo "🗄️  Database is available at: localhost:5432"
echo ""
echo "📋 Useful commands:"
echo "  View logs: docker-compose logs -f"
echo "  Stop services: docker-compose down"
echo "  Restart: docker-compose restart"
echo "  Shell access: docker-compose exec web bash"
