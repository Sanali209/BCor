This is what has been accomplished by Custom Agent "Plan":

Я выполню поиск по коду, чтобы найти места, где может использоваться `mu`, метрики (MAE) и предсказания — это позволит точно указать файлы для правок. Ожидаю список файлов с вхождениями для составления плана.## Plan: Валидация и корректировка масштабирования mu

Кратко: проверить, правильно ли переводятся прогнозы модели (в диапазоне 0–1) в метки (1–10), измерить MAE на валидации, определить и внедрить корректный метод масштабирования (и/или коррекции параметра `mu`), интегрировать в код и добавить тесты/скрипты для автоматической проверки и наблюдения за изменениями.

Предположения
1. Модель возвращает прогнозы y_pred в диапазоне [0,1] (float).
2. Целевые метки y_true находятся в диапазоне [1,10] (int/float).
3. `mu` — скаляр или вектор с текущим коэффициентом/смещением, применяемым к предсказаниям (точное место использования — требуется найти в коде).
4. В проекте есть файлы с вычислением MAE и обучающими/валидационными циклами (например, `Python/SLM/files_db/annotation_tool/avg_rating_train.py`).

Контракт
- Вход:
  - y_pred: array-like, значения в [0,1] (или близко к этому)
  - y_true: array-like, значения в [label_min,label_max] (по умолчанию [1,10])
  - mu (опционально): float или None
  - comparisons: int (число сравнений/пар за период)
- Выход:
  - scaled_pred: array-like, значения в [label_min,label_max]
  - val_mae: float (MAE между scaled_pred и y_true)
  - mu_adjustment: float (новая/предложенная величина mu или дельта)
- Ошибки/исключения:
  - ValueError при несовпадающих размерах y_pred/y_true
  - ValueError при пустых входах или comparisons <= 0 (обрабатывать отдельно)
  - На входе NaN/inf — валидировать и выдавать предупреждение/исключение

Шаги (пошагово)
1. Аудит кода — найти места, где используется `mu`, вычисляется MAE или выполняется масштабирование
   - Поискать в репозитории: `grep -R "mu" -n .`, `grep -R "MAE" -n .`, `grep -R "rating" -n .`
   - Файлы, которые скорее всего будут правиться: `Python/SLM/files_db/annotation_tool/avg_rating_train.py`, модули инференса в `Python/SLM/vision/...`, `Python/applications/llm_tags_to_xmp/tagger_engine.py`. Планируйте добавить/поправить `Python/SLM/metrics/scaling_utils.py` и тесты `tests/test_scaling.py`.

2. Верификация текущих данных и вычислений (локальная проверка формул)
   - Проверить диапазоны: убедиться, что min(y_pred) >= 0 и max(y_pred) <= 1 (иначе — логировать и clip).
   - Формула базового масштабирования: scaled_pred = y_pred * (label_max - label_min) + label_min
     - Для label_min=1, label_max=10: scaled_pred = y_pred * 9 + 1
   - Проверить текущую роль `mu`. Если `mu` применяется как multiplicative factor: predicted_mu = mu * scaled_pred; если как смещение: predicted_mu = scaled_pred + mu. Зафиксировать поведение.

3. Вычислить MAE на валидации
   - MAE = mean(abs(scaled_pred - y_true))
   - Добавить вычисление в валидационный цикл (в `avg_rating_train.py`) и собрать:
     - mean_error = mean(scaled_pred - y_true) (показывает смещение)
     - mae = mean(abs(scaled_pred - y_true))

4. Определить политику корректировки `mu`
   - Рекомендация A (аддитивная коррекция, предпочтительна): mu_new = mu_old + alpha * bias, где bias = mean(y_true - scaled_pred), alpha = learning_rate (например, alpha = 1 / comparisons или tuned = 0.1)
     - Преимущество: прямое исправление смещения.
   - Рекомендация B (мультипликативная коррекция): mu_new = mu_old * (1 + (error_percent/100) / max(1, comparisons))
     - error_percent = (mean(|y_true - scaled_pred|) / label_range) * 100
   - Рекомендация C (без mu): использовать только масштабирование (scaled_pred) и логировать mu как наблюдаемую метрику.
   - Пример формулы (аддитивно): mu_delta = alpha * bias; mu_new = mu_old + mu_delta

5. Интеграция в кодовую базу
   - Добавить/обновить модуль `Python/SLM/metrics/scaling_utils.py` с:
     - функции: `scale_predictions(y_pred, label_min=1, label_max=10) -> scaled_pred`
     - `compute_mae(y_true, scaled_pred) -> mae`
     - `adjust_mu(mu, bias, comparisons, method='add', alpha=None) -> mu_new`
   - Внедрить вызов в `avg_rating_train.py` и файлы инференса: заменять локальное масштабирование на вызов `scale_predictions`.
   - Логировать до/после: min/max y_pred, mean_bias, mae, mu_old -> mu_new, comparisons.

6. Тесты и скрипты
   - Создать `tests/test_scaling.py` с минимум 3 сценарииями (см. ниже).
   - Добавить скрипт `scripts/validate_mu.py`:
     - Загружает `preds.npy` и `labels.npy`, выполняет масштабирование, считает MAE и предлагает `mu_new`. Вывод в CSV/JSON.
   - Добавить CI/локальный тест: `python -m pytest tests/test_scaling.py`

Технические сниппеты/формулы (в виде одной строки)
- Базовое масштабирование: scaled = y_pred * (label_max - label_min) + label_min
- MAE: mae = mean(abs(scaled - y_true))
- Bias: bias = mean(y_true - scaled)
- Adд. коррекция mu: mu_new = mu_old + alpha * bias, alpha = 1 / max(1, comparisons)
- Мульт. коррекция mu (альтернатива): mu_new = mu_old * (1 + (mae/(label_max - label_min)) / max(1, comparisons))

Тесты (минимум 3 сценария)
1. Идеальный случай
   - y_pred = [0.0, 0.5, 1.0] => scaled = [1, 5.5, 10]; y_true = scaled
   - Ожидается: mae = 0, bias = 0, mu не меняется.
2. Постоянное недооценивание
   - y_pred = [0.0, 0.5, 1.0] => scaled = [1,5.5,10]; y_true = [2,6.5,11] (всегда +1)
   - Ожидается: mae = 1, bias = +1, mu_new = mu_old + alpha*1 (проверить корректность).
3. Шум + частичные выбросы
   - y_pred случайные в [0,1], y_true = scaled_pred + нормальный шум (std=1), + один выброс NaN
   - Ожидается: mae > 0, NaN корректно фильтруется, mu корректируется по bias устойчиво.

Возможные крайние случаи и их обработка
1. y_pred вне [0,1] — clip: y_pred = min(max(y_pred,0),1), логировать количество и диапазон выбросов.
2. y_true вне [label_min,label_max] — валидировать и при необходимости нормализовать/сигнализировать об ошибке данных.
3. comparisons = 0 — использовать alpha по умолчанию (например, 0.1) или не изменять mu; логировать предупреждение.
4. Малые батчи/малый N — использовать усреднение с экспоненциальным сглаживанием (EMA) для mu, чтобы избежать переправлений.
5. NaN/inf в входах — удалять/игнорировать соответствующие пары с логом.

Примеры команд (PowerShell)
- Запустить тесты: python -m pytest tests/test_scaling.py
- Запустить валидацию на файлах: python scripts/validate_mu.py --pred preds.npy --true labels.npy --label-min 1 --label-max 10
- Быстрая локальная проверка (одноразовый скрипт): python -c "import numpy as np; from SLM.metrics.scaling_utils import scale_predictions, compute_mae; p=np.array([0,0.5,1]); t=np.array([1,5.5,10]); print(compute_mae(t, scale_predictions(p)))"

Список файлов, которые, скорее всего, нужно изменить
- `Python/SLM/files_db/annotation_tool/avg_rating_train.py` (валидация, MAE логирование)
- Модули инференса/оценки в `Python/SLM/vision/...` (если используются предсказания рейтингов)
- `Python/applications/llm_tags_to_xmp/tagger_engine.py` (если там есть финализация рейтинга)
- Новый: `Python/SLM/metrics/scaling_utils.py` (утилиты масштабирования/коррекции mu)
- Новый: `scripts/validate_mu.py` (скрипт для оффлайн-проверки)
- Тесты: `tests/test_scaling.py`

Дальнейшие вопросы / варианты
1. Как именно используется `mu` сейчас — multiplicative или additive? (нужно подтвердить, чтобы выбрать формулу корректировки)
2. Хотите автообновление `mu` в продакшен/только валидационная рекомендация? (Option A: автоматический апдейт; Option B: предложить значение и логировать)
3. Нужна ли история изменений mu (лог/метрика) для мониторинга? Рекомендую хранить в CSV/MLFlow.

Это черновой план — подтвердите предположения про роль `mu` и укажите, хотите ли автоматическую коррекцию или только рекомендательную систему; после подтверждения дам точный набор правок и список кода/патчей для внедрения.
