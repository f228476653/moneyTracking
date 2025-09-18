#!/usr/bin/env python3
"""
Setup script for Bank Statement Parser
"""

import os
import sys
import subprocess
import shutil
from pathlib import Path

def run_command(command, description):
    """Run a shell command and handle errors"""
    print(f"🔄 {description}...")
    try:
        result = subprocess.run(command, shell=True, check=True, capture_output=True, text=True)
        print(f"✅ {description} completed successfully")
        return True
    except subprocess.CalledProcessError as e:
        print(f"❌ {description} failed: {e}")
        print(f"Error output: {e.stderr}")
        return False

def check_python_version():
    """Check if Python version is compatible"""
    if sys.version_info < (3, 11):
        print("❌ Python 3.11 or higher is required")
        print(f"Current version: {sys.version}")
        return False
    print(f"✅ Python version {sys.version_info.major}.{sys.version_info.minor} is compatible")
    return True

def check_dependencies():
    """Check if required system dependencies are installed"""
    print("🔍 Checking system dependencies...")
    
    # Check PostgreSQL
    if shutil.which('psql'):
        print("✅ PostgreSQL client is installed")
    else:
        print("⚠️  PostgreSQL client not found. You may need to install it.")
    
    # Check Docker
    if shutil.which('docker'):
        print("✅ Docker is installed")
    else:
        print("⚠️  Docker not found. You may need to install it for containerized deployment.")
    
    # Check Docker Compose
    if shutil.which('docker-compose'):
        print("✅ Docker Compose is installed")
    else:
        print("⚠️  Docker Compose not found. You may need to install it for containerized deployment.")

def create_directories():
    """Create necessary directories"""
    print("📁 Creating necessary directories...")
    
    directories = [
        'media',
        'media/statements',
        'static',
        'logs',
        'staticfiles'
    ]
    
    for directory in directories:
        Path(directory).mkdir(parents=True, exist_ok=True)
        print(f"✅ Created directory: {directory}")

def setup_environment():
    """Set up environment file"""
    print("🔧 Setting up environment configuration...")
    
    env_file = Path('.env')
    env_example = Path('env.example')
    
    if env_file.exists():
        print("✅ .env file already exists")
        return True
    
    if env_example.exists():
        shutil.copy(env_example, env_file)
        print("✅ Created .env file from env.example")
        print("⚠️  Please edit .env file with your database credentials")
        return True
    else:
        print("❌ env.example file not found")
        return False

def install_python_dependencies():
    """Install Python dependencies"""
    print("📦 Installing Python dependencies...")
    
    if not Path('requirements.txt').exists():
        print("❌ requirements.txt not found")
        return False
    
    return run_command('pip install -r requirements.txt', 'Installing Python dependencies')

def setup_database():
    """Set up database"""
    print("🗄️  Setting up database...")
    
    # Check if PostgreSQL is running
    if not run_command('pg_isready', 'Checking PostgreSQL connection'):
        print("⚠️  PostgreSQL is not running or not accessible")
        print("   Please start PostgreSQL and ensure it's accessible")
        return False
    
    # Create database
    if not run_command('createdb bank_parser', 'Creating database'):
        print("⚠️  Could not create database. It may already exist or you don't have permissions.")
    
    return True

def run_migrations():
    """Run Django migrations"""
    print("🔄 Running database migrations...")
    
    if not run_command('python manage.py makemigrations', 'Creating migrations'):
        return False
    
    if not run_command('python manage.py migrate', 'Applying migrations'):
        return False
    
    return True

def create_superuser():
    """Create Django superuser"""
    print("👤 Creating superuser...")
    
    # Check if superuser already exists
    try:
        result = subprocess.run(
            'python manage.py shell -c "from django.contrib.auth.models import User; print(User.objects.filter(is_superuser=True).count())"',
            shell=True, capture_output=True, text=True
        )
        if result.stdout.strip() == '0':
            print("⚠️  No superuser found. You can create one with:")
            print("   python manage.py createsuperuser")
        else:
            print("✅ Superuser already exists")
    except:
        print("⚠️  Could not check for existing superuser")

def collect_static():
    """Collect static files"""
    print("📁 Collecting static files...")
    
    return run_command('python manage.py collectstatic --noinput', 'Collecting static files')

def main():
    """Main setup function"""
    print("🚀 Bank Statement Parser Setup")
    print("=" * 40)
    
    # Check Python version
    if not check_python_version():
        sys.exit(1)
    
    # Check system dependencies
    check_dependencies()
    
    # Create directories
    create_directories()
    
    # Setup environment
    if not setup_environment():
        print("❌ Environment setup failed")
        sys.exit(1)
    
    # Install Python dependencies
    if not install_python_dependencies():
        print("❌ Python dependencies installation failed")
        sys.exit(1)
    
    # Setup database
    if not setup_database():
        print("⚠️  Database setup incomplete. Please check PostgreSQL configuration.")
    
    # Run migrations
    if not run_migrations():
        print("❌ Database migrations failed")
        sys.exit(1)
    
    # Create superuser
    create_superuser()
    
    # Collect static files
    if not collect_static():
        print("⚠️  Static file collection failed")
    
    print("\n🎉 Setup completed successfully!")
    print("\nNext steps:")
    print("1. Edit .env file with your database credentials")
    print("2. Create a superuser: python manage.py createsuperuser")
    print("3. Run the development server: python manage.py runserver")
    print("4. Visit http://localhost:8000 to access the application")
    print("\nFor Docker deployment:")
    print("1. cd deployment")
    print("2. docker-compose up --build")

if __name__ == '__main__':
    main()
