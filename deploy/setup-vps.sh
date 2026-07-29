#!/bin/bash
set -euo pipefail

DOMAIN="crm.ivro.com.br"
REPO="git@github.com:LucioHSantos/meu-crm.git"
APP_DIR="/var/www/crm"
DB_NAME="crm_db"
DB_USER="crm_user"

RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m'

log() { echo -e "${GREEN}[+]${NC} $1"; }
warn() { echo -e "${YELLOW}[!]${NC} $1"; }
err() { echo -e "${RED}[x]${NC} $1"; exit 1; }

if [ "$EUID" -ne 0 ]; then err "Run as root"; fi

log "Updating system packages"
apt update && apt upgrade -y

log "Installing dependencies"
apt install -y python3 python3-pip python3-venv postgresql nginx git certbot python3-certbot-nginx curl

if ! systemctl is-active --quiet postgresql; then
    systemctl start postgresql
fi

log "Creating PostgreSQL user and database"
su - postgres -c "psql -tc \"SELECT 1 FROM pg_roles WHERE rolname='$DB_USER'\" | grep -q 1 || psql -c \"CREATE USER $DB_USER WITH PASSWORD '$(openssl rand -base64 32)';\""
su - postgres -c "psql -tc \"SELECT 1 FROM pg_database WHERE datname='$DB_NAME'\" | grep -q 1 || psql -c \"CREATE DATABASE $DB_NAME OWNER $DB_USER;\""
su - postgres -c "psql -c \"ALTER USER $DB_USER CREATEDB;\""
DB_PASS=$(su - postgres -c "psql -tc \"SELECT password FROM pg_shadow WHERE usename='$DB_USER'\"" | xargs)
warn "Database password is set. Save it from /var/www/crm/.env later."

log "Setting up application directory"
rm -rf "$APP_DIR"
mkdir -p "$APP_DIR"
mkdir -p /var/www/letsencrypt

log "Cloning repository"
git clone "$REPO" "$APP_DIR"

log "Creating .env file"
cat > "$APP_DIR/.env" << EOF
SECRET_KEY=$(openssl rand -hex 32)
DEBUG=False
ALLOWED_HOSTS=$DOMAIN

DATABASE_NAME=$DB_NAME
DATABASE_USER=$DB_USER
DATABASE_PASSWORD=$(su - postgres -c "psql -t -c \"SELECT password FROM pg_shadow WHERE usename='$DB_USER'\"" | xargs)
DATABASE_HOST=localhost
DATABASE_PORT=5432

WHATSAPP_PHONE_NUMBER_ID=
WHATSAPP_ACCESS_TOKEN=
WHATSAPP_VERIFY_TOKEN=
WHATSAPP_API_VERSION=v18.0
OLLAMA_URL=http://localhost:11434
EOF

log "Creating virtual environment"
python3 -m venv "$APP_DIR/venv"
source "$APP_DIR/venv/bin/activate"
pip install --upgrade pip wheel setuptools
pip install -r "$APP_DIR/requirements.txt"
pip install gunicorn

log "Running migrations"
cd "$APP_DIR"
source venv/bin/activate
python manage.py migrate --settings=config.settings.production

log "Collecting static files"
python manage.py collectstatic --noinput --settings=config.settings.production

log "Creating media directory"
mkdir -p "$APP_DIR/media"

log "Setting permissions"
chown -R www-data:www-data "$APP_DIR"
chmod 755 "$APP_DIR"

log "Setting up Gunicorn service"
cp "$APP_DIR/deploy/crm.service" /etc/systemd/system/crm.service
systemctl daemon-reload
systemctl enable crm
systemctl start crm

log "Setting up Nginx"
cp "$APP_DIR/deploy/crm.nginx.conf" /etc/nginx/sites-available/crm
if [ -f /etc/nginx/sites-enabled/default ]; then
    rm /etc/nginx/sites-enabled/default
fi
ln -sf /etc/nginx/sites-available/crm /etc/nginx/sites-enabled/
nginx -t && systemctl reload nginx

log "Setting up SSL certificate"
certbot --nginx -d "$DOMAIN" --non-interactive --agree-tos --email admin@"$DOMAIN" --redirect || \
    warn "SSL failed. Run: certbot --nginx -d $DOMAIN"

log "Restarting services"
systemctl restart crm
systemctl reload nginx

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

log "=== SETUP COMPLETE ==="
echo ""
echo "  CRM: https://$DOMAIN"
echo "  Admin: https://$DOMAIN/admin/"
echo ""
echo "Next steps:"
echo "  1. Create superuser: cd $APP_DIR && source venv/bin/activate && python manage.py createsuperuser --settings=config.settings.production"
echo "  2. Configure WhatsApp credentials in $APP_DIR/.env"
echo "  3. Install Ollama: curl -fsSL https://ollama.ai/install.sh | sh && ollama pull llama3"
echo "  4. Configure WhatsApp webhook in Meta Developers -> URL: https://$DOMAIN/ai-agent/webhook/"
echo ""
