# Deployment instructies (Debian/Ubuntu)

Volledig stappenplan voor een verse Debian 12 of Ubuntu 22.04/24.04 server.

---

## 1. Systeem updaten en basispakketten installeren

```bash
apt update && apt upgrade -y

apt install -y \
  python3 python3-dev python3-pip python3-venv \
  nodejs npm \
  postgresql postgresql-client \
  nginx \
  certbot python3-certbot-nginx \
  git curl \
  gcc libffi-dev libssl-dev \
  build-essential \
  xvfb
```

> `xvfb` is nodig voor de Garmin-login (headless browser) op servers zonder scherm.

---

## 2. PostgreSQL instellen

```bash
systemctl enable --now postgresql

sudo -u postgres psql -c "CREATE USER garmin WITH PASSWORD 'jouwwachtwoord';"
sudo -u postgres psql -c "CREATE DATABASE garmin_training OWNER garmin;"
```

---

## 3. garmin-connect-mcp installeren

```bash
git clone https://github.com/etweisberg/garmin-connect-mcp /opt/garmin-connect-mcp
cd /opt/garmin-connect-mcp
npm install
npm run build

# Playwright Chromium installeren (vereist voor Garmin-login)
npx playwright install chromium
npx playwright install-deps chromium
```

---

## 4. Project installeren

```bash
git clone https://github.com/FutureCow/garmin-training.git /opt/garmin-training
cd /opt/garmin-training

# Systeemgebruiker aanmaken
useradd --system --no-create-home garmin

# Python venv aanmaken en dependencies installeren
python3 -m venv venv
venv/bin/pip install --upgrade pip
venv/bin/pip install -r requirements.txt
```

---

## 5. Omgevingsvariabelen instellen

```bash
cp .env.example .env
nano /opt/garmin-training/.env
```

Vul in:

```
DATABASE_URL=postgresql+asyncpg://garmin:jouwwachtwoord@localhost/garmin_training
JWT_SECRET=lang-willekeurig-geheim
FERNET_KEY=<zie hieronder>
ANTHROPIC_API_KEY=sk-ant-...
GARMIN_HOME_DIR=/opt/garmin-training/garmin-home
GARMIN_MCP_PATH=/opt/garmin-connect-mcp/dist/index.js
```

Genereer een Fernet key:

```bash
/opt/garmin-training/venv/bin/python3 -c \
  "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

Eigenaar en rechten instellen:

```bash
chown -R garmin:garmin /opt/garmin-training
chmod 600 /opt/garmin-training/.env
```

---

## 6. Garmin-home map aanmaken

```bash
mkdir -p /opt/garmin-training/garmin-home
chown -R garmin:garmin /opt/garmin-training/garmin-home
```

---

## 7. Database migraties uitvoeren

```bash
cd /opt/garmin-training
venv/bin/alembic upgrade head
```

---

## 8. Systemd service installeren

```bash
cp /opt/garmin-training/deployment/systemd/garmin-training.service \
   /etc/systemd/system/garmin-training.service

systemctl daemon-reload
systemctl enable --now garmin-training
```

Controleer of de service draait:

```bash
systemctl status garmin-training
journalctl -u garmin-training -f
```

---

## 9. Nginx configureren

```bash
cp /opt/garmin-training/deployment/nginx/garmin-training.conf \
   /etc/nginx/sites-available/garmin-training

# Vervang 'jouwdomein.nl' door je echte domeinnaam (2x)
nano /etc/nginx/sites-available/garmin-training

ln -s /etc/nginx/sites-available/garmin-training \
      /etc/nginx/sites-enabled/garmin-training

rm -f /etc/nginx/sites-enabled/default

nginx -t
systemctl enable --now nginx
```

---

## 10. SSL certificaat via Let's Encrypt

```bash
certbot --nginx -d jouwdomein.nl
```

Controleer automatische verlenging:

```bash
systemctl status certbot.timer
```

---

## 11. Controleren

```bash
systemctl status garmin-training
systemctl status nginx
systemctl status postgresql

curl -I https://jouwdomein.nl/
```

---

## 12. Eerste Garmin-login per gebruiker

garmin-connect-mcp vereist een eenmalige browserlogin per gebruiker. Na de login worden
cookies opgeslagen in `GARMIN_HOME_DIR/{user_id}/.garmin-connect-mcp/session.json`.

Zoek het database-ID van de gebruiker op:

```bash
sudo -u postgres psql garmin_training -c "SELECT id, email FROM users;"
```

Voer de login uit (vervang `<user_id>`). Op een server zonder scherm:

```bash
# Xvfb starten
Xvfb :99 -screen 0 1280x720x24 &
export DISPLAY=:99

# Login uitvoeren — opent een browservenster
HOME=/opt/garmin-training/garmin-home/<user_id> \
  DISPLAY=:99 \
  node /opt/garmin-connect-mcp/dist/index.js login
```

Er opent een browservenster met Garmin Connect. Log in, wacht tot je de activiteiten ziet,
en druk daarna op **Enter** in de terminal. De sessie wordt opgeslagen.

Rechten instellen na de login:

```bash
chown -R garmin:garmin /opt/garmin-training/garmin-home/
```

> **Tip:** Heb je een eigen PC of Mac? Doe de login daar (geen Xvfb nodig) en kopieer
> de sessie naar de server:
>
> ```bash
> # Lokaal (vervang <user_id>)
> HOME=./garmin-home/<user_id> node /opt/garmin-connect-mcp/dist/index.js login
>
> # Kopieer naar server
> scp -r garmin-home/<user_id> user@server:/opt/garmin-training/garmin-home/
> ```

---

## Herstart na update

```bash
cd /opt/garmin-training
git pull
venv/bin/pip install -r requirements.txt
venv/bin/alembic upgrade head
systemctl restart garmin-training
```

---

## Logbestanden

| Component | Loglocatie |
|---|---|
| Garmin Training App | `journalctl -u garmin-training` |
| Nginx | `/var/log/nginx/error.log` |
| PostgreSQL | `/var/log/postgresql/` |

---

## Problemen oplossen

**Fout: `No saved session found` bij schema genereren**

De Garmin-login is nog niet uitgevoerd voor deze gebruiker. Voer stap 12 uit.

**Fout: `connection refused` op PostgreSQL**

```bash
systemctl status postgresql
systemctl start postgresql
```

**Fout: `permission denied` op .env of garmin-home**

```bash
chown garmin:garmin /opt/garmin-training/.env
chmod 600 /opt/garmin-training/.env
chown -R garmin:garmin /opt/garmin-training/garmin-home/
```
