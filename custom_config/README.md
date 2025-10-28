# Custom Configurations

This directory contains custom configuration files for the Dead Link Checker.

## Usage

1. Copy an example configuration:
   ```bash
   cp example.yaml my-site.yaml
   ```

2. Edit the configuration file:
   ```bash
   nano my-site.yaml
   ```

3. Run the crawler and select your configuration:
   ```bash
   ./run
   ```

## Available Examples

- `example.yaml` - Basic example configuration
- `examples.yaml` - Comprehensive examples for different scenarios

## Configuration Options

### Basic Settings
- `start_url` - URL to start crawling from
- `timeout` - HTTP request timeout in seconds
- `delay` - Delay between requests in seconds
- `max_depth` - Maximum crawling depth (null = unlimited)
- `output_dir` - Directory for CSV reports
- `show_skipped_links` - Show skipped links in console output

### Advanced Settings
- `whitelist_codes` - HTTP codes that are not considered errors
- `domain_rules` - Specific rules for individual domains

## Notes

- If `start_url` is not specified, the program will prompt for domain
- All settings are optional and will use built-in defaults if not specified
- Domain rules help reduce false positives for known platforms
