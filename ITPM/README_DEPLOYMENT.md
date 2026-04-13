# Resource Allocation & Workforce Planning System - Deployment Guide

## 📋 Overview

Your **ITPM (IT Project Management)** application is ready for deployment! This guide covers multiple deployment options from simple to advanced.

```
Local Dev → Testing → Production
(localhost:5000) → (Your Server)
```

---

## 🚀 Quick Start (3 Steps)

### Step 1: Prepare Your Server
```bash
# On your Windows/Linux server
python -m venv venv
source venv/bin/activate  # Linux/Mac
# OR
.\venv\Scripts\activate   # Windows

pip install -r requirements.txt
```

### Step 2: Copy Application
```bash
# Copy entire ITPM folder to your server
# Example: C:\apps\ITPM  (Windows)
#          /home/ubuntu/itpm  (Linux)
```

### Step 3: Start Application
```bash
# Windows
start_production.bat

# Linux/Mac
bash start_production.sh

# Or with Docker
docker compose up -d
```

**Your app is now at:** `http://your-server-ip:5000` or `http://your-server-ip:8000`

---

## 📦 Deployment Methods (Ranked by Ease)

### Level 1️⃣: **Heroku** (Easiest - Cloud)
- ✅ No server management
- ✅ Free tier: 550 hours/month
- ✅ Automatic SSL
- ✅ URL: `https://yourapp.herokuapp.com`
- ⏱️ Setup time: 15 minutes

**Steps:**
```bash
heroku login
heroku create itpm-app
git push heroku main
heroku run python run.py init-db
heroku open
```

👉 **Best if:** You want "set and forget" hosting

---

### Level 2️⃣: **Docker** (Easy-Medium - Portable)
- ✅ Same setup on any machine
- ✅ Easy to scale
- ✅ Cloud-ready (AWS, Azure, Google Cloud)
- ⏱️ Setup time: 20 minutes

**Steps:**
```bash
docker build -t itpm:latest .
docker run -p 5000:5000 itpm:latest
```

👉 **Best if:** You want portability and might move hosting

---

### Level 3️⃣: **Windows Server + Gunicorn** (Easy - Windows)
- ✅ Direct control
- ✅ No containerization overhead
- ✅ Good performance
- ⏱️ Setup time: 30 minutes

**Steps:**
```batch
pip install gunicorn
python run.py init-db
start_production.bat
```

👉 **Best if:** You're using Windows Server

---

### Level 4️⃣: **AWS EC2** (Medium - Scalable)
- ✅ Full control
- ✅ Auto-scaling available
- ✅ Free tier: 1 year
- ✅ Cost: ~$5-15/month
- ⏱️ Setup time: 45 minutes

**Steps:**
1. Launch Ubuntu EC2 instance
2. SSH in and run:
```bash
git clone <your-repo>
cd itpm
bash start_production.sh
```

👉 **Best if:** You need scalability and cost flexibility

---

### Level 5️⃣: **IIS + Python** (Medium-Hard - Enterprise)
- ✅ Integrates with Windows infrastructure
- ✅ Domain authentication support
- ✓ Suitable for enterprise environments
- ⏱️ Setup time: 60+ minutes

👉 **Best if:** You're in an enterprise Windows environment

---

## 📊 Comparison Table

| Method | Cost | Setup Time | Performance | Scalability | Complexity |
|--------|------|-----------|-------------|------------|-----------|
| **Heroku** | $7/month | 15 min | Good | ⭐⭐⭐ | Easy |
| **Docker** | $5-20/month | 20 min | Excellent | ⭐⭐⭐⭐ | Medium |
| **Windows+Gunicorn** | Server cost | 30 min | Good | ⭐⭐ | Easy |
| **AWS EC2** | $5-15/month | 45 min | Excellent | ⭐⭐⭐⭐ | Medium |
| **Azure App Service** | $10-50/month | 30 min | Excellent | ⭐⭐⭐⭐ | Medium |
| **IIS** | Server cost | 60+ min | Good | ⭐⭐ | Hard |

---

## 🔧 Configuration Files Provided

| File | Purpose | Usage |
|------|---------|-------|
| `requirements.txt` | Python dependencies | `pip install -r` |
| `.env.example` | Environment variables | Copy to `.env` and edit |
| `start_production.bat` | Windows startup script | `.\start_production.bat` |
| `start_production.sh` | Linux/Mac startup script | `bash start_production.sh` |
| `Dockerfile` | Container image | `docker build -t itpm .` |
| `docker-compose.yml` | Docker with Nginx | `docker compose up` |
| `nginx.conf.example` | Nginx web server config | Copy to `/etc/nginx/` |
| `health_check.py` | System verification | `python health_check.py` |

---

## 📋 Pre-Deployment Checklist

- [ ] Test application locally
- [ ] Run health check: `python health_check.py`
- [ ] Database initialized: `python run.py init-db`
- [ ] All dependencies installed: `pip install -r requirements.txt`
- [ ] Copy `.env.example` to `.env`
- [ ] Update SECRET_KEY in `.env`
- [ ] Set DEBUG=False in production
- [ ] Backup database: `copy resource_allocation.db backup.db`
- [ ] Test all user roles
- [ ] Verify static files load
- [ ] Choose hosting provider ✅

---

## 🔒 Security Reminders

1. **Never commit `.env` to git**
   ```bash
   echo ".env" >> .gitignore
   ```

2. **Generate strong SECRET_KEY**
   ```bash
   python -c "import secrets; print(secrets.token_hex(32))"
   ```

3. **Always use HTTPS in production**
   - Heroku: Automatic
   - AWS: Use ACM certificate
   - Self-hosted: Use Let's Encrypt

4. **Backup your database regularly**
   ```bash
   # Daily backup
   copy resource_allocation.db "backups/db_$(date +%Y%m%d).db"
   ```

5. **Keep dependencies updated**
   ```bash
   pip install --upgrade -r requirements.txt
   ```

---

## 🐛 Troubleshooting

### Application won't start
```bash
# Check for errors
python run.py

# Check Python is installed
python --version

# Verify imports work
python -c "import flask; print('Flask OK')"
```

### Port already in use
```bash
# Windows
netstat -ano | findstr :5000
taskkill /PID <number> /F

# Linux/Mac
lsof -i :5000
kill -9 <PID>
```

### Database errors
```bash
# Reinitialize database
rm resource_allocation.db
python run.py init-db
```

### Static files 404
- Verify `app/static/` folder exists
- Check web server can access files
- Verify Nginx config points correctly

---

## 📞 Support Files

For detailed instructions, see:
- **DEPLOYMENT_GUIDE.md** - Comprehensive guide with all options
- **QUICK_DEPLOY.md** - Quick reference and checklists
- **health_check.py** - Automated system verification

---

## 🎯 Recommended Path by Scenario

### Scenario A: "I just want to get it online quickly"
→ Use **Heroku** (15 minutes)

### Scenario B: "I have a Windows server at work"
→ Use **Windows + Gunicorn** (30 minutes)

### Scenario C: "I want a professional setup"
→ Use **Docker + AWS** (90 minutes total)

### Scenario D: "I want maximum control"
→ Use **EC2 + Nginx** (45 minutes)

### Scenario E: "I'm in an enterprise"
→ Use **IIS** (60+ minutes) or **Azure App Service** (30 minutes)

---

## 📊 Post-Deployment

### 1. Verify It Works
```bash
python health_check.py
```

### 2. Set Up Monitoring
```bash
# Check logs
tail -f app.log

# Monitor CPU/Memory
# (Use your provider's tools)
```

### 3. Configure Backups
```bash
# Daily database backup (add to cron/Task Scheduler)
python -c "import shutil; shutil.copy('resource_allocation.db', f'backups/db_{__import__(\"datetime\").datetime.now():%Y%m%d_%H%M%S}.db')"
```

### 4. Set Up SSL/HTTPS
- **Heroku**: Automatic
- **AWS**: Use AWS Certificate Manager
- **Self-hosted**: Use Let's Encrypt (certbot)

---

## 🚢 Deployment Architecture

```
┌─────────────────┐
│  Client/Browser │
└────────┬────────┘
         │ HTTPS
         ▼
┌─────────────────┐
│   Nginx/Proxy   │ (80, 443)
└────────┬────────┘
         │ HTTP
         ▼
┌─────────────────┐
│ Gunicorn Workers│ (5000, 8000)
│  (4 processes)  │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  Flask App      │
│  Resource       │
│  Allocation &   │
│  Workforce      │
│  Planning       │
└────────┬────────┘
         │
         ▼
┌─────────────────┐
│  SQLite DB      │ (or PostgreSQL)
│  resource_      │
│  allocation.db  │
└─────────────────┘
```

---

## 📚 Learning Resources

- [Flask Deployment Documentation](https://flask.palletsprojects.com/deployment/)
- [Gunicorn Documentation](https://docs.gunicorn.org/)
- [Nginx Reverse Proxy Guide](https://nginx.org/en/docs/http/ngx_http_proxy_module.html)
- [Docker Getting Started](https://docs.docker.com/get-started/)
- [Heroku Python Support](https://devcenter.heroku.com/articles/python-support)

---

## ✅ Final Checklist

Before going live:

- [ ] Database backed up
- [ ] `.env` configured with real values
- [ ] DEBUG mode is False
- [ ] SECRET_KEY is random and secure
- [ ] Static files configured
- [ ] CORS properly configured
- [ ] SSL certificate installed (production)
- [ ] Monitoring set up
- [ ] Backup strategy in place
- [ ] Admin credentials changed from defaults

---

**🎉 You're ready to deploy! Choose your method above and follow the steps.**

For questions or issues, refer to DEPLOYMENT_GUIDE.md or QUICK_DEPLOY.md

