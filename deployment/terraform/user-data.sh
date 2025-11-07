#!/bin/bash
# EC2 User Data Script for Purp Application Setup
# This script runs on instance launch to configure the environment

set -e

# Update system
apt-get update
apt-get upgrade -y

# Install dependencies
apt-get install -y \
    python3.11 \
    python3.11-venv \
    python3-pip \
    nginx \
    git \
    postgresql-client \
    supervisor \
    fail2ban

# Create application user
useradd -r -s /bin/bash -d /opt/purp -m purp

# Create application directory
mkdir -p /opt/purp
cd /opt/purp

# Clone repository (replace with your actual repo)
git clone https://github.com/wanderinganalyst/purp.git .
chown -R purp:purp /opt/purp

# Create Python virtual environment
sudo -u purp python3.11 -m venv .venv
sudo -u purp .venv/bin/pip install --upgrade pip

# Install dependencies
sudo -u purp .venv/bin/pip install -r requirements.txt
sudo -u purp .venv/bin/pip install -r requirements-production.txt

# Create directories
mkdir -p /var/log/purp
chown purp:purp /var/log/purp

mkdir -p /etc/purp
chown purp:purp /etc/purp

# Create environment file
cat > /etc/purp/.env.production <<EOF
FLASK_APP=main.py
FLASK_ENV=production
SECRET_KEY=${secret_key}
DATABASE_URL=postgresql://${db_username}:${db_password}@${db_endpoint}/${db_name}

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/purp/app.log

# Gunicorn
GUNICORN_WORKERS=4
GUNICORN_PORT=8000
GUNICORN_TIMEOUT=30

# Cache
CACHE_TYPE=simple
CACHE_DEFAULT_TIMEOUT=300
EOF

chown purp:purp /etc/purp/.env.production
chmod 600 /etc/purp/.env.production

# Initialize database
sudo -u purp bash -c "cd /opt/purp && source .venv/bin/activate && python init_db.py"

# Sync initial data
sudo -u purp bash -c "cd /opt/purp && source .venv/bin/activate && python sync_bills.py"
sudo -u purp bash -c "cd /opt/purp && source .venv/bin/activate && python sync_reps.py"

# Create systemd service
cat > /etc/systemd/system/purp.service <<'SYSTEMD'
[Unit]
Description=Purp Flask Application
After=network.target

[Service]
Type=notify
User=purp
Group=purp
WorkingDirectory=/opt/purp
Environment="PATH=/opt/purp/.venv/bin"
EnvironmentFile=/etc/purp/.env.production
ExecStart=/opt/purp/.venv/bin/gunicorn -c gunicorn_config.py wsgi:app
ExecReload=/bin/kill -s HUP $MAINPID
KillMode=mixed
TimeoutStopSec=5
PrivateTmp=true
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
SYSTEMD

# Create Nginx configuration
cat > /etc/nginx/sites-available/purp <<'NGINX'
upstream purp_app {
    server 127.0.0.1:8000 fail_timeout=0;
}

server {
    listen 80;
    server_name _;

    client_max_body_size 10M;

    # Security headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;
    add_header Referrer-Policy "strict-origin-when-cross-origin" always;

    # Logging
    access_log /var/log/nginx/purp-access.log;
    error_log /var/log/nginx/purp-error.log;

    # Static files
    location /static {
        alias /opt/purp/static;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    # Proxy to Gunicorn
    location / {
        proxy_pass http://purp_app;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        proxy_buffering off;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Health check endpoint
    location /health {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
NGINX

# Enable Nginx site
ln -sf /etc/nginx/sites-available/purp /etc/nginx/sites-enabled/
rm -f /etc/nginx/sites-enabled/default

# Test Nginx configuration
nginx -t

# Enable and start services
systemctl daemon-reload
systemctl enable purp
systemctl start purp
systemctl enable nginx
systemctl restart nginx

# Configure fail2ban for SSH protection
systemctl enable fail2ban
systemctl start fail2ban

# Setup log rotation
cat > /etc/logrotate.d/purp <<'LOGROTATE'
/var/log/purp/*.log {
    daily
    missingok
    rotate 14
    compress
    delaycompress
    notifempty
    create 0640 purp purp
    sharedscripts
    postrotate
        systemctl reload purp > /dev/null 2>&1 || true
    endscript
}
LOGROTATE

# Create a simple health check script
cat > /usr/local/bin/purp-health-check <<'HEALTHCHECK'
#!/bin/bash
response=$(curl -s -o /dev/null -w "%%{http_code}" http://localhost/health)
if [ "$response" != "200" ]; then
    echo "Health check failed: $response"
    systemctl restart purp
fi
HEALTHCHECK

chmod +x /usr/local/bin/purp-health-check

# Add to cron (every 5 minutes)
echo "*/5 * * * * /usr/local/bin/purp-health-check" | crontab -u root -

echo "Purp application setup complete!"
