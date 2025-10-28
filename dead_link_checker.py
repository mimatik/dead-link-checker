#!/usr/bin/env python3
"""
Dead Link Checker - Web Crawler
Crawls a website and checks all links for dead/broken URLs
"""

import csv
import glob
import os
import time
from collections import deque
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urldefrag, urljoin, urlparse

import requests
import yaml
from bs4 import BeautifulSoup
from colorama import Fore, Style, init

# Initialize colorama for cross-platform colored terminal output
init(autoreset=True)


class ConsoleLogger:
    """Handles colored console output for crawler status"""

    def __init__(self):
        self.links_checked = 0
        self.errors_found = 0
        self.pages_crawled = 0

    def success(self, url: str):
        """Log successful link check (200-299)"""
        self.links_checked += 1
        print(f"{Fore.GREEN}✓{Style.RESET_ALL} OK: {url}")

    def warning(self, url: str, status_code: int):
        """Log warning (redirects, etc.)"""
        self.links_checked += 1
        print(f"{Fore.YELLOW}⚠{Style.RESET_ALL} WARNING [{status_code}]: {url}")

    def error(self, url: str, error_type: str):
        """Log error (404, 500, timeout, etc.)"""
        self.links_checked += 1
        self.errors_found += 1
        print(f"{Fore.RED}✗{Style.RESET_ALL} ERROR [{error_type}]: {url}")

    def info(self, message: str):
        """Log informational message"""
        print(f"{Fore.BLUE}ℹ{Style.RESET_ALL} {message}")

    def muted(self, message: str):
        """Log informational message in muted color"""
        print(f"{Style.DIM}{message}{Style.RESET_ALL}")

    def crawling(self, url: str, current: int, total: int):
        """Log currently crawling page"""
        self.pages_crawled = current
        print(
            f"\n{Fore.CYAN}🔍 Crawling [{current}/{total if total else '?'}]: {url}{Style.RESET_ALL}"
        )

    def statistics(self):
        """Print final statistics"""
        print(f"\n{Fore.BLUE}{'=' * 60}{Style.RESET_ALL}")
        print(f"{Fore.BLUE}📊 STATISTICS:{Style.RESET_ALL}")
        print(f"   Pages crawled: {self.pages_crawled}")
        print(f"   Links checked: {self.links_checked}")
        print(f"   Errors found: {Fore.RED}{self.errors_found}{Style.RESET_ALL}")
        print(f"{Fore.BLUE}{'=' * 60}{Style.RESET_ALL}")


class LinkChecker:
    """Checks individual URLs for availability"""

    def __init__(self, timeout: int = 10, config: dict = None):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "DeadLinkChecker/1.0 (Python)"})

        # Load configuration or use defaults
        config = config or {}

        # Define whitelist of HTTP codes that are not actual errors
        # These codes indicate the page exists but has access restrictions
        self.whitelist_codes = set(config.get("whitelist_codes", [403, 999]))

        # Domain-specific rules for known platforms
        default_domain_rules = {
            "linkedin.com": {
                "allowed_codes": {999},  # LinkedIn rate limiting is normal
                "description": "LinkedIn rate limiting",
                "ignore_timeouts": False,
            },
            "twitter.com": {
                "allowed_codes": {403},  # Twitter often returns 403 for embedded links
                "description": "Twitter access restriction",
                "ignore_timeouts": False,
            },
            "x.com": {
                "allowed_codes": {
                    403
                },  # Twitter/X often returns 403 for embedded links
                "description": "X/Twitter access restriction",
                "ignore_timeouts": False,
            },
        }

        # Merge with config domain rules
        config_domain_rules = config.get("domain_rules", {})
        self.domain_rules = {**default_domain_rules, **config_domain_rules}

    def _get_domain(self, url: str) -> str:
        """Extract domain from URL, removing www prefix"""
        parsed_url = urlparse(url)
        domain = parsed_url.netloc.lower()
        return domain[4:] if domain.startswith("www.") else domain

    def check_link(self, url: str) -> Tuple[bool, Optional[int], Optional[str]]:
        """
        Check if a link is accessible

        Returns:
            Tuple of (is_error, status_code, error_message)
        """
        try:
            response = self.session.head(
                url, timeout=self.timeout, allow_redirects=True
            )

            # If HEAD doesn't work, try GET
            if response.status_code == 405 or response.status_code == 404:
                response = self.session.get(
                    url, timeout=self.timeout, allow_redirects=True
                )

            status_code = response.status_code

            # Consider 2xx as success
            if 200 <= status_code < 300:
                return False, status_code, None

            # 3xx redirects are warnings but not errors
            elif 300 <= status_code < 400:
                return False, status_code, f"Redirect {status_code}"

            # Check domain-specific rules first
            domain = self._get_domain(url)

            # Check if this domain has specific rules
            if domain in self.domain_rules:
                domain_rule = self.domain_rules[domain]
                if status_code in domain_rule["allowed_codes"]:
                    # This is not an error for this domain
                    return (
                        False,
                        status_code,
                        f"{domain_rule['description']} ({status_code})",
                    )

            # Check global whitelist
            if status_code in self.whitelist_codes:
                return False, status_code, f"Access restricted ({status_code})"

            # 4xx and 5xx are errors (unless whitelisted above)
            else:
                return True, status_code, f"HTTP {status_code}"

        except requests.exceptions.Timeout:
            # Check if this domain should ignore timeouts
            domain = self._get_domain(url)

            # Check if this domain should ignore timeouts
            if domain in self.domain_rules:
                domain_rule = self.domain_rules[domain]
                if domain_rule.get("ignore_timeouts", False):
                    return (
                        False,
                        None,
                        f"{domain_rule['description']} (timeout ignored)",
                    )

            return True, None, "Timeout"

        except requests.exceptions.ConnectionError:
            return True, None, "Connection Error"

        except requests.exceptions.TooManyRedirects:
            return True, None, "Too Many Redirects"

        except requests.exceptions.RequestException as e:
            return True, None, f"Request Error: {str(e)}"

        except Exception as e:
            return True, None, f"Unknown Error: {str(e)}"


class WebCrawler:
    """Crawls website and checks all links"""

    def __init__(self, start_url: str, config: dict, logger: ConsoleLogger):
        self.start_url = start_url
        self.config = config
        self.logger = logger
        self.link_checker = LinkChecker(
            timeout=config.get("timeout", 10), config=config
        )

        # Parse domain from start URL
        parsed = urlparse(start_url)
        self.domain = f"{parsed.scheme}://{parsed.netloc}"
        self.base_domain = parsed.netloc

        # Track visited and to-visit URLs
        self.visited_pages: Set[str] = set()
        self.to_visit: deque = deque([start_url])
        self.checked_links: Set[str] = set()

        # Store errors for CSV output
        self.errors: List[Dict[str, str]] = []

        # Delay between requests
        self.delay = config.get("delay", 0.5)
        self.max_depth = config.get("max_depth")

        # Display settings
        self.show_skipped_links = config.get("show_skipped_links", False)

    def _should_add_to_queue(self, link_url: str) -> bool:
        """Check if internal link should be added to crawl queue"""
        return self.is_internal_url(link_url) and link_url not in self.visited_pages

    def is_internal_url(self, url: str) -> bool:
        """Check if URL belongs to the same domain"""
        parsed = urlparse(url)
        return parsed.netloc == self.base_domain or parsed.netloc == ""

    def normalize_url(self, url: str, base_url: str) -> Optional[str]:
        """Normalize and validate URL"""
        # Remove fragment
        url, _ = urldefrag(url)

        # Skip empty URLs, anchors, mailto, tel, javascript
        if (
            not url
            or url.startswith("#")
            or url.startswith("mailto:")
            or url.startswith("tel:")
            or url.startswith("javascript:")
        ):
            return None

        # Convert relative URLs to absolute
        absolute_url = urljoin(base_url, url)

        return absolute_url

    def extract_links(self, html: str, base_url: str) -> List[Tuple[str, str]]:
        """
        Extract all links from HTML

        Returns:
            List of tuples (url, link_text)
        """
        soup = BeautifulSoup(html, "html.parser")
        links = []

        for anchor in soup.find_all("a", href=True):
            url = anchor["href"]
            text = anchor.get_text(strip=True) or "[No text]"

            normalized_url = self.normalize_url(url, base_url)
            if normalized_url:
                links.append((normalized_url, text))

        return links

    def crawl(self):
        """Main crawling method"""
        self.logger.info(f"Starting crawl from: {self.start_url}")
        self.logger.info(f"Domain: {self.base_domain}")
        self.logger.info(
            f"Max depth: {self.max_depth if self.max_depth else 'Unlimited'}"
        )

        while self.to_visit:
            current_url = self.to_visit.popleft()

            # Skip if already visited
            if current_url in self.visited_pages:
                continue

            self.visited_pages.add(current_url)

            # Log crawling status
            self.logger.crawling(
                current_url,
                len(self.visited_pages),
                len(self.visited_pages) + len(self.to_visit),
            )

            # Fetch page content
            try:
                response = self.link_checker.session.get(
                    current_url, timeout=self.config.get("timeout", 10)
                )

                if response.status_code != 200:
                    self.logger.warning(current_url, response.status_code)
                    continue

                # Extract all links from page
                links = self.extract_links(response.text, current_url)
                self.logger.info(f"Found {len(links)} links on this page")

                # Check each link
                checked_count = 0
                skipped_count = 0
                for link_url, link_text in links:
                    # Skip if already checked
                    if link_url in self.checked_links:
                        if self.show_skipped_links:
                            self.logger.info(f"⏭ Skipped (already checked): {link_url}")
                        skipped_count += 1
                        continue

                    self.checked_links.add(link_url)
                    checked_count += 1

                    # Check link
                    is_error, status_code, error_message = self.link_checker.check_link(
                        link_url
                    )

                    if is_error:
                        self.logger.error(link_url, error_message)

                        # Store error for CSV
                        self.errors.append(
                            {
                                "error_type": error_message,
                                "link_url": link_url,
                                "link_text": link_text,
                                "source_page": current_url,
                            }
                        )
                    elif 300 <= (status_code or 0) < 400:
                        self.logger.warning(link_url, status_code)
                    else:
                        self.logger.success(link_url)

                    # Add internal links to crawl queue
                    if self._should_add_to_queue(link_url):
                        self.to_visit.append(link_url)

                    # Delay between requests
                    time.sleep(self.delay)

                # Show summary for this page
                if skipped_count > 0:
                    self.logger.muted(
                        f"Summary: {checked_count} checked, {skipped_count} skipped (already checked)"
                    )

            except Exception as e:
                self.logger.error(current_url, f"Crawl error: {str(e)}")
                continue

        self.logger.statistics()

    def save_report(self):
        """Save errors to CSV file"""
        if not self.errors:
            self.logger.info("No errors found - no report generated")
            return

        # Create output directory
        output_dir = self.config.get("output_dir", "reports")
        os.makedirs(output_dir, exist_ok=True)

        # Generate filename with domain and timestamp
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        domain_name = (
            self.base_domain.replace("www.", "").replace(".", "_").replace("-", "_")
        )
        filename = os.path.join(
            output_dir, f"dead_links_report_{domain_name}_{timestamp}.csv"
        )

        # Write CSV
        with open(filename, "w", newline="", encoding="utf-8") as csvfile:
            fieldnames = ["error_type", "link_url", "link_text", "source_page"]
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)

            writer.writeheader()
            for error in self.errors:
                writer.writerow(error)

        self.logger.info(f"Report saved to: {filename}")


def find_custom_configs() -> List[str]:
    """Find all YAML configuration files in custom_config/ directory"""
    custom_config_dir = "custom_config"
    if not os.path.exists(custom_config_dir):
        return []

    # Find all .yaml and .yml files in custom_config directory
    config_files = glob.glob(os.path.join(custom_config_dir, "*.yaml")) + glob.glob(
        os.path.join(custom_config_dir, "*.yml")
    )

    return sorted(config_files)


def select_config() -> str:
    """Allow user to select configuration file"""
    custom_configs = find_custom_configs()

    # If no custom configs found, use default config.yaml
    if not custom_configs:
        print(
            f"{Fore.BLUE}ℹ{Style.RESET_ALL} "
            f"No custom configurations found in custom_config/"
        )
        print(f"{Fore.BLUE}ℹ{Style.RESET_ALL} Using default config.yaml")
        return "config.yaml"

    # Display available configurations
    print(f"{Fore.CYAN}📁 Available configurations:{Style.RESET_ALL}")
    print()

    for i, config_path in enumerate(custom_configs, 1):
        config_name = os.path.basename(config_path)
        print(f"  {i}. {config_name}")

    print(f"  {len(custom_configs) + 1}. Use default config.yaml")
    print()

    # Get user selection
    while True:
        try:
            choice = input(
                f"{Fore.YELLOW}Select configuration "
                f"(1-{len(custom_configs) + 1}): {Style.RESET_ALL}"
            )
            choice_num = int(choice)

            if 1 <= choice_num <= len(custom_configs):
                selected_config = custom_configs[choice_num - 1]
                print(
                    f"{Fore.GREEN}✓{Style.RESET_ALL} "
                    f"Selected: {os.path.basename(selected_config)}"
                )
                return selected_config
            elif choice_num == len(custom_configs) + 1:
                print(f"{Fore.GREEN}✓{Style.RESET_ALL} Using default config.yaml")
                return "config.yaml"
            else:
                print(
                    f"{Fore.RED}Invalid choice. Please enter a number "
                    f"between 1 and {len(custom_configs) + 1}{Style.RESET_ALL}"
                )
        except ValueError:
            print(f"{Fore.RED}Invalid input. Please enter a number{Style.RESET_ALL}")
        except KeyboardInterrupt:
            print(f"\n{Fore.YELLOW}Operation cancelled{Style.RESET_ALL}")
            exit(0)


def load_config(config_path: str = "config.yaml") -> dict:
    """Load configuration from YAML file"""
    try:
        with open(config_path, "r", encoding="utf-8") as f:
            return yaml.safe_load(f)
    except FileNotFoundError:
        print(
            f"{Fore.RED}Error: Configuration file '{config_path}' "
            f"not found{Style.RESET_ALL}"
        )
        exit(1)
    except yaml.YAMLError as e:
        print(f"{Fore.RED}Error parsing configuration file: {e}{Style.RESET_ALL}")
        exit(1)


def main():
    """Main entry point"""
    print(f"{Fore.CYAN}{'=' * 60}")
    print(f"{'Dead Link Checker':^60}")
    print(f"{'=' * 60}{Style.RESET_ALL}\n")

    # Select and load configuration
    config_path = select_config()
    config = load_config(config_path)
    start_url = config.get("start_url")

    if not start_url:
        print(
            f"{Fore.RED}Error: start_url not specified in "
            f"{config_path}{Style.RESET_ALL}"
        )
        exit(1)

    # Initialize logger and crawler
    logger = ConsoleLogger()
    crawler = WebCrawler(start_url, config, logger)

    # Start crawling
    try:
        crawler.crawl()
        crawler.save_report()
    except KeyboardInterrupt:
        print(f"\n\n{Fore.YELLOW}Crawling interrupted by user{Style.RESET_ALL}")
        crawler.save_report()
    except Exception as e:
        print(f"\n\n{Fore.RED}Unexpected error: {e}{Style.RESET_ALL}")
        import traceback

        traceback.print_exc()


if __name__ == "__main__":
    main()
