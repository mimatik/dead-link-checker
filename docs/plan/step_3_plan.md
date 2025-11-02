# Railway Docker Deployment & CI/CD

## Přehled

Tento plán pokrývá kompletní setup Docker kontejnerizace, Railway deployment s persistent storage a GitHub Actions CI/CD pipeline s automatickým deploymentem.

## Fáze 1: Příprava aplikace pro production

### 1.1 HTTP Basic Authentication

Přidat Flask middleware pro HTTP Basic Auth ochranu celé aplikace.

**Soubor:** `app/__init__.py`

```python
from flask_httpauth import HTTPBasicAuth
from werkzeug.security import check_password_hash, generate_password_hash

auth = HTTPBasicAuth()

users = {
    os.environ.get("AUTH_USERNAME", "preview"): generate_password_hash(
        os.environ.get("AUTH_PASSWORD", "pl34s3")
    )
}

@auth.verify_password
def verify_password(username, password):
    if username in users and check_password_hash(users.get(username), password):
        return username

# Aplikovat na všechny routes
@app.before_request
def require_auth():
    if os.environ.get("FLASK_ENV") == "production":
        auth.login_required()
```

**Nové dependency:** Přidat `flask-httpauth` do `pyproject.toml`

### 1.2 Konfigurace pro Railway volumes

Upravit `app/core/config.py` pro podporu Railway persistent storage.

```python
# Detect Railway environment
IS_RAILWAY = os.environ.get("RAILWAY_ENVIRONMENT") is not None

if IS_RAILWAY:
    # Use Railway volume mount
    VOLUME_PATH = "/data"
    CONFIG_DIR = os.path.join(VOLUME_PATH, "custom_config_json")
    REPORTS_DIR = os.path.join(VOLUME_PATH, "reports")
    DATA_DIR = os.path.join(VOLUME_PATH, ".data")
else:
    # Local development paths
    CONFIG_DIR = os.path.join(PROJECT_ROOT, "custom_config_json")
    REPORTS_DIR = os.path.join(PROJECT_ROOT, "reports")
    DATA_DIR = os.path.join(PROJECT_ROOT, ".data")
```

### 1.3 Gunicorn production server config

Vytvořit `gunicorn.conf.py` pro production WSGI server:

```python
bind = f"0.0.0.0:{os.environ.get('PORT', '5555')}"
workers = 2
worker_class = "sync"
timeout = 120
keepalive = 5
errorlog = "-"
accesslog = "-"
loglevel = "info"
```

## Fáze 2: Docker kontejnerizace

### 2.1 Vytvořit Dockerfile

Multi-stage build pro optimální image size s uv package managerem.

**Soubor:** `Dockerfile`

```dockerfile
# Stage 1: Frontend build
FROM node:20-alpine AS frontend-builder
WORKDIR /app/frontend
COPY frontend/package*.json ./
RUN npm ci
COPY frontend/ ./
RUN npm run build

# Stage 2: Python app
FROM python:3.11-slim
WORKDIR /app

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv

# Copy Python dependencies
COPY pyproject.toml uv.lock ./
RUN uv sync --frozen --no-dev

# Copy application code
COPY app/ ./app/
COPY cli.py ./

# Copy built frontend
COPY --from=frontend-builder /app/frontend/dist ./frontend/dist

# Create volume mount point
RUN mkdir -p /data

# Expose port
EXPOSE 5555

# Start with gunicorn
CMD ["uv", "run", "gunicorn", "-c", "gunicorn.conf.py", "app:create_app()"]
```

### 2.2 Vytvořit .dockerignore

```
node_modules/
frontend/node_modules/
frontend/dist/
__pycache__/
*.pyc
.git/
.data/
reports/
custom_config_json/*.json
!custom_config_json/example.json
.env
```

### 2.3 Testovat Docker build lokálně

```bash
docker build -t dead-link-crawler .
docker run -p 5555:5555 \
  -e FLASK_ENV=production \
  -e AUTH_USERNAME=preview \
  -e AUTH_PASSWORD=pl34s3 \
  dead-link-crawler
```

## Fáze 3: Railway setup (MANUÁLNÍ KROKY)

### 3.1 Railway account a CLI setup

**MANUÁLNÍ:**

1. Vytvořit account na https://railway.app
2. Nainstalovat Railway CLI:
   ```bash
   npm install -g @railway/cli
   # nebo
   brew install railway
   ```

3. Login do Railway:
   ```bash
   railway login
   ```


### 3.2 Vytvořit Railway projekt

**MANUÁLNÍ:**

```bash
railway init
# Zadej název projektu: "dead-link-crawler"
```

### 3.3 Vytvořit Railway volume

**MANUÁLNÍ:**

1. V Railway dashboardu: Project Settings → Volumes
2. Klikni "New Volume"
3. Mount path: `/data`
4. Size: 1GB (nebo dle potřeby)

### 3.4 Nastavit environment variables v Railway

**MANUÁLNÍ - v Railway dashboardu (Variables tab):**

```
FLASK_APP=app:create_app
FLASK_ENV=production
PYTHON_VERSION=3.11
AUTH_USERNAME=preview
AUTH_PASSWORD=pl34s3
```

### 3.5 Propojit GitHub repository

**MANUÁLNÍ:**

1. Railway dashboard → Settings → Connect Repo
2. Vybrat GitHub repository
3. Nastavit deploy branch: `deploy_railway`
4. Railway automaticky detekuje Dockerfile

## Fáze 4: GitHub Actions CI/CD

### 4.1 Vytvořit workflow pro CI/CD

**Soubor:** `.github/workflows/railway-deploy.yml`

```yaml
name: Railway Deploy

on:
  push:
    branches:
         - deploy_railway

jobs:
  lint-and-test:
    runs-on: ubuntu-latest
    steps:
         - uses: actions/checkout@v4
      
         - name: Install uv
        uses: astral-sh/setup-uv@v2
      
         - name: Set up Python
        run: uv python install 3.11
      
         - name: Install dependencies
        run: uv sync
      
         - name: Lint Python code
        run: uv run ruff check app/ cli.py
      
         - name: Setup Node.js
        uses: actions/setup-node@v4
        with:
          node-version: '20'
      
         - name: Install frontend dependencies
        run: |
          cd frontend
          npm ci
      
         - name: Lint frontend
        run: |
          cd frontend
          npm run lint
      
         - name: Build frontend
        run: |
          cd frontend
          npm run build

  deploy:
    needs: lint-and-test
    runs-on: ubuntu-latest
    steps:
         - uses: actions/checkout@v4
      
         - name: Install Railway CLI
        run: npm install -g @railway/cli
      
         - name: Deploy to Railway
        env:
          RAILWAY_TOKEN: ${{ secrets.RAILWAY_TOKEN }}
        run: railway up --detach
```

### 4.2 Získat Railway API token (MANUÁLNÍ)

**MANUÁLNÍ:**

1. Railway dashboard → Account Settings → Tokens
2. Klikni "Create Token"
3. Zkopíruj token
4. V GitHub repo: Settings → Secrets → Actions
5. Vytvoř nový secret: `RAILWAY_TOKEN` = [zkopírovaný token]

### 4.3 Vytvořit branch pro deployment (MANUÁLNÍ)

**MANUÁLNÍ:**

```bash
git checkout -b deploy_railway
git push -u origin deploy_railway
```

## Fáze 5: Railway nixpacks config (optional)

### 5.1 Vytvořit railway.toml

Pro explicitní Railway konfiguraci (optional, Dockerfile má prioritu):

**Soubor:** `railway.toml`

```toml
[build]
builder = "dockerfile"
dockerfilePath = "Dockerfile"

[deploy]
startCommand = "uv run gunicorn -c gunicorn.conf.py 'app:create_app()'"
healthcheckPath = "/api/configs"
healthcheckTimeout = 100
restartPolicyType = "on_failure"
restartPolicyMaxRetries = 3
```

## Fáze 6: Dokumentace

### 6.1 Aktualizovat README.md

Přidat sekci "Deployment" s Railway instrukcemi a production environment variables.

### 6.2 Vytvořit DEPLOYMENT.md

Detailní deployment guide pro budoucí reference.

## Co budeš muset udělat RUČNĚ:

1. **Railway Account Setup** (Fáze 3.1)

      - Registrace na railway.app
      - Instalace Railway CLI
      - Login přes CLI

2. **Railway Project Creation** (Fáze 3.2)

      - Vytvořit nový projekt přes CLI nebo dashboard

3. **Railway Volume Setup** (Fáze 3.3)

      - V dashboardu vytvořit volume s mount path `/data`

4. **Environment Variables** (Fáze 3.4)

      - Nastavit všechny env vars v Railway dashboardu

5. **GitHub Connection** (Fáze 3.5)

      - Propojit Railway projekt s GitHub repo
      - Nastavit deploy branch na `deploy_railway`

6. **Railway API Token** (Fáze 4.2)

      - Vygenerovat token v Railway
      - Přidat jako GitHub secret `RAILWAY_TOKEN`

7. **Create Deploy Branch** (Fáze 4.3)

      - Vytvořit a pushnout branch `deploy_railway`

8. **První Deploy Test**

      - Po pushnu do nové branch zkontrolovat GitHub Actions log
      - Zkontrolovat Railway deployment log
      - Otestovat URL z Railway dashboardu (mělo by vyžadovat HTTP auth)

## Co udělám já (automatizovaně):

- Přidat HTTP Basic Auth do Flask app
- Upravit config.py pro Railway volumes
- Vytvořit gunicorn.conf.py
- Vytvořit Dockerfile s multi-stage build
- Vytvořit .dockerignore
- Vytvořit GitHub Actions workflow
- Vytvořit railway.toml (optional config)
- Aktualizovat README.md s deployment instrukcemi
- Vytvořit DEPLOYMENT.md guide

## Poznámky:

- Railway automaticky přidělí URL ve formátu `https://dead-link-crawler-production.up.railway.app`
- HTTP Basic Auth bude aktivní pouze v production (FLASK_ENV=production)
- Volumes zajistí, že konfigurace a reporty přežijí restart containeru
- První deploy může trvat 3-5 minut (build + deploy)
- Railway má free tier s omezeními (500 hodin/měsíc, pak $5/měsíc)