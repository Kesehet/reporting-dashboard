# Deployment Guide

## Overview

This guide covers the deployment process for the eStore Digital Reporting System, including prerequisites, build steps, and deployment configurations.

## Prerequisites

### System Requirements
- **Operating System**: Windows Server 2019+ or Linux (Ubuntu 20.04+)
- **Memory**: 8GB RAM minimum, 16GB recommended
- **Storage**: 50GB free space for application and data
- **Network**: Internet access for dependency downloads

### Software Dependencies
- **Python**: 3.8 or higher
- **Node.js**: 19.x or higher
- **SQL Server**: 2019 or higher
- **Redis**: 6.0 or higher
- **Git**: For source code management

### Infrastructure Components
- **Web Server**: IIS (Windows) or Nginx (Linux)
- **SSL Certificate**: For HTTPS encryption
- **Domain**: Registered domain name
- **DNS**: Configured DNS records

## Environment Setup

### 1. Database Setup

#### SQL Server Configuration
```sql
-- Create database
CREATE DATABASE DigitalReport;

-- Create login
CREATE LOGIN eStoreApp WITH PASSWORD = 'StrongPassword123!';

-- Create user and grant permissions
USE DigitalReport;
CREATE USER eStoreApp FOR LOGIN eStoreApp;
ALTER ROLE db_datareader ADD MEMBER eStoreApp;
ALTER ROLE db_datawriter ADD MEMBER eStoreApp;

-- Enable encryption
ALTER DATABASE DigitalReport SET ENCRYPTION ON;
```

#### Database Schema Creation
```bash
# Run schema creation scripts
sqlcmd -S localhost -U sa -P password -d DigitalReport -i schema.sql
```

### 2. Redis Setup

#### Windows Installation
```powershell
# Install Redis using Chocolatey
choco install redis-64

# Start Redis service
redis-server --service-install
redis-server --service-start
```

#### Linux Installation
```bash
# Install Redis
sudo apt update
sudo apt install redis-server

# Start Redis
sudo systemctl start redis
sudo systemctl enable redis
```

### 3. Application Server Setup

#### Python Environment
```bash
# Create virtual environment
python -m venv estore_env
estore_env\Scripts\activate  # Windows
# source estore_env/bin/activate  # Linux

# Install dependencies
pip install -r requirements.txt
```

#### Node.js Environment
```bash
# Install dependencies
npm install

# Build application
npm run build
```

## Build Process

### Frontend Build
```bash
# Development build
npm run build

# Production build with optimizations
NODE_ENV=production npm run build
```

### Backend Build
```bash
# Install Python dependencies
pip install -r requirements.txt

# Build executables (optional)
pyinstaller --onefile api-server/serve.py
pyinstaller --onefile api-server/csvLoader.py
pyinstaller --onefile api-server/cache_gen.py
```

### CI/CD Pipeline

The project includes Azure Pipelines configuration:

```yaml
# azure-pipelines.yml
trigger:
- develop

pool: 'Default'

steps:
- task: NodeTool@0
  inputs:
    versionSpec: '19.x'
  displayName: 'Install Node.js'

- script: |
    npm install
    npm run build
  displayName: 'Build Frontend'

- task: CopyFiles@2
  inputs:
    contents: 'build/*'
    targetFolder: $(Build.ArtifactStagingDirectory)
  displayName: 'Copy Build Artifacts'

- task: PublishBuildArtifacts@1
  inputs:
    pathToPublish: $(Build.ArtifactStagingDirectory)
    artifactName: digital-reporting
```

## Deployment Configurations

### Environment Variables

Create `.env` file with the following variables:

```env
# Database Configuration
SQL_HOST=localhost
SQL_DATABASE=DigitalReport
SQL_USER=eStoreApp
SQL_PASSWORD=StrongPassword123!

# API Configuration
REACT_APP_API_SERVER_BASE_URL=https://api.estore.domain.com
RELAY_SERVER_SECRET=your-jwt-secret-key

# Authentication
REACT_APP_JOURNEY_MANAGER_USER=jm_user
REACT_APP_JOURNEY_MANAGER_PASSWORD=jm_password
JM_BASE_URL=https://jm-api.domain.com/secure/rest/fluentapi

# Redis Configuration
REDIS_HOST=localhost
REDIS_PORT=6379
REDIS_PASSWORD=

# MSAL Configuration
REACT_APP_CLIENT_ID=azure-client-id
REACT_APP_AUTHORITY=https://login.microsoftonline.com/tenant-id

# API Keys
ALL_FILTERS_CHART_API_KEY=your-api-key
```

### Web Server Configuration

#### IIS Configuration (Windows)
```xml
<!-- web.config -->
<?xml version="1.0" encoding="UTF-8"?>
<configuration>
    <system.webServer>
        <rewrite>
            <rules>
                <rule name="React Routes" stopProcessing="true">
                    <match url=".*" />
                    <conditions logicalGrouping="MatchAll">
                        <add input="{REQUEST_FILENAME}" matchType="IsFile" negate="true" />
                        <add input="{REQUEST_FILENAME}" matchType="IsDirectory" negate="true" />
                    </conditions>
                    <action type="Rewrite" url="/index.html" />
                </rule>
            </rules>
        </rewrite>
        <staticContent>
            <mimeMap fileExtension=".json" mimeType="application/json" />
        </staticContent>
    </system.webServer>
</configuration>
```

#### Nginx Configuration (Linux)
```nginx
server {
    listen 80;
    server_name estore.domain.com;

    location / {
        root /var/www/estore/build;
        index index.html;
        try_files $uri $uri/ /index.html;
    }

    location /api {
        proxy_pass http://localhost:5000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
    }
}
```

### SSL Configuration

#### Let's Encrypt (Linux)
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d estore.domain.com -d api.estore.domain.com
```

#### Windows IIS SSL
1. Obtain SSL certificate from trusted CA
2. Import certificate using IIS Manager
3. Bind certificate to website

## Application Deployment

### Backend Deployment

#### Windows Service
```powershell
# Create Windows service for Flask app
nssm install eStoreAPI "C:\Python\python.exe"
nssm set eStoreAPI AppDirectory "C:\inetpub\estore\api-server"
nssm set eStoreAPI AppParameters "serve.py"
nssm start eStoreAPI
```

#### Linux Service
```bash
# Create systemd service
sudo tee /etc/systemd/system/estore-api.service > /dev/null <<EOF
[Unit]
Description=eStore API Server
After=network.target

[Service]
User=www-data
WorkingDirectory=/var/www/estore/api-server
ExecStart=/var/www/estore/estore_env/bin/python serve.py
Restart=always

[Install]
WantedBy=multi-user.target
EOF

# Enable and start service
sudo systemctl daemon-reload
sudo systemctl enable estore-api
sudo systemctl start estore-api
```

### Frontend Deployment

#### Static File Hosting
```bash
# Copy build files to web root
cp -r build/* /var/www/estore/html/

# Set proper permissions
chown -R www-data:www-data /var/www/estore
```

## Monitoring and Maintenance

### Health Checks

#### API Health Check
```bash
# Test API endpoint
curl -f https://api.estore.domain.com/health
```

#### Database Connectivity
```sql
-- Test database connection
SELECT @@VERSION;
SELECT COUNT(*) FROM Transactions;
```

### Log Management

#### Application Logs
- Flask application logs: `/var/log/estore/api.log`
- Web server logs: `/var/log/nginx/access.log`
- System logs: `/var/log/syslog`

#### Log Rotation
```bash
# Configure logrotate for application logs
sudo tee /etc/logrotate.d/estore > /dev/null <<EOF
/var/log/estore/*.log {
    daily
    rotate 30
    compress
    delaycompress
    missingok
    create 644 www-data www-data
    postrotate
        systemctl reload estore-api
    endscript
}
EOF
```

### Backup Strategy

#### Database Backup
```sql
-- Daily backup script
BACKUP DATABASE DigitalReport
TO DISK = 'C:\Backups\DigitalReport_$(DATE).bak'
WITH FORMAT;
```

#### File System Backup
```bash
# Backup application files
tar -czf /backups/estore-$(date +%Y%m%d).tar.gz /var/www/estore
```

### Performance Monitoring

#### Key Metrics to Monitor
- API response times
- Database query performance
- Redis cache hit rates
- Application error rates
- System resource usage

#### Monitoring Tools
- **Application Insights**: For application telemetry
- **SQL Server Profiler**: For database performance
- **Redis INFO command**: For cache statistics
- **Prometheus/Grafana**: For comprehensive monitoring

## Troubleshooting

### Common Issues

#### API Connection Issues
```bash
# Check if API service is running
sudo systemctl status estore-api

# Check API logs
tail -f /var/log/estore/api.log
```

#### Database Connection Issues
```bash
# Test database connectivity
python -c "import pyodbc; conn = pyodbc.connect('connection_string'); print('Connected')"
```

#### Frontend Loading Issues
```bash
# Check web server configuration
nginx -t

# Check file permissions
ls -la /var/www/estore/build/
```

### Rollback Procedure

1. **Stop Application Services**
   ```bash
   sudo systemctl stop estore-api
   ```

2. **Restore Previous Version**
   ```bash
   # Restore from backup
   cp -r /backups/estore-previous/* /var/www/estore/
   ```

3. **Restart Services**
   ```bash
   sudo systemctl start estore-api
   ```

4. **Verify Functionality**
   ```bash
   curl -f https://api.estore.domain.com/health
   ```

## Security Hardening

### Network Security
- Configure firewall rules
- Use HTTPS only
- Implement rate limiting
- Regular security updates

### Application Security
- Keep dependencies updated
- Use secure headers
- Implement input validation
- Regular security audits

### Data Protection
- Encrypt sensitive data
- Implement backup encryption
- Secure credential management
- Regular vulnerability scans