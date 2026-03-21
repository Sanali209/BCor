from PIL.ImageOps import expand
from langchain import OpenAI
from langchain.chains import ConversationChain
from langchain.memory import ConversationBufferMemory
from langchain.llms.base import LLM
from langchain.agents import Tool, initialize_agent, AgentType
from langchain.tools import tool
from langchain.utilities import SerpAPIWrapper
from typing import Optional
import requests
import flet as ft


class LMStudioLLM(LLM):
    api_url: str = "http://localhost:1234/api/chat"  # URL LM Studio API

    def _call(self, prompt: str, stop: Optional[str] = None) -> str:
        """Вызов LM Studio для получения ответа."""
        payload = {"prompt": prompt}
        response = requests.post(self.api_url, json=payload)
        if response.status_code == 200:
            return response.json().get("response", "")
        else:
            raise ValueError(f"Ошибка LM Studio: {response.status_code} - {response.text}")

    @property
    def _identifying_params(self):
        return {"api_url": self.api_url}

    @property
    def _llm_type(self):
        return "lmstudio"


class Llama32LLM(LLM):
    api_url: str = "http://localhost:1234/api/chat"  # URL Llama-3.2-1b-instruct API

    def _call(self, prompt: str, stop: Optional[str] = None) -> str:
        """Вызов Llama-3.2-1b-instruct для получения ответа."""
        payload = {"prompt": prompt}
        payload["nodel"] = "llama-3.2-1b-instruct"
        response = requests.post(self.api_url, json=payload)
        if response.status_code == 200:
            return response.json().get("response", "")
        else:
            raise ValueError(f"Ошибка Llama: {response.status_code} - {response.text}")

    @property
    def _identifying_params(self):
        return {"api_url": self.api_url}

    @property
    def _llm_type(self):
        return "llama-3.2-1b-instruct"


llm = Llama32LLM(api_url="http://localhost:1234/v1/chat/completions")

# Создание памяти для хранения истории чата
memory = ConversationBufferMemory()

# Создание цепочки общения
conversation = ConversationChain(llm=llm, memory=memory)


class KnowledgeBase:
    def __init__(self):
        self.text = ""

    def refresh(self, user_message):
        pass


knowledge_base = KnowledgeBase()


def process_user_input(user_message, role):
    knowledge_base.refresh(user_message)
    knowledge_results = knowledge_base.text
    knowledge_text = "\n".join(knowledge_results) if knowledge_results else "Нет дополнительных знаний."
    prompt = (
        f"Роль: {role}\n"
        f"Пользователь: {user_message}\n"
        f"Дополнительные знания:\n{knowledge_text}\n"
        "Ответьте, учитывая знания и предыдущий контекст."
    )
    return conversation.run(prompt)


@tool
def web_search_tool(query: str) -> str:
    """Выполнить веб-поиск для получения информации."""
    search = SerpAPIWrapper()
    results = search.run(query)
    return results


# Инициализация инструментов
tools = [
    Tool(name="Web Search", func=web_search_tool, description="Инструмент для выполнения веб-поиска."),
]


def main(page: ft.Page):
    page.title = "Чат с LangChain и LM Studio"
    page.horizontal_alignment = ft.CrossAxisAlignment.CENTER
    page.vertical_alignment = ft.MainAxisAlignment.CENTER

    document_editor = ft.TextField(value="Документ: пока пусто.", multiline=True, width=400, height=300)
    cnowledge_editor = ft.TextField(value="Знания: пока пусто.", multiline=True, width=400, height=300)
    role_field = ft.TextField(label="Роль помощника", value="Помощник", width=400, multiline=True)
    chat_history = ft.Column()
    input_field = ft.TextField(label="Введите сообщение", width=400)

    markdown_preview = ft.Text(value="", selectable=True, width=400, height=300)

    def send_message(e):
        user_message = input_field.value
        role = role_field.value
        if user_message.strip():
            response = process_user_input(user_message, role)
            chat_history.controls.append(ft.Text(f"Вы: {user_message}"))
            chat_history.controls.append(ft.Text(f"Модель: {response}"))
            page.update()
        input_field.value = ""

    def update_document_with_llm(e):
        current_content = document_editor.value
        prompt = (
            f"Вот текущий документ:\n{current_content}\n"
            "Предложите улучшение или продолжение документа."
        )
        new_content = conversation.run(prompt)
        document_editor.value = new_content
        page.update()

    def preview_markdown(e):
        markdown_preview.value = document_editor.value
        page.update()

    send_button = ft.ElevatedButton("Отправить", on_click=send_message)
    update_button = ft.ElevatedButton("Обновить документ с LLM", on_click=update_document_with_llm)
    preview_button = ft.ElevatedButton("Предпросмотр как Markdown", on_click=preview_markdown)

    page.add(
        ft.Row(
            [
                ft.Column([ft.Text("Документ"), document_editor, update_button, preview_button, markdown_preview],
                          expand=True),
                ft.Column([
                    ft.Column([ft.Text("Чат"), role_field, chat_history, ft.Row([input_field, send_button])],
                              expand=True),
                    ft.Column([ft.Text("Знания"), cnowledge_editor], expand=True),
                ], expand=True)
            ]
        , expand=True)
    )


if __name__ == "__main__":
    ft.app(target=main)
