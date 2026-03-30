# Deployment op Alpine Linux

Alpine Linux gebruikt `apk` als pakketbeheerder en `OpenRC` als init-systeem (geen systemd). Dit document beschrijft de volledige installatie op Alpine Linux 3.21+.

> **Verschillen met standaard Linux:**
> - `apk` in plaats van `apt`/`yum`
> - `rc-service` / `rc-update` in plaats van `systemctl`
> - OpenRC init scripts in `/etc/init.d/` in plaats van systemd units
> - `adduser` in plaats van `useradd`
> - Python 3.12 beschikbaar via `python3` (3.11 via `python3.11`)

---

## 1. Systeem updaten en basispakketten installeren

```bash
apk update && apk upgrade

apk add \
  python3 python3-dev py3-pip \
  postgresql17 postgresql17-client \
  nginx \
  certbot certbot-nginx \
  git curl bash \
  gcc musl-dev libffi-dev openssl-dev \
  build-base
```

> `gcc`, `musl-dev` en `build-base` zijn nodig om Python packages met C-extensies te compileren (bcrypt, cryptography, asyncpg).
> Node.js is **niet** meer vereist — pirate-garmin is een pure Python library.

---

## 2. PostgreSQL instellen

```bash
# Database initialiseren
mkdir -p /var/lib/postgresql/data
chown postgres:postgres /var/lib/postgresql/data
su - postgres -s /bin/sh -c "initdb -D /var/lib/postgresql/data"

# PostgreSQL starten en autostart inschakelen
rc-service postgresql start
rc-update add postgresql default

# Database en gebruiker aanmaken
su - postgres -s /bin/sh -c "psql -c \"CREATE USER garmin WITH PASSWORD 'jouwwachtwoord';\""
su - postgres -s /bin/sh -c "psql -c \"CREATE DATABASE garmin_training OWNER garmin;\""
```

---

## 3. Project installeren

```bash
# Project clonen
git clone https://github.com/FutureCow/garmin-training.git /opt/garmin-training
cd /opt/garmin-training

# Systeemgebruiker aanmaken (Alpine gebruikt adduser)
adduser -S -H -D garmin

# Python venv aanmaken en dependencies installeren
python3 -m venv venv
venv/bin/pip install --upgrade pip
venv/bin/pip install -r requirements.txt

# Playwright Chromium installeren (vereist voor eerste Garmin-login)
venv/bin/playwright install chromium
venv/bin/playwright install-deps chromium
```

---

## 5. Omgevingsvariabelen instellen

```bash
cp .env.example .env
```

Bewerk `.env`:

```bash
vi /opt/garmin-training/.env
```

Inhoud:

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

Eigenaar instellen:

```bash
chown -R garmin:garmin /opt/garmin-training
chmod 600 /opt/garmin-training/.env
```

Maak de tokens-map aan en stel eigenaar in:

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

## 7. OpenRC init script aanmaken

Alpine gebruikt geen systemd. Maak een OpenRC script aan:

```bash
cat > /etc/init.d/garmin-training << 'EOF'
#!/sbin/openrc-run

name="garmin-training"
description="Garmin Training App"

command="/opt/garmin-training/venv/bin/uvicorn"
command_args="backend.main:app --host 127.0.0.1 --port 8000"
command_user="garmin"
directory="/opt/garmin-training"
pidfile="/run/${RC_SVCNAME}.pid"
command_background=true

# Laad .env als omgevingsvariabelen
env_vars=""
if [ -f /opt/garmin-training/.env ]; then
    export $(grep -v '^#' /opt/garmin-training/.env | xargs)
fi

depend() {
    need net postgresql
    after logger
}
EOF

chmod +x /etc/init.d/garmin-training

# Service starten en autostart inschakelen
rc-service garmin-training start
rc-update add garmin-training default
```

Controleer of de service draait:

```bash
rc-service garmin-training status
# Of bekijk de logs:
tail -f /var/log/messages
```

---

## 8. Nginx configureren

```bash
# Kopieer de Nginx config
cp /opt/garmin-training/deployment/nginx/garmin-training.conf \
   /etc/nginx/http.d/garmin-training.conf

# Pas het domeinnaam aan in het bestand
vi /etc/nginx/http.d/garmin-training.conf
# Vervang 'jouwdomein.nl' door je echte domeinnaam (2x)

# Verwijder de standaard Nginx config als die conflicteert
rm -f /etc/nginx/http.d/default.conf

# Nginx testen en starten
nginx -t
rc-service nginx start
rc-update add nginx default
```

> **Let op:** Alpine slaat Nginx configs op in `/etc/nginx/http.d/` (niet in `sites-available/sites-enabled/`).

---

## 9. SSL certificaat via Let's Encrypt

```bash
certbot --nginx -d jouwdomein.nl
```

Certbot automatische verlenging via crontab instellen:

```bash
# Voeg toe aan crontab (als root)
crontab -e
```

Voeg deze regel toe:

```
0 3 * * * certbot renew --quiet && rc-service nginx reload
```

---

## 10. Controleren

```bash
# Service status
rc-service garmin-training status
rc-service nginx status
rc-service postgresql status

# HTTP-test
curl -I https://jouwdomein.nl/
```

---

## Herstart na update

```bash
cd /opt/garmin-training
git pull
venv/bin/pip install -r requirements.txt
venv/bin/alembic upgrade head
rc-service garmin-training restart
```

---

## Logbestanden

| Component | Loglocatie |
|---|---|
| Garmin Training App | `/var/log/messages` (via syslog) |
| Nginx | `/var/log/nginx/error.log` |
| PostgreSQL | `/var/lib/postgresql/data/pg_log/` |

Live logs bekijken:

```bash
tail -f /var/log/messages | grep garmin
```

---

## Problemen oplossen

**Fout: `playwright._impl._errors.Error` of `Executable doesn't exist`**

Playwright Chromium is niet geïnstalleerd:

```bash
/opt/garmin-training/venv/bin/playwright install chromium
/opt/garmin-training/venv/bin/playwright install-deps chromium
```

**Fout: `pirate_garmin.auth.AuthenticationError` bij schema genereren**

De Garmin sessie-tokens zijn verlopen of nog niet aangemaakt. Voer de eerste login uit als de `garmin`-user:

```bash
su -s /bin/bash garmin -c \
  "GARMIN_USERNAME=jouw@email.nl GARMIN_PASSWORD=jouwwachtwoord \
   /opt/garmin-training/venv/bin/pirate-garmin login \
   --app-dir /opt/garmin-training/garmin-tokens/<user_id>"
```

Vervang `<user_id>` door het database-ID van de gebruiker (zie `SELECT id FROM users WHERE email='...'`).

**Fout: `connection refused` op PostgreSQL**

```bash
rc-service postgresql status
# Als gestopt:
rc-service postgresql start
```

**Fout: `permission denied` op .env**

```bash
chown garmin:garmin /opt/garmin-training/.env
chmod 600 /opt/garmin-training/.env
```
