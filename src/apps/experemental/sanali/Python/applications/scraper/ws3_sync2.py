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
from urllib.parse import urlparse, parse_qs

import playwright
from bs4 import BeautifulSoup, Tag
from loguru import logger
# Use sync_api imports
from playwright.sync_api import (
    sync_playwright,
    Playwright,
    Browser,
    Page,
    APIRequestContext,  # For type hinting
    Error as PlaywrightError,
    TimeoutError as PlaywrightTimeoutError
)
from slugify import slugify  # Для безопасных имен файлов/директорий

# --- Конфигурация Логгирования ---
logger.add("../scraper_sync.log", rotation="10 MB", level="INFO")  # Use a different log file name


# planed futures
# field post proccesing
# site loging
# navigate delay

@dataclass
class FieldConfig:
    name: str
    selector: str
    type: str  # 'text', 'resource_url'
    required: bool = False
    attribute: Optional[str] = None  # Атрибут для извлечения URL (для type='resource_url', по умолчанию 'src')
    multiple: bool = False  # Извлекать ли текст из всех найденных элементов
    filter_regex: Optional[str] = None  # Regex для фильтрации строк в multiple=True text
    path_join_separator: Optional[str] = None  # Разделитель для объединения list в path
    exclude_extensions: Optional[List[str]] = field(
        default_factory=lambda: ["gif"])  # Список исключеных расширений для ресурсов


@dataclass
class ProjectConfig:
    start_urls: List[str]  # Changed from start_url: str
    save_path: str
    metadata_filename: str
    progress_file: str
    resource_save_path_pattern: str
    save_every_n_items: int
    overwrite_metadata: bool
    overwrite_resources: bool
    selectors: Dict[str, str]
    fields_to_parse: List[FieldConfig]
    download_delay_seconds: float = 0.0
    navigate_delay_seconds: float = 1.5  # Used for time.sleep between actions if needed
    min_topic_content_lent: int = 200000  # Renamed variable to be consistent
    # Playwright timeouts (added for sync API clarity)
    navigation_timeout_ms: int = 60000
    download_timeout_ms: int = 30000  # Timeout for context.request.get

    @classmethod
    def load_from_file(cls, filepath: str = "config.json") -> 'ProjectConfig':
        try:
            with open(filepath, 'r', encoding='utf-8') as f:
                config_data = json.load(f)

            # Backwards compatibility checks (keep as is)
            if "image_save_path_pattern" in config_data:
                config_data["resource_save_path_pattern"] = config_data.pop("image_save_path_pattern")
                logger.warning(
                    "Обнаружен устаревший ключ 'image_save_path_pattern' в config.json. Используйте 'resource_save_path_pattern'.")
            if "overwrite_images" in config_data:
                config_data["overwrite_resources"] = config_data.pop("overwrite_images")
                logger.warning(
                    "Обнаружен устаревший ключ 'overwrite_images' в config.json. Используйте 'overwrite_resources'.")

            fields = [FieldConfig(**field_data) for field_data in config_data.get("fields_to_parse", [])]
            config_data["fields_to_parse"] = fields

            if not config_data.get("resource_save_path_pattern"):
                raise ValueError("Ключ 'resource_save_path_pattern' должен быть указан в конфигурации.")
            if "{ext}" not in config_data["resource_save_path_pattern"]:
                logger.warning(
                    "Паттерн 'resource_save_path_pattern' не содержит '{ext}'. Расширение файла может быть некорректным.")

            # Add default timeouts if not present in config
            config_data.setdefault("navigation_timeout_ms", 60000)
            config_data.setdefault("download_timeout_ms", 30000)
            config_data.setdefault("min_topic_content_lent", 200000)  # Add default if missing

            # Handle start_url (string) or start_urls (list) for backward compatibility
            if "start_url" in config_data and "start_urls" not in config_data:
                logger.warning("Обнаружен устаревший ключ 'start_url'. Используйте 'start_urls' (список строк).")
                config_data["start_urls"] = [config_data.pop("start_url")]
            elif "start_urls" in config_data and not isinstance(config_data["start_urls"], list):
                raise ValueError("'start_urls' должен быть списком строк.")
            elif "start_urls" not in config_data:
                raise ValueError("Ключ 'start_urls' (список строк) должен быть указан в конфигурации.")

            return cls(**config_data)
        except FileNotFoundError:
            logger.error(f"Конфигурационный файл не найден: {filepath}")
            raise
        except json.JSONDecodeError:
            logger.error(f"Ошибка декодирования JSON в файле: {filepath}")
            raise
        except Exception as e:
            logger.error(f"Неожиданная ошибка при загрузке конфигурации: {e}")
            raise


def extract_id_from_url(url: str) -> Optional[str]:
    """
    Пытается извлечь числовой ID из параметра 'id' в URL.
    Пример: https://gelbooru.com/index.php?page=post&s=view&id=11809334 -> '11809334'
    """
    try:
        parsed_url = urlparse(url)
        query_params = parse_qs(parsed_url.query)
        if 'id' in query_params:
            id_val = query_params['id'][0]
            if id_val.isdigit():
                return id_val
    except Exception as e:
        logger.warning(f"Ошибка при извлечении ID из URL '{url}': {e}")
    return None


@dataclass
class TopicData:
    topic_id: str
    topic_url: str
    fields: Dict[str, Any] = field(default_factory=dict)
    resource_urls_to_download: Dict[str, str] = field(default_factory=dict)

    @staticmethod
    def generate_id(url: str) -> str:
        """
        Генерирует ID для топика. Сначала пытается извлечь числовой ID из URL.
        Если не удается, использует хэш URL в качестве fallback.
        """
        extracted_id = extract_id_from_url(url)
        if extracted_id:
            logger.trace(f"Извлечен ID '{extracted_id}' из URL: {url}")
            return extracted_id
        else:
            fallback_id = hashlib.sha1(url.encode('utf-8')).hexdigest()
            logger.trace(f"ID из URL не извлечен, используется fallback хэш '{fallback_id}' для URL: {url}")
            return fallback_id

    def to_dict(self) -> Dict[str, Any]:
        data = asdict(self)
        data.pop('resource_urls_to_download', None)
        return data


class DataSaver:
    def __init__(self, config: ProjectConfig):
        self.config = config
        self.metadata_path = os.path.join(config.save_path, config.metadata_filename)
        self.progress_path = os.path.join(config.save_path, config.progress_file)
        os.makedirs(config.save_path, exist_ok=True)

    def load_metadata_ids(self) -> Set[str]:
        ids = set()
        if self.config.overwrite_metadata:
            logger.warning("overwrite_metadata=True, существующие метаданные будут проигнорированы.")
            return ids

        if not os.path.exists(self.metadata_path):
            logger.info("Файл метаданных не найден, начинаем с нуля.")
            return ids

        try:
            with open(self.metadata_path, 'r', encoding='utf-8') as f:
                for line in f:
                    try:
                        data = json.loads(line)
                        if 'topic_id' in data:
                            ids.add(str(data['topic_id']))  # Убедимся, что ID - строка
                    except json.JSONDecodeError:
                        logger.warning(f"Пропуск некорректной строки в {self.metadata_path}: {line.strip()}")
            logger.info(f"Загружено {len(ids)} ID из существующего файла метаданных.")
        except Exception as e:
            logger.error(f"Ошибка при загрузке ID из метаданных ({self.metadata_path}): {e}")
        return ids

    def save_metadata_item(self, item: TopicData):
        try:
            with open(self.metadata_path, 'a', encoding='utf-8') as f:
                json.dump(item.to_dict(), f, ensure_ascii=False)
                f.write('\n')
        except Exception as e:
            logger.error(f"Ошибка при дозаписи элемента в {self.metadata_path}: {e}")

    def load_progress(self) -> Set[str]:
        if not os.path.exists(self.progress_path):
            logger.info("Файл прогресса не найден.")
            return set()
        try:
            with open(self.progress_path, 'r', encoding='utf-8') as f:
                # Убедимся, что все ID загружаются как строки
                ids = set(map(str, json.load(f)))
            logger.info(f"Загружено {len(ids)} ID из файла прогресса.")
            return ids
        except json.JSONDecodeError:
            logger.error(f"Ошибка декодирования JSON в файле прогресса: {self.progress_path}. Начинаем с нуля.")
            return set()
        except Exception as e:
            logger.error(f"Ошибка при загрузке прогресса ({self.progress_path}): {e}")
            return set()

    def save_progress(self, ids: Set[str]):
        logger.debug(f"Сохранение {len(ids)} ID в файл прогресса: {self.progress_path}")
        try:
            # Сохраняем ID как строки
            with open(self.progress_path, 'w', encoding='utf-8') as f:
                json.dump(list(ids), f, indent=2)
        except Exception as e:
            logger.error(f"Ошибка при сохранении прогресса ({self.progress_path}): {e}")


class ResourceDownloader:
    # Принимает sync APIRequestContext напрямую
    def __init__(self, config: ProjectConfig, context: APIRequestContext):  # Removed page from __init__
        self.config = config
        self.context = context  # Сохраняем sync API context
        self.page: Optional[Page] = None  # Page will be set dynamically
        self.field_name_regex_cache: Dict[str, re.Pattern] = {}
        self.field_configs: Dict[str, FieldConfig] = {
            field.name: field for field in config.fields_to_parse
        }
        self.skip_req_download:bool = False  # Flag to skip request download if page is set

    def set_page(self, page: Optional[Page]):  # Allow setting page to None as well
        """Set the current page for navigation. Can be None if page is closed."""
        if page and page.is_closed():
            logger.warning("Attempted to set a closed page to ResourceDownloader. Setting to None.")
            self.page = None
        else:
            self.page = page
            if page:
                logger.trace(f"ResourceDownloader page set to: {page.url if page else 'None'}")
            else:
                logger.trace("ResourceDownloader page set to None.")

    def _get_extension_from_url(self, url: str) -> str:
        path = urllib.parse.urlparse(url).path
        ext = os.path.splitext(path)[1].lower()
        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.mp4', '.webm', '.jfif', '.avif']:  # Added avif
            return ext[1:]
        return 'bin'

    def _get_extension_from_content_type(self, content_type: Optional[str]) -> Optional[str]:
        if not content_type:
            return None
        mime_type = content_type.split(';')[0].strip()
        ext = mimetypes.guess_extension(mime_type)
        if ext == '.jpe': ext = '.jpeg'
        return ext[1:] if ext else None

    def _format_path_component(self, value: Any, field_name: str) -> str:
        field_conf = self.field_configs.get(field_name)
        separator = field_conf.path_join_separator if field_conf else "_"
        if separator is None: separator = ","
        if isinstance(value, list):
            slugified_parts = [slugify(str(item), separator=" ") for item in value if item]
            joined_value = separator.join(slugified_parts)
            return joined_value if joined_value else "list_field_empty"
        elif value is None:
            return "none"
        else:
            # Используем slugify для topic_id тоже, на случай если он не числовой (fallback)
            if field_name == 'topic_id':
                return slugify(str(value))
            return slugify(str(value))

    def _download_via_navigation(self, resource_url: str, resource_field_name: str, topic_data: TopicData) -> Optional[
        Tuple[bytes, Optional[str]]]:  # Return body and content_type
        """
        Download image by navigating to it in browser and getting the content
        Returns (content_bytes, content_type_header)
        """
        if not self.page or self.page.is_closed():  # Check if page is closed
            logger.error(
                f"[{topic_data.topic_id}/{resource_field_name}] Page not available or closed for navigation download for {resource_url}")
            return None

        try:
            logger.debug(
                f"[{topic_data.topic_id}/{resource_field_name}] Attempting navigation download for: {resource_url} (current page: {self.page.url})")

            # Navigate to the image URL directly on the CURRENT page
            # Using a longer timeout for direct resource navigation as it might be large
            response = self.page.goto(resource_url, wait_until='domcontentloaded',  # or 'load' for images
                                      timeout=self.config.download_timeout_ms * 2)  # Give more time for nav download

            if not response or not response.ok:
                status = response.status if response else "N/A"
                logger.error(
                    f"[{topic_data.topic_id}/{resource_field_name}] Navigation to resource URL {resource_url} failed with status {status}")
                # Navigate back to topic_url to restore state for subsequent operations if needed,
                # but this might be complex if the original page state was important for other fields.
                # For now, we just fail the download.
                # Consider if self.page.go_back() is appropriate or re-navigating to topic_data.topic_url
                return None

            # It's possible the resource_url is an HTML page displaying the image
            # (e.g. Danbooru's /posts/ID page if 'main_resource' selector targets the image on that page)
            # In this case, the resource_url itself *is* the page we want to extract from.
            # If resource_url is a direct image link, response.body() will be the image.

            body = response.body()
            content_type_header = response.headers.get('content-type')
            logger.info(
                f"[{topic_data.topic_id}/{resource_field_name}] Navigation download for {resource_url} successful. Content-Type: {content_type_header}, Size: {len(body)} bytes")
            return body, content_type_header

        except PlaywrightTimeoutError:
            logger.error(
                f"[{topic_data.topic_id}/{resource_field_name}] Navigation timeout for resource: {resource_url}")
            return None
        except PlaywrightError as e:
            # This can happen if the page is closed during navigation, or other PW errors
            logger.error(
                f"[{topic_data.topic_id}/{resource_field_name}] Playwright navigation error for resource {resource_url}: {e}")
            return None
        except Exception as e:
            logger.error(
                f"[{topic_data.topic_id}/{resource_field_name}] Unexpected error during navigation download for {resource_url}: {e}")
            return None

    def download(self, resource_url: str, resource_field_name: str, topic_data: TopicData) -> Optional[str]:
        """
        Скачивает ресурс синхронно, сначала через API, потом через навигацию, и возвращает относительный путь.
        """
        if not resource_url:
            logger.warning(f"[{topic_data.topic_id}/{resource_field_name}] Пустой URL ресурса.")
            return None

        absolute_path_str = "unknown_path"  # For logging in case of early errors
        try:
            url_ext = self._get_extension_from_url(resource_url)
            format_data = {
                "topic_id": slugify(str(topic_data.topic_id)),
                "field_name": slugify(resource_field_name),
                "ext": url_ext,
                **{fname: self._format_path_component(fvalue, fname)
                   for fname, fvalue in topic_data.fields.items()}
            }
            try:
                relative_path = self.config.resource_save_path_pattern.format(**format_data)
            except KeyError as e:
                logger.error(
                    f"[{topic_data.topic_id}/{resource_field_name}] Ошибка в resource_save_path_pattern: ключ {e} не найден. URL: {resource_url}")
                return None

            absolute_path_str = os.path.join(self.config.save_path, relative_path)

            if not self.config.overwrite_resources and os.path.exists(absolute_path_str):
                logger.debug(
                    f"[{topic_data.topic_id}/{resource_field_name}] Ресурс уже существует ({relative_path}), overwrite_resources=False.")
                return relative_path

            delay = self.config.download_delay_seconds + random.uniform(0, 1)  # Max 1s random extra
            if delay > 0:
                logger.trace(f"[{topic_data.topic_id}/{resource_field_name}] Пауза перед скачиванием: {delay:.2f} сек.")
                time.sleep(delay)

            body_bytes: Optional[bytes] = None
            content_type_header: Optional[str] = None
            download_source = "N/A"

            # Attempt 1: Playwright API Request
            logger.debug(f"[{topic_data.topic_id}/{resource_field_name}] Attempting API download: {resource_url}")
            headers = {
                "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
                "Accept": "image/webp,image/apng,image/svg+xml,image/*,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Accept-Encoding": "gzip, deflate, br",  # Playwright handles decompression automatically
                "Cache-Control": "no-cache", "Pragma": "no-cache",
                "Sec-Fetch-Dest": "image", "Sec-Fetch-Mode": "no-cors", "Sec-Fetch-Site": "cross-site",
                "Referer": topic_data.topic_url,  # Important
            }
            if "donmai.us" in resource_url or "cdn.donmai.us" in resource_url:  # Danbooru family
                headers.update({
                    "Origin": urllib.parse.urlunparse(
                        urlparse(topic_data.topic_url)._replace(path='', params='', query='', fragment='')),
                    # e.g. https://danbooru.donmai.us
                    "Sec-Ch-Ua": '"Not_A Brand";v="8", "Chromium";v="120", "Google Chrome";v="120"',
                    "Sec-Ch-Ua-Mobile": "?0", "Sec-Ch-Ua-Platform": '"Windows"',
                })
            if not self.skip_req_download:  # Only attempt API download if not set to skip
                try:
                    api_response = self.context.request.get(
                        resource_url,
                        timeout=self.config.download_timeout_ms,
                        headers=headers
                    )
                    if api_response.ok:
                        body_bytes = api_response.body()
                        content_type_header = api_response.headers.get('content-type')
                        download_source = f"API (status {api_response.status})"
                        logger.debug(
                            f"[{topic_data.topic_id}/{resource_field_name}] API download successful for {resource_url}")
                    else:
                        logger.warning(
                            f"[{topic_data.topic_id}/{resource_field_name}] API request for {resource_url} failed with status {api_response.status}. Headers: {api_response.headers}")
                except PlaywrightTimeoutError:
                    logger.warning(f"[{topic_data.topic_id}/{resource_field_name}] API request timeout for {resource_url}")
                except PlaywrightError as api_e:  # More general Playwright network errors
                    logger.warning(
                        f"[{topic_data.topic_id}/{resource_field_name}] API request PlaywrightError for {resource_url}: {api_e}")
                except Exception as api_e:  # Other unexpected errors
                    logger.warning(
                        f"[{topic_data.topic_id}/{resource_field_name}] API request unexpected error for {resource_url}: {api_e}")
                    self.skip_req_download = True  # Skip request download if page is set
            else:
                logger.debug(
                    f"[{topic_data.topic_id}/{resource_field_name}] Skipping API download for {resource_url} as skip_req_download is True.")
                body_bytes = None  # Reset body_bytes if skipping

            # Attempt 2: Browser Navigation (if API failed)
            if not body_bytes:
                logger.info(
                    f"[{topic_data.topic_id}/{resource_field_name}] API download failed, attempting navigation download for: {resource_url}")
                nav_result = self._download_via_navigation(resource_url, resource_field_name, topic_data)
                if nav_result:
                    body_bytes, nav_content_type = nav_result
                    content_type_header = nav_content_type  # Prioritize content type from navigation if successful
                    download_source = "Navigation"
                    logger.info(
                        f"[{topic_data.topic_id}/{resource_field_name}] Navigation download successful for {resource_url}")
                else:
                    logger.error(
                        f"[{topic_data.topic_id}/{resource_field_name}] Navigation download also failed for: {resource_url}")

            if not body_bytes:
                logger.error(
                    f"[{topic_data.topic_id}/{resource_field_name}] All download methods failed for: {resource_url}")
                return None

            # Determine final extension
            content_type_ext = self._get_extension_from_content_type(content_type_header)
            final_ext = url_ext
            if content_type_ext and content_type_ext != 'bin':
                final_ext = content_type_ext

            if final_ext != url_ext:
                logger.debug(
                    f"[{topic_data.topic_id}/{resource_field_name}] Extension refined by {download_source} content-type ('{content_type_header}'): {url_ext} -> {final_ext}")
                format_data["ext"] = final_ext
                try:
                    relative_path = self.config.resource_save_path_pattern.format(**format_data)
                except KeyError as e:  # Should not happen if first format worked, but defensive
                    logger.error(
                        f"[{topic_data.topic_id}/{resource_field_name}] Error in resource_save_path_pattern (refined ext): key {e}. URL: {resource_url}")
                    return None
                absolute_path_str = os.path.join(self.config.save_path, relative_path)

                # Re-check existence with new path
                if not self.config.overwrite_resources and os.path.exists(absolute_path_str):
                    logger.debug(
                        f"[{topic_data.topic_id}/{resource_field_name}] Resource (refined path: {relative_path}) already exists, overwrite_resources=False.")
                    return relative_path

            # Save file
            absolute_dir = os.path.dirname(absolute_path_str)
            os.makedirs(absolute_dir, exist_ok=True)
            with open(absolute_path_str, 'wb') as f:
                f.write(body_bytes)

            logger.info(
                f"[{topic_data.topic_id}/{resource_field_name}] Resource saved via {download_source} to: {relative_path} (Size: {len(body_bytes)})")
            return relative_path

        except IOError as e:
            logger.error(
                f"[{topic_data.topic_id}/{resource_field_name}] IOError saving resource to {absolute_path_str} for {resource_url}: {e}")
            return None
        except Exception as e:
            logger.exception(
                f"[{topic_data.topic_id}/{resource_field_name}] Unexpected error processing resource {resource_url} to {absolute_path_str}: {e}")
            return None


class ScraperApp:
    def __init__(self, config: ProjectConfig, post_processors: Optional[Dict[str, callable]] = None):
        self.config = config
        self.data_saver = DataSaver(config)
        self.resource_downloader: Optional[ResourceDownloader] = None
        self.processed_topic_ids: Set[str] = set()
        self.items_since_last_save: int = 0
        self.total_processed_count: int = 0
        self.session_start_time = time.time()
        self.filter_regex_cache: Dict[str, re.Pattern] = {}

        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        # BrowserContext is Playwright's term, APIRequestContext is for raw requests.
        # For page operations, we use BrowserContext. For API requests, we use its request property.
        self.browser_context: Optional[playwright.sync_api.BrowserContext] = None
        self.page: Optional[Page] = None  # Current active page, managed per start_url

        self.post_processors = post_processors if post_processors else {}
        logger.info(f"Загружено {len(self.post_processors)} функций пост-обработки.")

    def _initialize(self):
        logger.info("=" * 30 + " Инициализация Скрапера (Sync) " + "=" * 30)
        # ... (logging config details) ...

        progress_ids = self.data_saver.load_progress()
        metadata_ids = self.data_saver.load_metadata_ids()
        self.processed_topic_ids = progress_ids.union(metadata_ids)
        logger.info(f"Всего уникальных ID для пропуска: {len(self.processed_topic_ids)}")

        logger.info("Запуск Playwright (sync)...")
        try:
            self.playwright = sync_playwright().start()
            self.browser = self.playwright.chromium.launch(headless=False)  # Обычно True для продакшена

            # Use BrowserContext, not APIRequestContext here for general browser operations
            self.browser_context = self.browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
                viewport={'width': 1920, 'height': 1080}, # Example
                # locale='en-US', # Example
                # bypass_csp=True # Can be helpful for some sites if CSP blocks resource loading in navigation
            )
            self.browser_context.set_default_navigation_timeout(self.config.navigation_timeout_ms)
            self.browser_context.set_default_timeout(self.config.navigation_timeout_ms)  # General action timeout

            # The APIRequestContext is derived from the browser_context if needed for cookies, etc.
            # Or create a new one if independent requests are fine.
            # For downloading, using browser_context.request is fine.
            self.resource_downloader = ResourceDownloader(self.config,
                                                          self.browser_context.request)  # Pass context's request API
            logger.info("Playwright (sync) context успешно запущен и настроен.")

        except PlaywrightError as e:
            logger.error(f"Ошибка инициализации Playwright (sync): {e}")
            self._safe_close_playwright()
            raise
        except Exception as e:
            logger.error(f"Неожиданная ошибка при инициализации Playwright (sync): {e}")
            self._safe_close_playwright()
            raise

        self.items_since_last_save = 0
        self.total_processed_count = 0
        self.session_start_time = time.time()
        logger.info("Инициализация завершена.")

    def _safe_close_playwright(self):
        logger.warning("Попытка безопасного закрытия Playwright...")
        # Page is managed per start_url, so check if the *current* self.page exists
        if self.page and not self.page.is_closed():
            try:
                self.page.close()
                logger.debug("Активная страница Playwright закрыта.")
            except Exception as e:
                logger.error(f"Ошибка при закрытии активной страницы: {e}")

        # Close context first, then browser
        if self.browser_context:  # Changed from self.context
            try:
                self.browser_context.close()
                logger.debug("Контекст браузера Playwright закрыт.")
            except Exception as e:
                logger.error(f"Ошибка при закрытии контекста браузера: {e}")
        if self.browser:
            try:
                self.browser.close()
                logger.debug("Браузер Playwright закрыт.")
            except Exception as e:
                logger.error(f"Ошибка при закрытии браузера: {e}")
        if self.playwright:
            try:
                self.playwright.stop()
                logger.debug("Playwright остановлен.")
            except Exception as e:
                logger.error(f"Ошибка при остановке Playwright: {e}")
        logger.info("Закрытие Playwright завершено (или не требовалось).")

    def _finalize(self):
        logger.info("=" * 30 + " Завершение Скрапера (Sync) " + "=" * 30)
        if self.items_since_last_save > 0:
            logger.info("Выполнение финального сохранения прогресса...")
            self._save_state()
        self._safe_close_playwright()
        elapsed_time = time.time() - self.session_start_time
        logger.info(f"Скрапинг завершен. Обработано за сессию: {self.total_processed_count} топиков.")
        logger.info(f"Общее время работы сессии: {elapsed_time:.2f} секунд.")

    def _save_state(self):
        logger.info(f"Периодическое сохранение прогресса ({len(self.processed_topic_ids)} ID)...")
        self.data_saver.save_progress(self.processed_topic_ids)
        self.items_since_last_save = 0

    def _parse_field(self, soup: BeautifulSoup, field_conf: FieldConfig, base_url: str, topic_id: str) -> Any:
        elements = soup.select(field_conf.selector)
        field_name = field_conf.name

        if not elements:
            if field_conf.required:
                logger.error(
                    f"[{topic_id}/{field_name}] Обязательное поле не найдено (селектор: {field_conf.selector})")
                raise ValueError(f"Required field '{field_name}' not found")
            logger.trace(f"[{topic_id}/{field_name}] Необязательное поле не найдено (селектор: {field_conf.selector})")
            return None

        if field_conf.type == 'text':
            if field_conf.multiple:
                texts = [el.get_text(strip=True) for el in elements]
                if field_conf.filter_regex:
                    if field_conf.filter_regex not in self.filter_regex_cache:
                        try:
                            self.filter_regex_cache[field_conf.filter_regex] = re.compile(field_conf.filter_regex)
                        except re.error as e:
                            logger.error(
                                f"[{topic_id}/{field_name}] Ошибка компиляции regex '{field_conf.filter_regex}': {e}. Фильтрация отключена.")
                            self.filter_regex_cache[field_conf.filter_regex] = None  # Mark as bad

                    compiled_regex = self.filter_regex_cache.get(field_conf.filter_regex)
                    if compiled_regex:
                        original_count = len(texts)
                        texts = [t for t in texts if t and not compiled_regex.search(t)]  # Added check for t
                        if original_count != len(texts):
                            logger.debug(
                                f"[{topic_id}/{field_name}] Отфильтровано {original_count - len(texts)}/{original_count} элементов regex: {field_conf.filter_regex}")
                return texts if texts else None
            else:
                return elements[0].get_text(strip=True)

        elif field_conf.type == 'resource_url':
            # For multiple resource URLs (e.g., all images in a gallery post)
            if field_conf.multiple:
                urls = []
                attr_name = field_conf.attribute if field_conf.attribute else 'src'
                for element in elements:
                    resource_relative_url = element.get(attr_name)
                    if resource_relative_url:
                        resource_absolute_url = urllib.parse.urljoin(base_url, resource_relative_url)
                        urls.append(resource_absolute_url)
                    else:
                        logger.warning(
                            f"[{topic_id}/{field_name}] Атрибут '{attr_name}' пуст для одного из элементов селектора {field_conf.selector}")
                logger.debug(f"[{topic_id}/{field_name}] Найдено {len(urls)} URL ресурсов (multiple): {urls[:3]}...")
                return urls if urls else None
            else:  # Single resource URL
                element = elements[0]
                attr_name = field_conf.attribute if field_conf.attribute else 'src'
                resource_relative_url = element.get(attr_name)
                if not resource_relative_url:
                    logger.warning(
                        f"[{topic_id}/{field_name}] Атрибут '{attr_name}' пуст для селектора {field_conf.selector}")
                    return None
                resource_absolute_url = urllib.parse.urljoin(base_url, resource_relative_url)
                logger.debug(f"[{topic_id}/{field_name}] Найден URL ресурса: {resource_absolute_url}")
                return resource_absolute_url
        else:
            logger.error(f"[{topic_id}/{field_name}] Неизвестный тип поля: {field_conf.type}")
            return None

    def _navigate_to(self, url: str) -> bool:
        if not self.page or self.page.is_closed():  # Check if page is closed
            logger.error(f"Страница Playwright не инициализирована или закрыта для навигации на {url}.")
            return False
        logger.debug(f"Переход на URL: {url} (текущая страница: {self.page.url})")
        try:
            response = self.page.goto(url, wait_until='domcontentloaded')
            if response is None or not response.ok:
                status = response.status if response else "N/A"
                logger.error(f"Ошибка при переходе на {url}: статус {status}")
                return False
            logger.debug(f"Успешно перешел на: {url} (Статус: {response.status})")
            if self.config.navigate_delay_seconds > 0:
                time.sleep(self.config.navigate_delay_seconds)
            return True
        except PlaywrightTimeoutError:
            logger.error(f"Тайм-аут ({self.config.navigation_timeout_ms}ms) при переходе на URL: {url}")
            return False
        except PlaywrightError as e:
            logger.error(f"Ошибка Playwright при переходе на {url}: {e} (Страница могла быть закрыта)")
            return False
        except Exception as e:
            logger.error(f"Неожиданная ошибка при переходе на {url}: {e}")
            return False

    def _get_page_content(self) -> Optional[str]:
        if not self.page or self.page.is_closed():  # Check if page is closed
            logger.error("Страница Playwright не инициализирована или закрыта для получения контента.")
            return None
        logger.debug(f"Получение контента страницы: {self.page.url}")
        try:
            content = self.page.content()
            logger.debug(f"Контент получен (длина: {len(content)}).")
            return content
        except PlaywrightError as e:  # Catches if page is closed during content() call
            logger.error(f"Ошибка Playwright при получении контента: {e}")
            return None
        except Exception as e:
            logger.error(f"Неожиданная ошибка при получении контента: {e}")
            return None

    def _process_topic_page(self, topic_url: str):
        topic_id = TopicData.generate_id(topic_url)
        if topic_id in self.processed_topic_ids:
            logger.debug(f"Пропуск уже обработанного топика: {topic_url} (ID: {topic_id})")
            return

        logger.info(f"Обработка топика: {topic_url} (ID: {topic_id})")

        if not self.page or self.page.is_closed():
            logger.error(f"[{topic_id}] Невозможно обработать топик, страница не активна перед навигацией.")
            return

        if not self._navigate_to(topic_url):
            logger.warning(
                f"[{topic_id}] Первая попытка перейти на страницу топика не удалась: {topic_url}. Повторная попытка...")
            if not self._navigate_to(topic_url):  # Second attempt
                logger.error(
                    f"[{topic_id}] Вторая попытка перейти на страницу топика также не удалась: {topic_url}. Пропуск топика.")
                return

        html_content = self._get_page_content()
        if not html_content:
            logger.error(f"[{topic_id}] Не удалось получить контент страницы топика: {topic_url}. Пропуск.")
            return
        if len(html_content) < self.config.min_topic_content_lent:
            logger.warning(
                f"[{topic_id}] Контент страницы топика слишком короткий ({len(html_content)} байт, < {self.config.min_topic_content_lent}): {topic_url}")
            return

        try:
            soup = BeautifulSoup(html_content, 'lxml')
            topic_data = TopicData(topic_id=topic_id, topic_url=topic_url)

            # *** CRITICAL FIX: Set the current page for the downloader ***
            if self.resource_downloader:
                self.resource_downloader.set_page(self.page)  # Pass the ScraperApp's current page
            # *** END FIX ***

            for field_conf in self.config.fields_to_parse:
                field_name = field_conf.name
                try:
                    value = self._parse_field(soup, field_conf, topic_url, topic_id)
                    if field_name in self.post_processors:
                        process_funct = self.post_processors[field_name]
                        value = process_funct(topic_data, value, soup)  # Pass topic_data for modification

                    if field_conf.type == 'resource_url' and value:
                        # Handle single or multiple URLs
                        urls_to_process = [value] if isinstance(value, str) else (
                            value if isinstance(value, list) else [])
                        processed_paths = []

                        for i, res_url in enumerate(urls_to_process):
                            if not res_url: continue

                            # Use a suffix for multiple resources from the same field_name
                            current_field_name_for_download = field_name
                            if field_conf.multiple and len(urls_to_process) > 1:
                                current_field_name_for_download = f"{field_name}_{i + 1:03d}"

                            res_ext = self.resource_downloader._get_extension_from_url(res_url)
                            if res_ext in field_conf.exclude_extensions:
                                logger.debug(
                                    f"[{topic_id}/{current_field_name_for_download}] Исключаем URL ресурса с расширением {res_ext}: {res_url}")
                                continue  # Skip this resource

                            # Add to download queue (or download immediately if preferred)
                            # For simplicity here, we'll assume direct download and storing path
                            if self.resource_downloader:
                                local_path = self.resource_downloader.download(
                                    resource_url=res_url,
                                    resource_field_name=current_field_name_for_download,
                                    # Use modified name for multiples
                                    topic_data=topic_data
                                )
                                if local_path:
                                    processed_paths.append(local_path)
                            else:
                                logger.error(
                                    f"[{topic_id}/{current_field_name_for_download}] ResourceDownloader не инициализирован!")

                        # Store paths: single string or list of strings
                        if field_conf.multiple:
                            topic_data.fields[field_name] = processed_paths if processed_paths else None
                        elif processed_paths:  # Single URL
                            topic_data.fields[field_name] = processed_paths[0]
                        else:  # Single URL, download failed or excluded
                            topic_data.fields[field_name] = None
                        # No need for resource_urls_to_download if downloading immediately
                    else:
                        topic_data.fields[field_name] = value
                except ValueError as e:  # Required field not found
                    logger.error(
                        f"[{topic_id}] Ошибка парсинга обязательного поля '{field_name}' для {topic_url}: {e}. Топик пропущен.")
                    return  # Skip this topic
                except Exception as e:
                    logger.error(f"[{topic_id}/{field_name}] Неожиданная ошибка при парсинге поля: {e}")
                    topic_data.fields[field_name] = None  # Set to None and continue

            self.data_saver.save_metadata_item(topic_data)
            self.processed_topic_ids.add(topic_id)
            self.items_since_last_save += 1
            self.total_processed_count += 1

            if self.items_since_last_save >= self.config.save_every_n_items:
                self._save_state()

        except Exception as e:
            logger.exception(f"[{topic_id}] Критическая ошибка при обработке страницы {topic_url}: {e}")
        finally:
            # After processing a topic page, it's a good idea to ensure the downloader's page
            # reference is either cleared or explicitly handled if the main page (self.page) might close.
            # For now, if self.page is closed in _scrape_site's finally, downloader's page will become stale.
            # ResourceDownloader.set_page(None) could be called if self.page is about to be closed.
            # This is handled by set_page in the next iteration or scrape_site's finally block.
            pass

    def _scrape_site(self):
        if not self.browser_context:  # Changed from self.context
            logger.critical("Контекст браузера Playwright не инициализирован. Невозможно начать скрапинг.")
            return

        for start_url in self.config.start_urls:
            logger.info(f"\n{'=' * 20} Начало обработки стартового URL: {start_url} {'=' * 20}")
            self.page = None  # Ensure page is reset for this start_url loop
            if self.resource_downloader:  # Clear page from downloader too
                self.resource_downloader.set_page(None)

            try:
                self.page = self.browser_context.new_page()  # Create a new page
                logger.debug(f"Создана новая страница для {start_url}")
                if self.resource_downloader:  # Set page for downloader
                    self.resource_downloader.set_page(self.page)

                current_url: Optional[str] = start_url
                page_num = 1

                while current_url:
                    logger.info(f"\n--- Обработка страницы списка #{page_num} для {start_url}: {current_url} ---")
                    if not self._navigate_to(current_url):
                        logger.error(
                            f"Не удалось загрузить страницу списка: {current_url}. Прерывание для {start_url}.")
                        break

                    # Optional: Wait for user actions or specific conditions on list page
                    # logger.info(f"Ожидание {10} секунд на странице списка для возможных действий пользователя...")
                    # time.sleep(10) # Consider removing or making configurable if not always needed

                    html_content = self._get_page_content()
                    if not html_content:
                        logger.error(
                            f"Не удалось получить контент страницы списка: {current_url}. Прерывание для {start_url}.")
                        break

                    soup = BeautifulSoup(html_content, 'lxml')
                    previews = soup.select(self.config.selectors['topic_preview'])
                    logger.info(f"Найдено {len(previews)} превью топиков на странице.")

                    topic_urls_on_page = []
                    for preview_idx, preview in enumerate(previews):
                        link_tag = preview.select_one(self.config.selectors['topic_link'])
                        if link_tag and link_tag.get('href'):
                            topic_relative_url = link_tag.get('href')
                            topic_absolute_url = urllib.parse.urljoin(current_url, topic_relative_url)
                            topic_id_check = TopicData.generate_id(topic_absolute_url)
                            if topic_id_check not in self.processed_topic_ids:
                                topic_urls_on_page.append(topic_absolute_url)
                            else:
                                logger.trace(
                                    f"Топик {topic_absolute_url} (ID: {topic_id_check}) уже обработан, пропуск из списка.")
                        else:
                            logger.warning(
                                f"Превью #{preview_idx + 1}: не удалось найти ссылку на топик (селектор: {self.config.selectors['topic_link']})")

                    logger.info(
                        f"Найдено {len(topic_urls_on_page)} новых ссылок на топики для обработки на {current_url}.")

                    for i, topic_url_item in enumerate(topic_urls_on_page):
                        logger.info(
                            f"--- Обработка топика [{i + 1}/{len(topic_urls_on_page)}] со страницы {page_num} ({current_url}) ---")
                        # _process_topic_page will navigate self.page to topic_url_item
                        # and update resource_downloader's page reference.
                        self._process_topic_page(topic_url_item)
                        # After _process_topic_page, self.page is on the topic_url_item.
                        # For the next topic or next list page, we need to navigate away.
                        # The next _navigate_to (either for next topic or next list page) will handle this.

                    next_page_tag = soup.select_one(self.config.selectors['pagination_next'])
                    if next_page_tag and next_page_tag.get('href'):
                        next_page_relative_url = next_page_tag.get('href')
                        if next_page_relative_url.startswith(
                                ('javascript:', '#')) or not next_page_relative_url.strip():
                            logger.info(
                                f"Ссылка 'далее' невалидна ({next_page_relative_url}). Завершение пагинации для {start_url}.")
                            current_url = None
                        else:
                            current_url = urllib.parse.urljoin(current_url, next_page_relative_url)
                            page_num += 1
                            logger.debug(f"Найдена следующая страница ({page_num}): {current_url}")
                    else:
                        logger.info(f"Ссылка на следующую страницу не найдена для {start_url}. Завершение пагинации.")
                        current_url = None
            except Exception as e:
                logger.exception(f"Ошибка во время обработки стартового URL {start_url}: {e}")
            finally:
                if self.page and not self.page.is_closed():
                    try:
                        self.page.close()
                        logger.debug(f"Страница для {start_url} закрыта.")
                    except Exception as e:
                        logger.error(f"Ошибка при закрытии страницы для {start_url}: {e}")
                self.page = None  # Clear ScraperApp's page reference
                if self.resource_downloader:  # Also clear it from downloader
                    self.resource_downloader.set_page(None)
            logger.info(f"\n{'=' * 20} Завершение обработки стартового URL: {start_url} {'=' * 20}")

    def run(self):
        try:
            self._initialize()
            if self.browser_context:  # Changed from self.context
                self._scrape_site()
            else:
                logger.critical(
                    "Контекст браузера Playwright не был успешно инициализирован. Скрапинг не может быть запущен.")
        except KeyboardInterrupt:
            logger.warning("Скрапинг прерван пользователем (KeyboardInterrupt).")
        except Exception as e:
            logger.exception(f"Критическая ошибка во время выполнения скрапера: {e}")
        finally:
            self._finalize()


rating_list = []  # Global, consider moving into a class or context if state becomes complex


def create_simple_copiright(topic_data: TopicData, value: Optional[List[str]], soup: BeautifulSoup):
    # This function now directly modifies topic_data.fields
    # The 'value' is the parsed copyright tags (expected to be a list of strings or None)

    # Process copyright tags
    if value and isinstance(value, list) and value:
        topic_data.fields["simple_copiright"] = value[0]  # Takes the first copyright tag
        # If you want all, it's already in topic_data.fields['tags_copyright'] = value
    elif isinstance(value, str):  # If somehow it's a single string from parser
        topic_data.fields["simple_copiright"] = value
    else:
        topic_data.fields["simple_copiright"] = None  # Or some default

    # Extract other stats
    # Note: These selectors should ideally be in config.json if they are generic enough
    # For now, hardcoding as an example of post-processing
    try:
        all_li_tags = soup.select('#tag-list > ul > li')  # More specific selector for Danbooru stats
        if not all_li_tags:  # Fallback for older structure or different sites
            all_li_tags = soup.find_all('li')

        for li in all_li_tags:
            text_content = li.get_text(separator=" ", strip=True)  # Get text more robustly

            if "Source:" in text_content:
                link_tag = li.find('a', href=True)
                if link_tag:
                    topic_data.fields["stat_source_url"] = urllib.parse.urljoin(topic_data.topic_url, link_tag['href'])

            if "Rating:" in text_content:
                # Example: "Rating: Safe" or "Rating: Explicit (some text)"
                # Regex might be more robust here
                try:
                    # Try to split and get the part after "Rating:"
                    rating_parts = re.split(r'Rating:\s*', text_content, flags=re.IGNORECASE)
                    if len(rating_parts) > 1:
                        # Take the text immediately following "Rating:", then split by space to get first word
                        potential_rating = rating_parts[1].split()[0].lower()
                        if potential_rating:
                            if potential_rating not in rating_list:  # Global rating_list
                                rating_list.append(potential_rating)
                                logger.trace(f"New rating found and added to global list: {potential_rating}")
                            topic_data.fields["stat_rating_raw"] = potential_rating
                except Exception as e_rating:
                    logger.warning(f"Could not parse rating from '{text_content}': {e_rating}")

    except Exception as e_stats:
        logger.error(f"Error in post-processor create_simple_copiright (stats extraction): {e_stats}")

    # The function modifies topic_data directly, so it doesn't need to return the 'value' for 'tags_copyright'
    # The original 'tags_copyright' value is already set in topic_data.fields by the main parsing loop.
    # If this post-processor is *only* for 'tags_copyright', it should return the modified value.
    # But since it adds new fields, it's more of a general topic data enhancer.
    # For clarity, if it's a post-processor FOR 'tags_copyright', it should return the value for 'tags_copyright'.
    # The current implementation adds new fields, which is also a valid use of post-processing.
    # To avoid confusion, ensure the original 'value' for 'tags_copyright' is preserved or intentionally modified.
    return value  # Return the original (or potentially modified) value for the field it's registered for


# --- Точка входа ---
if __name__ == "__main__":
    CONFIG_FILE = "danbooru.json"  # Make sure this matches your actual config file
    try:
        config = ProjectConfig.load_from_file(CONFIG_FILE)

        # Post-processors: key is field_name from fields_to_parse
        processors = {
            "tags_copyright": create_simple_copiright
            # This means create_simple_copiright will be called *after* 'tags_copyright' is parsed.
            # The 'value' passed to it will be the result of parsing 'tags_copyright'.
        }

        app = ScraperApp(config, processors)
        app.run()
    except FileNotFoundError:
        logger.critical(f"Не найден файл конфигурации {CONFIG_FILE}. Убедитесь, что он существует.")
    except ValueError as e:  # Catches JSON errors, missing keys from ProjectConfig.load_from_file
        logger.critical(f"Ошибка в файле конфигурации {CONFIG_FILE} или его структуре: {e}")
    except PlaywrightError as e:  # More specific for Playwright issues during init
        logger.critical(f"Ошибка Playwright при инициализации: {e}")
    except Exception as e:
        logger.critical(f"Критическая ошибка при инициализации или загрузке конфигурации: {e}", exc_info=True)

    if rating_list:
        logger.info(f"Обнаруженные варианты рейтинга за сессию: {sorted(list(set(rating_list)))}")