# Boru Scraper

A highly configurable, Playwright-based web scraper designed for scraping image board sites (e.g., Danbooru, Gelbooru, Rule34). It supports advanced features like resumable scraping, deduplication, and metadata extraction.

## Table of Contents
- [Features](FEATURES.md)
- [Installation](#installation)
- [Usage](#usage)
- [Configuration](#configuration)

## Installation

### Prerequisites
- Python 3.8+
- [Playwright](https://playwright.dev/python/)

### Setup
1. Clone the repository:
   ```bash
   git clone <repository_url>
   cd "boru scraper"
   ```

2. Install Python dependencies:
   ```bash
   pip install playwright beautifulsoup4 loguru diskcache slugify tqdm
   ```
   *(Note: A `requirements.txt` file is not currently provided, but these are the main dependencies based on imports).*

3. Install Playwright browsers:
   ```bash
   playwright install chromium
   ```

## Usage

The main scraper script is `scraper/ws4_s1.py`.

Currently, the configuration file path is hardcoded in the script (defaulting to `rule34.json`). You may need to edit the `__main__` block in `scraper/ws4_s1.py` to point to your desired configuration file.

Run the scraper:
```bash
python scraper/ws4_s1.py
```

## Configuration
The scraper is controlled by JSON configuration files. Examples are provided in the `scraper/` directory (e.g., `rule34.json`, `danbooru.json`).

### Key Configuration Options
- **start_urls**: List of URLs to start scraping from (e.g., a specific tag search page).
- **save_path**: Base directory to save scraped content.
- **resource_save_path_pattern**: Template string for file naming (e.g., `images/{topic_id}_{field_name}.{ext}`).
- **selectors**: CSS selectors for navigating the site (pagination, topic links).
- **fields_to_parse**: List of fields to extract from topic pages.
    - `name`: Field name.
    - `selector`: CSS selector.
    - `type`: `text` or `resource_url`.
    - `multiple`: Boolean, true for lists of tags.
- **delays**: Configuration for throttling requests.
    - `delay_between_list_pages_s`: Seconds to wait between pagination.
    - `download_delay_range_s`: Min/Max seconds to wait before downloads.

## Metadata Writing
The scraper works with an optional `MDManager` module (if present in `SLM/metadata/MDManager/mdmanager.py`) to write XMP metadata directly to downloaded files. If this library is missing, metadata writing is automatically disabled with a warning.
