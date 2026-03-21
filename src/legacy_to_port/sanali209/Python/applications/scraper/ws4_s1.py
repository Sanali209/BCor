import json
import hashlib
import os
import random
import time
import urllib.parse
import mimetypes
import re
from dataclasses import dataclass, field, asdict
from typing import List, Dict, Any, Optional, Set, Tuple

import diskcache
from bs4 import BeautifulSoup, Tag
from urllib.parse import urlparse, parse_qs
from loguru import logger
from playwright.sync_api import (
    sync_playwright,
    Playwright,
    Browser,
    Page,
    BrowserContext,
    Error as PlaywrightError,
    TimeoutError as PlaywrightTimeoutError,
)
from slugify import slugify
from tqdm import tqdm

# Attempt to import the custom MDManager
try:
    from SLM.metadata.MDManager.mdmanager import MDManager
except ImportError:
    logger.error("Could not import MDManager. Metadata writing will be disabled.")
    MDManager = None

# --- LOGGING CONFIGURATION ---
logger.add(
    "../scraper_sync_{time}.log",
    rotation="10 MB",
    level="INFO",
    format="{time:YYYY-MM-DD HH:mm:ss.SSS} | {level: <8} | {name}:{function}:{line} - {message}",
)


# --- DATA CLASSES FOR CONFIGURATION ---
@dataclass
class DelaysConfig:
    initial_manual_action_delay_s: int = 0
    delay_between_list_pages_s: float = 2.0
    delay_between_topics_s: float = 1.0
    download_delay_range_s: List[float] = field(default_factory=lambda: [0.5, 2.5])
    long_pause_every_n_pages: Dict[str, int] = field(
        default_factory=lambda: {"pages": 10, "seconds": 30}
    )


@dataclass
class MetadataWritingConfig:
    enabled: bool = False
    metadata_cache_path: str = "./metadata_cache"
    tag_prefixes: Dict[str, str] = field(default_factory=dict)
    rating_field: str = "stat_rating_raw"
    rating_prefix: str = "metadata/rating/"


@dataclass
class FieldConfig:
    name: str
    selector: str
    type: str
    required: bool = False
    attribute: Optional[str] = None
    multiple: bool = False
    filter_regex: Optional[str] = None
    path_join_separator: Optional[str] = None
    exclude_extensions: Optional[List[str]] = field(default_factory=list)


@dataclass
class ProjectConfig:
    start_urls: List[str]
    save_path: str
    resource_save_path_pattern: str
    selectors: Dict[str, str]
    fields_to_parse: List[FieldConfig]
    pagination_progress_file: str = "pagination_progress.json"
    save_every_n_items: int = 10
    overwrite_metadata: bool = False
    overwrite_resources: bool = False
    min_topic_content_lent: int = 10000
    min_list_content_lent: int = 5000
    captcha_selector: Optional[str] = None
    cache_path: str = ".scraper_cache"
    md5_cache_path: str = ".md5_cache"
    cache_size_gb: int = 10
    delays: DelaysConfig = field(default_factory=DelaysConfig)
    metadata_writing: MetadataWritingConfig = field(
        default_factory=MetadataWritingConfig
    )
    navigation_timeout_ms: int = 60000
    download_timeout_ms: int = 45000

    @classmethod
    def load_from_file(cls, filepath: str) -> "ProjectConfig":
        logger.info(f"Loading configuration from: {filepath}")
        try:
            with open(filepath, "r", encoding="utf-8") as f:
                config_data = json.load(f)

            # --- Type conversions for nested dataclasses ---
            config_data["fields_to_parse"] = [
                FieldConfig(**f) for f in config_data.get("fields_to_parse", [])
            ]
            if "delays" in config_data:
                config_data["delays"] = DelaysConfig(**config_data["delays"])
            if "metadata_writing" in config_data:
                config_data["metadata_writing"] = MetadataWritingConfig(
                    **config_data["metadata_writing"]
                )

            return cls(**config_data)
        except FileNotFoundError:
            logger.error(f"Configuration file not found: {filepath}")
            raise
        except (json.JSONDecodeError, TypeError, KeyError) as e:
            logger.error(f"Error decoding or parsing configuration file {filepath}: {e}")
            raise


# --- DATA HANDLING CLASSES ---
@dataclass
class TopicData:
    topic_id: str
    topic_url: str
    fields: Dict[str, Any] = field(default_factory=dict)

    @staticmethod
    def generate_id(url: str) -> str:
        extracted_id = extract_id_from_url(url)
        if extracted_id:
            return extracted_id
        return hashlib.sha1(url.encode("utf-8")).hexdigest()

    def to_dict(self) -> Dict[str, Any]:
        return asdict(self)


def extract_id_from_url(url: str) -> Optional[str]:
    try:
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        if "id" in query_params:
            id_val = query_params["id"][0]
            if id_val.isdigit():
                return None
    except Exception:
        pass
    return None


class CacheManager:
    def __init__(self, path: str, size_limit_gb: int):
        self.path = path
        self.size_limit_bytes = size_limit_gb * (1024 ** 3)
        logger.info(
            f"Initializing disk cache at '{path}' with size limit {size_limit_gb} GB."
        )
        os.makedirs(path, exist_ok=True)
        self.cache = diskcache.Cache(path, size_limit=self.size_limit_bytes)

    def __contains__(self, key: str) -> bool:
        return key in self.cache

    def add(self, key: str, value: Any):
        self.cache[key] = value

    def close(self):
        self.cache.close()

    def __len__(self) -> int:
        return len(self.cache)


class DataSaver:
    def __init__(self, config: ProjectConfig):
        self.pagination_progress_path = os.path.join(
            config.save_path, config.pagination_progress_file
        )
        os.makedirs(config.save_path, exist_ok=True)

    def load_pagination_progress(self) -> Dict[str, str]:
        if not os.path.exists(self.pagination_progress_path):
            logger.info("Pagination progress file not found. Starting from scratch.")
            return {}
        try:
            with open(self.pagination_progress_path, "r", encoding="utf-8") as f:
                progress = json.load(f)
                logger.info(
                    f"Loaded pagination progress for {len(progress)} start URLs."
                )
                return progress
        except (json.JSONDecodeError, FileNotFoundError):
            logger.warning(
                f"Could not read pagination progress from {self.pagination_progress_path}. Starting fresh."
            )
            return {}

    def save_pagination_progress(self, progress: Dict[str, str]):
        try:
            with open(self.pagination_progress_path, "w", encoding="utf-8") as f:
                json.dump(progress, f, indent=2)
            logger.debug(
                f"Saved pagination progress to {self.pagination_progress_path}"
            )
        except Exception as e:
            logger.error(
                f"Failed to save pagination progress to {self.pagination_progress_path}: {e}"
            )


class MetadataWriter:
    def __init__(self, config: MetadataWritingConfig, save_path: str):
        self.config = config
        cache_full_path = os.path.join(save_path, config.metadata_cache_path)
        self.cache = (
            CacheManager(cache_full_path, 10) if config.enabled else None
        )
        if config.enabled and not MDManager:
            logger.error(
                "MDManager not available, disabling metadata writing feature."
            )
            self.config.enabled = False

    def write_tags(self, file_path: str, topic_data: TopicData):
        if not self.config.enabled or not file_path:
            return

        if not os.path.exists(file_path):
            logger.warning(f"File not found for metadata writing: {file_path}")
            return

        if self.cache and file_path in self.cache:
            logger.trace(f"Skipping already metadata-tagged file: {file_path}")
            return

        try:
            all_tags = []
            fields_data = topic_data.fields

            for tag_type, prefix in self.config.tag_prefixes.items():
                tags = fields_data.get(tag_type)
                if tags and isinstance(tags, list):
                    all_tags.extend([f"{prefix}{tag}" for tag in tags])

            rating = fields_data.get(self.config.rating_field)
            if rating:
                all_tags.append(f"{self.config.rating_prefix}{rating}")

            if all_tags:
                md_manager = MDManager(file_path)
                md_manager.metadata["XMP:Subject"] = all_tags
                md_manager.Save()
                if self.cache:
                    self.cache.add(file_path)
                logger.success(f"Successfully wrote {len(all_tags)} tags to: {file_path}")

        except Exception as e:
            logger.error(f"Failed to write metadata for {file_path}: {e}")


class ResourceDownloader:
    def __init__(self, config: ProjectConfig, context: BrowserContext, md5_cache: "CacheManager"):
        self.config = config
        self.context = context
        self.md5_cache = md5_cache
        self.page: Optional[Page] = None
        self.field_configs: Dict[str, FieldConfig] = {
            field.name: field for field in config.fields_to_parse
        }

    def set_page(self, page: Optional[Page]):
        self.page = page if page and not page.is_closed() else None

    def _get_extension(self, url: str, content_type: Optional[str]) -> str:
        # Prefer content-type, fallback to URL
        if content_type:
            mime_type = content_type.split(";")[0].strip()
            ext = mimetypes.guess_extension(mime_type)
            if ext:
                return ext[1:] if ext.startswith(".") else ext

        path = urllib.parse.urlparse(url).path
        ext = os.path.splitext(path)[1]
        return ext[1:] if ext else "bin"

    def _format_path_component(self, value: Any, field_name: str) -> str:
        field_conf = self.field_configs.get(field_name, FieldConfig("", "", ""))
        separator = field_conf.path_join_separator or "_"
        if isinstance(value, list):
            return separator.join(
                [slugify(str(item), separator=" ") for item in value if item]
            )
        return slugify(str(value)) if value is not None else "none"

    def _download_via_navigation(
            self, resource_url: str
    ) -> Optional[Tuple[bytes, Optional[str]]]:
        if not self.page:
            return None
        try:
            response = self.page.goto(
                resource_url,
                wait_until="domcontentloaded",
                timeout=self.config.download_timeout_ms,
            )
            if response and response.ok:
                return response.body(), response.headers.get("content-type")
        except PlaywrightError as e:
            logger.warning(f"Navigation download failed for {resource_url}: {e}")
        return None

    def download(
            self, resource_url: str, resource_field_name: str, topic_data: TopicData
    ) -> Optional[str]:
        if not resource_url:
            return None

        # Initial path generation with URL extension
        url_ext = self._get_extension(resource_url, None)
        format_data = {
            "topic_id": slugify(str(topic_data.topic_id)),
            "field_name": slugify(resource_field_name),
            "ext": url_ext,
            **{
                fname: self._format_path_component(fvalue, fname)
                for fname, fvalue in topic_data.fields.items()
            },
        }
        relative_path = self.config.resource_save_path_pattern.format(**format_data)
        absolute_path = os.path.join(self.config.save_path, relative_path)
        delay_range = self.config.delays.download_delay_range_s
        time.sleep(random.uniform(delay_range[0], delay_range[1]))
        if not self.config.overwrite_resources and os.path.exists(absolute_path):
            logger.debug(f"Resource exists, skipping: {relative_path}")
            return relative_path

        body_bytes, content_type = None, None
        # Attempt 1: API Request
        try:
            api_response = self.context.request.get(
                resource_url,
                timeout=self.config.download_timeout_ms,
                headers={"Referer": topic_data.topic_url},
            )
            if api_response.ok:
                body_bytes = api_response.body()
                content_type = api_response.headers.get("content-type")
                logger.debug(f"API download successful for: {resource_url}")
        except PlaywrightError as e:
            logger.warning(f"API download failed for {resource_url}: {e}. Falling back.")

        # Attempt 2: Navigation Fallback
        if not body_bytes:
            nav_result = self._download_via_navigation(resource_url)
            if nav_result:
                body_bytes, content_type = nav_result
                logger.debug(f"Navigation download successful for: {resource_url}")

        if not body_bytes:
            logger.error(f"All download methods failed for: {resource_url}")
            return None

        # --- MD5 Check ---
        if self.md5_cache:
            try:
                md5_hash = hashlib.md5(body_bytes).hexdigest()
                if md5_hash in self.md5_cache:
                    logger.info(f"Duplicate content (MD5: {md5_hash}). Skipping save for {resource_url}")
                    return None  # Do not save the file
            except Exception as e:
                logger.warning(f"Could not perform MD5 check for {resource_url}: {e}")
        # --- End MD5 Check ---

        # Refine path with final extension
        final_ext = self._get_extension(resource_url, content_type)
        if final_ext != url_ext:
            format_data["ext"] = final_ext
            relative_path = self.config.resource_save_path_pattern.format(
                **format_data
            )
            absolute_path = os.path.join(self.config.save_path, relative_path)

        # Save file
        try:
            os.makedirs(os.path.dirname(absolute_path), exist_ok=True)
            with open(absolute_path, "wb") as f:
                f.write(body_bytes)

            # Add MD5 to cache after successful save
            if self.md5_cache and 'md5_hash' in locals():
                self.md5_cache.add(md5_hash, True)

            logger.info(f"Resource saved: {relative_path}")
            return relative_path
        except IOError as e:
            logger.error(f"IOError saving resource {absolute_path}: {e}")
            return None


class ScraperApp:
    def __init__(self, config: ProjectConfig, post_processors: Dict[str, callable]):
        self.config = config
        self.post_processors = post_processors
        self.data_saver = DataSaver(config)

        item_cache_path = os.path.join(config.save_path, config.cache_path)
        self.item_cache = CacheManager(item_cache_path, config.cache_size_gb)

        md5_cache_path = os.path.join(config.save_path, config.md5_cache_path)
        self.md5_cache = CacheManager(md5_cache_path, config.cache_size_gb)

        self.metadata_writer = MetadataWriter(config.metadata_writing, config.save_path)
        self.pagination_progress = self.data_saver.load_pagination_progress()

        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.resource_downloader: Optional[ResourceDownloader] = None
        self.filter_regex_cache: Dict[str, re.Pattern] = {}

    def _initialize(self):
        logger.info("=" * 30 + " Initializing Scraper " + "=" * 30)
        self.playwright = sync_playwright().start()
        self.browser = self.playwright.chromium.launch(headless=False)
        self.context = self.browser.new_context(
            user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36",
            viewport={"width": 1920, "height": 1080},
        )
        self.context.set_default_navigation_timeout(self.config.navigation_timeout_ms)
        self.resource_downloader = ResourceDownloader(self.config, self.context, self.md5_cache)
        logger.info("Scraper initialized successfully.")

    def _finalize(self):
        logger.info("=" * 30 + " Finalizing Scraper " + "=" * 30)
        self.data_saver.save_pagination_progress(self.pagination_progress)
        self.item_cache.close()
        self.md5_cache.close()
        if self.metadata_writer.cache:
            self.metadata_writer.cache.close()
        if self.context:
            self.context.close()
        if self.browser:
            self.browser.close()
        if self.playwright:
            self.playwright.stop()
        logger.info("Scraper finalized.")

    def _handle_captcha(self, page: Page) -> bool:
        if not self.config.captcha_selector:
            return False
        try:
            if page.locator(self.config.captcha_selector).is_visible():
                logger.warning("CAPTCHA detected! Please solve it in the browser.")
                input("Press Enter after solving the CAPTCHA to continue...")
                logger.info("Resuming scraping after CAPTCHA.")
                return True
        except PlaywrightError:
            return False
        return False

    def _navigate_to(self, page: Page, url: str) -> bool:
        try:
            logger.debug(f"Navigating to: {url}")
            response = page.goto(url, wait_until="domcontentloaded")
            if not response or not response.ok:
                logger.error(f"Navigation failed for {url} with status {response.status if response else 'N/A'}")
                input("solve captcha and press Enter to continue...")
                return False
            self._handle_captcha(page)
            return True
        except (PlaywrightTimeoutError, PlaywrightError) as e:
            logger.error(f"Navigation error for {url}: {e}")
            return False

    def _parse_field(self, soup: BeautifulSoup, field_conf: FieldConfig, base_url: str) -> Any:
        elements = soup.select(field_conf.selector)
        if not elements:
            if field_conf.required:
                raise ValueError(f"Required field '{field_conf.name}' not found")
            return None

        if field_conf.type == "text":
            texts = [el.get_text(strip=True) for el in elements]
            if field_conf.filter_regex:
                if field_conf.filter_regex not in self.filter_regex_cache:
                    self.filter_regex_cache[field_conf.filter_regex] = re.compile(field_conf.filter_regex)
                compiled_regex = self.filter_regex_cache[field_conf.filter_regex]
                texts = [t for t in texts if not compiled_regex.search(t)]
            return texts if field_conf.multiple else (texts[0] if texts else None)

        if field_conf.type == "resource_url":
            urls = []
            attr = field_conf.attribute or "src"
            for el in elements:
                if url := el.get(attr):
                    abs_url = urllib.parse.urljoin(base_url, url)
                    ext = self.resource_downloader._get_extension(abs_url, None)
                    if ext not in field_conf.exclude_extensions:
                        urls.append(abs_url)
            return urls if field_conf.multiple else (urls[0] if urls else None)
        return None

    def _process_topic_page(self, page: Page, topic_url: str):
        topic_id = TopicData.generate_id(topic_url)
        if topic_id in self.item_cache:
            logger.trace(f"Skipping cached item: {topic_url}")
            return

        if not self._navigate_to(page, topic_url):
            return

        content = page.content()
        if len(content) < self.config.min_topic_content_lent:
            logger.warning(f"Topic page content too small ({len(content)} bytes): {topic_url}")
            return

        soup = BeautifulSoup(content, "lxml")
        topic_data = TopicData(topic_id=topic_id, topic_url=topic_url)

        for field_conf in self.config.fields_to_parse:
            try:
                value = self._parse_field(soup, field_conf, topic_url)
                if field_conf.name in self.post_processors:
                    value = self.post_processors[field_conf.name](topic_data, value, soup)

                if field_conf.type == "resource_url" and value:
                    urls_to_process = value if isinstance(value, list) else [value]
                    downloaded_paths = []
                    for i, url in enumerate(urls_to_process):
                        field_name_for_download = f"{field_conf.name}_{i + 1:03d}" if len(
                            urls_to_process) > 1 else field_conf.name
                        if path := self.resource_downloader.download(url, field_name_for_download, topic_data):
                            downloaded_paths.append(path)
                            self.metadata_writer.write_tags(os.path.join(self.config.save_path, path), topic_data)
                    topic_data.fields[field_conf.name] = downloaded_paths if field_conf.multiple else (
                        downloaded_paths[0] if downloaded_paths else None)
                else:
                    topic_data.fields[field_conf.name] = value
            except Exception as e:
                logger.error(f"Error parsing field '{field_conf.name}' for {topic_url}: {e}")

        self.item_cache.add(topic_id, topic_data.to_dict())
        logger.info(f"Successfully processed and cached topic: {topic_url}")

    def _scrape_site(self):
        if not self.context or not self.resource_downloader:
            logger.critical("Context or downloader not initialized.")
            return

        for start_url in self.config.start_urls:
            page = self.context.new_page()
            self.resource_downloader.set_page(page)

            current_url = self.pagination_progress.get(start_url, start_url)
            page_num = 1

            try:
                # --- Initial Navigation and Manual Action Delay ---
                logger.info(f"Navigating to initial page for '{start_url}': {current_url}")
                if not self._navigate_to(page, current_url):
                    raise Exception(f"Could not load initial page for {start_url}")

                if self.config.delays.initial_manual_action_delay_s > 0:
                    logger.warning(
                        f"Pausing for {self.config.delays.initial_manual_action_delay_s} seconds for manual actions (e.g., login)..."
                    )
                    time.sleep(self.config.delays.initial_manual_action_delay_s)
                    logger.info("Resuming scraping.")
                # --- End Initial Delay ---

                while current_url:
                    # If this is not the first page (i.e., we looped), navigate again.
                    if page_num > 1:
                        logger.info(f"Processing list page #{page_num}: {current_url}")
                        if not self._navigate_to(page, current_url):
                            break
                    else:  # For the first page, we are already there
                        logger.info(f"Processing list page #{page_num}: {current_url}")

                    content = page.content()
                    if len(content) < self.config.min_list_content_lent:
                        logger.warning(f"List page content too small ({len(content)} bytes): {current_url}")
                        break

                    soup = BeautifulSoup(content, "lxml")
                    topic_links = [
                        urllib.parse.urljoin(current_url, a["href"])
                        for preview in soup.select(self.config.selectors["topic_preview"])
                        if (a := preview.select_one(self.config.selectors["topic_link"])) and a.get("href")
                    ]

                    logger.info(f"Found {len(topic_links)} topic links on page.")
                    for topic_url in tqdm(topic_links, desc=f"Scraping Page {page_num}"):
                        self._process_topic_page(page, topic_url)
                        time.sleep(self.config.delays.delay_between_topics_s)

                    self.pagination_progress[start_url] = current_url
                    self.data_saver.save_pagination_progress(self.pagination_progress)

                    next_page_tag = soup.select_one(self.config.selectors["pagination_next"])
                    if next_page_tag and next_page_tag.get("href"):
                        current_url = urllib.parse.urljoin(current_url, next_page_tag["href"])
                        page_num += 1

                        pause_config = self.config.delays.long_pause_every_n_pages
                        if page_num % pause_config["pages"] == 0:
                            logger.info(f"Taking a long pause for {pause_config['seconds']} seconds.")
                            time.sleep(pause_config["seconds"])
                        else:
                            time.sleep(self.config.delays.delay_between_list_pages_s)
                    else:
                        logger.info("No next page found. Ending pagination for this start URL.")
                        current_url = None
            finally:
                page.close()

    def run(self):
        try:
            self._initialize()
            self._scrape_site()
        except KeyboardInterrupt:
            logger.warning("Scraping interrupted by user.")
        except Exception as e:
            logger.exception(f"A critical error occurred: {e}")
        finally:
            self._finalize()


def def_simple_copiright(topic_data: TopicData, value, soup):
    """Example post-processor. Modifies topic_data in place."""
    getv = topic_data.fields.get("simple_copiright", "Unknown")
    topic_data.fields["simple_copiright"] = getv
    return value  # Must return the value for proper field processing


def create_simple_copiright(topic_data: TopicData, value, soup):
    """Example post-processor. Modifies topic_data in place."""
    if value:
        try:
            topic_data.fields["simple_copiright"] = value[0]
        except (IndexError, TypeError):
            topic_data.fields["simple_copiright"] = value
    else:
        topic_data.fields["simple_copiright"] = "Unknown"

    # Extract rating and source
    try:
        for li in soup.find_all('li'):
            if "Source:" in li.text and (link := li.find('a')):
                topic_data.fields["stat_source_url"] = link.get('href')
            if "Rating:" in li.text:
                rating = li.text.split("Rating:")[-1].strip().lower()
                topic_data.fields["stat_rating_raw"] = rating
    except Exception as e:
        logger.warning(f"Could not post-process rating/source: {e}")
    return value


if __name__ == "__main__":
    CONFIG_FILE = "rule34.json"
    try:
        config = ProjectConfig.load_from_file(CONFIG_FILE)
        processors = {"tags_copyright": create_simple_copiright,
                      "main_resource_url": def_simple_copiright}
        app = ScraperApp(config, processors)
        app.run()
    except Exception as e:
        logger.critical(f"Failed to start application: {e}", exc_info=True)
