import sys
import json
import math
import speech_recognition as sr
import markdown
from mlx_lm import load, generate

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QDialog,
    QVBoxLayout,
    QHBoxLayout,
    QFormLayout,
    QLineEdit,
    QPlainTextEdit,
    QTextBrowser,
    QPushButton,
    QComboBox,
    QSlider,
    QSystemTrayIcon,
    QMenu,
    QColorDialog,
)
from PyQt6.QtCore import (
    Qt,
    QPoint,
    QPointF,
    QSize,
    QTimer,
    QThread,
    QPropertyAnimation,
    QEasingCurve,
    QBuffer,
    QIODevice,
    pyqtSignal,
)
from PyQt6.QtGui import (
    QIcon,
    QPixmap,
    QColor,
    QPainter,
    QPen,
    QGuiApplication,
    QShortcut,
    QKeySequence,
    QKeyEvent,
    QDragEnterEvent,
    QDropEvent,
)
from PyQt6.QtSvg import QSvgRenderer


class ShortcutRecorder(QLineEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setReadOnly(True)
        self.setPlaceholderText("Press a key combination")

    def keyPressEvent(self, event: QKeyEvent):
        modifiers = []
        if event.modifiers() & Qt.KeyboardModifier.ControlModifier:
            modifiers.append("Ctrl")
        if event.modifiers() & Qt.KeyboardModifier.AltModifier:
            modifiers.append("Alt")
        if event.modifiers() & Qt.KeyboardModifier.ShiftModifier:
            modifiers.append("Shift")
        if event.modifiers() & Qt.KeyboardModifier.MetaModifier:
            modifiers.append("Meta")

        key = event.key()
        if key not in (
            Qt.Key.Key_Control,
            Qt.Key.Key_Shift,
            Qt.Key.Key_Alt,
            Qt.Key.Key_Meta,
        ):
            key_string = "+".join(modifiers + [QKeySequence(key).toString()])
            self.setText(key_string)

        event.accept()


class SettingsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.layout = QFormLayout(self)

        self.shortcut_recorder = ShortcutRecorder()
        self.layout.addRow("Shortcut:", self.shortcut_recorder)

        self.reset_shortcut_button = QPushButton("Reset Shortcut")
        self.reset_shortcut_button.clicked.connect(self.reset_shortcut)
        self.layout.addRow(self.reset_shortcut_button)

        self.color_button = QPushButton("Choose Color")
        self.color_button.clicked.connect(self.choose_color)
        self.layout.addRow("Background Color:", self.color_button)

        self.transparency_slider = QSlider(Qt.Orientation.Horizontal)
        self.transparency_slider.setRange(10, 100)
        self.transparency_slider.setValue(90)
        self.layout.addRow("Transparency:", self.transparency_slider)

        self.ai_model_combo = QComboBox()
        self.ai_model_combo.addItems(["Llama 1B", "Llama 3B"])
        self.layout.addRow("AI Model:", self.ai_model_combo)

        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.accept)
        self.layout.addRow(self.save_button)

        self.load_settings()

    def choose_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.color = color

    def reset_shortcut(self):
        self.shortcut_recorder.setText("Ctrl+Shift+Space")

    def load_settings(self):
        try:
            with open("settings.json", "r") as f:
                settings = json.load(f)
            self.shortcut_recorder.setText(settings.get("shortcut", "Ctrl+Shift+Space"))
            self.color = QColor(settings.get("color", "#1E1E1E"))
            self.transparency_slider.setValue(int(settings.get("transparency", 90)))
            self.ai_model_combo.setCurrentText(settings.get("ai_model", "Llama 1B"))
        except FileNotFoundError:
            self.color = QColor("#1E1E1E")
            self.shortcut_recorder.setText("Ctrl+Shift+Space")

    def get_settings(self):
        return {
            "shortcut": self.shortcut_recorder.text(),
            "color": self.color.name(),
            "transparency": self.transparency_slider.value(),
            "ai_model": self.ai_model_combo.currentText(),
        }


class SpeechRecognitionThread(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.stop_listening = False

    def run(self):
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)
            while not self.stop_listening:
                try:
                    audio = self.recognizer.listen(
                        source, timeout=1, phrase_time_limit=10
                    )
                    text = self.recognizer.recognize_google(audio)
                    self.finished.emit(text)
                except sr.WaitTimeoutError:
                    continue
                except sr.UnknownValueError:
                    self.error.emit("Could not understand audio")
                except sr.RequestError as e:
                    self.error.emit(f"Could not request results; {e}")

    def stop(self):
        self.stop_listening = True


class CustomPlainTextEdit(QPlainTextEdit):
    def __init__(self, submit_func, parent=None):
        super().__init__(parent)
        self.submit_func = submit_func

    def keyPressEvent(self, event: QKeyEvent):
        if (
            event.key() == Qt.Key.Key_Return
            and event.modifiers() == Qt.KeyboardModifier.ShiftModifier
        ):
            super().keyPressEvent(event)
        elif event.key() == Qt.Key.Key_Return:
            self.submit_func()
        else:
            super().keyPressEvent(event)


class LoadingAnimation(QWidget):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setFixedSize(60, 60)
        self.rotation = 0
        self.dot_count = 8
        self.dot_radius = 3
        self.circle_radius = 20

        self.animation = QPropertyAnimation(self, b"rotation")
        self.animation.setDuration(1500)
        self.animation.setStartValue(0)
        self.animation.setEndValue(360)
        self.animation.setLoopCount(-1)
        self.animation.setEasingCurve(QEasingCurve.Type.Linear)

    def start_animation(self):
        self.show()
        self.animation.start()

    def stop_animation(self):
        self.animation.stop()
        self.hide()

    def paintEvent(self, event):
        painter = QPainter(self)
        painter.setRenderHint(QPainter.RenderHint.Antialiasing)

        painter.translate(self.width() / 2, self.height() / 2)
        painter.rotate(self.rotation)

        for i in range(self.dot_count):
            angle = 360 / self.dot_count * i
            x = self.circle_radius * math.cos(math.radians(angle))
            y = self.circle_radius * math.sin(math.radians(angle))

            opacity = (i + 1) / self.dot_count
            color = QColor(255, 255, 255, int(255 * opacity))
            painter.setBrush(color)
            painter.setPen(Qt.PenStyle.NoPen)

            painter.drawEllipse(QPointF(x, y), self.dot_radius, self.dot_radius)

    @property
    def rotation(self):
        return self._rotation

    @rotation.setter
    def rotation(self, value):
        self._rotation = value
        self.update()


class AIAssistant(QMainWindow):
    def __init__(self):
        super().__init__()
        self.load_settings()
        self.initUI()
        self.initTray()
        self.setup_global_shortcut()
        self.load_model()
        self.last_response = ""
        self.dropped_image = None
        self.speech_thread = None
        self.is_listening = False

    def load_model(self):
        self.model, self.tokenizer = load("mlx-community/Llama-3.2-1B-Instruct-4bit")

    def load_settings(self):
        try:
            with open("settings.json", "r") as f:
                self.settings = json.load(f)
        except FileNotFoundError:
            self.settings = {
                "shortcut": "Ctrl+Shift+Space",
                "color": "#1E1E1E",
                "transparency": 90,
                "ai_model": "Llama 1B",
            }

    def save_settings(self):
        with open("settings.json", "w") as f:
            json.dump(self.settings, f)

    def initUI(self):
        self.setWindowTitle("AI Assistant")
        self.setFixedSize(600, 100)
        self.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        )
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)

        top_layout = QHBoxLayout()

        self.input_field = CustomPlainTextEdit(self.on_submit, self)
        self.input_field.setPlaceholderText("Ask me anything...")
        self.input_field.setAcceptDrops(True)
        self.input_field.dragEnterEvent = self.dragEnterEvent
        self.input_field.dropEvent = self.dropEvent
        top_layout.addWidget(self.input_field)

        self.mic_button = QPushButton(self)
        mic_icon = QIcon("mic_icon.png")
        self.mic_button.setIcon(mic_icon)
        self.mic_button.setIconSize(QSize(24, 24))
        self.mic_button.setFixedSize(40, 40)
        self.mic_button.setStyleSheet(
            """
            QPushButton {
                background-color: transparent;
                border: none;
            }
            QPushButton:hover {
                background-color: rgba(255, 255, 255, 0.1);
                border-radius: 20px;
            }
        """
        )
        self.mic_button.clicked.connect(self.toggle_voice_input)
        top_layout.addWidget(self.mic_button)

        close_button = QPushButton("×", self)
        close_button.setStyleSheet(
            """
            QPushButton {
                background-color: rgba(255, 0, 0, 0.7);
                color: white;
                border: none;
                border-radius: 15px;
                font-size: 20px;
                padding: 5px;
                width: 30px;
                height: 30px;
            }
            QPushButton:hover {
                background-color: rgba(255, 0, 0, 0.9);
            }
        """
        )
        close_button.clicked.connect(self.hide)
        top_layout.addWidget(close_button)

        main_layout.addLayout(top_layout)

        self.chat_box = QTextBrowser(self)
        self.chat_box.setOpenExternalLinks(True)
        self.chat_box.setFixedHeight(300)
        self.chat_box.hide()
        main_layout.addWidget(self.chat_box)

        self.copy_button = QPushButton("Copy Result", self)
        self.copy_button.clicked.connect(self.copy_result)
        self.copy_button.hide()
        main_layout.addWidget(self.copy_button)

        self.loading_animation = LoadingAnimation(self)
        self.loading_animation.setFixedSize(50, 50)
        self.loading_animation.hide()

        self.oldPos = self.pos()

        self.center_on_screen()
        self.update_styles()

        self.esc_shortcut = QShortcut(QKeySequence("Esc"), self)
        self.esc_shortcut.activated.connect(self.hide)

    def setup_global_shortcut(self):
        self.shortcut = QShortcut(QKeySequence(self.settings["shortcut"]), self)
        self.shortcut.activated.connect(self.toggle_visibility)
        self.shortcut.setContext(Qt.ShortcutContext.ApplicationShortcut)

    def update_styles(self):
        opacity = self.settings.get("transparency", 90) / 100
        base_style = f"""
            background-color: rgba{QColor(self.settings["color"]).getRgb()[:3] + (opacity,)};
            border: none;
            border-radius: 20px;
            color: white;
            padding: 10px 15px;
            font-size: 16px;
        """
        self.input_field.setStyleSheet(
            f"""
            QPlainTextEdit {{
                {base_style}
                height: 80px;
            }}
        """
        )
        self.chat_box.setStyleSheet(f"QTextBrowser {{ {base_style} }}")
        self.copy_button.setStyleSheet(f"QPushButton {{ {base_style} }}")

    def center_on_screen(self):
        screen = QGuiApplication.primaryScreen().geometry()
        size = self.geometry()
        self.move(
            int((screen.width() - size.width()) / 2),
            int((screen.height() - size.height()) / 2),
        )

    def initTray(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.create_tray_icon())

        tray_menu = QMenu()
        show_action = tray_menu.addAction("Show")
        show_action.triggered.connect(self.show)
        settings_action = tray_menu.addAction("Settings")
        settings_action.triggered.connect(self.open_settings)
        quit_action = tray_menu.addAction("Quit")
        quit_action.triggered.connect(QApplication.quit)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.show()

    def open_settings(self):
        dialog = SettingsDialog(self)
        if dialog.exec():
            new_settings = dialog.get_settings()
            self.settings.update(new_settings)
            self.save_settings()
            self.update_styles()
            self.shortcut.setKey(QKeySequence(self.settings["shortcut"]))

    def create_tray_icon(self):
        svg_content = """
        <svg xmlns="http://www.w3.org/2000/svg" width="48" height="48" viewBox="0 0 24 24">
            <circle cx="12" cy="12" r="10" fill="#4A90E2"/>
            <text x="12" y="16" font-family="Arial" font-size="12" fill="white" text-anchor="middle">AI</text>
        </svg>
        """
        renderer = QSvgRenderer()
        buffer = QBuffer()
        buffer.open(QIODevice.OpenModeFlag.WriteOnly)
        buffer.write(svg_content.encode())
        buffer.close()
        renderer.load(buffer.data())

        pixmap = QPixmap(24, 24)
        pixmap.fill(Qt.GlobalColor.transparent)
        painter = QPainter(pixmap)
        renderer.render(painter)
        painter.end()

        return QIcon(pixmap)

    def toggle_visibility(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.activateWindow()
            self.raise_()
            self.input_field.setFocus()

    def on_submit(self):
        message = self.input_field.toPlainText()
        self.input_field.clear()
        self.loading_animation.move(self.width() // 2 - 25, self.height() // 2 - 25)
        self.loading_animation.start_animation()

        if self.dropped_image:
            self.process_image_with_prompt(self.dropped_image, message)
            self.dropped_image = None
        else:
            QTimer.singleShot(100, lambda: self.process_text(message))

    def process_text(self, message):
        prompt = message + " \n" + "Generate a short and simple response."

        if (
            hasattr(self.tokenizer, "apply_chat_template")
            and self.tokenizer.chat_template is not None
        ):
            messages = [{"role": "user", "content": prompt}]
            prompt = self.tokenizer.apply_chat_template(
                messages, tokenize=False, add_generation_prompt=True
            )

        response = generate(
            self.model, self.tokenizer, prompt=prompt, max_tokens=2048, verbose=True
        )
        self.last_response = response

        self.chat_box.append(f"<b>You:</b> {message}")
        self.chat_box.append(f"<b>AI:</b> {markdown.markdown(response)}")
        self.loading_animation.stop_animation()
        self.show_chat_box()

    def process_image_with_prompt(self, image_path, prompt):
        self.chat_box.append(f"<b>You:</b> [Uploaded an image: {image_path}]")
        self.chat_box.append(f"<b>You:</b> {prompt}")
        self.chat_box.append(
            f"<b>AI:</b> I've received your image and prompt. Here's a mock analysis using {self.settings['ai_model']}:"
        )
        self.chat_box.append("- The image appears to be a photograph")
        self.chat_box.append("- It contains various colors and shapes")
        self.chat_box.append(f"- Your prompt: {prompt}")
        self.chat_box.append(
            "- Further analysis would be performed by an actual AI model"
        )

        example_image_url = "https://example.com/ai_generated_image.jpg"
        self.chat_box.append(f'<img src="{example_image_url}" width="200">')
        self.loading_animation.stop_animation()
        self.show_chat_box()

    def show_chat_box(self):
        if self.chat_box.isHidden():
            self.chat_box.show()
            self.copy_button.show()
            self.setFixedHeight(450)
        self.chat_box.verticalScrollBar().setValue(
            self.chat_box.verticalScrollBar().maximum()
        )

    def copy_result(self):
        if self.last_response:
            clipboard = QApplication.clipboard()
            clipboard.setText(self.last_response)
            self.hide()

    def dragEnterEvent(self, event: QDragEnterEvent):
        if event.mimeData().hasUrls():
            event.accept()
        else:
            event.ignore()

    def dropEvent(self, event: QDropEvent):
        files = [u.toLocalFile() for u in event.mimeData().urls()]
        for file_path in files:
            if file_path.lower().endswith((".png", ".jpg", ".jpeg", ".gif", ".bmp")):
                self.dropped_image = file_path
                self.input_field.setPlaceholderText("Enter a prompt for the image...")
                break

    def mousePressEvent(self, event):
        self.oldPos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        delta = QPoint(event.globalPosition().toPoint() - self.oldPos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPosition().toPoint()

    def toggle_voice_input(self):
        if not self.is_listening:
            self.start_voice_input()
        else:
            self.stop_voice_input()

    def start_voice_input(self):
        if self.speech_thread is None or not self.speech_thread.isRunning():
            self.is_listening = True
            self.mic_button.setStyleSheet(
                """
                QPushButton {
                    background-color: rgba(255, 0, 0, 0.3);
                    border: none;
                    border-radius: 20px;
                }
                QPushButton:hover {
                    background-color: rgba(255, 0, 0, 0.5);
                }
            """
            )
            self.speech_thread = SpeechRecognitionThread()
            self.speech_thread.finished.connect(self.on_speech_recognized)
            self.speech_thread.error.connect(self.on_speech_error)
            self.speech_thread.start()

    def stop_voice_input(self):
        if self.speech_thread and self.speech_thread.isRunning():
            self.is_listening = False
            self.speech_thread.stop()
            self.speech_thread.wait()
            self.mic_button.setStyleSheet(
                """
                QPushButton {
                    background-color: transparent;
                    border: none;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.1);
                    border-radius: 20px;
                }
            """
            )

    def on_speech_recognized(self, text):
        current_text = self.input_field.toPlainText()
        if current_text:
            self.input_field.setPlainText(f"{current_text}\n{text}")
        else:
            self.input_field.setPlainText(text)

    def on_speech_error(self, error_message):
        print(error_message)


if __name__ == "__main__":
    app = QApplication(sys.argv)
    ex = AIAssistant()
    ex.show()
    sys.exit(app.exec())
