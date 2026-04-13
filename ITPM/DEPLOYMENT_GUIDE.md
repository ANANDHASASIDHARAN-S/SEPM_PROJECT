# Deployment Guide - Resource Allocation & Workforce Planning System

## Table of Contents
1. [Local Development](#local-development)
2. [Production Deployment (Windows)](#production-deployment-windows)
3. [Cloud Deployment](#cloud-deployment)
4. [Docker Deployment](#docker-deployment)
5. [Database Backup & Migration](#database-backup--migration)

---

## Local Development

### Running Locally (Current Setup)
```bash
# Navigate to project folder
cd c:\Users\91988\OneDrive\Desktop\ITPM

# Initialize database (if needed)
python run.py init-db

# Start development server
python run.py

# Access at http://localhost:5000
```

**Demo Credentials:**
- Admin: `admin` / `Admin@123`
- HR Manager: `hr_manager` / `HR@123`
- Project Manager: `pm_john` / `PM@123`
- Executive: `exec` / `Exec@123`
- Employee: `alice` / `Employee@123`

---

## Production Deployment (Windows)

### Option 1: Windows Server with IIS

#### Prerequisites
1. Windows Server 2019+
2. Python 3.9+
3. IIS with CGI/FastCGI enabled

#### Steps

**1. Install Python on Server**
```bash
# Download from python.org and install
# Add Python to PATH during installation
# Verify: python --version
```

**2. Transfer Application**
```bash
# Copy entire ITPM folder to server
# Example: C:\apps\ITPM
```

**3. Install Dependencies**
```bash
cd C:\apps\ITPM
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
```

**4. Create requirements.txt** (if not exists)
```bash
# Generate from current environment
pip freeze > requirements.txt

# Or use our base requirements:
Flask==2.3.3
Flask-SQLAlchemy==3.0.5
Flask-Login==0.6.2
Flask-WTF==1.1.1
WTForms==3.0.1
python-dateutil==2.8.2
```

**5. Configure IIS**
- Open IIS Manager
- Create New Site: "ITPM" → Physical path: `C:\apps\ITPM`
- Bind to port (e.g., 8080 or 80)
- Create FastCGI application pointing to Python
- Add web.config (see below)

**6. Create web.config**
```xml
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
  <system.webServer>
    <handlers>
      <add name="FastCGI" path="*" verb="*" modules="FastCgiModule" scriptProcessor="C:\apps\ITPM\venv\Scripts\python.exe|C:\apps\ITPM\app.wsgi" resourceType="Unspecified" requireAccess="Script" />
    </handlers>
  </system.webServer>
</configuration>
```

---

### Option 2: Gunicorn + Nginx (Recommended)

#### Prerequisites
- Windows Server or any Windows machine
- Python 3.9+
- Nginx

#### Steps

**1. Install Gunicorn**
```bash
pip install gunicorn
pip install -r requirements.txt
```

**2. Create Gunicorn Config** (`gunicorn_config.py`)
```python
import multiprocessing

# Server socket
bind = "127.0.0.1:8000"
backlog = 2048

# Worker processes
workers = multiprocessing.cpu_count() * 2 + 1
worker_class = "sync"
worker_connections = 1000
timeout = 30
keepalive = 2

# Logging
accesslog = "-"
errorlog = "-"
loglevel = "info"

# Server hooks
max_requests = 1000
max_requests_jitter = 50
```

**3. Create Startup Script** (`start_gunicorn.bat`)
```batch
@echo off
cd C:\apps\ITPM
venv\Scripts\activate
gunicorn -c gunicorn_config.py "app:create_app()"
pause
```

**4. Create Windows Service** (using NSSM)
```bash
# Download NSSM: https://nssm.cc/download
# Place in C:\tools\nssm

# Install service
C:\tools\nssm install ITpmService "C:\apps\ITPM\start_gunicorn.bat"
C:\tools\nssm start ITpmService
```

**5. Install and Configure Nginx**
- Download from https://nginx.org
- Extract to `C:\nginx`

**6. Create nginx.conf**
```nginx
upstream gunicorn {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name yourdomain.com;
    client_max_body_size 10M;

    location / {
        proxy_pass http://gunicorn;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }

    location /static {
        alias C:\apps\ITPM\app\static;
        expires 30d;
    }
}
```

**7. Start Nginx**
```bash
cd C:\nginx
nginx.exe

# Stop: nginx.exe -s stop
# Reload config: nginx.exe -s reload
```

---

## Cloud Deployment

### Option 1: Heroku (Easiest)

**1. Create Heroku Account**
- Sign up at https://www.heroku.com

**2. Install Heroku CLI**
```bash
# Download from https://devcenter.heroku.com/articles/heroku-cli
heroku --version
```

**3. Create Procfile** (`Procfile`)
```
web: gunicorn "app:create_app()"
```

**4. Create runtime.txt** (`runtime.txt`)
```
python-3.10.0
```

**5. Deploy**
```bash
cd C:\Users\91988\OneDrive\Desktop\ITPM
heroku login
heroku create itpm-app
git push heroku main

# Initialize database
heroku run python run.py init-db

# View logs
heroku logs --tail
```

**Access:** https://itpm-app.herokuapp.com

---

### Option 2: AWS EC2

**1. Launch EC2 Instance**
- Choose: Ubuntu 20.04 or Windows Server 2019
- Instance type: t3.micro (free tier eligible)
- Open ports: 80, 443, 22

**2. Connect via SSH/RDP**
```bash
# For Linux:
ssh -i "your-key.pem" ubuntu@your-instance-ip

# For Windows:
# Use RDP client
```

**3. Install Dependencies** (Ubuntu example)
```bash
sudo apt update
sudo apt install python3-pip python3-venv
sudo apt install nginx

cd /home/ubuntu
git clone <your-repo>
cd ITPM
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
pip install gunicorn
```

**4. Configure Nginx**
```bash
sudo nano /etc/nginx/sites-available/default
# (paste nginx config from above)
sudo systemctl restart nginx
```

**5. Run Gunicorn**
```bash
gunicorn -w 4 -b 127.0.0.1:8000 "app:create_app()"
```

**6. Set up Systemd Service** (`/etc/systemd/system/itpm.service`)
```ini
[Unit]
Description=ITPM Application
After=network.target

[Service]
Type=notify
User=ubuntu
WorkingDirectory=/home/ubuntu/ITPM
Environment="PATH=/home/ubuntu/ITPM/venv/bin"
ExecStart=/home/ubuntu/ITPM/venv/bin/gunicorn -w 4 -b 127.0.0.1:8000 "app:create_app()"
Restart=always

[Install]
WantedBy=multi-user.target
```

**7. Enable Service**
```bash
sudo systemctl enable itpm
sudo systemctl start itpm
```

---

### Option 3: Azure App Service

**1. Create App Service Plan**
```bash
az login
az appservice plan create --name itpm-plan --resource-group mygroup --sku B1 --is-linux
```

**2. Create Web App**
```bash
az webapp create --resource-group mygroup --plan itpm-plan --name itpm-app --runtime "python|3.10"
```

**3. Deploy**
```bash
# Initialize local git
git init
git add .
git commit -m "Initial commit"

# Get deployment credentials
az webapp deployment user set --user-name <username>

# Add remote
git remote add azure https://<username>@itpm-app.scm.azurewebsites.net/itpm-app.git

# Deploy
git push azure master
```

**4. Initialize Database**
```bash
az webapp ssh --resource-group mygroup --name itpm-app

# In SSH terminal:
python run.py init-db
```

**Access:** https://itpm-app.azurewebsites.net

---

## Docker Deployment

### Create Docker Setup

**1. Create Dockerfile**
```dockerfile
FROM python:3.10-slim

WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy application
COPY . .

# Set environment
ENV FLASK_APP=app
ENV FLASK_ENV=production

# Expose port
EXPOSE 5000

# Health check
HEALTHCHECK --interval=30s --timeout=10s --start-period=40s --retries=3 \
    CMD python -c "import urllib.request; urllib.request.urlopen('http://localhost:5000/').read()"

# Run application
CMD ["gunicorn", "-b", "0.0.0.0:5000", "-w", "4", "app:create_app()"]
```

**2. Create docker-compose.yml**
```yaml
version: '3.8'

services:
  web:
    build: .
    ports:
      - "5000:5000"
    environment:
      - FLASK_ENV=production
      - SECRET_KEY=your-secret-key-here
    volumes:
      - ./app:/app/app
      - ./resource_allocation.db:/app/resource_allocation.db
    restart: unless-stopped

  nginx:
    image: nginx:latest
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf:ro
    depends_on:
      - web
    restart: unless-stopped
```

**3. Build and Run**
```bash
docker-compose up -d

# View logs
docker-compose logs -f web

# Stop
docker-compose down
```

**4. Deploy to Docker Hub**
```bash
# Login
docker login

# Build image
docker build -t yourusername/itpm:1.0 .

# Push
docker push yourusername/itpm:1.0

# Others can run:
docker run -p 5000:5000 yourusername/itpm:1.0
```

---

## Database Backup & Migration

### Backup Database

**1. Backup SQLite Database**
```bash
# Simple copy
copy resource_allocation.db resource_allocation_backup_$(date +%Y%m%d).db

# Or use Python
python -c "import shutil; shutil.copy('resource_allocation.db', f'backup/db_{__import__(\"datetime\").datetime.now().strftime(\"%Y%m%d_%H%M%S\")}.db')"
```

**2. Export to SQL**
```bash
# Install sqlite3 command line tools
sqlite3 resource_allocation.db ".dump" > database_dump.sql
```

**3. Restore from Backup**
```bash
copy resource_allocation_backup.db resource_allocation.db
```

### Production Database Configuration

**1. Environment Variables** (`.env` file)
```
FLASK_ENV=production
SECRET_KEY=your-super-secret-key-12345
DATABASE_URL=sqlite:///resource_allocation.db
DEBUG=False
```

**2. Update app/__init__.py**
```python
import os
from dotenv import load_dotenv

load_dotenv()

app.config['SECRET_KEY'] = os.getenv('SECRET_KEY', 'dev-key')
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URL', 'sqlite:///resource_allocation.db')
app.config['DEBUG'] = os.getenv('DEBUG', False)
```

**3. Install python-dotenv**
```bash
pip install python-dotenv
```

---

## Security Checklist for Production

- [ ] Set `DEBUG=False` in production
- [ ] Use strong `SECRET_KEY` (min 32 characters)
- [ ] Enable HTTPS (SSL certificate)
- [ ] Set up database backups (daily)
- [ ] Configure firewall rules
- [ ] Use environment variables for secrets
- [ ] Enable audit logging (already implemented)
- [ ] Set up monitoring and alerts
- [ ] Configure rate limiting
- [ ] Update all dependencies regularly

---

## Performance Optimization

### 1. Database Indexing
```python
# Add to models.py if not present
class ResourceAllocation(db.Model):
    __table_args__ = (
        db.Index('idx_employee_project', 'employee_id', 'project_id'),
    )
```

### 2. Caching
```bash
pip install flask-caching redis
```

### 3. Load Balancing
- Use Nginx/HAProxy for load balancing
- Configure multiple Gunicorn workers
- Use sticky sessions for user sessions

### 4. CDN for Static Files
- Configure CloudFront/CloudFlare for static assets
- Enable gzip compression

---

## Quick Start - Production Deployment

### Fastest Way (Gunicorn + Nginx on Windows Server):

```bash
# 1. Install Python & dependencies
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
pip install gunicorn

# 2. Initialize database
python run.py init-db

# 3. Run Gunicorn
gunicorn -w 4 -b 0.0.0.0:8000 "app:create_app()"

# 4. Configure Nginx to proxy to :8000

# 5. Access via http://your-server-ip
```

---

## Troubleshooting

### Application won't start
```bash
# Check logs
python run.py  # Run in foreground to see errors

# Verify Python path
python --version

# Test imports
python -c "from app import create_app; print('OK')"
```

### Database errors
```bash
# Reinitialize database
python run.py init-db

# Check database file permissions
ls -la resource_allocation.db
```

### Port already in use
```bash
# Find process using port 5000
netstat -ano | findstr :5000
taskkill /PID <PID> /F
```

### 404 on static files
- Ensure static folder exists: `app/static/`
- Check Nginx/web server can access files
- Verify file permissions

---

## Support & Documentation

- Flask Documentation: https://flask.palletsprojects.com
- SQLAlchemy: https://docs.sqlalchemy.org
- Gunicorn: https://docs.gunicorn.org
- Nginx: https://nginx.org/en/docs
- Docker: https://docs.docker.com

