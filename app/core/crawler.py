"""Core crawler logic - extracted from original dead_link_checker.py"""

import csv
import os
import time
from collections import deque
from datetime import datetime
from typing import Dict, List, Optional, Set, Tuple
from urllib.parse import urldefrag, urljoin, urlparse

import requests
from bs4 import BeautifulSoup


class LinkChecker:
    """Checks individual URLs for availability"""

    def __init__(self, timeout: int = 10, config: dict = None):
        self.timeout = timeout
        self.session = requests.Session()
        self.session.headers.update({"User-Agent": "DeadLinkChecker/1.0 (Python)"})

        # Load configuration or use defaults
        config = config or {}

        # Define whitelist of HTTP codes that are not actual errors
        self.whitelist_codes = set(config.get("whitelist_codes", [403, 999]))

        # Domain-specific rules for known platforms
        default_domain_rules = {
            "linkedin.com": {
                "allowed_codes": {999},
                "description": "LinkedIn rate limiting",
                "ignore_timeouts": False,
            },
            "twitter.com": {
                "allowed_codes": {403},
                "description": "Twitter access restriction",
                "ignore_timeouts": False,
            },
            "x.com": {
                "allowed_codes": {403},
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
            domain = self._get_domain(url)
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

    def __init__(self, start_url: str, config: dict, progress_callback=None):
        self.start_url = start_url
        self.config = config
        self.progress_callback = progress_callback
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

        # Statistics
        self.links_checked = 0
        self.errors_found = 0
        self.pages_crawled = 0

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

    def _emit_progress(self, event_type: str, data: dict):
        """Emit progress event if callback is set"""
        if self.progress_callback:
            self.progress_callback(event_type, data)

    def crawl(self):
        """Main crawling method"""
        self._emit_progress(
            "start",
            {
                "start_url": self.start_url,
                "domain": self.base_domain,
                "max_depth": self.max_depth,
            },
        )

        while self.to_visit:
            current_url = self.to_visit.popleft()

            # Skip if already visited
            if current_url in self.visited_pages:
                continue

            self.visited_pages.add(current_url)
            self.pages_crawled = len(self.visited_pages)

            self._emit_progress(
                "page_crawled",
                {
                    "url": current_url,
                    "pages_crawled": self.pages_crawled,
                    "links_checked": self.links_checked,
                    "errors_found": self.errors_found,
                },
            )

            # Fetch page content
            try:
                response = self.link_checker.session.get(
                    current_url, timeout=self.config.get("timeout", 10)
                )

                if response.status_code != 200:
                    self._emit_progress(
                        "warning",
                        {
                            "url": current_url,
                            "status_code": response.status_code,
                        },
                    )
                    continue

                # Extract all links from page
                links = self.extract_links(response.text, current_url)
                self._emit_progress(
                    "info", {"message": f"Found {len(links)} links on this page"}
                )

                # Check each link
                checked_count = 0
                skipped_count = 0
                for link_url, link_text in links:
                    # Skip if already checked
                    if link_url in self.checked_links:
                        skipped_count += 1
                        continue

                    self.checked_links.add(link_url)
                    checked_count += 1
                    self.links_checked += 1

                    # Check link
                    is_error, status_code, error_message = self.link_checker.check_link(
                        link_url
                    )

                    if is_error:
                        self.errors_found += 1
                        self._emit_progress(
                            "error",
                            {
                                "url": link_url,
                                "error_type": error_message,
                            },
                        )

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
                        self._emit_progress(
                            "warning",
                            {
                                "url": link_url,
                                "status_code": status_code,
                            },
                        )
                    else:
                        self._emit_progress("success", {"url": link_url})

                    # Emit progress update with current stats
                    self._emit_progress(
                        "link_checked",
                        {
                            "pages_crawled": self.pages_crawled,
                            "links_checked": self.links_checked,
                            "errors_found": self.errors_found,
                        },
                    )

                    # Add internal links to crawl queue
                    if self._should_add_to_queue(link_url):
                        self.to_visit.append(link_url)

                    # Delay between requests
                    time.sleep(self.delay)

            except Exception as e:
                self._emit_progress(
                    "error",
                    {
                        "url": current_url,
                        "error_type": f"Crawl error: {str(e)}",
                    },
                )
                continue

        self._emit_progress(
            "complete",
            {
                "pages_crawled": self.pages_crawled,
                "links_checked": self.links_checked,
                "errors_found": self.errors_found,
            },
        )

    def save_report(self) -> Optional[str]:
        """
        Save errors to CSV file

        Returns:
            Path to the report file, or None if no errors
        """
        if not self.errors:
            return None

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

        return filename


def run_crawl(config: dict, progress_callback=None) -> dict:
    """
    Run a crawl with the given configuration

    Args:
        config: Configuration dictionary with start_url and other settings
        progress_callback: Optional callback function(event_type, data)

    Returns:
        Dictionary with crawl results including report_path
    """
    start_url = config.get("start_url")
    if not start_url:
        raise ValueError("start_url is required in config")

    crawler = WebCrawler(start_url, config, progress_callback)
    crawler.crawl()
    report_path = crawler.save_report()

    return {
        "report_path": report_path,
        "pages_crawled": crawler.pages_crawled,
        "links_checked": crawler.links_checked,
        "errors_found": crawler.errors_found,
    }
