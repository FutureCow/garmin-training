# Deployment instructies

## Vereisten op de Linux server

- Python 3.11+
- Node.js 20+ (voor garmin-connect-mcp subprocess)
- PostgreSQL 15
- Nginx
- Certbot

## Stappen

```bash
# 1. Kopieer project naar server
scp -r garmin-training/ user@server:/opt/garmin-training

# 2. Maak system user aan
useradd --system --no-create-home garmin

# 3. Installeer garmin-connect-mcp
git clone https://github.com/etweisberg/garmin-connect-mcp /opt/garmin-connect-mcp
cd /opt/garmin-connect-mcp && npm install && npm run build

# 4. Python venv instellen
cd /opt/garmin-training
python3 -m venv venv
venv/bin/pip install -r requirements.txt

# 5. Maak .env aan (kopieer van .env.example en vul in)
cp .env.example .env
# Genereer Fernet key:
# python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# 6. Database aanmaken
sudo -u postgres createuser garmin
sudo -u postgres createdb garmin_training -O garmin
sudo -u postgres psql -c "ALTER USER garmin WITH PASSWORD 'yourpassword';"

# 7. Migraties uitvoeren
cd /opt/garmin-training
venv/bin/alembic upgrade head

# 8. Systemd service installeren
cp deployment/systemd/garmin-training.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable garmin-training
systemctl start garmin-training

# 9. Nginx configureren
cp deployment/nginx/garmin-training.conf /etc/nginx/sites-available/garmin-training
ln -s /etc/nginx/sites-available/garmin-training /etc/nginx/sites-enabled/
# Pas jouwdomein.nl aan naar je echte domeinnaam!
nginx -t && systemctl reload nginx

# 10. SSL certificaat
certbot --nginx -d jouwdomein.nl

# 11. Controleer
systemctl status garmin-training
curl -I https://jouwdomein.nl/index.html
```
