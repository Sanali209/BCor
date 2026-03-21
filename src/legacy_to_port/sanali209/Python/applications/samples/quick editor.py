from PySide6.QtWidgets import QApplication, QWidget, QVBoxLayout, QTextEdit, QLineEdit, QPushButton, QLabel
from PySide6.QtCore import QTimer, QThreadPool, QRunnable, Signal, QObject
import asyncio
from langchain.chat_models import ChatOpenAI
from langchain.schema import HumanMessage

# Подключение к локальному серверу LM Studio с использованием Phi-3.1-mini-128k-instruct-GGUF
llm = ChatOpenAI(base_url="http://localhost:1234/v1", openai_api_key="lm-studio",
                 model_name="granite-3.1-8b-instruct-GGUF/granite-3.1-8b-instruct-Q4_K_M.gguf")


class SuggestionWorker(QRunnable):
    def __init__(self, text, size, callback):
        super().__init__()
        self.text = text
        self.size = size
        self.callback = callback

    def run(self):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        prompt = f"Based on the role and memory, suggest a natural continuation for this text (max {self.size} chars):\n{self.text}\n\nProvide a fluent and context-aware suggestion."
        response = llm([HumanMessage(content=prompt)])
        suggestion = response.content.strip()[:self.size]
        self.callback(suggestion)


class AIEditor(QWidget):
    def __init__(self):
        super().__init__()
        self.initUI()

        # Таймер для автодополнения
        self.suggestion_timer = QTimer()
        self.suggestion_timer.setInterval(1000)  # Запрос после 1 секунды бездействия
        self.suggestion_timer.timeout.connect(self.fetch_suggestion)
        self.suggested_text = ""
        self.suggestion_size = 50  # Контроль размера предложения
        self.thread_pool = QThreadPool()

    def initUI(self):
        layout = QVBoxLayout()

        self.label_role = QLabel("Agent Role:")
        self.text_role = QLineEdit()

        self.label_memory = QLabel("Memory:")
        self.text_memory = QTextEdit()

        self.label_doc = QLabel("Work Document:")
        self.text_doc = QTextEdit()
        self.text_doc.textChanged.connect(self.start_suggestion_timer)
        self.text_doc.keyPressEvent = self.handle_key_press

        self.label_suggestion = QLabel("Suggestion:")
        self.text_suggestion = QLabel("")  # Поле для отображения предложения

        self.btn_suggest = QPushButton("Suggest Text")
        self.btn_improve = QPushButton("Improve Text")
        self.btn_format = QPushButton("Improve Formatting")
        self.btn_extract = QPushButton("Extract Important Data")

        layout.addWidget(self.label_role)
        layout.addWidget(self.text_role)
        layout.addWidget(self.label_memory)
        layout.addWidget(self.text_memory)
        layout.addWidget(self.label_doc)
        layout.addWidget(self.text_doc)
        layout.addWidget(self.label_suggestion)
        layout.addWidget(self.text_suggestion)
        layout.addWidget(self.btn_suggest)
        layout.addWidget(self.btn_improve)
        layout.addWidget(self.btn_format)
        layout.addWidget(self.btn_extract)

        self.setLayout(layout)
        self.setWindowTitle("AI Editor with CrewAI and LangChain")

        # Подключение кнопок к функциям
        self.btn_suggest.clicked.connect(self.suggest_text)
        self.btn_improve.clicked.connect(self.improve_text)
        self.btn_format.clicked.connect(self.improve_formatting)
        self.btn_extract.clicked.connect(self.extract_data)

    def start_suggestion_timer(self):
        self.suggestion_timer.start()

    def fetch_suggestion(self):
        self.suggestion_timer.stop()
        doc = self.text_doc.toPlainText()
        if not doc.strip():
            return
        worker = SuggestionWorker(doc, self.suggestion_size, self.update_suggestion)
        self.thread_pool.start(worker)

    def update_suggestion(self, suggestion):
        self.suggested_text = suggestion
        self.text_suggestion.setText(self.suggested_text)  # Отображаем предложение

    def handle_key_press(self, event):
        if event.key() == 16777217:  # Tab key
            cursor = self.text_doc.textCursor()
            cursor.insertText(self.suggested_text)
            self.suggested_text = ""
            self.text_suggestion.setText("")  # Очищаем отображение предложения
        else:
            QTextEdit.keyPressEvent(self.text_doc, event)

    def suggest_text(self):
        self.fetch_suggestion()

    def improve_text(self):
        doc = self.text_doc.toPlainText()
        role = self.text_role.text()
        memory = self.text_memory.toPlainText()
        prompt = f"As a {role}, using the following memory:\n{memory}\n\nImprove the following text while keeping its meaning:\n{doc}"
        response = llm([HumanMessage(content=prompt)])
        self.text_doc.setPlainText(response.content)

    def improve_formatting(self):
        doc = self.text_doc.toPlainText()
        prompt = f"Format the following text properly, making it structured and readable:\n{doc}"
        response = llm([HumanMessage(content=prompt)])
        self.text_doc.setPlainText(response.content)

    def extract_data(self):
        doc = self.text_doc.toPlainText()
        prompt = f"Extract the key points and important information from the following text:\n{doc}\n\nProvide a concise summary."
        response = llm([HumanMessage(content=prompt)])
        self.text_memory.setPlainText(response.content)


if __name__ == "__main__":
    app = QApplication([])
    editor = AIEditor()
    editor.show()
    app.exec()
