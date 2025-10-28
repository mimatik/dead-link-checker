# Dead Link Checker

Standalone Python web crawler for detecting dead links on websites.

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

1. **Navigate to project folder:**
```bash
cd dead_link_crawler
```

2. **Create virtual environment:**
```bash
python3 -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. **Install dependencies:**
```bash
pip install -r requirements.txt
```

4. **Edit config.yaml:**
```bash
nano config.yaml  # or vim, or open in editor
```

Change the line:
```yaml
start_url: "https://your-domain.com"
```

5. **Run crawler:**
```bash
./run
```

Script automatically:
- ✅ Activates virtual environment
- ✅ Checks dependencies
- ✅ Runs crawler

6. **Find results in:**
```
reports/dead_links_report_DOMAIN_YYYYMMDD_HHMMSS.csv
```

## Configuration

Edit the `config.yaml` file:

```yaml
start_url: "https://example.com"  # URL to start crawling from
timeout: 15                        # Timeout for HTTP requests (seconds)
delay: 1.0                         # Delay between requests (seconds)
max_depth: null                    # Maximum crawling depth (null = unlimited)
output_dir: "reports"              # Directory for CSV reports
show_skipped_links: false          # Show skipped links in console output

# HTTP codes that are not errors (page exists but access restricted)
whitelist_codes: [401, 403, 429, 451, 999]

# Domain-specific rules for known platforms
domain_rules:
  linkedin.com:
    allowed_codes: [999, 429]
    description: "LinkedIn rate limiting"
  twitter.com:
    allowed_codes: [403]
    description: "Twitter access restriction"
  mckinsey.com:
    allowed_codes: [429]
    description: "McKinsey rate limiting"
    ignore_timeouts: true
```

### Parameters

- **start_url**: Starting URL for crawling (required)
- **timeout**: Maximum time to wait for server response in seconds
- **delay**: Delay between requests (respecting the server)
- **max_depth**: Maximum crawling depth (null = crawl entire domain)
- **output_dir**: Directory where CSV reports are saved
- **show_skipped_links**: Whether to display skipped links in console output
- **whitelist_codes**: HTTP codes that are not considered errors globally
- **domain_rules**: Specific rules for individual domains

## Example Output

```
============================================================
                   Dead Link Checker                      
============================================================

ℹ Starting crawl from: https://example.com
ℹ Domain: example.com
ℹ Max depth: Unlimited

🔍 Crawling [1/3]: https://example.com
ℹ Found 25 links on this page
✓ OK: https://example.com/about
✓ OK: https://example.com/contact
✓ OK: LinkedIn rate limiting (999): https://linkedin.com/in/profile
✓ OK: Twitter access restriction (403): https://twitter.com/intent/tweet?url=...
✗ ERROR [HTTP 404]: https://example.com/old-page
⚠ WARNING [301]: https://example.com/redirect

============================================================
📊 STATISTICS:
   Pages crawled: 15
   Links checked: 127
   Errors found: 3
============================================================
ℹ Report saved to: reports/dead_links_report_example_com_20251027_143022.csv
```

## CSV Report

The CSV file contains the following columns:

| Column | Description |
|--------|-------------|
| **error_type** | Error type (HTTP 404, HTTP 500, Timeout, Connection Error, etc.) |
| **link_url** | URL of the problematic link |
| **link_text** | Link text (anchor text) |
| **source_page** | URL of the page where the link is located |

Example:
```csv
error_type,link_url,link_text,source_page
HTTP 404,https://example.com/old-page,Old Page,https://example.com/
Timeout,https://slow-site.com,External Link,https://example.com/about
Connection Error,https://broken-site.com,Broken,https://example.com/contact
```

## Advanced Configuration

### Whitelist Codes
These HTTP codes indicate the page exists but has access restrictions:
- **401**: Unauthorized (paywall, login required)
- **403**: Forbidden (geo-blocking, bot protection)
- **429**: Too Many Requests (rate limiting)
- **451**: Unavailable For Legal Reasons (geo-blocking)
- **999**: LinkedIn Rate Limiting (LinkedIn-specific)

### Domain Rules
You can define specific rules for individual domains:

```yaml
domain_rules:
  linkedin.com:
    allowed_codes: [999, 429]
    description: "LinkedIn rate limiting"
  reuters.com:
    allowed_codes: [401]
    description: "Reuters access restriction"
  mckinsey.com:
    allowed_codes: [429]
    description: "McKinsey rate limiting"
    ignore_timeouts: true  # Ignore timeout errors for this domain
```

## Usage Examples

### Production Website (careful approach)
```yaml
start_url: "https://www.mysite.com"
timeout: 15
delay: 1.5  # Longer delay for prod server
max_depth: null
output_dir: "reports"
```

### Quick Testing (main pages only)
```yaml
start_url: "https://www.mysite.com"
timeout: 5
delay: 0.2
max_depth: 2  # Only 2 levels deep
output_dir: "reports"
```

### Local Development Server
```yaml
start_url: "http://localhost:8000"
timeout: 5
delay: 0.1  # No delay for local
max_depth: null
output_dir: "reports"
```

## Tips and Recommendations

1. **For large websites** use higher `delay` (1-2 seconds) to avoid overloading the server
2. **For testing** you can use lower `max_depth` for faster results
3. **CSV reports** can be opened in Excel, Google Sheets or processed programmatically
4. **For errors** try increasing `timeout` if server responds slowly
5. **Interruption**: CTRL+C - crawler saves partial report

## Technical Details

### How it works

1. **Crawling**: Script starts at `start_url` and traverses all found internal links (same domain)
2. **Link checking**: Every found link (internal and external) is checked with HTTP request
3. **Error detection**: Links with error codes (4xx, 5xx) or network errors are recorded
4. **Smart filtering**: Applies whitelist codes and domain rules to reduce false positives
5. **Reporting**: All found errors are saved to CSV file with domain name

### Detected Errors

- **HTTP 4xx**: Client errors (404 Not Found, 403 Forbidden, etc.)
- **HTTP 5xx**: Server errors (500 Internal Server Error, 503 Service Unavailable, etc.)
- **Timeout**: Server didn't respond within time limit
- **Connection Error**: Cannot establish connection to server
- **Too Many Redirects**: Too many redirects
- **Request Error**: Other HTTP request errors

### Technology

- **Python 3.6+**
- **requests** - HTTP requests
- **BeautifulSoup4** - HTML parsing
- **PyYAML** - Configuration reading
- **colorama** - Colored console output

## License

Free to use.