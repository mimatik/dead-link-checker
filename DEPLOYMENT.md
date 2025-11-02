# Deployment Guide - Railway

Tento dokument obsahuje detailní instrukce pro deployment aplikace Dead Link Crawler na Railway.

## Přehled

Aplikace je kontejnerizovaná s Docker a používá:
- **Frontend**: React + Vite (build při Docker build)
- **Backend**: Flask + Gunicorn (WSGI server)
- **Package Manager**: uv (fast Python package manager)
- **Persistent Storage**: Railway volumes pro konfigurace, reporty a job data
- **Authentication**: HTTP Basic Auth (pouze v production)
- **CI/CD**: GitHub Actions pro automatický deployment

## Požadavky

- Railway account (https://railway.app)
- Railway CLI nainstalované
- GitHub repository s projektem
- Docker (pro lokální testování)

## Krok 1: Railway Account a CLI Setup

### 1.1 Vytvořit Railway účet

Jdi na https://railway.app a zaregistruj se (můžeš použít GitHub account).

### 1.2 Nainstalovat Railway CLI

```bash
# macOS (Homebrew)
brew install railway

# nebo npm
npm install -g @railway/cli
```

### 1.3 Login do Railway

```bash
railway login
```

Otevře se browser pro autorizaci.

## Krok 2: Vytvořit Railway Projekt

```bash
# V root adresáři projektu
railway init

# Railway CLI se zeptá:
# - Project name: zadej "dead-link-crawler" (nebo jiný název)
# - Environment: vyber "production"
```

Alternativně můžeš vytvořit projekt přímo v Railway dashboardu.

## Krok 3: Nastavit Railway Volume

Railway volumes poskytují persistent storage, který přežije restart containeru.

**V Railway Dashboard:**

1. Otevři projekt v Railway dashboard
2. Klikni na "Settings" → "Volumes"
3. Klikni "New Volume"
4. Nastav:
   - **Mount Path**: `/data`
   - **Size**: 1 GB (nebo dle potřeby)
5. Klikni "Create"

## Krok 4: Nastavit Environment Variables

**V Railway Dashboard → Variables:**

Přidej následující environment variables:

```bash
# Flask configuration
FLASK_APP=app:create_app
FLASK_ENV=production
PYTHON_VERSION=3.11

# HTTP Basic Authentication
AUTH_USERNAME=preview
AUTH_PASSWORD=pl34s3

# Railway automaticky nastaví:
# - PORT (internal)
# - RAILWAY_ENVIRONMENT (automatic)
```

**Poznámka**: Změň `AUTH_USERNAME` a `AUTH_PASSWORD` na vlastní hodnoty!

## Krok 5: Propojit GitHub Repository

**V Railway Dashboard:**

1. Otevři projekt
2. Jdi na "Settings" → "Source"
3. Klikni "Connect Repo"
4. Vyber GitHub repository
5. Nastav:
   - **Branch**: `deploy_railway`
   - **Auto-deploy**: Zapnuto (Railway automaticky detekuje Dockerfile)

Railway automaticky vytvoří webhook v GitHub repository.

## Krok 6: GitHub Actions CI (Volitelné)

> **ℹ️ Poznámka:** Railway automaticky deployuje při detekci změn v repozitáři pomocí GitHub integration (nastavena v Kroku 5), takže **není potřeba RAILWAY_TOKEN** ani deploy step v GitHub Actions.

GitHub Actions workflow `.github/workflows/lint-and-test.yml` automaticky:
1. ✅ Lintuje Python kód (ruff)
2. ✅ Lintuje frontend kód (ESLint)
3. ✅ Testuje frontend build

**Deploy probíhá přímo z Railway**, ne z GitHub Actions.

## Krok 7: Vytvořit Deploy Branch a Push

```bash
# Vytvoř novou branch pro deployment
git checkout -b deploy_railway

# Push do remote repository
git push -u origin deploy_railway
```

Tento push:
1. ✅ Spustí GitHub Actions (lint & test)
2. ✅ Railway automaticky detekuje změny a spustí build + deploy

## Krok 8: Monitorování Deployment

### 8.1 GitHub Actions Log (CI pouze)

V GitHub repository:
- Jdi na "Actions" tab
- Sleduj běžící workflow "Lint and Test"
- Zkontroluj, že všechny lint kroky proběhly úspěšně

### 8.2 Railway Deployment Log (Hlavní Deploy)

V Railway Dashboard:
- Otevři projekt
- Sleduj "Deployments" tab
- První build může trvat 3-5 minut (multi-stage Docker build)

### 8.3 Získat Application URL

Railway automaticky přidělí URL:
- V Railway Dashboard → "Settings" → "Domains"
- Defaultní URL: `https://[project-name]-production.up.railway.app`
- Můžeš přidat vlastní custom domain

## Krok 9: Testování Production Aplikace

### 9.1 HTTP Basic Auth

Aplikace je chráněna HTTP Basic Authentication:

```bash
# Test pomocí curl
curl -u preview:pl34s3 https://[your-railway-url]/api/configs
```

V browseru se zobrazí login dialog.

### 9.2 Ověřit funkčnost

1. **Test health endpoint** (bez autentizace):
   ```bash
   curl https://[your-railway-url]/health
   # Očekávaný výstup: {"status":"healthy","service":"dead-link-crawler"}
   ```

2. Otevři Railway URL v browseru
3. Zadej username a password (z environment variables)
4. Zkontroluj, že se načítá frontend
5. Vytvoř testovací konfiguraci
6. Spusť crawl job
7. Ověř, že se job zobrazuje na dashboardu

### 9.3 Ověřit persistent storage

Data v `/data` volume by měla přežít restart containeru:

1. Vytvoř konfiguraci v UI
2. V Railway dashboard → "Deployments" → klikni "Restart"
3. Zkontroluj, že konfigurace stále existuje

## Troubleshooting

### Build Fails

**Problem**: Docker build failuje

**Řešení**:
- Zkontroluj Railway build logs
- Ověř, že všechny soubory existují (Dockerfile, gunicorn.conf.py, atd.)
- Zkus build lokálně: `docker build -t test .`

### Application Won't Start

**Problem**: Container startuje, ale aplikace nefunguje

**Řešení**:
- Zkontroluj Railway deployment logs
- Ověř environment variables (zvlášť `FLASK_APP`)
- Zkontroluj, že PORT není hardcoded (Railway nastaví dynamicky)

### Healthcheck Fails

**Problem**: Deployment failuje s "healthcheck failed" nebo "service unavailable"

**Řešení**:
- Railway healthcheck endpoint: `/health` (bez autentizace)
- Ověř v logs, že aplikace naslouchá na správném PORT
- Railway používá hostname `healthcheck.railway.app` - musí být povolen
- Test lokálně: `curl http://localhost:5555/health`
- Zkontroluj `railway.toml`: `healthcheckPath = "/health"`
- Default timeout je 100 sekund, můžeš zvýšit v `railway.toml`

### Volume Data Not Persisting

**Problem**: Data se ztrácí při restartu

**Řešení**:
- Ověř, že volume je správně připojený na `/data`
- Zkontroluj, že `RAILWAY_ENVIRONMENT` env var je nastavená (automaticky)
- V logs zkontroluj, že aplikace používá správnou cestu

### HTTP 401 Unauthorized

**Problem**: Nelze se přihlásit

**Řešení**:
- Ověř `AUTH_USERNAME` a `AUTH_PASSWORD` environment variables
- Zkontroluj, že `FLASK_ENV=production` je nastaveno
- Zkus default credentials: `preview` / `pl34s3`

### GitHub Actions Fails

**Problem**: Deployment workflow failuje

**Řešení**:
- Ověř, že `RAILWAY_TOKEN` secret je správně nastavený
- Zkontroluj GitHub Actions logs
- Ověř, že Railway CLI má přístup k projektu

## Lokální Docker Testing

Před deployment na Railway můžeš otestovat Docker build lokálně:

```bash
# Build image
docker build -t dead-link-crawler .

# Run container
docker run -p 5555:5555 \
  -e FLASK_ENV=production \
  -e AUTH_USERNAME=preview \
  -e AUTH_PASSWORD=pl34s3 \
  -e PORT=5555 \
  dead-link-crawler

# Test
curl -u preview:pl34s3 http://localhost:5555/api/configs
```

## Continuous Deployment

Po initial setup:

1. Pushni změny do `deploy_railway` branch
2. GitHub Actions automaticky spustí lint + test
3. Railway automaticky detekuje změny a deployne
4. Railway rebuillde Docker image a restartuje aplikaci

## Costs

Railway free tier:
- 500 hours/měsíc zdarma
- Po překročení: $5/měsíc za základní plan
- Volume storage: zdarma do 1 GB

## Další Kroky

- **Custom Domain**: Přidat vlastní doménu v Railway Settings
- **Monitoring**: Integrovat logging service (Railway má built-in logs)
- **Backups**: Nastavit pravidelné backupy volume dat
- **Scaling**: Zvýšit počet gunicorn workers pro větší traffic

## Reference

- Railway Documentation: https://docs.railway.app
- Railway CLI: https://docs.railway.app/develop/cli
- Dockerfile Best Practices: https://docs.docker.com/develop/dev-best-practices/

