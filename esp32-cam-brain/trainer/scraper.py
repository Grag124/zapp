#!/usr/bin/env python3
"""
trainer/scraper.py — Web scraping module for training images.

Auto-scrapes images from public sources (Wikimedia Commons, Wikipedia)
for target object classes. Runs on a schedule (every 6 hours via cron).

Features:
- Retry logic with exponential backoff
- Rate limiting (respectful to source servers)
- Graceful error handling (continues on individual failures)
- Saves to data/train/<class_name>/

Usage:
    python3 trainer/scraper.py --class water_bottle --limit 50
    python3 trainer/scraper.py --all --limit 100   # scrape all target classes

Target classes: water_bottle, book, pen, toy_car, cell_phone, cup, bowl, spoon
"""

import argparse
import json
import logging
import os
import sys
import time
import random
import urllib.parse
from pathlib import Path
from urllib.request import Request, urlopen
from urllib.error import URLError, HTTPError

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler('training.log'),
        logging.StreamHandler(sys.stdout)
    ]
)
logger = logging.getLogger(__name__)

# Target object classes for the robot brain to recognize
TARGET_CLASSES = [
    "water_bottle", "book", "pen", "toy_car", "cell_phone",
    "cup", "bowl", "spoon", "remote", "keyboard"
]

# Wikimedia Commons API endpoint (public, no API key required)
WIKIMEDIA_API = "https://commons.wikimedia.org/w/api.php"

# User agent — identify ourselves politely to the servers
USER_AGENT = "ESP32-CAM-Robot-Brain-Training/1.0 (educational project)"


def exponential_backoff(attempt: int, base_delay: float = 1.0, max_delay: float = 30.0) -> float:
    """Calculate backoff delay with jitter: base * 2^attempt + random jitter."""
    delay = min(base_delay * (2 ** attempt), max_delay)
    jitter = random.uniform(0, 1.0)
    return delay + jitter


def fetch_with_retry(url: str, max_retries: int = 5, timeout: int = 15):
    """
    Fetch a URL with exponential backoff retry logic.
    Returns the response bytes or None on failure.
    """
    for attempt in range(max_retries):
        try:
            req = Request(url, headers={"User-Agent": USER_AGENT})
            with urlopen(req, timeout=timeout) as resp:
                if resp.status == 200:
                    return resp.read()
                logger.warning("HTTP %d for %s", resp.status, url)
        except HTTPError as e:
            logger.warning("HTTP error %d for %s (attempt %d/%d)",
                           e.code, url, attempt + 1, max_retries)
        except URLError as e:
            logger.warning("URL error for %s: %s (attempt %d/%d)",
                           url, e.reason, attempt + 1, max_retries)
        except Exception as e:
            logger.warning("Unexpected error for %s: %s (attempt %d/%d)",
                           url, e, attempt + 1, max_retries)

        if attempt < max_retries - 1:
            delay = exponential_backoff(attempt)
            logger.info("Retrying in %.1f seconds...", delay)
            time.sleep(delay)

    logger.error("Failed to fetch %s after %d attempts", url, max_retries)
    return None


def search_wikimedia_images(query: str, limit: int = 50):
    """
    Search Wikimedia Commons for images matching a query.
    Returns a list of image URLs.
    """
    params = {
        "action": "query",
        "format": "json",
        "list": "search",
        "srsearch": f"filetype:bitmap {query}",
        "srnamespace": 6,  # File namespace
        "srlimit": limit,
    }

    # Build query string with proper URL encoding
    qs = urllib.parse.urlencode(params)
    url = f"{WIKIMEDIA_API}?{qs}"

    data = fetch_with_retry(url)
    if data is None:
        return []

    import json
    try:
        result = json.loads(data)
    except json.JSONDecodeError as e:
        logger.error("Failed to parse Wikimedia JSON: %s", e)
        return []

    image_urls = []
    for item in result.get("query", {}).get("search", []):
        title = item.get("title", "")
        if not title.startswith("File:"):
            continue

        # Get image info to find the actual image URL
        info_params = {
            "action": "query",
            "format": "json",
            "prop": "imageinfo",
            "iiprop": "url",
            "titles": title,
        }
        info_qs = urllib.parse.urlencode(info_params)
        info_url = f"{WIKIMEDIA_API}?{info_qs}"

        info_data = fetch_with_retry(info_url)
        if info_data is None:
            continue

        try:
            info_result = json.loads(info_data)
            pages = info_result.get("query", {}).get("pages", {})
            for page in pages.values():
                for ii in page.get("imageinfo", []):
                    url = ii.get("url")
                    if url and url.lower().endswith(('.jpg', '.jpeg', '.png')):
                        image_urls.append(url)
                        break
        except json.JSONDecodeError:
            continue

        # Rate limit: be respectful to Wikimedia
        time.sleep(0.5)

        if len(image_urls) >= limit:
            break

    return image_urls


def download_image(url: str, output_path: Path) -> bool:
    """Download a single image to output_path. Returns True on success."""
    data = fetch_with_retry(url)
    if data is None:
        return False

    try:
        output_path.write_bytes(data)
        return True
    except OSError as e:
        logger.error("Failed to write %s: %s", output_path, e)
        return False


def scrape_class(class_name: str, limit: int = 50, output_dir: str = "data/train"):
    """Scrape images for a single class."""
    class_dir = Path(output_dir) / class_name
    class_dir.mkdir(parents=True, exist_ok=True)

    # Count existing images
    existing = len(list(class_dir.glob("*.jpg"))) + len(list(class_dir.glob("*.png")))
    needed = max(0, limit - existing)
    if needed == 0:
        logger.info("[scraper] %s: already has %d images, skipping", class_name, existing)
        return existing

    logger.info("[scraper] %s: fetching %d new images...", class_name, needed)

    image_urls = search_wikimedia_images(class_name, limit=needed)
    logger.info("[scraper] %s: found %d candidate URLs", class_name, len(image_urls))

    downloaded = 0
    for i, url in enumerate(image_urls):
        output_path = class_dir / f"{class_name}_{existing + i:04d}.jpg"
        if download_image(url, output_path):
            downloaded += 1
            logger.debug("[scraper] %s: saved %s", class_name, output_path.name)

        # Rate limit between downloads
        time.sleep(0.3)

    logger.info("[scraper] %s: downloaded %d/%d images", class_name, downloaded, needed)
    return downloaded


def scrape_all(limit: int = 50, output_dir: str = "data/train"):
    """Scrape images for all target classes."""
    logger.info("[scraper] Starting scrape for %d classes (limit=%d each)",
                len(TARGET_CLASSES), limit)

    total = 0
    for class_name in TARGET_CLASSES:
        try:
            count = scrape_class(class_name, limit=limit, output_dir=output_dir)
            total += count
        except Exception as e:
            logger.error("Error scraping %s: %s — continuing with next class",
                         class_name, e)

    logger.info("[scraper] Complete. Total new images: %d", total)
    return total


def main():
    parser = argparse.ArgumentParser(
        description="Scrape training images for ESP32-CAM robot brain"
    )
    parser.add_argument("--class", dest="class_name",
                        help="Single class to scrape (e.g. water_bottle)")
    parser.add_argument("--all", action="store_true",
                        help="Scrape all target classes")
    parser.add_argument("--limit", type=int, default=50,
                        help="Max images per class")
    parser.add_argument("--output", default="data/train",
                        help="Output directory base")
    args = parser.parse_args()

    if args.class_name:
        scrape_class(args.class_name, limit=args.limit, output_dir=args.output)
    elif args.all:
        scrape_all(limit=args.limit, output_dir=args.output)
    else:
        parser.print_help()
        sys.exit(1)


if __name__ == "__main__":
    main()
