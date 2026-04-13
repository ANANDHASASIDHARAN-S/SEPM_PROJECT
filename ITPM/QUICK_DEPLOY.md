# Quick Deployment Checklist

## Pre-Deployment ✓

- [ ] Test application locally: `python run.py`
- [ ] Initialize database: `python run.py init-db`
- [ ] Verify all features work
- [ ] Test with different user roles
- [ ] Create backup of database
- [ ] Update `.env` with production values
- [ ] Generate new SECRET_KEY (32+ characters, random)

---

## Deployment Options (Choose One)

### Option A: Windows Server + Gunicorn (Easiest for Windows)
**Time: 30 mins | Difficulty: Easy | Performance: Good**

```batch
REM 1. Copy folder to server (e.g., C:\apps\ITPM)
REM 2. Run in PowerShell:
python -m venv venv
.\venv\Scripts\activate
pip install -r requirements.txt
pip install gunicorn

REM 3. Start application:
start_production.bat

REM 4. In browser: http://localhost:8000 or http://server-ip:8000
```

✓ Best if: You're on Windows Server  
✓ No configuration needed  
✓ Can install as Windows Service with NSSM  

---

### Option B: Heroku (Cloud - Easiest)
**Time: 15 mins | Difficulty: Very Easy | Cost: Free tier available**

```bash
# 1. heroku login
# 2. heroku create itpm-app
# 3. git push heroku main
# 4. heroku run python run.py init-db
# 5. heroku open
```

✓ No server management  
✓ Auto-scaling  
✓ Free tier includes 550 hours/month  
✓ URL: https://itpm-app.herokuapp.com  

---

### Option C: Docker (Most Professional)
**Time: 20 mins | Difficulty: Medium | Performance: Excellent**

```bash
# 1. docker build -t itpm:latest .
# 2. docker run -p 5000:5000 itpm:latest
# 3. Access: http://localhost:5000
```

✓ Same everywhere (dev to prod)  
✓ Easy to scale  
✓ Can deploy on Docker Hub  

---

### Option D: AWS EC2 (Scalable)
**Time: 45 mins | Difficulty: Medium | Cost: Low ($5-10/month)**

```bash
# 1. Launch Ubuntu EC2 instance
# 2. SSH into instance
# 3. Clone repository
# 4. Run: start_production.sh
# 5. Configure Nginx
# 6. Setup SSL (optional)
```

✓ Full control  
✓ Pay per use  
✓ Auto-scaling capabilities  

---

## Post-Deployment ✓

- [ ] Test all features in production
- [ ] Verify SSL certificate (if using HTTPS)
- [ ] Set up automated backups
- [ ] Configure monitoring
- [ ] Set up alerts for errors
- [ ] Test user roles and permissions
- [ ] Verify email notifications (if configured)
- [ ] Document admin password and access

---

## File Structure

```
ITPM/
├── app/                          # Application code
│   ├── static/                   # CSS, JS, images
│   ├── templates/                # HTML files
│   ├── routes/                   # Flask blueprints
│   ├── models.py                 # Database models
│   └── forms.py                  # WTForms
├── resource_allocation.db        # SQLite database
├── run.py                        # Entry point
├── requirements.txt              # Python dependencies
├── start_production.bat          # Windows startup
├── start_production.sh           # Linux/Mac startup
├── Dockerfile                    # Docker image
├── docker-compose.yml            # Docker Compose config
├── nginx.conf.example            # Nginx config template
├── .env.example                  # Environment template
├── DEPLOYMENT_GUIDE.md           # Full guide
└── README.md                     # Project info
```

---

## Common Issues & Fixes

**Error: "ModuleNotFoundError: No module named 'flask'"**
```bash
# Solution: Install dependencies
pip install -r requirements.txt
```

**Error: "Port 5000 already in use"**
```bash
# Windows:
netstat -ano | findstr :5000
taskkill /PID <PID> /F

# Linux/Mac:
lsof -i :5000
kill -9 <PID>
```

**Error: "Database is locked"**
```bash
# Solution: Delete and reinitalize
rm resource_allocation.db
python run.py init-db
```

**Error: "Static files not loading (404)"**
- Verify `app/static/` folder exists
- Check file permissions
- Ensure web server can access files

**Error: "Secret key not set"**
```bash
# Create random secret key
python -c "import secrets; print(secrets.token_hex(16))"

# Add to .env:
SECRET_KEY=<YOUR_KEY_HERE>
```

---

## Performance Tips

1. **Enable Caching**
   ```bash
   pip install flask-caching redis
   ```

2. **Use Multiple Workers**
   ```bash
   gunicorn -w 4 -b 0.0.0.0:8000 ...
   ```

3. **Enable Gzip Compression**
   - Nginx: `gzip on;` in nginx.conf

4. **Use CDN for Static Files**
   - CloudFront, CloudFlare, or similar

5. **Database Optimization**
   - Regular backups
   - Index frequently queried columns
   - Archive old data

---

## Security Checklist

- [ ] DEBUG = False
- [ ] SECRET_KEY is random (32+ chars)
- [ ] HTTPS enabled
- [ ] Regular database backups
- [ ] Update dependencies monthly
- [ ] Use strong passwords
- [ ] Enable audit logging (already included)
- [ ] Firewall configured to allow only needed ports
- [ ] CORS configured properly
- [ ] SQL injection prevented (SQLAlchemy ORM used)

---

## Monitoring & Alerts

### Application Health Check
```bash
# Every 5 minutes, ping the app
curl -f http://your-app.com/ || alert "App is down!"
```

### Log Monitoring
```bash
# Stream logs in real-time
tail -f /var/log/itpm.log | grep ERROR
```

### Database Backup
```bash
# Daily backup script
@echo off
for /f "tokens=2-4 delims=/ " %%a in ('date /t') do (set mydate=%%c%%a%%b)
copy resource_allocation.db backup\db_%mydate%.db
```

---

## Database Migration (SQLite → Production DB)

If you need to switch from SQLite to PostgreSQL:

```bash
# 1. Export SQLite
sqlite3 resource_allocation.db ".dump" > dump.sql

# 2. Install PostgreSQL and create DB
# 3. Update DATABASE_URL in .env:
DATABASE_URL=postgresql://user:password@host:5432/itpm

# 4. Install PostgreSQL driver
pip install psycopg2-binary

# 5. Recreate tables and import data
```

---

## Support

- **Issues?** Check DEPLOYMENT_GUIDE.md for detailed instructions
- **Questions?** Review the full documentation
- **Need help?** Check application logs for error messages

