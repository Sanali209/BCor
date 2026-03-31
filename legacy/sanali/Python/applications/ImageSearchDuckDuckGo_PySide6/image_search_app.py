import sys
import os
import requests
import re # Для очистки имени файла/директории
import json # Для сохранения метаданных
from PySide6.QtWidgets import (
    QApplication, QWidget, QVBoxLayout, QHBoxLayout,
    QLineEdit, QPushButton, QLabel, QFileDialog,
    QScrollArea, QGridLayout, QSpinBox, QMessageBox
)
from PySide6.QtGui import QPixmap, QImage
from PySide6.QtCore import Qt, QThread, Signal
from duckduckgo_search import DDGS

class ImageDownloaderThread(QThread):
    image_downloaded = Signal(QPixmap, str) # Pixmap and original URL
    finished_one = Signal()
    error_occurred = Signal(str)

    def __init__(self, image_result_data, download_path, base_filename):
        super().__init__()
        self.image_result_data = image_result_data # Полные данные о результате изображения
        self.url = image_result_data.get('image')
        self.download_path = download_path
        self.base_filename = base_filename # Имя файла без расширения

    def run(self):
        if not self.url:
            self.error_occurred.emit(f"Отсутствует URL изображения в данных: {self.image_result_data.get('title', 'Без названия')}")
            self.finished_one.emit()
            return
        
        image_filename_ext = os.path.splitext(self.url.split("?")[0])[-1]
        if not image_filename_ext or len(image_filename_ext) > 5 or len(image_filename_ext) < 2 :
            image_filename_ext = ".jpg" # Default extension
        
        image_full_filename = self.base_filename + image_filename_ext
        metadata_filename = self.base_filename + ".json"
        try:
            response = requests.get(self.url, stream=True, timeout=10)
            response.raise_for_status()

            image = QImage()
            image.loadFromData(response.content)
            pixmap = QPixmap.fromImage(image)

            if not pixmap.isNull():
                # Save the full image
                full_image_path = os.path.join(self.download_path, image_full_filename)
                if not os.path.exists(self.download_path):
                    os.makedirs(self.download_path) # Это должно быть сделано раньше, но на всякий случай
                
                # Try to save in original format if possible, otherwise PNG
                saved_successfully = False
                # Используем image_full_filename для определения расширения
                if image_full_filename.lower().endswith(('.png', '.jpg', '.jpeg', '.gif', '.bmp')):
                    try:
                        with open(full_image_path, 'wb') as f:
                            f.write(response.content)
                        saved_successfully = True
                    except Exception as e:
                        print(f"Error saving in original format ({image_full_filename}): {e}, falling back to PNG")
                
                if not saved_successfully:
                    # Если оригинальное расширение не сработало или не было одним из известных,
                    # пытаемся сохранить как PNG, изменив имя файла.
                    png_image_full_filename = self.base_filename + ".png"
                    full_image_path = os.path.join(self.download_path, png_image_full_filename)
                    if not pixmap.save(full_image_path): 
                         self.error_occurred.emit(f"Не удалось сохранить изображение: {png_image_full_filename}")
                         self.finished_one.emit()
                         return
                    else:
                        # Обновляем имя файла, если сохранили как PNG
                        image_full_filename = png_image_full_filename


                # Save metadata as a JSON sidecar file
                metadata_file_path = os.path.join(self.download_path, metadata_filename)
                try:
                    with open(metadata_file_path, 'w', encoding='utf-8') as mf:
                        json.dump(self.image_result_data, mf, ensure_ascii=False, indent=4)
                except Exception as e:
                    self.error_occurred.emit(f"Не удалось сохранить метаданные для {image_full_filename}: {e}")
                    # Продолжаем, даже если метаданные не сохранились

                # Create a thumbnail for display
                thumbnail_pixmap = pixmap.scaled(150, 150, Qt.KeepAspectRatio, Qt.SmoothTransformation)
                self.image_downloaded.emit(thumbnail_pixmap, self.url) # URL используется как ключ для обновления UI
            else:
                self.error_occurred.emit(f"Не удалось загрузить изображение с URL: {self.url}")
        except requests.exceptions.RequestException as e:
            self.error_occurred.emit(f"Ошибка сети при загрузке {self.url}: {e}")
        except Exception as e:
            self.error_occurred.emit(f"Неизвестная ошибка при загрузке {self.url}: {e}")
        finally:
            self.finished_one.emit()


class ImageSearchApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Поиск изображений DuckDuckGo")
        self.setGeometry(100, 100, 800, 600)

        self.download_threads = []
        self.current_images_info = [] # Stores (url, filename)

        self.init_ui()

    def init_ui(self):
        main_layout = QVBoxLayout(self)

        # Search input
        search_layout = QHBoxLayout()
        self.search_input = QLineEdit()
        self.search_input.setPlaceholderText("Введите поисковый запрос...")
        search_layout.addWidget(self.search_input)

        self.max_results_input = QSpinBox()
        self.max_results_input.setMinimum(1)
        self.max_results_input.setMaximum(1000) # DDGS might have its own limits
        self.max_results_input.setValue(200)
        search_layout.addWidget(QLabel("Макс. результатов:"))
        search_layout.addWidget(self.max_results_input)

        self.search_button = QPushButton("Поиск")
        self.search_button.clicked.connect(self.perform_search)
        search_layout.addWidget(self.search_button)
        main_layout.addLayout(search_layout)

        # Download directory
        dir_layout = QHBoxLayout()
        self.dir_label = QLabel("Директория для скачивания: не выбрана")
        dir_layout.addWidget(self.dir_label)
        self.select_dir_button = QPushButton("Выбрать основную директорию")
        self.select_dir_button.clicked.connect(self.select_download_directory)
        dir_layout.addWidget(self.select_dir_button)
        main_layout.addLayout(dir_layout)
        self.base_download_directory = "" # Изменено имя переменной

        # Image display area
        self.scroll_area = QScrollArea()
        self.scroll_area.setWidgetResizable(True)
        self.scroll_content_widget = QWidget()
        self.image_grid_layout = QGridLayout(self.scroll_content_widget)
        self.scroll_area.setWidget(self.scroll_content_widget)
        main_layout.addWidget(self.scroll_area)
        
        # Status label
        self.status_label = QLabel("")
        main_layout.addWidget(self.status_label)

        self.search_input.returnPressed.connect(self.perform_search)


    def select_download_directory(self):
        directory = QFileDialog.getExistingDirectory(self, "Выберите основную директорию для сохранения")
        if directory:
            self.base_download_directory = directory # Изменено имя переменной
            self.dir_label.setText(f"Основная директория: {directory}")

    def _sanitize_filename(self, name):
        # Удаляем недопустимые символы и заменяем пробелы на подчеркивания
        name = re.sub(r'[\\/*?:"<>|]', "", name)
        name = re.sub(r'\s+', '_', name)
        return name[:100] # Ограничиваем длину

    def perform_search(self):
        query = self.search_input.text()
        max_results = self.max_results_input.value()

        if not query:
            QMessageBox.warning(self, "Внимание", "Пожалуйста, введите поисковый запрос.")
            return

        if not self.base_download_directory: # Изменено имя переменной
            QMessageBox.warning(self, "Внимание", "Пожалуйста, выберите основную директорию для скачивания.")
            return
        
        # Создаем поддиректорию для текущего поиска
        search_specific_dirname = self._sanitize_filename(query)
        current_search_download_path = os.path.join(self.base_download_directory, search_specific_dirname)
        
        if not os.path.exists(current_search_download_path):
            try:
                os.makedirs(current_search_download_path)
            except OSError as e:
                QMessageBox.critical(self, "Ошибка", f"Не удалось создать директорию для поиска: {current_search_download_path}\n{e}")
                self.status_label.setText(f"Ошибка создания директории: {e}")
                return

        self.clear_image_grid()
        self.status_label.setText(f"Поиск изображений для '{query}'...")
        QApplication.processEvents() # Update UI

        try:
            with DDGS() as ddgs:
                results = list(ddgs.images(
                    keywords=query,
                    region='wt-wt',
                    safesearch='off', # Изменено на 'off'
                    size=None,
                    color=None,
                    type_image=None,
                    layout=None,
                    license_image=None,
                    max_results=max_results 
                ))
            
            self.current_images_info = []
            if not results:
                self.status_label.setText(f"Изображения по запросу '{query}' не найдены.")
                return

            self.status_label.setText(f"Найдено {len(results)} изображений. Загрузка...")
            
            self.download_threads = []
            self.images_loaded_count = 0
            self.total_images_to_load = len(results)

            for i, result in enumerate(results):
                image_url = result.get('image')
                if image_url:
                    # Create a base filename (without extension)
                    # Используем более короткую и уникальную часть запроса для имени файла
                    query_part_for_filename = self._sanitize_filename(query) 
                    base_filename_for_item = f"{query_part_for_filename}_{i}"
                                        
                    self.current_images_info.append({'url': image_url, 'base_filename': base_filename_for_item, 'pixmap_widget': None, 'full_result': result})

                    # Передаем result (полные данные) и base_filename_for_item
                    thread = ImageDownloaderThread(result, current_search_download_path, base_filename_for_item)
                    thread.image_downloaded.connect(self.add_image_to_grid)
                    thread.finished_one.connect(self.check_if_all_loaded)
                    thread.error_occurred.connect(self.handle_download_error)
                    self.download_threads.append(thread)
                    thread.start()
        
        except Exception as e:
            self.status_label.setText(f"Ошибка при поиске: {e}")
            QMessageBox.critical(self, "Ошибка", f"Произошла ошибка при поиске: {e}")


    def add_image_to_grid(self, pixmap, url):
        if pixmap.isNull():
            print(f"Получен пустой pixmap для URL: {url}")
            return

        image_label = QLabel()
        image_label.setPixmap(pixmap)
        image_label.setFixedSize(150, 150)
        image_label.setAlignment(Qt.AlignCenter)
        
        # Store the label widget with its info
        for img_info in self.current_images_info:
            if img_info['url'] == url and img_info['pixmap_widget'] is None:
                img_info['pixmap_widget'] = image_label
                break

        row = self.images_loaded_count // 5
        col = self.images_loaded_count % 5
        self.image_grid_layout.addWidget(image_label, row, col)
        self.images_loaded_count += 1
        self.status_label.setText(f"Загружено {self.images_loaded_count}/{self.total_images_to_load} изображений...")


    def check_if_all_loaded(self):
        all_finished = all(thread.isFinished() for thread in self.download_threads)
        if all_finished:
            self.status_label.setText(f"Загрузка завершена. Отображено {self.images_loaded_count} из {self.total_images_to_load} найденных изображений.")
            # Clean up threads
            self.download_threads = []


    def handle_download_error(self, error_message):
        print(f"Ошибка загрузки: {error_message}")
        # Optionally show a message to the user or log it more formally
        # self.status_label.setText(f"Ошибка: {error_message}")


    def clear_image_grid(self):
        self.images_loaded_count = 0
        self.current_images_info = []
        for i in reversed(range(self.image_grid_layout.count())):
            widget_to_remove = self.image_grid_layout.itemAt(i).widget()
            if widget_to_remove:
                widget_to_remove.deleteLater()
        # Stop any ongoing downloads
        for thread in self.download_threads:
            if thread.isRunning():
                thread.quit() # Request termination
                thread.wait() # Wait for it to finish
        self.download_threads = []


    def closeEvent(self, event):
        self.clear_image_grid() # Ensure threads are stopped
        event.accept()


if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = ImageSearchApp()
    window.show()
    sys.exit(app.exec())
