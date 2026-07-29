#!/bin/bash
set -euo pipefail

# ==============================================================
#  CRM - Auto Installer for Ubuntu/Debian VPS
#  Usage: curl -sL https://raw.githubusercontent.com/LucioHSantos/meu-crm/main/deploy/setup-vps.sh | bash
# ==============================================================

DOMAIN="crm.ivro.com.br"
REPO_HTTPS="https://github.com/LucioHSantos/meu-crm.git"
APP_DIR="/var/www/crm"
DB_NAME="crm_db"
DB_USER="crm_user"

RED='\033[0;31m'; GREEN='\033[0;32m'; YELLOW='\033[1;33m'; CYAN='\033[0;36m'; NC='\033[0m'
log()  { echo -e "${GREEN}[✓]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
err()  { echo -e "${RED}[✗]${NC} $1"; exit 1; }
info() { echo -e "${CYAN}[i]${NC} $1"; }

if [ "$EUID" -ne 0 ]; then err "Run as root: sudo bash $0"; fi

echo ""
echo -e "${CYAN}============================================${NC}"
echo -e "${CYAN}   CRM PREMIUM - AUTO INSTALLER${NC}"
echo -e "${CYAN}   Domain: $DOMAIN${NC}"
echo -e "${CYAN}============================================${NC}"
echo ""

# --- GitHub Token ---
if [ -z "${GITHUB_TOKEN:-}" ]; then
    echo -e "${YELLOW}Precisamos do seu GitHub Token para clonar o repositório privado.${NC}"
    echo -e "${YELLOW}Crie um token em: https://github.com/settings/tokens (escopo: repo)${NC}"
    read -rsp "GitHub Token: " GITHUB_TOKEN
    echo ""
fi

REPO_AUTH="https://${GITHUB_TOKEN}@github.com/LucioHSantos/meu-crm.git"

# --- System Packages ---
log "Updating system packages"
apt update && apt upgrade -y

log "Installing dependencies"
apt install -y python3 python3-pip python3-venv postgresql nginx git certbot python3-certbot-nginx curl openssl

# --- PostgreSQL ---
if ! systemctl is-active --quiet postgresql; then
    systemctl start postgresql
fi
systemctl enable postgresql

DB_PASS=$(openssl rand -base64 32)

log "Creating PostgreSQL user and database"
su - postgres -c "psql -tc \"SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'\" | grep -q 1 || psql -c \"CREATE USER $DB_USER WITH PASSWORD '$DB_PASS';\"" 2>/dev/null
su - postgres -c "psql -tc \"SELECT 1 FROM pg_database WHERE datname='$DB_NAME'\" | grep -q 1 || psql -c \"CREATE DATABASE $DB_NAME OWNER $DB_USER;\"" 2>/dev/null
su - postgres -c "psql -c \"ALTER USER $DB_USER CREATEDB;\"" 2>/dev/null

# --- Clone Repo ---
log "Cloning repository..."
rm -rf "$APP_DIR"
git clone "$REPO_AUTH" "$APP_DIR"
cd "$APP_DIR"
git config --local credential.helper ""
cd /

# --- .env ---
SECRET_KEY=$(openssl rand -hex 32)

log "Creating .env file"
cat > "$APP_DIR/.env" << EOF
SECRET_KEY=$SECRET_KEY
DEBUG=False
ALLOWED_HOSTS=$DOMAIN

DATABASE_NAME=$DB_NAME
DATABASE_USER=$DB_USER
DATABASE_PASSWORD=$DB_PASS
DATABASE_HOST=localhost
DATABASE_PORT=5432

WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_ACCESS_TOKEN=
WHATSAPP_VERIFY_TOKEN=
WHATSAPP_API_VERSION=v18.0
OLLAMA_URL=http://localhost:11434
EOF

# --- Virtual Environment ---
log "Creating Python virtual environment"
python3 -m venv "$APP_DIR/venv"
source "$APP_DIR/venv/bin/activate"
pip install --upgrade pip wheel setuptools -q
pip install -r "$APP_DIR/requirements.txt" -q
pip install gunicorn -q

# --- Django Setup ---
log "Running database migrations"
cd "$APP_DIR"
source "$APP_DIR/venv/bin/activate"
python manage.py migrate --settings=config.settings.production

log "Collecting static files"
python manage.py collectstatic --noinput --settings=config.settings.production

mkdir -p "$APP_DIR/media"

log "Setting permissions"
chown -R www-data:www-data "$APP_DIR"
chmod 755 "$APP_DIR"

# --- Create Superuser ---
log "Creating admin user"
cd "$APP_DIR"
source "$APP_DIR/venv/bin/activate"
python manage.py shell --settings=config.settings.production << 'PYEOF'
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(username='admin').exists():
    User.objects.create_superuser('admin', 'admin@crm.ivro.com.br', 'admin123')
    print('Superuser created: admin / admin123')
else:
    print('Superuser already exists')
PYEOF

# --- Gunicorn Service ---
log "Setting up Gunicorn service"
cat > /etc/systemd/system/crm.service << 'SERVICE'
[Unit]
Description=CRM Django Application
After=network.target postgresql.service

[Service]
Type=exec
User=www-data
Group=www-data
WorkingDirectory=/var/www/crm
Environment=DJANGO_SETTINGS_MODULE=config.settings.production
EnvironmentFile=/var/www/crm/.env
ExecStart=/var/www/crm/venv/bin/gunicorn config.wsgi:application --bind unix:/run/crm.sock --workers 3 --timeout 120
Restart=always
RestartSec=5

[Install]
WantedBy=multi-user.target
SERVICE

systemctl daemon-reload
systemctl enable crm
systemctl start crm

# --- Nginx ---
log "Setting up Nginx"
cat > /etc/nginx/sites-available/crm << 'NGINX'
server {
    listen 80;
    server_name crm.ivro.com.br;

    location /.well-known/acme-challenge/ {
        root /var/www/letsencrypt;
    }

    location / {
        return 301 https://$host$request_uri;
    }
}

server {
    listen 443 ssl http2;
    server_name crm.ivro.com.br;

    ssl_certificate /etc/letsencrypt/live/crm.ivro.com.br/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/crm.ivro.com.br/privkey.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    client_max_body_size 20M;
    location = /favicon.ico { access_log off; log_not_found off; }
    location /static/ { alias /var/www/crm/staticfiles/; expires 30d; add_header Cache-Control "public, immutable"; }
    location /media/ { alias /var/www/crm/media/; expires 30d; add_header Cache-Control "public, immutable"; }
    location / {
        include proxy_params;
        proxy_pass http://unix:/run/crm.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }
}
NGINX

if [ -f /etc/nginx/sites-enabled/default ]; then
    rm /etc/nginx/sites-enabled/default
fi
ln -sf /etc/nginx/sites-available/crm /etc/nginx/sites-enabled/
mkdir -p /var/www/letsencrypt
nginx -t && systemctl reload nginx

# --- SSL Certificate ---
log "Setting up SSL certificate"
if certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --email admin@"$DOMAIN" --redirect 2>/dev/null; then
    log "SSL certificate installed"
else
    warn "SSL failed. Run manually: certbot --nginx -d $DOMAIN"
    warn "Temporary: using HTTP-only config"
    cat > /etc/nginx/sites-available/crm << 'NGINX_HTTP'
server {
    listen 80;
    server_name crm.ivro.com.br;
    client_max_body_size 20M;
    location = /favicon.ico { access_log off; log_not_found off; }
    location /static/ { alias /var/www/crm/staticfiles/; expires 30d; }
    location /media/ { alias /var/www/crm/media/; expires 30d; }
    location / {
        include proxy_params;
        proxy_pass http://unix:/run/crm.sock;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_read_timeout 120s;
    }
}
NGINX_HTTP
    nginx -t && systemctl reload nginx
fi

systemctl restart crm 2>/dev/null || true

# --- Backup Script ---
log "Creating backup script"
cat > /usr/local/bin/backup-crm.sh << 'BACKUP'
#!/bin/bash
BACKUP_DIR="/var/backups/crm"
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
mkdir -p "$BACKUP_DIR"
source /var/www/crm/.env
PGPASSWORD="$DATABASE_PASSWORD" pg_dump -U "$DATABASE_USER" -h "$DATABASE_HOST" "$DATABASE_NAME" > "$BACKUP_DIR/db_$TIMESTAMP.sql"
tar -czf "$BACKUP_DIR/media_$TIMESTAMP.tar.gz" -C /var/www/crm media
find "$BACKUP_DIR" -name "*.sql" -mtime +7 -delete
find "$BACKUP_DIR" -name "*.tar.gz" -mtime +7 -delete
echo "Backup completed: $TIMESTAMP"
BACKUP
chmod +x /usr/local/bin/backup-crm.sh
echo "0 3 * * * root /usr/local/bin/backup-crm.sh" > /etc/cron.d/crm-backup

# --- Ollama Install Hint ---
log "Installing Ollama (AI engine)..."
if curl -fsSL https://ollama.com/install.sh | sh 2>/dev/null; then
    ollama pull llama3.2:3b 2>/dev/null &
    log "Ollama installed. Model downloading in background."
else
    warn "Ollama install failed. Run manually: curl -fsSL https://ollama.com/install.sh | sh"
fi

# --- Done ---
log "=========================================="
log "  INSTALLATION COMPLETE!"
log "=========================================="
echo ""
info "  CRM:       https://$DOMAIN (ou http://$DOMAIN se SSL falhou)"
info "  Admin:     https://$DOMAIN/admin/"
info "  Usuário:   admin"
info "  Senha:     admin123"
echo ""
info "  WhatsApp credenciais em: $APP_DIR/.env"
info "  Backup automático: 3h da manhã (cron)"
echo ""
echo -e "${YELLOW}PRÓXIMOS PASSOS:${NC}"
echo "  1. Altere a senha do admin: entre no admin e troque a senha"
echo "  2. Configure WhatsApp: edite $APP_DIR/.env"
echo "  3. Configure DNS: aponte crm.ivro.com.br para este servidor"
echo "  4. Se SSL falhou, rode: certbot --nginx -d $DOMAIN"
echo "  5. Alimente a base de conhecimento do robô em /ai-agent/"
echo ""
echo -e "${YELLOW}Se precisar de ajuda com o WhatsApp API, me chame!${NC}"
echo ""
