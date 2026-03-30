# Deployment instructies (Debian/Ubuntu)

Volledig stappenplan voor een verse Debian 12 of Ubuntu 22.04/24.04 server.

---

## 1. Systeem updaten en basispakketten installeren

```bash
apt update && apt upgrade -y

apt install -y \
  python3 python3-dev python3-pip python3-venv \
  postgresql postgresql-client \
  nginx \
  certbot python3-certbot-nginx \
  git curl \
  gcc libffi-dev libssl-dev \
  build-essential \
  xvfb
```

> `xvfb` is nodig voor Playwright (headless browser) op servers zonder scherm.

---

## 2. PostgreSQL instellen

```bash
# PostgreSQL starten en autostart inschakelen
systemctl enable --now postgresql

# Database en gebruiker aanmaken
sudo -u postgres psql -c "CREATE USER garmin WITH PASSWORD 'jouwwachtwoord';"
sudo -u postgres psql -c "CREATE DATABASE garmin_training OWNER garmin;"
```

---

## 3. Project installeren

```bash
# Repository clonen
git clone https://github.com/FutureCow/garmin-training.git /opt/garmin-training
cd /opt/garmin-training

# Systeemgebruiker aanmaken
useradd --system --no-create-home garmin

# Python venv aanmaken en dependencies installeren
python3 -m venv venv
venv/bin/pip install --upgrade pip
venv/bin/pip install -r requirements.txt

# Playwright Chromium installeren (vereist voor eerste Garmin-login)
venv/bin/playwright install chromium
venv/bin/playwright install-deps chromium
```

---

## 4. Omgevingsvariabelen instellen

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
GARMIN_TOKENS_DIR=/opt/garmin-training/garmin-tokens
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

## 5. Tokens-map aanmaken

```bash
mkdir -p /opt/garmin-training/garmin-tokens
chown -R garmin:garmin /opt/garmin-training/garmin-tokens
```

---

## 6. Database migraties uitvoeren

```bash
cd /opt/garmin-training
venv/bin/alembic upgrade head
```

---

## 7. Systemd service installeren

```bash
cp /opt/garmin-training/deployment/systemd/garmin-training.service \
   /etc/systemd/system/garmin-training.service

systemctl daemon-reload
systemctl enable --now garmin-training
```

Controleer of de service draait:

```bash
systemctl status garmin-training
# Of bekijk de logs:
journalctl -u garmin-training -f
```

---

## 8. Nginx configureren

```bash
# Pas domeinnaam aan in het config-bestand
cp /opt/garmin-training/deployment/nginx/garmin-training.conf \
   /etc/nginx/sites-available/garmin-training

# Vervang 'jouwdomein.nl' door je echte domeinnaam (2x)
nano /etc/nginx/sites-available/garmin-training

# Activeren
ln -s /etc/nginx/sites-available/garmin-training \
      /etc/nginx/sites-enabled/garmin-training

# Verwijder de standaard Nginx config als die conflicteert
rm -f /etc/nginx/sites-enabled/default

# Testen en starten
nginx -t
systemctl enable --now nginx
```

---

## 9. SSL certificaat via Let's Encrypt

```bash
certbot --nginx -d jouwdomein.nl
```

Certbot stelt automatische verlenging in via een systemd-timer. Controleer:

```bash
systemctl status certbot.timer
```

---

## 10. Controleren

```bash
systemctl status garmin-training
systemctl status nginx
systemctl status postgresql

curl -I https://jouwdomein.nl/
```

---

## 11. Eerste Garmin-login per gebruiker

pirate-garmin vereist een eenmalige browser-gebaseerde login per gebruiker om OAuth-tokens op te slaan.
Na de eerste login werkt de app automatisch met de gecachete tokens.

Voer dit uit nadat een gebruiker zich in de app heeft geregistreerd en zijn Garmin-credentials heeft ingevuld. Zoek het database-ID van de gebruiker op:

```bash
sudo -u postgres psql garmin_training -c "SELECT id, email FROM users;"
```

Voer daarna de login uit als de `garmin`-serviceuser (vervang `<user_id>` en credentials):

```bash
# Xvfb starten zodat Playwright een display heeft
Xvfb :99 -screen 0 1280x720x24 &
export DISPLAY=:99

# Login uitvoeren
su -s /bin/bash garmin -c \
  "DISPLAY=:99 \
   GARMIN_USERNAME=gebruiker@email.nl \
   GARMIN_PASSWORD=garminwachtwoord \
   /opt/garmin-training/venv/bin/pirate-garmin login \
   --app-dir /opt/garmin-training/garmin-tokens/<user_id>"
```

Na succesvolle login worden de tokens opgeslagen in `/opt/garmin-training/garmin-tokens/<user_id>/`.
Playwright is daarna niet meer nodig voor die gebruiker.

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

**Fout: `playwright._impl._errors.Error` of `Executable doesn't exist`**

```bash
/opt/garmin-training/venv/bin/playwright install chromium
/opt/garmin-training/venv/bin/playwright install-deps chromium
```

**Fout: `AuthenticationError` bij schema genereren**

De Garmin sessie-tokens zijn verlopen of nog niet aangemaakt. Voer stap 11 opnieuw uit voor de betreffende gebruiker.

**Fout: `connection refused` op PostgreSQL**

```bash
systemctl status postgresql
# Als gestopt:
systemctl start postgresql
```

**Fout: `permission denied` op .env**

```bash
chown garmin:garmin /opt/garmin-training/.env
chmod 600 /opt/garmin-training/.env
```
