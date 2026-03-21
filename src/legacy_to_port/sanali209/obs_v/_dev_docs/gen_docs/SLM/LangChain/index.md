# LangChain Integration (`LangChainHelper.py`)

Этот модуль предоставляет вспомогательные классы и функции для интеграции SLM с библиотекой LangChain, облегчая использование больших языковых моделей (LLM).

## Конфигурация

*   **Google AI Studio API Key:** В коде жестко задан ключ `GOOGLE_AI_STUDIO_API_KEY`. Для использования моделей Gemini через этот модуль необходимо убедиться, что этот ключ действителен или заменить его на свой. **Внимание:** Хранение ключей API непосредственно в коде является небезопасной практикой. Рекомендуется использовать переменные окружения или другие методы управления секретами.
    ```python
    # GOOGLE_AI_STUDIO_API_KEY = "AIzaSyB..." # Hardcoded key
    # genai.configure(api_key=GOOGLE_AI_STUDIO_API_KEY)
    ```

## Класс `GeminiLLM`

*   **Назначение:** Кастомная реализация базового класса `langchain.llms.base.LLM` для взаимодействия с моделями Google Gemini (например, `gemini-1.5-flash`) через библиотеку `google.generativeai`.
*   **Наследование:** `LLM`
*   **Атрибуты:**
    *   `model_name`: Имя модели Gemini (по умолчанию "gemini-1.5-flash").
*   **Методы:**
    *   `_call(prompt, stop=None)`: Основной метод, вызываемый LangChain. Он использует `genai.GenerativeModel` для генерации ответа на `prompt` и возвращает текст ответа.
    *   `_llm_type`: Возвращает "gemini".
    *   `_identifying_params`: Возвращает параметры, идентифицирующие модель.

## Функции

*   **`LLM_hugingface_model_inference(model_name="google/gemma-7b", temperature=0.1, max_length=4096)`:**
    *   **Назначение:** (Предположительно) Создание экземпляра `HuggingFaceHub` из LangChain для инференса моделей с Hugging Face Hub (например, Gemma, Mistral, Flan-T5).
    *   **Параметры:** `model_name`, `temperature`, `max_length`.
    *   **Возвращает:** Экземпляр `HuggingFaceHub`.
    *   **Примечание:** В текущем коде отсутствует импорт `HuggingFaceHub` (`from langchain.llms import HuggingFaceHub`).

*   **`vhat_bot_llm(model_name="google/gemma-7b", temperature=0.1, max_length=4096)`:**
    *   **Назначение:** (Предположительно) Создание пайплайна для генерации текста (`pipeline("text-generation", ...)`) и шаблона промпта (`PromptTemplate`) для возможного использования в чат-боте.
    *   **Примечание:** В текущем коде отсутствуют импорты `pipeline` (`from transformers import pipeline`) и `PromptTemplate` (`from langchain.prompts import PromptTemplate`). Функция не завершена (не возвращает созданные объекты).

## Пример использования `GeminiLLM`

```python
from Python.SLM.LangChain.LangChainHelper import GeminiLLM

# Убедитесь, что GOOGLE_AI_STUDIO_API_KEY настроен
llm = GeminiLLM(model_name="gemini-1.5-flash") 

prompt = "Explain the concept of Large Language Models in simple terms."
response = llm(prompt) 
# или response = llm.invoke(prompt) # В более новых версиях LangChain

print(response)
```

## Связанные концепции

*   [Core Concepts](../core_concepts.md)
*   [Architecture](../architecture.md)
*   [Setup Instructions](../setup.md) (Может потребоваться установка `langchain`, `google-generativeai`, `transformers`, `torch`)
*   [Chains Module](../chains/index.md) (LLM могут использоваться в цепочках)
*   [Actions Module](../actions/index.md) (LLM могут использоваться в действиях)
