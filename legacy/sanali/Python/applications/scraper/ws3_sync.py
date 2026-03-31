#TODO: improve download speed by changeable delay before download

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

import requests  # Keep for potential future use, though not strictly needed for Playwright download
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
    def __init__(self, config: ProjectConfig, context: APIRequestContext):
        self.config = config
        self.context = context  # Сохраняем sync API context
        self.field_name_regex_cache: Dict[str, re.Pattern] = {}
        self.field_configs: Dict[str, FieldConfig] = {
            field.name: field for field in config.fields_to_parse
        }

    # Методы _get_extension..., _format_path_component остаются без изменений

    def _get_extension_from_url(self, url: str) -> str:
        path = urllib.parse.urlparse(url).path
        ext = os.path.splitext(path)[1].lower()
        if ext in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.mp4', '.webm', '.jfif']:
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

    def download(self, resource_url: str, resource_field_name: str, topic_data: TopicData) -> Optional[str]:
        """
        Скачивает ресурс синхронно, используя self.context, и возвращает относительный путь.
        """
        if not resource_url:
            logger.warning(f"[{topic_data.topic_id}/{resource_field_name}] Пустой URL ресурса.")
            return None

        absolute_path = None  # Define for potential use in exception logging
        try:
            # 1. Определить первоначальное расширение по URL
            url_ext = self._get_extension_from_url(resource_url)

            # 2. Подготовить данные для форматирования пути
            format_data = {
                # Убедимся, что topic_id всегда строка и slugified
                "topic_id": slugify(str(topic_data.topic_id)),
                "field_name": slugify(resource_field_name),
                "ext": url_ext,
                **{fname: self._format_path_component(fvalue, fname)
                   for fname, fvalue in topic_data.fields.items()}
            }

            # 3. Сформировать первоначальный относительный путь
            try:
                relative_path = self.config.resource_save_path_pattern.format(**format_data)
            except KeyError as e:
                logger.error(
                    f"[{topic_data.topic_id}/{resource_field_name}] Ошибка в resource_save_path_pattern: ключ {e} не найден. URL: {resource_url}")
                return None
            except Exception as e:
                logger.error(
                    f"[{topic_data.topic_id}/{resource_field_name}] Неожиданная ошибка форматирования пути: {e}. URL: {resource_url}. Данные: {format_data}")
                return None

            absolute_path = os.path.join(self.config.save_path, relative_path)

            # 4. Проверка существования файла
            if not self.config.overwrite_resources and os.path.exists(absolute_path):
                logger.debug(
                    f"[{topic_data.topic_id}/{resource_field_name}] Ресурс уже существует ({relative_path}), overwrite_resources=False.")
                return relative_path

            # 5. Задержка перед скачиванием
            delay = self.config.download_delay_seconds
            delay += random.uniform(0, 3)  # Добавляем случайную задержку до 1 секунды
            if delay > 0:
                logger.debug(f"[{topic_data.topic_id}/{resource_field_name}] Пауза перед скачиванием: {delay:.2f} сек.")
                time.sleep(delay)

            # 6. Скачивание через Playwright Sync API
            logger.debug(
                f"[{topic_data.topic_id}/{resource_field_name}] Попытка скачивания ресурса через Playwright Sync API: {resource_url}")
            body_bytes: Optional[bytes] = None
            content_type: Optional[str] = None

            try:
                # Используем self.context напрямую с таймаутом из конфига
                # set context referrer here if needed
                self.context.set_extra_http_headers({"Referer": topic_data.topic_url})

                response = self.context.request.get(resource_url, timeout=self.config.download_timeout_ms)

                if not response.ok:
                    logger.error(
                        f"[{topic_data.topic_id}/{resource_field_name}] Playwright Sync API request failed for {resource_url} with status {response.status}")
                    # Не закрываем приложение здесь, просто возвращаем None
                    return None

                body_bytes = response.body()  # sync call
                content_type = response.headers.get('content-type')

                if not body_bytes:
                    logger.error(
                        f"[{topic_data.topic_id}/{resource_field_name}] Получено пустое тело ответа для: {resource_url}")
                    return None

                logger.debug(
                    f"Успешно получены байты для {resource_url} (Content-Type: {content_type}, Size: {len(body_bytes)})")

            except PlaywrightTimeoutError:
                logger.error(
                    f"[{topic_data.topic_id}/{resource_field_name}] Таймаут ({self.config.download_timeout_ms}ms) при скачивании ресурса: {resource_url}")
                return None
            except PlaywrightError as e:
                logger.error(
                    f"[{topic_data.topic_id}/{resource_field_name}] Playwright Sync API request error for {resource_url}: {e}")
                return None
            except Exception as e:  # Ловим и другие возможные ошибки запроса (e.g., network issues)
                logger.error(
                    f"[{topic_data.topic_id}/{resource_field_name}] Unexpected Sync API request error for {resource_url}: {e}")
                return None

            # 7. Уточнение расширения по Content-Type
            content_type_ext = self._get_extension_from_content_type(content_type)
            final_ext = content_type_ext if content_type_ext and content_type_ext != 'bin' else url_ext

            # 8. Перегенерация пути, если расширение уточнилось
            if final_ext != url_ext:
                logger.debug(
                    f"[{topic_data.topic_id}/{resource_field_name}] Расширение уточнено: {url_ext} -> {final_ext} (Content-Type: {content_type})")
                format_data["ext"] = final_ext
                try:
                    relative_path = self.config.resource_save_path_pattern.format(**format_data)
                except KeyError as e:
                    logger.error(
                        f"[{topic_data.topic_id}/{resource_field_name}] Ошибка в resource_save_path_pattern (уточн. ext): ключ {e} не найден. URL: {resource_url}")
                    return None
                except Exception as e:
                    logger.error(
                        f"[{topic_data.topic_id}/{resource_field_name}] Неожиданная ошибка форматирования пути (уточн. ext): {e}. URL: {resource_url}. Данные: {format_data}")
                    return None

                absolute_path = os.path.join(self.config.save_path, relative_path)
                if not self.config.overwrite_resources and os.path.exists(absolute_path):
                    logger.debug(
                        f"[{topic_data.topic_id}/{resource_field_name}] Ресурс уже существует (уточненный путь: {relative_path}), overwrite_resources=False.")
                    return relative_path

            # 9. Создание директории
            absolute_dir = os.path.dirname(absolute_path)
            os.makedirs(absolute_dir, exist_ok=True)

            # 10. Сохранение файла
            with open(absolute_path, 'wb') as f:
                f.write(body_bytes)

            logger.info(f"[{topic_data.topic_id}/{resource_field_name}] Ресурс сохранен: {relative_path}")
            return relative_path

        except IOError as e:
            # Log absolute_path if it was determined
            log_path = absolute_path if absolute_path else "unknown path"
            logger.error(
                f"[{topic_data.topic_id}/{resource_field_name}] Ошибка ввода-вывода при сохранении ресурса {log_path}: {e}")
            return None
        except Exception as e:
            logger.exception(
                f"[{topic_data.topic_id}/{resource_field_name}] Неожиданная ошибка при обработке ресурса {resource_url}: {e}")
            return None


# --- Основной класс приложения (модифицирован для sync API) ---

class ScraperApp:
    def __init__(self, config: ProjectConfig, post_processors: Optional[Dict[str, callable]] = None):
        self.config = config
        self.data_saver = DataSaver(config)
        # ResourceDownloader инициализируется позже, в _initialize, когда context будет создан
        self.resource_downloader: Optional[ResourceDownloader] = None
        self.processed_topic_ids: Set[str] = set()  # Убедимся, что это Set[str]
        self.items_since_last_save: int = 0
        self.total_processed_count: int = 0
        self.session_start_time = time.time()
        self.filter_regex_cache: Dict[str, re.Pattern] = {}
        # min_content_lenth уже в config
        # Playwright Sync objects - будут инициализированы в _initialize
        self.playwright: Optional[Playwright] = None
        self.browser: Optional[Browser] = None
        self.context: Optional[APIRequestContext] = None  # Контекст используется и для страниц, и для API
        self.page: Optional[Page] = None

        # Сохраняем словарь пост-процессоров
        self.post_processors = post_processors if post_processors else {}
        logger.info(f"Загружено {len(self.post_processors)} функций пост-обработки.")

    def _initialize(self):
        """Инициализация перед запуском скрапинга, включая запуск Playwright."""
        logger.info("=" * 30 + " Инициализация Скрапера (Sync) " + "=" * 30)
        logger.info(f"Стартовые URL: {self.config.start_urls}")  # Log list of URLs
        logger.info(f"Путь сохранения: {self.config.save_path}")
        logger.info(f"Шаблон сохранения ресурсов: {self.config.resource_save_path_pattern}")
        logger.info(f"Сохранять каждые {self.config.save_every_n_items} элементов.")
        logger.info(f"Таймаут навигации: {self.config.navigation_timeout_ms} мс")
        logger.info(f"Таймаут скачивания ресурсов: {self.config.download_timeout_ms} мс")

        progress_ids = self.data_saver.load_progress()
        metadata_ids = self.data_saver.load_metadata_ids()
        # Объединяем множества строк
        self.processed_topic_ids = progress_ids.union(metadata_ids)
        logger.info(f"Всего уникальных ID для пропуска: {len(self.processed_topic_ids)}")

        # --- Запуск Playwright Sync ---
        logger.info("Запуск Playwright (sync)...")
        try:
            self.playwright = sync_playwright().start()
            # Можно выбрать firefox или webkit
            self.browser = self.playwright.chromium.launch(headless=False)  # headless=False для отладки
            self.context = self.browser.new_context(
                user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/91.0.4472.124 Safari/537.36',
                # Можно добавить viewport, locale и т.д.
                viewport={'width': 1920, 'height': 1080}
                #,extra_http_headers={"Referrer": "https://example.com"},
                # locale='ru-RU'
            )
            # Опционально: блокировка ресурсов через route (sync)
            # self.context.route("**/*.{png,jpg,jpeg,gif,svg,css,woff,woff2}", lambda route: route.abort())

            # Устанавливаем стандартный таймаут для навигации контекста/страницы
            self.context.set_default_navigation_timeout(self.config.navigation_timeout_ms)
            # Таймаут для действий (клики, заполнение и т.д.)
            # self.context.set_default_timeout(some_other_timeout)

            # self.page = self.context.new_page() # Page will be created per start_url now
            logger.info("Playwright (sync) context успешно запущен и настроен.")

            # --- Инициализация ResourceDownloader с созданным context ---
            self.resource_downloader = ResourceDownloader(self.config, self.context)

        except PlaywrightError as e:
            logger.error(f"Ошибка инициализации Playwright (sync): {e}")
            # Попытка закрыть то, что могло запуститься
            self._safe_close_playwright()
            raise  # Прерываем выполнение приложения
        except Exception as e:
            logger.error(f"Неожиданная ошибка при инициализации Playwright (sync): {e}")
            self._safe_close_playwright()
            raise

        self.items_since_last_save = 0
        self.total_processed_count = 0
        self.session_start_time = time.time()
        logger.info("Инициализация завершена.")

    def _safe_close_playwright(self):
        """Безопасное закрытие ресурсов Playwright, если они были созданы."""
        logger.warning("Попытка безопасного закрытия Playwright...")
        # Check if page exists and is not already closed
        if self.page and not self.page.is_closed():
            try:
                self.page.close()
                logger.debug("Страница Playwright закрыта.")
            except Exception as e:
                logger.error(f"Ошибка при закрытии страницы: {e}")
        elif self.page and self.page.is_closed():
            logger.debug("Страница Playwright уже была закрыта.")

        if self.context:
            try:
                self.context.close()
                logger.debug("Контекст Playwright закрыт.")
            except Exception as e:
                logger.error(f"Ошибка при закрытии контекста: {e}")
        if self.browser:
            try:
                self.browser.close()
            except Exception as e:
                logger.error(f"Ошибка при закрытии браузера: {e}")
        if self.playwright:
            try:
                self.playwright.stop()
            except Exception as e:
                logger.error(f"Ошибка при остановке Playwright: {e}")
        logger.info("Закрытие Playwright завершено (или не требовалось).")

    def _finalize(self):
        """Завершение работы скрапера, включая закрытие Playwright."""
        logger.info("=" * 30 + " Завершение Скрапера (Sync) " + "=" * 30)
        if self.items_since_last_save > 0:
            logger.info("Выполнение финального сохранения прогресса...")
            self._save_state()
        else:
            logger.info("Нет несохраненных элементов для финального сохранения.")

        # --- Закрытие Playwright Sync ---
        self._safe_close_playwright()

        elapsed_time = time.time() - self.session_start_time
        logger.info(f"Скрапинг завершен. Обработано за сессию: {self.total_processed_count} топиков.")
        logger.info(f"Общее время работы сессии: {elapsed_time:.2f} секунд.")
        logger.info("=" * 70)

    def _save_state(self):
        """Сохраняет текущее состояние (прогресс)."""
        logger.info(f"Периодическое сохранение прогресса ({len(self.processed_topic_ids)} ID)...")
        self.data_saver.save_progress(self.processed_topic_ids)
        self.items_since_last_save = 0

    # _parse_field остается без изменений, т.к. работает с BeautifulSoup

    def _parse_field(self, soup: BeautifulSoup, field_conf: FieldConfig, base_url: str, topic_id: str) -> Any:
        """Извлекает данные для поля, применяет фильтрацию для текста."""
        elements = soup.select(field_conf.selector)
        field_name = field_conf.name

        if not elements:
            if field_conf.required:
                logger.error(
                    f"[{topic_id}/{field_name}] Обязательное поле не найдено (селектор: {field_conf.selector})")
                raise ValueError(f"Required field '{field_name}' not found")
            else:
                logger.trace(
                    f"[{topic_id}/{field_name}] Необязательное поле не найдено (селектор: {field_conf.selector})")
                return None

        if field_conf.type == 'text':
            if field_conf.multiple:
                texts = [el.get_text(strip=True) for el in elements]
                if field_conf.filter_regex:
                    if field_conf.filter_regex not in self.filter_regex_cache:
                        try:
                            self.filter_regex_cache[field_conf.filter_regex] = re.compile(field_conf.filter_regex)
                            logger.debug(f"Скомпилировано regex для '{field_name}': {field_conf.filter_regex}")
                        except re.error as e:
                            logger.error(
                                f"[{topic_id}/{field_name}] Ошибка компиляции regex '{field_conf.filter_regex}': {e}. Фильтрация отключена.")
                            self.filter_regex_cache[field_conf.filter_regex] = None

                    compiled_regex = self.filter_regex_cache.get(field_conf.filter_regex)
                    if compiled_regex:
                        original_count = len(texts)
                        texts = [t for t in texts if not compiled_regex.search(t)]
                        filtered_count = len(texts)
                        if original_count != filtered_count:
                            logger.debug(
                                f"[{topic_id}/{field_name}] Отфильтровано {original_count - filtered_count}/{original_count} элементов regex: {field_conf.filter_regex}")
                    else:
                        logger.warning(
                            f"[{topic_id}/{field_name}] Не удалось применить фильтрацию (ошибка компиляции regex): {field_conf.filter_regex}")

                return texts if texts else None
            else:
                return elements[0].get_text(strip=True)

        elif field_conf.type == 'resource_url':
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
        """Обертка для page.goto с логированием и обработкой ошибок."""
        if not self.page:
            logger.error("Страница Playwright не инициализирована для навигации.")
            return False
        logger.debug(f"Переход на URL: {url}")
        try:
            # Используем таймаут, установленный для контекста/страницы
            response = self.page.goto(url, wait_until='domcontentloaded')
            if response is None or not response.ok:
                status = response.status if response else "N/A"
                logger.error(f"Ошибка при переходе на {url}: статус {status}")
                return False
            logger.debug(f"Успешно перешел на: {url} (Статус: {response.status})")
            # Дополнительная задержка после навигации, если требуется
            # if content size is less than 1000 bytes, we can wait for a while
            lenth = len(self.page.content())
            if lenth < 200000:
                logger.debug(f"Контент страницы {url} слишком короткий, возможно, требуется дополнительная задержка.")
                #wait user action and return inputh
                input(f"Пауза после перехода на {url}. Нажмите Enter для продолжения...")
            if self.config.navigate_delay_seconds > 0:
                time.sleep(self.config.navigate_delay_seconds)
            return True
        except PlaywrightTimeoutError:
            logger.error(f"Тайм-аут ({self.config.navigation_timeout_ms}ms) при переходе на URL: {url}")
            return False
        except PlaywrightError as e:
            # Может быть DNS error, connection refused и т.д.
            logger.error(f"Ошибка Playwright при переходе на {url}: {e}")
            return False
        except Exception as e:
            logger.error(f"Неожиданная ошибка при переходе на {url}: {e}")
            return False

    def _get_page_content(self) -> Optional[str]:
        """Обертка для page.content с логированием и обработкой ошибок."""
        if not self.page:
            logger.error("Страница Playwright не инициализирована для получения контента.")
            return None
        logger.debug("Получение контента страницы...")
        try:
            content = self.page.content()
            logger.debug(f"Контент получен (длина: {len(content)}).")
            return content
        except PlaywrightError as e:
            logger.error(f"Ошибка Playwright при получении контента: {e}")
            return None
        except Exception as e:
            logger.error(f"Неожиданная ошибка при получении контента: {e}")
            return None

    def _process_topic_page(self, topic_url: str):
        """Обрабатывает одну страницу топика с использованием sync API."""
        # Генерируем ID с использованием новой логики
        topic_id = TopicData.generate_id(topic_url)

        # Сравниваем строки
        if topic_id in self.processed_topic_ids:
            logger.debug(f"Пропуск уже обработанного топика: {topic_url} (ID: {topic_id})")
            return

        logger.info(f"Обработка топика: {topic_url} (ID: {topic_id})")

        # Используем обертку для навигации
        if not self._navigate_to(topic_url):
            logger.warning(f"Первая попытка перейти на страницу топика не удалась: {topic_url}. Повторная попытка...")
            # Повторная попытка навигации без input()
            if not self._navigate_to(topic_url):
                logger.error(
                    f"Вторая попытка перейти на страницу топика также не удалась: {topic_url}. Пропуск топика.")
                return

        # Используем обертку для получения контента
        html_content = self._get_page_content()
        if not html_content:
            logger.error(f"Не удалось получить контент страницы топика: {topic_url}. Пропуск.")
            return

        # Проверка длины контента
        if len(html_content) < self.config.min_topic_content_lent:
            logger.warning(
                f"Контент страницы топика слишком короткий ({len(html_content)} байт, < {self.config.min_topic_content_lent}): {topic_url}")
            # Решаем, что делать: пропустить или выдать ошибку. Пока пропускаем с warning.
            # raise RuntimeError(...) # Если это критично
            return

        try:
            soup = BeautifulSoup(html_content, 'lxml')  # или 'html.parser'
            topic_data = TopicData(topic_id=topic_id, topic_url=topic_url)

            # Шаг 1: Парсинг всех полей
            for field_conf in self.config.fields_to_parse:
                field_name = field_conf.name
                try:
                    value = self._parse_field(soup, field_conf, topic_url, topic_id)
                    if field_name in self.post_processors:
                        process_funct = self.post_processors[field_name]
                        value = process_funct(topic_data, value, soup)
                    if field_conf.type == 'resource_url' and value:
                        ext = self.resource_downloader._get_extension_from_url(value)
                        if ext in field_conf.exclude_extensions:
                            logger.debug(
                                f"[{topic_id}/{field_name}] Исключаем URL ресурса с расширением {ext}: {value}")
                            value = None
                        topic_data.resource_urls_to_download[field_name] = value
                        topic_data.fields[field_name] = None
                    else:
                        topic_data.fields[field_name] = value
                except ValueError as e:
                    logger.error(
                        f"Ошибка парсинга обязательного поля '{field_name}' для {topic_url}: {e}. Топик пропущен.")
                    return
                except Exception as e:
                    logger.error(f"[{topic_id}/{field_name}] Неожиданная ошибка при парсинге поля: {e}")
                    topic_data.fields[field_name] = None

            # Шаг 2: Скачивание ресурсов (использует sync ResourceDownloader)
            if self.resource_downloader and topic_data.resource_urls_to_download:
                logger.debug(
                    f"[{topic_id}] Найдено {len(topic_data.resource_urls_to_download)} URL ресурсов для скачивания.")
                for field_name, resource_url in topic_data.resource_urls_to_download.items():
                    res_ext = self.resource_downloader._get_extension_from_url(resource_url)

                    local_path = self.resource_downloader.download(
                        resource_url=resource_url,
                        resource_field_name=field_name,
                        topic_data=topic_data
                    )
                    topic_data.fields[field_name] = local_path  # Записываем путь или None
            elif not self.resource_downloader:
                logger.error("ResourceDownloader не инициализирован!")
            else:
                logger.debug(f"[{topic_id}] URL ресурсов для скачивания не найдены.")

            # Шаг 3: Сохранение метаданных и обновление состояния (без изменений)
            self.data_saver.save_metadata_item(topic_data)
            self.processed_topic_ids.add(topic_id)  # Добавляем строку ID
            self.items_since_last_save += 1
            self.total_processed_count += 1

            if self.items_since_last_save >= self.config.save_every_n_items:
                self._save_state()

        except Exception as e:
            logger.exception(f"Критическая ошибка при обработке страницы {topic_url}: {e}")

    def _scrape_site(self):
        """Основной цикл скрапинга сайта с пагинацией (sync) для нескольких стартовых URL."""
        if not self.context:
            logger.critical("Контекст Playwright не инициализирован. Невозможно начать скрапинг.")
            return

        for start_url in self.config.start_urls:
            time.sleep(10)
            logger.info(f"\n{'=' * 20} Начало обработки стартового URL: {start_url} {'=' * 20}")
            self.page = None  # Reset page reference
            try:
                self.page = self.context.new_page()  # Create a new page for this start_url
                logger.debug(f"Создана новая страница для {start_url}")
                current_url: Optional[str] = start_url
                page_num = 1

                while current_url:
                    time.sleep(1)
                    logger.info(f"\n--- Обработка страницы списка #{page_num} для {start_url}: {current_url} ---")
                    if page_num % 10 == 0:
                        time.sleep(30)
                    # Используем обертку для навигации
                    if not self._navigate_to(current_url):
                        logger.error(
                            f"Не удалось загрузить страницу списка: {current_url}. Прерывание для {start_url}.")
                        break  # Выход из while current_url

                    # Используем обертку для получения контента
                    html_content = self._get_page_content()
                    if not html_content:
                        logger.error(
                            f"Не удалось получить контент страницы списка: {current_url}. Прерывание для {start_url}.")
                        break  # Выход из while current_url

                    soup = BeautifulSoup(html_content, 'lxml')

                    previews = soup.select(self.config.selectors['topic_preview'])
                    logger.info(f"Найдено {len(previews)} превью топиков на странице.")

                    topic_urls_on_page = []
                    for preview in previews:
                        link_tag = preview.select_one(self.config.selectors['topic_link'])
                        if link_tag and link_tag.get('href'):
                            topic_relative_url = link_tag.get('href')
                            topic_absolute_url = urllib.parse.urljoin(current_url, topic_relative_url)
                            # Генерируем ID здесь, чтобы проверить, обработан ли он уже
                            topic_id = TopicData.generate_id(topic_absolute_url)
                            # Сравниваем строки
                            if topic_id not in self.processed_topic_ids:
                                topic_urls_on_page.append(topic_absolute_url)
                            else:
                                logger.trace(f"Топик {topic_absolute_url} (ID: {topic_id}) уже обработан, пропуск.")
                        else:
                            logger.warning(
                                f"Не удалось найти ссылку на топик в превью (селектор: {self.config.selectors['topic_link']})")

                    logger.info(f"Найдено {len(topic_urls_on_page)} новых ссылок на топики для обработки.")

                    # Обработка топиков
                    for i, topic_url in enumerate(topic_urls_on_page):
                        logger.info(
                            f"--- Обработка топика [{i + 1}/{len(topic_urls_on_page)}] со страницы {page_num} ---")
                        self._process_topic_page(topic_url)
                        # Задержка между обработкой топиков, если настроено (не путать с navigate_delay)
                        # if self.config.some_other_delay > 0: time.sleep(self.config.some_other_delay)

                    # Поиск следующей страницы (логика без изменений)
                    next_page_tag = soup.select_one(self.config.selectors['pagination_next'])
                    if next_page_tag and next_page_tag.get('href'):
                        next_page_relative_url = next_page_tag.get('href')
                        if next_page_relative_url.startswith(('javascript:', '#')) or not next_page_relative_url:
                            logger.info("Ссылка 'далее' невалидна. Завершение пагинации.")
                            current_url = None
                        else:
                            current_url = urllib.parse.urljoin(current_url, next_page_relative_url)
                            page_num += 1
                            logger.debug(f"Найдена следующая страница: {current_url}")
                            # Задержка перед переходом на след. страницу УЖЕ встроена в _navigate_to
                    else:
                        logger.info(
                            f"Ссылка на следующую страницу не найдена для {start_url}. Завершение пагинации для этого URL.")
                        current_url = None
                # Конец цикла while current_url
            except Exception as e:
                logger.exception(f"Ошибка во время обработки стартового URL {start_url}: {e}")
            finally:
                # Этот блок выполнится после завершения цикла while или при возникновении исключения в try
                if self.page and not self.page.is_closed():
                    try:
                        self.page.close()
                        logger.debug(f"Страница для {start_url} закрыта.")
                    except Exception as e:
                        logger.error(f"Ошибка при закрытии страницы для {start_url}: {e}")
                self.page = None  # Clear reference after closing or error

            logger.info(f"\n{'=' * 20} Завершение обработки стартового URL: {start_url} {'=' * 20}")

    def run(self):
        """Запускает весь процесс скрапинга."""
        try:
            self._initialize()  # Инициализирует Playwright sync
            # Проверяем только context, так как page создается для каждого start_url
            if self.context:  # Убедимся, что инициализация контекста прошла успешно
                self._scrape_site()
            else:
                logger.critical("Контекст Playwright не был успешно инициализирован. Скрапинг не может быть запущен.")
        except KeyboardInterrupt:
            logger.warning("Скрапинг прерван пользователем (KeyboardInterrupt).")
        except Exception as e:
            logger.exception(f"Критическая ошибка во время выполнения скрапера: {e}")
        finally:
            self._finalize()  # Гарантированно закрывает Playwright sync


rating_list = []


def create_simple_copiright(topic_data: TopicData, value, soup):
    try:
        topic_data.fields["simple_copiright"] = value[0]
    except Exception:
        topic_data.fields["simple_copiright"] = value
        topic_data.fields["tags_copyright"] = value

    # extract stat_rating_raw with regex

    result = soup.find_all('li')
    for li in result:
        if "Source:" in li.text:
            link = li.find('a')
            if link:
                topic_data.fields["stat_source_url"] = link.get('href')

        if "Rating:" in li.text:
            rating = li.text.split("Rating:")[-1].strip().lower()
            if rating:
                if rating not in rating_list:
                    rating_list.append(rating)
                topic_data.fields["stat_rating_raw"] = rating


# --- Точка входа ---
if __name__ == "__main__":
    # Используйте другое имя конфига, если он отличается
    CONFIG_FILE = "revers.json"
    try:
        config = ProjectConfig.load_from_file(CONFIG_FILE)
        processors = {"tags_copyright": create_simple_copiright}
        app = ScraperApp(config, processors)
        app.run()
    except FileNotFoundError:
        logger.critical(f"Не найден файл конфигурации {CONFIG_FILE}. Убедитесь, что он существует.")
    except ValueError as e:
        logger.critical(f"Ошибка в файле конфигурации {CONFIG_FILE}: {e}")
    except Exception as e:
        logger.critical(f"Критическая ошибка при инициализации или загрузке конфигурации: {e}", exc_info=True)
