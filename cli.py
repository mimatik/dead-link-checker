#!/usr/bin/env python3
"""CLI for dead link crawler"""

import json

import click
from colorama import Fore, Style, init

from app.core import config_store, crawler

# Initialize colorama
init(autoreset=True)


@click.group()
def cli():
    """Dead Link Crawler CLI"""
    pass


@cli.command()
@click.option("--config-id", help="Configuration ID from custom_config_json/")
@click.option("--config-path", help="Path to JSON configuration file")
@click.option("--url", help="URL to crawl (uses default config)")
def crawl(config_id, config_path, url):
    """Run a crawl job"""

    # Load configuration
    if config_id:
        try:
            config = config_store.get_config(config_id)
            click.echo(f"{Fore.GREEN}✓{Style.RESET_ALL} Using config: {config_id}")
        except FileNotFoundError:
            click.echo(
                f"{Fore.RED}✗ Configuration '{config_id}' not found{Style.RESET_ALL}"
            )
            return
    elif config_path:
        try:
            with open(config_path, "r", encoding="utf-8") as f:
                config = json.load(f)
            click.echo(
                f"{Fore.GREEN}✓{Style.RESET_ALL} Using config from: {config_path}"
            )
        except FileNotFoundError:
            click.echo(
                f"{Fore.RED}✗ Config file '{config_path}' not found{Style.RESET_ALL}"
            )
            return
        except json.JSONDecodeError as e:
            click.echo(f"{Fore.RED}✗ Invalid JSON in config file: {e}{Style.RESET_ALL}")
            return
    elif url:
        config = config_store.get_default_config()
        config["start_url"] = url
        click.echo(f"{Fore.GREEN}✓{Style.RESET_ALL} Using URL: {url}")
    else:
        msg = "--config-id, --config-path, or --url"
        click.echo(f"{Fore.RED}✗ Please provide {msg}{Style.RESET_ALL}")
        return

    # Validate config
    if not config.get("start_url"):
        msg = "Configuration must have 'start_url'"
        click.echo(f"{Fore.RED}✗ {msg}{Style.RESET_ALL}")
        return

    # Progress callback for CLI output
    def progress_callback(event_type: str, data: dict):
        if event_type == "start":
            url = data["start_url"]
            click.echo(f"\n{Fore.CYAN}🔍 Starting crawl from: {url}{Style.RESET_ALL}")
            click.echo(f"{Fore.CYAN}Domain: {data['domain']}{Style.RESET_ALL}")
            max_d = data.get("max_depth") or "Unlimited"
            click.echo(f"{Fore.CYAN}Max depth: {max_d}{Style.RESET_ALL}\n")
        elif event_type == "crawling":
            url = data["url"]
            cur = data["current"]
            tot = data["total"]
            click.echo(
                f"\n{Fore.CYAN}🔍 Crawling [{cur}/{tot}]: {url}{Style.RESET_ALL}"
            )
        elif event_type == "success":
            click.echo(f"{Fore.GREEN}✓{Style.RESET_ALL} OK: {data['url']}")
        elif event_type == "warning":
            status = data.get("status_code", "?")
            url = data["url"]
            click.echo(f"{Fore.YELLOW}⚠{Style.RESET_ALL} WARNING [{status}]: {url}")
        elif event_type == "error":
            err = data["error_type"]
            url = data["url"]
            click.echo(f"{Fore.RED}✗{Style.RESET_ALL} ERROR [{err}]: {url}")
        elif event_type == "info":
            msg = data["message"]
            click.echo(f"{Fore.BLUE}ℹ{Style.RESET_ALL} {msg}")
        elif event_type == "complete":
            sep = "=" * 60
            click.echo(f"\n{Fore.BLUE}{sep}{Style.RESET_ALL}")
            click.echo(f"{Fore.BLUE}📊 STATISTICS:{Style.RESET_ALL}")
            click.echo(f"   Pages crawled: {data['pages_crawled']}")
            click.echo(f"   Links checked: {data['links_checked']}")
            errors = data["errors_found"]
            click.echo(f"   Errors found: {Fore.RED}{errors}{Style.RESET_ALL}")
            click.echo(f"{Fore.BLUE}{sep}{Style.RESET_ALL}")

    # Run crawl
    try:
        result = crawler.run_crawl(config, progress_callback)

        if result.get("report_path"):
            path = result["report_path"]
            click.echo(f"\n{Fore.GREEN}✓ Report saved to: {path}{Style.RESET_ALL}")
        else:
            msg = "No errors found - no report generated"
            click.echo(f"\n{Fore.GREEN}✓ {msg}{Style.RESET_ALL}")

    except KeyboardInterrupt:
        msg = "Crawl interrupted by user"
        click.echo(f"\n{Fore.YELLOW}⚠ {msg}{Style.RESET_ALL}")
    except Exception as e:
        click.echo(f"\n{Fore.RED}✗ Error: {e}{Style.RESET_ALL}")


@cli.command()
def list_configs():
    """List available configurations"""
    configs = config_store.list_configs()

    if not configs:
        click.echo(f"{Fore.YELLOW}No configurations found{Style.RESET_ALL}")
        return

    click.echo(f"{Fore.CYAN}Available configurations:{Style.RESET_ALL}\n")
    for config in configs:
        click.echo(f"  • {Fore.GREEN}{config['id']}{Style.RESET_ALL}")
        click.echo(f"    Name: {config.get('name', 'N/A')}")
        click.echo(f"    URL: {config.get('start_url', 'N/A')}")
        click.echo()


@cli.command()
@click.argument("config_id")
def show_config(config_id):
    """Show configuration details"""
    try:
        config = config_store.get_config(config_id)
        click.echo(f"{Fore.CYAN}Configuration: {config_id}{Style.RESET_ALL}\n")
        click.echo(json.dumps(config, indent=2))
    except FileNotFoundError:
        msg = f"Configuration '{config_id}' not found"
        click.echo(f"{Fore.RED}✗ {msg}{Style.RESET_ALL}")


if __name__ == "__main__":
    cli()
