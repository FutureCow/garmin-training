# Deployment instructies

## Vereisten op de Linux server

- Python 3.11+
- PostgreSQL 17
- Nginx
- Certbot
- Playwright Chromium (eenmalig, voor eerste Garmin-login per gebruiker)

## Stappen

```bash
# 1. Kopieer project naar server
scp -r garmin-training/ user@server:/opt/garmin-training

# 2. Maak system user aan
useradd --system --no-create-home garmin

# 3. Python venv instellen
cd /opt/garmin-training
python3 -m venv venv
venv/bin/pip install -r requirements.txt

# Playwright Chromium installeren
venv/bin/playwright install chromium

# 4. Maak .env aan (kopieer van .env.example en vul in)
cp .env.example .env
# Genereer Fernet key:
# python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"

# 5. Tokens-map aanmaken
mkdir -p /opt/garmin-training/garmin-tokens
chown -R garmin:garmin /opt/garmin-training/garmin-tokens

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

## Eerste Garmin-login per gebruiker

pirate-garmin vereist een eenmalige browser-gebaseerde login per gebruiker om OAuth-tokens op te slaan.
Na de eerste login werkt de app automatisch met de gecachete tokens.

```bash
# Voer uit als de garmin-serviceuser, na registratie van de gebruiker in de app
# Vervang <user_id> door het database-ID (SELECT id FROM users WHERE email='...')
su -s /bin/bash garmin -c \
  "GARMIN_USERNAME=gebruiker@email.nl GARMIN_PASSWORD=wachtwoord \
   /opt/garmin-training/venv/bin/pirate-garmin login \
   --app-dir /opt/garmin-training/garmin-tokens/<user_id>"
```

> **Let op:** Playwright heeft een display nodig. Gebruik `Xvfb` op servers zonder scherm:
> ```bash
> apk add xvfb  # Alpine
> # of: apt install xvfb  # Debian/Ubuntu
> Xvfb :99 -screen 0 1280x720x24 &
> export DISPLAY=:99
> ```
