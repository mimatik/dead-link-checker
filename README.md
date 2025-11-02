# Dead Link Checker

Python web crawler for detecting dead links on websites.

## Features

- ✅ Crawls entire domain (all internal pages)
- ✅ Checks all links (internal and external)
- ✅ Detects dead links (404, 500, timeout, etc.)
- ✅ Colored real-time console output
- ✅ Exports results to CSV file with domain name
- ✅ Configuration via YAML file
- ✅ Smart error detection (ignores false positives)
- ✅ Crawling progress statistics

## Quick Start

1. **Setup:**
```bash
git clone git@github.com:mimatik/dead-link-checker.git
cd dead-link-checker
curl -LsSf https://astral.sh/uv/install.sh | sh  # Install uv
uv sync  # Install dependencies
```

2. **Run via CLI:**
```bash
# Using a config file
uv run python cli.py crawl --config-id example

# Using a direct URL
uv run python cli.py crawl --url https://example.com

# List available configs
uv run python cli.py list-configs
```

3. **Run via API + Web UI:**

**Development mode (with hot reload):**
```bash
# Terminal 1: Start Flask API server (port 5555 kvůli AirPlay na Macu)
uv run flask --app app --debug run --port 5555

# Terminal 2: Start Vite dev server
cd frontend
npm run dev
# Open http://localhost:5173
```

**Production mode (single server):**
```bash
# Build frontend
cd frontend && npm run build && cd ..

# Start Flask (serves API + built frontend)
uv run flask --app app run --port 5555
# Open http://localhost:5555
```

4. **Results:** `reports/dead_links_report_DOMAIN_TIMESTAMP.csv`

## Development

This project uses [uv](https://docs.astral.sh/uv/) for fast dependency management and Python environment handling.

### Project Structure

```
dead_link_crawler/
├── app/
│   ├── core/
│   │   ├── crawler.py      # Core crawling logic
│   │   ├── config_store.py # Config CRUD operations
│   │   └── jobs.py         # Job management
│   ├── api/
│   │   └── routes.py       # Flask API endpoints
│   └── __init__.py         # Flask app factory
├── cli.py                  # CLI interface
├── custom_config_json/     # JSON configurations
├── reports/                # Generated CSV reports
└── .data/                  # Job state persistence
```

### Commands

**Backend:**
```bash
# Install Python dependencies
uv sync

# Install with dev dependencies (for linting)
uv sync --extra dev

# Run CLI
uv run python cli.py crawl --config-id example

# Run API server
uv run flask --app app run

# Run in development mode with auto-reload
uv run flask --app app --debug run

# Lint code with ruff
uv run ruff check app/ cli.py

# Add new Python dependencies
uv add package-name

# Update Python dependencies
uv lock --upgrade
```

**Frontend:**
```bash
cd frontend

# Install dependencies (first time only)
npm install

# Run development server
npm run dev

# Build for production
npm run build

# Preview production build
npm run preview
```

## Configuration

Configurations are stored as JSON files in `custom_config_json/` directory.

### Creating a Configuration

Create a new JSON file in `custom_config_json/`:

```json
{
  "name": "My Website",
  "start_url": "https://mywebsite.com",
  "timeout": 15,
  "delay": 0.5,
  "max_depth": null,
  "output_dir": "reports",
  "show_skipped_links": false,
  "whitelist_codes": [403, 999],
  "domain_rules": {
    "linkedin.com": {
      "allowed_codes": [999, 429],
      "description": "LinkedIn rate limiting"
    },
    "twitter.com": {
      "allowed_codes": [403],
      "description": "Twitter access restriction"
    }
  }
}
```

### Configuration Options

- `start_url` (required): Starting URL for the crawl
- `timeout`: Request timeout in seconds (default: 15)
- `delay`: Delay between requests in seconds (default: 0.5)
- `max_depth`: Maximum crawl depth, null for unlimited (default: null)
- `output_dir`: Directory for reports (default: "reports")
- `show_skipped_links`: Show skipped links in output (default: false)
- `whitelist_codes`: HTTP status codes to treat as non-errors
- `domain_rules`: Domain-specific rules for handling certain sites

### Using Configurations

**CLI:**
```bash
uv run python cli.py crawl --config-id mywebsite
uv run python cli.py list-configs
uv run python cli.py show-config mywebsite
```

**API:**
```bash
# List configs
curl http://localhost:5000/api/configs

# Get config
curl http://localhost:5000/api/configs/mywebsite

# Start crawl with config
curl -X POST http://localhost:5000/api/crawl \
  -H "Content-Type: application/json" \
  -d '{"configId": "mywebsite"}'
```

## Output

```
🔍 Crawling [1/3]: https://example.com
✓ OK: https://example.com/about
✗ ERROR [HTTP 404]: https://example.com/old-page
⚠ WARNING [301]: https://example.com/redirect

📊 STATISTICS:
   Pages crawled: 15
   Links checked: 127
   Errors found: 3
```

## CSV Report

| Column | Description |
|--------|-------------|
| error_type | Error type (HTTP 404, Timeout, etc.) |
| link_url | URL of the problematic link |
| link_text | Link text |
| source_page | Page where the link is located |

## Web UI

Modern React-based web interface with:

- **Dashboard** - View recent jobs and their status with live updates
- **Configurations** - Create, edit, and manage crawl configurations
- **Run Crawl** - Select a configuration and start a new crawl
- **Reports** - Browse and download generated CSV reports

The UI automatically refreshes job statuses and provides real-time feedback.

## API Endpoints

### Configurations
- `GET /api/configs` - List all configurations
- `GET /api/configs/:id` - Get configuration by ID
- `POST /api/configs` - Create new configuration
- `PUT /api/configs/:id` - Update configuration
- `DELETE /api/configs/:id` - Delete configuration

### Jobs
- `POST /api/crawl` - Start new crawl job
- `GET /api/jobs` - List recent jobs
- `GET /api/jobs/:id` - Get job status and details

### Reports
- `GET /api/reports` - List available reports
- `GET /api/reports/:filename` - Download report file

## Deployment

### Production Deployment na Railway

Aplikace je připravená pro deployment na Railway s Docker kontejnerizací.

**Quick Start:**

1. Vytvoř Railway účet a nainstaluj CLI
2. Vytvoř Railway projekt a volume (`/data`, 1GB)
3. Nastav environment variables (viz níže)
4. Propoj GitHub repo s Railway
5. Vytvoř GitHub secret `RAILWAY_TOKEN`
6. Push do branch `build_flask_react_railway`

**Environment Variables (Railway Dashboard):**

```bash
FLASK_APP=app:create_app
FLASK_ENV=production
PYTHON_VERSION=3.11
AUTH_USERNAME=preview        # Změň!
AUTH_PASSWORD=pl34s3         # Změň!
```

**HTTP Basic Authentication:**

V production je aplikace chráněna HTTP Basic Auth s credentials z environment variables.

**Detailní instrukce:** Viz [DEPLOYMENT.md](DEPLOYMENT.md)

### Docker Build Lokálně

```bash
# Build image
docker build -t dead-link-crawler .

# Run container
docker run -p 5555:5555 \
  -e FLASK_ENV=production \
  -e AUTH_USERNAME=preview \
  -e AUTH_PASSWORD=pl34s3 \
  dead-link-crawler

# Test
curl -u preview:pl34s3 http://localhost:5555/api/configs
```

### CI/CD

GitHub Actions automaticky deployne na Railway při push do `build_flask_react_railway`:
- Lint Python kódu (ruff)
- Lint frontend kódu (eslint)
- Build frontend
- Deploy na Railway

## Tips

- **Large websites:** Use `delay: 1-2` seconds
- **Testing:** Set `max_depth: 2` for faster results
- **Interruption:** CTRL+C saves partial report (CLI only)
- **Production:** HTTP Basic Auth je aktivní pouze když `FLASK_ENV=production`

## License

MIT License - Free to use.