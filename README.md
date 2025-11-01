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
```bash
# Start Flask API server
uv run flask --app app run

# API will be available at http://localhost:5000
# Web UI (after frontend setup) at http://localhost:5000
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

```bash
# Install dependencies
uv sync

# Run CLI
uv run python cli.py crawl --config-id example

# Run API server
uv run flask --app app run

# Run in development mode with auto-reload
uv run flask --app app --debug run

# Add new dependencies
uv add package-name

# Update dependencies
uv lock --upgrade
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

## Tips

- **Large websites:** Use `delay: 1-2` seconds
- **Testing:** Set `max_depth: 2` for faster results
- **Interruption:** CTRL+C saves partial report (CLI only)

## License

MIT License - Free to use.