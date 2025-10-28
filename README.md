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
python3 -m venv venv
```

2. **Configuration:**
```bash
nano config.yaml  # Change start_url
```

3. **Run:**
```bash
./run
```

4. **Results:** `reports/dead_links_report_DOMAIN_TIMESTAMP.csv`

## Configuration

### Basic Settings
```yaml
start_url: "https://your-domain.com"
timeout: 15
delay: 0.5
max_depth: null  # null = unlimited
```

### Custom Configuration
```bash
cp config.yaml custom_config/my-site.yaml
# Edit custom_config/my-site.yaml
# Run ./run and select configuration
```

### Domain Rules (reduce false positives)
```yaml
domain_rules:
  linkedin.com:
    allowed_codes: [999, 429]
    description: "LinkedIn rate limiting"
  twitter.com:
    allowed_codes: [403]
    description: "Twitter access restriction"
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

## Tips

- **Large websites:** Use `delay: 1-2` seconds
- **Testing:** Set `max_depth: 2` for faster results
- **Interruption:** CTRL+C saves partial report

## License

MIT License - Free to use.