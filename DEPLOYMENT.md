# Linux Server Deployment Guide

## Overview
This guide covers deploying the Anesthesiology Pre-Consultation Chatbot System to a Linux production server using MySQL database.

## Server Requirements

### Minimum Hardware
- **CPU**: 2 cores
- **RAM**: 2GB minimum, 4GB recommended
- **Storage**: 20GB minimum, 50GB recommended
- **Network**: Static IP with domain name

### Software Requirements
- **OS**: Ubuntu 20.04+ or CentOS 7+
- **Python**: 3.8+
- **Database**: MySQL 8.0+
- **Web Server**: Nginx
- **Process Manager**: Supervisor
- **SSL**: Let's Encrypt or commercial certificate

## Pre-Deployment Setup

### 1. Update System
```bash
sudo apt update && sudo apt upgrade -y
```

### 2. Install System Dependencies
```bash
sudo apt install -y python3 python3-pip python3-venv nginx mysql-server git supervisor ufw certbot python3-certbot-nginx
```

### 3. Configure Firewall
```bash
sudo ufw allow OpenSSH
sudo ufw allow 'Nginx Full'
sudo ufw enable
```

## Database Setup

### 1. Secure MySQL Installation
```bash
sudo mysql_secure_installation
```

### 2. Create Database and User
```bash
sudo mysql -u root -p
```

```sql
CREATE DATABASE patients CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'anespr1'@'localhost' IDENTIFIED BY 'your_secure_password_here';
GRANT ALL PRIVILEGES ON patients.* TO 'anespr1'@'localhost';
FLUSH PRIVILEGES;
EXIT;
```

### 3. Test Database Connection
```bash
mysql -u anespr1 -p patients
```

## Application Deployment

### 1. Clone Repository
```bash
cd /opt
sudo git clone https://github.com/yourusername/anespr1.git
sudo chown -R www-data:www-data /opt/anespr1
```

### 2. Setup Python Environment
```bash
cd /opt/anespr1
sudo -u www-data python3 -m venv venv
sudo -u www-data ./venv/bin/pip install --upgrade pip
sudo -u www-data ./venv/bin/pip install -r requirements.txt
sudo -u www-data ./venv/bin/pip install gunicorn pymysql
```

### 3. Configure Environment Variables
```bash
sudo -u www-data nano /opt/anespr1/.env
```

```env
# Database Configuration
DATABASE_URL=mysql+pymysql://anespr1:your_secure_password_here@localhost/patients

# AI API Keys
GOOGLE_API_KEY=your_gemini_api_key
AZURE_OPENAI_API_KEY=your_azure_openai_api_key
AZURE_OPENAI_ENDPOINT=https://your-resource-name.openai.azure.com/
AZURE_OPENAI_API_VERSION=2024-12-01-preview
AZURE_OPENAI_DEPLOYMENT_NAME=your-deployment-name

# Model Configuration
USE_LOCAL_MODEL=false
OLLAMA_URL=http://localhost:11434
OLLAMA_MODEL=gemma3:latest

# Application Configuration
FLASK_ENV=production
SECRET_KEY=your_very_secure_secret_key_here
PORT=8000
```

### 4. Initialize Database
```bash
cd /opt/anespr1
sudo -u www-data ./venv/bin/python init_db.py
sudo -u www-data ./venv/bin/python create_admin.py
```

### 5. Test Application
```bash
sudo -u www-data ./venv/bin/python app_tocloud.py
```

## Production Configuration

### 1. Create Gunicorn Configuration
```bash
sudo nano /opt/anespr1/gunicorn.conf.py
```

```python
bind = "127.0.0.1:8000"
workers = 4
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
preload_app = True
keepalive = 5
timeout = 120
```

### 2. Create Supervisor Configuration
```bash
sudo nano /etc/supervisor/conf.d/anespr1.conf
```

```ini
[program:anespr1]
command=/opt/anespr1/venv/bin/gunicorn --config /opt/anespr1/gunicorn.conf.py app_tocloud:app
directory=/opt/anespr1
user=www-data
group=www-data
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/anespr1.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=5
environment=PATH="/opt/anespr1/venv/bin"
```

### 3. Start Supervisor Service
```bash
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start anespr1
sudo supervisorctl status
```

### 4. Configure Nginx
```bash
sudo nano /etc/nginx/sites-available/anespr1
```

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;
    
    # SSL Configuration (will be updated by certbot)
    ssl_certificate /etc/letsencrypt/live/your-domain.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/your-domain.com/privkey.pem;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Gzip compression
    gzip on;
    gzip_comp_level 6;
    gzip_types text/plain text/css application/json application/javascript text/xml application/xml application/xml+rss text/javascript;
    
    # Static files
    location /static/ {
        alias /opt/anespr1/static/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Main application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }
    
    # File upload size limit
    client_max_body_size 10M;
}
```

### 5. Enable Nginx Site
```bash
sudo ln -s /etc/nginx/sites-available/anespr1 /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 6. Setup SSL Certificate
```bash
sudo certbot --nginx -d your-domain.com -d www.your-domain.com
```

## Security Hardening

### 1. Configure Fail2Ban
```bash
sudo apt install fail2ban
sudo nano /etc/fail2ban/jail.local
```

```ini
[DEFAULT]
bantime = 3600
findtime = 600
maxretry = 3

[sshd]
enabled = true

[nginx-http-auth]
enabled = true

[nginx-limit-req]
enabled = true
```

### 2. Setup Log Rotation
```bash
sudo nano /etc/logrotate.d/anespr1
```

```
/var/log/anespr1.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 www-data www-data
    postrotate
        supervisorctl restart anespr1
    endscript
}
```

### 3. Database Backup Script
```bash
sudo nano /opt/backup-db.sh
```

```bash
#!/bin/bash
BACKUP_DIR="/opt/backups"
DATE=$(date +%Y%m%d_%H%M%S)
mkdir -p $BACKUP_DIR

mysqldump -u anespr1 -p'your_secure_password_here' patients > $BACKUP_DIR/patients_$DATE.sql
gzip $BACKUP_DIR/patients_$DATE.sql

# Keep only last 7 days
find $BACKUP_DIR -name "patients_*.sql.gz" -mtime +7 -delete
```

```bash
sudo chmod +x /opt/backup-db.sh
sudo crontab -e
# Add: 0 2 * * * /opt/backup-db.sh
```

## Monitoring & Maintenance

### 1. Health Check Endpoint
Add to your application if not present:
```python
@app.route('/health')
def health_check():
    return {'status': 'healthy', 'timestamp': datetime.now().isoformat()}
```

### 2. Monitor Logs
```bash
# Application logs
sudo tail -f /var/log/anespr1.log

# Nginx logs
sudo tail -f /var/log/nginx/access.log
sudo tail -f /var/log/nginx/error.log

# System logs
sudo journalctl -u supervisor -f
```

### 3. Regular Maintenance Tasks

#### Weekly:
- Review application logs for errors
- Check disk space usage
- Verify SSL certificate status

#### Monthly:
- Update system packages
- Review database performance
- Backup verification
- Security audit

## Troubleshooting

### Common Issues

1. **Application won't start**
   ```bash
   sudo supervisorctl status anespr1
   sudo supervisorctl tail -f anespr1
   ```

2. **Database connection errors**
   ```bash
   mysql -u anespr1 -p patients
   sudo systemctl status mysql
   ```

3. **SSL certificate issues**
   ```bash
   sudo certbot certificates
   sudo certbot renew --dry-run
   ```

4. **High memory usage**
   ```bash
   sudo supervisorctl restart anespr1
   htop
   ```

## Performance Optimization

### 1. Database Optimization
```sql
-- Add indexes for common queries
CREATE INDEX idx_patient_created_at ON Patient(created_at);
CREATE INDEX idx_chat_history_patient_id ON ChatHistory(patient_id);
CREATE INDEX idx_chat_history_timestamp ON ChatHistory(timestamp);
```

### 2. Application Caching
Consider implementing Redis for session storage and caching:
```bash
sudo apt install redis-server
pip install redis flask-session
```

### 3. CDN Integration
For static assets, consider using a CDN service like CloudFlare.

## Rollback Plan

1. **Stop application**: `sudo supervisorctl stop anespr1`
2. **Restore database**: `mysql -u anespr1 -p patients < backup_file.sql`
3. **Revert code**: `git checkout previous_commit`
4. **Restart**: `sudo supervisorctl start anespr1`

## Support Contacts

- **System Admin**: [Your contact info]
- **Database Issues**: [DBA contact]
- **Application Issues**: [Developer contact]
- **SSL/Domain Issues**: [IT contact]

---

**Last Updated**: $(date +%Y-%m-%d)
**Version**: 1.0