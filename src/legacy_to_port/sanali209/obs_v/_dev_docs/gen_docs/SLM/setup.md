# Инструкции по установке SLM

Это руководство содержит подробные инструкции по установке и настройке системы SLM и всех её компонентов.

## Системные требования

### Базовые требования
- Python 3.8 или выше
- 4 ГБ ОЗУ (минимум)
- 8 ГБ свободного места на диске
- CUDA-совместимая видеокарта (опционально)

### Зависимости
- exiftool (для работы с метаданными)
- MongoDB (для хранения данных)
- PyTorch (для ML-компонентов)
- OpenCV (для обработки изображений)

## Пошаговая установка

### 1. Подготовка окружения

#### Windows
```bash
# 1. Установка Python
# Скачайте и установите Python с python.org

# 2. Установка MongoDB
# Скачайте и установите MongoDB Community Edition

# 3. Установка ExifTool
# Распакуйте exiftool.exe в директорию Python/SLM/
```

#### Linux
```bash
# 1. Установка Python и pip
sudo apt update
sudo apt install python3.8 python3-pip

# 2. Установка MongoDB
sudo apt install mongodb

# 3. Установка ExifTool
sudo apt install libimage-exiftool-perl
```

### 2. Клонирование репозитория
```bash
git clone https://github.com/your-org/SLM.git
cd SLM
```

### 3. Установка Python-зависимостей

#### Основные зависимости
```bash
pip install -r requirements.txt
```

#### ML-компоненты (с CUDA)
```bash
pip install torch torchvision torchaudio --index-url https://download.pytorch.org/whl/cu118
```

#### ML-компоненты (CPU)
```bash
pip install torch torchvision torchaudio
```

### 4. Настройка конфигурации

#### Создание конфигурационного файла
```bash
cp config.example.yml config.yml
```

#### Настройка параметров
```yaml
# config.yml
database:
  host: localhost
  port: 27017
  name: slm_db

storage:
  path: /path/to/storage
  temp: /path/to/temp

ai:
  openai_key: your_key_here
  model: gpt-3.5-turbo
```

### 5. Настройка переменных окружения

#### Windows
```powershell
setx SLM_CONFIG_PATH "C:\path\to\config.yml"
setx OPENAI_API_KEY "your-api-key"
```

#### Linux/macOS
```bash
echo 'export SLM_CONFIG_PATH="/path/to/config.yml"' >> ~/.bashrc
echo 'export OPENAI_API_KEY="your-api-key"' >> ~/.bashrc
source ~/.bashrc
```

## Проверка установки

### 1. Базовая проверка
```bash
python -c "import SLM; print(SLM.__version__)"
```

### 2. Проверка компонентов
```python
from SLM.core import test_installation

# Запуск тестов установки
test_installation()
```

### 3. Запуск модульных тестов
```bash
python -m pytest tests/
```

## Типичные проблемы

### 1. Ошибки импорта
```
ModuleNotFoundError: No module named 'SLM'
```
**Решение**: Убедитесь, что путь к модулю добавлен в PYTHONPATH
```bash
export PYTHONPATH="${PYTHONPATH}:/path/to/SLM"
```

### 2. Проблемы с MongoDB
```
MongoConnectionError: Connection refused
```
**Решение**: Проверьте, что MongoDB запущен
```bash
# Windows
net start MongoDB

# Linux
sudo service mongodb start
```

### 3. Ошибки CUDA
```
RuntimeError: CUDA driver initialization failed
```
**Решение**: Проверьте установку CUDA и драйверов
```bash
nvidia-smi
python -c "import torch; print(torch.cuda.is_available())"
```

## Дополнительные настройки

### 1. Оптимизация производительности

#### MongoDB индексы
```python
from SLM.db import create_indexes
create_indexes()
```

#### Кэширование
```python
# config.yml
cache:
  enabled: true
  path: /path/to/cache
  max_size: 10GB
```

### 2. Настройка логирования
```python
# config.yml
logging:
  level: INFO
  file: logs/slm.log
  format: '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
```

### 3. Безопасность
```python
# config.yml
security:
  enable_auth: true
  ssl_cert: /path/to/cert.pem
  allowed_hosts: ['localhost', '127.0.0.1']
```

## Обновление системы

### 1. Обновление кода
```bash
git pull origin main
```

### 2. Обновление зависимостей
```bash
pip install -r requirements.txt --upgrade
```

### 3. Миграция данных
```bash
python -m SLM.db.migrations
```

## Дополнительные ресурсы

- [Полная документация](https://slm.readthedocs.io/)
- [API Reference](https://slm.readthedocs.io/api/)
- [Примеры использования](https://github.com/your-org/SLM/examples)
- [FAQ](https://slm.readthedocs.io/faq/)
