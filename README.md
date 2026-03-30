# Garmin Training App

Een webapplicatie voor hardlopers die via Garmin Connect een gepersonaliseerd trainingsschema laten genereren door Claude (Anthropic AI).

## Wat doet de app?

- Koppelt aan **Garmin Connect** via [pirate-garmin](https://github.com/jeffton/pirate-garmin)
- Analyseert je volledige trainingshistorie (activiteiten, VO2max, hartslag, hersteltijd, slaap)
- Genereert een gepersonaliseerd trainingsschema via **Claude (claude-opus-4-6)**
- Ondersteunt meerdere gebruikers, elk met eigen Garmin-account

## Functionaliteiten

- Registratie en inloggen (JWT-authenticatie)
- Garmin-credentials veilig opslaan (Fernet-encryptie)
- Trainingsvoorkeuren instellen:
  - Welke dagen je traint (per dag selecteerbaar)
  - Dag voor de lange duurloop
  - Doelafstand (5K / 10K / halve marathon / marathon)
  - Doeltempo en/of doeltijd
  - Vaste periode (x weken) of rolling schema
- Schema bekijken per week (met uitleg per training)
- Schema-historiek inzien

## Technische stack

| Laag | Technologie |
|---|---|
| Backend | Python 3.11+, FastAPI, SQLAlchemy (async), asyncpg |
| Database | PostgreSQL 17 |
| AI | Anthropic Claude (claude-opus-4-6) via MCP |
| Garmin | pirate-garmin (Python, Playwright) |
| Frontend | Vanilla JS (ES modules), HTML, CSS |
| Deployment | Nginx, systemd, Let's Encrypt |

## Vereisten

- Python 3.11+
- PostgreSQL 17
- Nginx
- Certbot (Let's Encrypt)
- Anthropic API key
- Garmin Connect account
- Playwright Chromium (eenmalig, voor eerste Garmin-login)

## Installatie

### 1. Repository clonen

```bash
git clone https://github.com/FutureCow/garmin-training.git /opt/garmin-training
cd /opt/garmin-training
```

### 2. Python omgeving

```bash
cd /opt/garmin-training
python3 -m venv venv
venv/bin/pip install -r requirements.txt

# Playwright Chromium installeren (vereist voor eerste Garmin-login per gebruiker)
venv/bin/playwright install chromium
```

### 4. Omgevingsvariabelen

```bash
cp .env.example .env
nano .env
```

Vul in `.env` in:

```
DATABASE_URL=postgresql+asyncpg://garmin:jouwwachtwoord@localhost/garmin_training
JWT_SECRET=lang-willekeurig-geheim
FERNET_KEY=<genereer hieronder>
ANTHROPIC_API_KEY=sk-ant-...
GARMIN_TOKENS_DIR=/opt/garmin-training/garmin-tokens
```

Genereer een Fernet key:
```bash
python3 -c "from cryptography.fernet import Fernet; print(Fernet.generate_key().decode())"
```

### 5. Database aanmaken

```bash
sudo -u postgres createuser garmin
sudo -u postgres createdb garmin_training -O garmin
sudo -u postgres psql -c "ALTER USER garmin WITH PASSWORD 'jouwwachtwoord';"
```

### 6. Migraties uitvoeren

```bash
venv/bin/alembic upgrade head
```

### 7. Systemd service

```bash
sudo useradd --system --no-create-home garmin
sudo cp deployment/systemd/garmin-training.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable --now garmin-training
```

### 8. Nginx + SSL

```bash
# Pas 'jouwdomein.nl' aan in het config-bestand
sudo cp deployment/nginx/garmin-training.conf /etc/nginx/sites-available/garmin-training
sudo ln -s /etc/nginx/sites-available/garmin-training /etc/nginx/sites-enabled/
sudo nginx -t && sudo systemctl reload nginx
sudo certbot --nginx -d jouwdomein.nl
```

### 9. Controleer

```bash
sudo systemctl status garmin-training
curl -I https://jouwdomein.nl/
```

## Projectstructuur

```
garmin-training/
├── backend/
│   ├── main.py          # FastAPI app & routes
│   ├── auth.py          # JWT, bcrypt, Fernet, get_current_user
│   ├── config.py        # Instellingen via .env
│   ├── database.py      # Async SQLAlchemy engine
│   ├── garmin.py        # MCP subprocess context manager
│   ├── models.py        # ORM modellen
│   ├── scheduler.py     # Claude schemageneratie via MCP
│   ├── schemas.py       # Pydantic request/response modellen
│   └── routes/
│       ├── auth.py      # /auth/register, /auth/login, /auth/refresh
│       ├── preferences.py  # /preferences, /garmin-credentials
│       └── schemas.py   # /schemas/generate, /schemas/active, etc.
├── frontend/
│   ├── index.html       # Login / Registratie
│   ├── dashboard.html   # Dashboard
│   ├── schema.html      # Schema-weergave
│   ├── settings.html    # Instellingen
│   ├── history.html     # Historiek
│   ├── css/style.css
│   └── js/
│       ├── api.js       # Fetch wrapper met JWT refresh
│       ├── auth.js
│       ├── dashboard.js
│       ├── schema.js
│       ├── settings.js
│       └── history.js
├── alembic/             # Database migraties
├── tests/               # pytest testsuites
├── deployment/
│   ├── nginx/           # Nginx configuratie
│   ├── systemd/         # systemd service
│   └── README.md        # Uitgebreide deploy-instructies
├── requirements.txt
└── .env.example
```

## Tests uitvoeren

Vereist een draaiende PostgreSQL-testdatabase. Stel `TEST_DATABASE_URL` in als omgevingsvariabele of gebruik de standaard (`garmin_training_test`).

```bash
# Testdatabase aanmaken
sudo -u postgres createdb garmin_training_test -O garmin

# Tests draaien
venv/bin/pytest tests/ -v
```

## Licentie

MIT
