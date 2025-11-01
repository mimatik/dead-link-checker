# JSON Configuration Files

This directory contains JSON configuration files for the dead link crawler.

## Configuration Format

Each JSON file should have the following structure:

```json
{
  "name": "Configuration Name",
  "start_url": "https://example.com",
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
    }
  }
}
```

## Fields

- **name**: Human-readable name for the configuration
- **start_url**: Starting URL for the crawl (required)
- **timeout**: Request timeout in seconds (default: 15)
- **delay**: Delay between requests in seconds (default: 0.5)
- **max_depth**: Maximum crawl depth, null for unlimited (default: null)
- **output_dir**: Directory for reports (default: "reports")
- **show_skipped_links**: Show skipped links in output (default: false)
- **whitelist_codes**: HTTP status codes to treat as non-errors
- **domain_rules**: Domain-specific rules for handling certain sites

## Usage

### CLI
```bash
uv run python cli.py crawl --config-id example
uv run python cli.py list-configs
uv run python cli.py show-config example
```

### API
```bash
curl http://localhost:5000/api/configs
curl http://localhost:5000/api/configs/example
```

