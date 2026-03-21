import sys
import threading
import speech_recognition as sr
from PySide6.QtWidgets import (
    QApplication, QWidget, QPushButton, QVBoxLayout, QTextEdit
)
from PySide6.QtCore import Qt, QTimer


class SpeechApp(QWidget):
    def __init__(self):
        super().__init__()
        self.setWindowTitle("Голосовой ввод")
        self.resize(400, 300)

        self.layout = QVBoxLayout(self)

        self.text_display = QTextEdit()
        self.text_display.setReadOnly(True)
        self.layout.addWidget(self.text_display)

        self.toggle_button = QPushButton("Начать запись")
        self.toggle_button.clicked.connect(self.toggle_recording)
        self.layout.addWidget(self.toggle_button)

        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.listening = False
        self.stop_listening = None
        self.lock = threading.Lock()

    def toggle_recording(self):
        if not self.listening:
            self.start_listening()
            self.toggle_button.setText("Остановить")
        else:
            self.stop_listening(wait_for_stop=False)
            self.listening = False
            self.toggle_button.setText("Начать запись")

    def start_listening(self):
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source, duration=1)

        self.listening = True
        self.stop_listening = self.recognizer.listen_in_background(
            self.microphone, self.callback
        )

    def callback(self, recognizer, audio):
        try:
            text = recognizer.recognize_google(audio, language="ru-RU")
            print(">>", text)
            # Потокобезопасно обновляем GUI
            self.update_text(text)
        except sr.UnknownValueError:
            pass
        except sr.RequestError as e:
            self.update_text(f"[Ошибка запроса: {e}]")

    def update_text(self, text):
        # Безопасно вызываем обновление QTextEdit в основном потоке
        QTimer.singleShot(0, lambda: self.text_display.append(text))

if __name__ == "__main__":
    app = QApplication(sys.argv)
    window = SpeechApp()
    window.show()
    sys.exit(app.exec())
