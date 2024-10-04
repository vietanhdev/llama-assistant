import json
import copy
import time
from importlib import resources
from pathlib import Path
import traceback

from PyQt6.QtWidgets import (
    QApplication,
    QMainWindow,
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextBrowser,
    QPushButton,
    QSystemTrayIcon,
    QMenu,
    QLabel,
    QScrollArea,
    QMessageBox,
)
from PyQt6.QtCore import (
    Qt,
    QPoint,
    QSize,
    QTimer,
    QThread,
    pyqtSignal,
)
from PyQt6.QtGui import (
    QIcon,
    QPixmap,
    QColor,
    QPainter,
    QGuiApplication,
    QShortcut,
    QKeySequence,
    QDragEnterEvent,
    QDropEvent,
    QBitmap,
    QTextCursor,
)

from llama_assistant import config
from llama_assistant.wake_word_detector import WakeWordDetector
from llama_assistant.custom_plaintext_editor import CustomPlainTextEdit
from llama_assistant.global_hotkey import GlobalHotkey
from llama_assistant.setting_dialog import SettingsDialog
from llama_assistant.speech_recognition_thread import SpeechRecognitionThread
from llama_assistant.utils import image_to_base64_data_uri, load_image
from llama_assistant.model_handler import handler as model_handler
from llama_assistant.icons import (
    create_icon_from_svg,
    copy_icon_svg,
    clear_icon_svg,
    microphone_icon_svg,
)


class ProcessingThread(QThread):
    update_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, model, prompt, image=None):
        super().__init__()
        self.model = model
        self.prompt = prompt
        self.image = image

    def run(self):
        output = model_handler.chat_completion(
            self.model, self.prompt, image=self.image, stream=True
        )
        for chunk in output:
            delta = chunk["choices"][0]["delta"]
            if "role" in delta:
                print(delta["role"], end=": ")
            elif "content" in delta:
                print(delta["content"], end="")
                self.update_signal.emit(delta["content"])
        self.finished_signal.emit()


class LlamaAssistant(QMainWindow):
    def __init__(self):
        super().__init__()
        self.wake_word_detector = None
        self.load_settings()
        self.init_ui()
        self.init_tray()
        self.setup_global_shortcut()
        self.last_response = ""
        self.dropped_image = None
        self.speech_thread = None
        self.is_listening = False
        self.image_label = None
        self.current_text_model = self.settings.get("text_model")
        self.current_multimodal_model = self.settings.get("multimodal_model")
        self.processing_thread = None
        self.response_start_position = 0

    def init_wake_word_detector(self):
        if self.wake_word_detector is not None:
            self.deinit_wake_word_detector()
        self.wake_word_detector = WakeWordDetector()
        self.wake_word_detector.wakeword_detected.connect(self.on_wake_word_detected)
        self.wake_word_detector.start()

    def deinit_wake_word_detector(self):
        if self.wake_word_detector.running:
            self.wake_word_detector.stop()
        self.wake_word_detector = None

    def load_settings(self):
        home_dir = Path.home()
        settings_dir = home_dir / "llama_assistant"
        settings_file = settings_dir / "settings.json"

        if not settings_dir.exists():
            settings_dir.mkdir(parents=True)

        if settings_file.exists():
            with open(settings_file, "r") as f:
                self.settings = json.load(f)
            self.settings["text_model"] = self.settings.get(
                "text_model", config.DEFAULT_SETTINGS["text_model"]
            )
            self.settings["multimodal_model"] = self.settings.get(
                "multimodal_model", config.DEFAULT_SETTINGS["multimodal_model"]
            )
        else:
            self.settings = copy.deepcopy(config.DEFAULT_SETTINGS)
            self.save_settings()
        if self.settings.get("hey_llama_chat", False) and self.wake_word_detector is None:
            self.init_wake_word_detector()
        if not self.settings.get("hey_llama_chat", False) and self.wake_word_detector is not None:
            self.deinit_wake_word_detector()
        self.current_text_model = self.settings.get("text_model")
        self.current_multimodal_model = self.settings.get("multimodal_model")

    def setup_global_shortcut(self):
        try:
            if hasattr(self, "global_hotkey"):
                self.global_hotkey.stop()
                time.sleep(0.1)  # Give a short delay to ensure the previous listener has stopped
            try:
                self.global_hotkey = GlobalHotkey(self.settings["shortcut"])
                self.global_hotkey.activated.connect(self.toggle_visibility)
            except Exception as e:
                print(f"Error setting up global shortcut: {e}")
                # Fallback to default shortcut if there's an error
                self.global_hotkey = GlobalHotkey(config.DEFAULT_LAUNCH_SHORTCUT)
                self.global_hotkey.activated.connect(self.toggle_visibility)
        except Exception as e:
            print(f"Error setting up global shortcut: {e}")
            traceback.print_exc()

    def open_settings(self):
        dialog = SettingsDialog(self)
        if dialog.exec():
            new_settings = dialog.get_settings()
            old_shortcut = self.settings["shortcut"]
            self.settings.update(new_settings)
            self.save_settings()
            self.load_settings()
            self.update_styles()

            if old_shortcut != self.settings["shortcut"]:
                msg = QMessageBox()
                msg.setIcon(QMessageBox.Icon.Information)
                msg.setText("Global shortcut has been updated")
                msg.setInformativeText(
                    "The changes will take effect after you restart the application."
                )
                msg.setWindowTitle("Restart Required")
                msg.setStandardButtons(
                    QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.No
                )
                msg.button(QMessageBox.StandardButton.Yes).setText("Restart Now")
                msg.button(QMessageBox.StandardButton.No).setText("Restart Later")
                msg.setDefaultButton(QMessageBox.StandardButton.Yes)

                result = msg.exec()

                if result == QMessageBox.StandardButton.Yes:
                    self.restart_application()
                else:
                    print("User chose to restart later.")

    def restart_application(self):
        QApplication.quit()
        # The application will restart automatically because it is being run from a script

    def save_settings(self):
        home_dir = Path.home()
        settings_file = home_dir / "llama_assistant" / "settings.json"
        with open(settings_file, "w") as f:
            json.dump(self.settings, f)

    def init_ui(self):
        self.setWindowTitle("AI Assistant")
        self.setFixedSize(600, 200)
        self.setWindowFlags(Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint)
        self.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        central_widget = QWidget(self)
        self.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)

        # Image thumbnail layout
        self.image_layout = QHBoxLayout()
        self.image_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        main_layout.addLayout(self.image_layout)

        top_layout = QHBoxLayout()

        self.input_field = CustomPlainTextEdit(self.on_submit, self)
        self.input_field.setPlaceholderText("Ask me anything...")
        self.input_field.setAcceptDrops(True)
        self.input_field.setFixedHeight(100)
        self.input_field.dragEnterEvent = self.dragEnterEvent
        self.input_field.dropEvent = self.dropEvent
        self.input_field.setStyleSheet(
            f"""
            QPlainTextEdit {{
                background-color: rgba{QColor(self.settings["color"]).getRgb()[:3] + (self.settings["transparency"] / 100,)};
                color: white;
                border: none;
                border-radius: 20px;
                padding: 10px 15px;
                font-size: 16px;
                height: 40px;
            }}
            """
        )
        top_layout.addWidget(self.input_field)

        self.mic_button = QPushButton(self)
        self.mic_button.setIcon(create_icon_from_svg(microphone_icon_svg))
        self.mic_button.setIconSize(QSize(24, 24))
        self.mic_button.setFixedSize(40, 40)
        self.mic_button.setStyleSheet(
            """
            QPushButton {
                background-color: rgba(100, 100, 100, 200);
                border: none;
                border-radius: 20px;
            }
            QPushButton:hover {
                background-color: rgba(100, 100, 100, 230);
            }
        """
        )
        self.mic_button.clicked.connect(self.toggle_voice_input)
        top_layout.addWidget(self.mic_button)

        close_button = QPushButton("×", self)
        close_button.setStyleSheet(
            """
            QPushButton {
                background-color: rgba(255, 0, 0, 150);
                color: white;
                border: none;
                border-radius: 15px;
                font-size: 20px;
                padding: 5px;
                width: 30px;
                height: 30px;
            }
            QPushButton:hover {
                background-color: rgba(255, 0, 0, 200);
            }
        """
        )
        close_button.clicked.connect(self.hide)
        top_layout.addWidget(close_button)

        main_layout.addLayout(top_layout)

        # Add new buttons
        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.summarize_button = QPushButton("Summarize", self)
        self.rephrase_button = QPushButton("Rephrase", self)
        self.fix_grammar_button = QPushButton("Fix Grammar", self)
        self.brainstorm_button = QPushButton("Brainstorm", self)
        self.write_email_button = QPushButton("Write Email", self)

        # Add new buttons to layout
        result_layout = QHBoxLayout()
        result_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        # Create and set up the Copy Result button
        self.copy_button = QPushButton("Copy Result", self)
        self.copy_button.setIcon(create_icon_from_svg(copy_icon_svg))
        self.copy_button.setIconSize(QSize(18, 18))
        self.copy_button.setStyleSheet(
            """
            QPushButton { padding-left: 4px; padding-right: 8px; }
            QPushButton::icon { margin-right: 4px; }
        """
        )
        self.copy_button.clicked.connect(self.copy_result)
        self.copy_button.hide()

        # Create and set up the Clear button
        self.clear_button = QPushButton("Clear", self)
        self.clear_button.setIcon(create_icon_from_svg(clear_icon_svg))
        self.clear_button.setIconSize(QSize(18, 18))
        self.clear_button.setStyleSheet(
            """
            QPushButton { padding-left: 4px; padding-right: 8px; }
            QPushButton::icon { margin-right: 4px; }
        """
        )
        self.clear_button.clicked.connect(self.clear_chat)
        self.clear_button.hide()

        result_layout.addWidget(self.copy_button)
        result_layout.addWidget(self.clear_button)

        for button in [
            self.summarize_button,
            self.rephrase_button,
            self.fix_grammar_button,
            self.brainstorm_button,
            self.write_email_button,
        ]:
            button.clicked.connect(self.on_task_button_clicked)
            button_layout.addWidget(button)

        main_layout.addLayout(button_layout)
        main_layout.addLayout(result_layout)

        # Create a scroll area for the chat box
        self.scroll_area = QScrollArea(self)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setStyleSheet(
            """
            QScrollArea {
                border: none;
                background-color: transparent;
                border-radius: 10px;
            }
            QScrollBar:vertical {
                border: none;
                background: rgba(255, 255, 255, 200);
                width: 10px;
                margin: 0px 0px 0px 0px;
            }
            QScrollBar::handle:vertical {
                background: rgba(255, 255, 255, 230);
                min-height: 20px;
                border-radius: 5px;
            }
            QScrollBar::add-line:vertical, QScrollBar::sub-line:vertical {
                border: none;
                background: none;
            }
            """
        )

        self.chat_box = QTextBrowser(self.scroll_area)
        self.chat_box.setOpenExternalLinks(True)
        self.scroll_area.setWidget(self.chat_box)
        self.scroll_area.hide()
        main_layout.addWidget(self.scroll_area)

        self.oldPos = self.pos()

        self.center_on_screen()
        self.update_styles()

        self.esc_shortcut = QShortcut(QKeySequence("Esc"), self)
        self.esc_shortcut.activated.connect(self.hide)

    def on_task_button_clicked(self):
        message = self.input_field.toPlainText()
        if message == "":
            # Show a message box if the input field is empty
            msg = QMessageBox()
            msg.setText("Please enter a message first.")
            msg.setWindowTitle("No Input")
            msg.exec()
            return
        sender = self.sender()
        task = sender.text().lower()
        self.input_field.clear()
        self.process_text(message, task)

    def update_styles(self):
        opacity = self.settings.get("transparency", 90) / 100
        base_style = f"""
            border: none;
            border-radius: 20px;
            color: white;
            padding: 10px 15px;
            font-size: 16px;
        """
        self.input_field.setStyleSheet(
            f"""
            QPlainTextEdit {{
                background-color: rgba{QColor(self.settings["color"]).getRgb()[:3] + (opacity,)};
                {base_style}
            }}
            """
        )
        self.chat_box.setStyleSheet(
            f"""QTextBrowser {{ {base_style}
                                    background-color: rgba{QColor(self.settings["color"]).lighter(120).getRgb()[:3] + (opacity,)};
                                    border-radius: 10px;
                                    }}"""
        )
        button_style = f"""
            QPushButton {{
                {base_style}
                padding: 2.5px 5px;
                border-radius: 5px;
                background-color: rgba{QColor(self.settings["color"]).getRgb()[:3] + (opacity,)};
            }}
            QPushButton:hover {{
                background-color: rgba{QColor(self.settings["color"]).lighter(120).getRgb()[:3] + (opacity,)};
            }}
        """
        for button in [
            self.rephrase_button,
            self.fix_grammar_button,
            self.brainstorm_button,
            self.write_email_button,
            self.summarize_button,
        ]:
            button.setStyleSheet(button_style)

        button_style = f"""
            QPushButton {{
                {base_style}
                padding: 2.5px 5px;
                border-radius: 5px;
                background-color: rgba{QColor(self.settings["color"]).lighter(120).getRgb()[:3] + (opacity,)};
            }}
            QPushButton:hover {{
                background-color: rgba{QColor(self.settings["color"]).lighter(150).getRgb()[:3] + (opacity,)};
            }}
        """
        for button in [self.copy_button, self.clear_button]:
            button.setStyleSheet(button_style)

    def center_on_screen(self):
        screen = QGuiApplication.primaryScreen().geometry()
        size = self.geometry()
        self.move(
            int((screen.width() - size.width()) / 2),
            int((screen.height() - size.height()) / 2),
        )

    def init_tray(self):
        self.tray_icon = QSystemTrayIcon(self)
        self.tray_icon.setIcon(self.load_tray_icon())

        tray_menu = QMenu()
        show_action = tray_menu.addAction("Show")
        show_action.triggered.connect(self.show)
        settings_action = tray_menu.addAction("Settings")
        settings_action.triggered.connect(self.open_settings)
        quit_action = tray_menu.addAction("Quit")
        quit_action.triggered.connect(QApplication.quit)

        self.tray_icon.setContextMenu(tray_menu)
        self.tray_icon.activated.connect(self.tray_icon_activated)
        self.tray_icon.show()

    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.toggle_visibility()

    def load_tray_icon(self):
        icon_path = "llama_assistant/resources/logo.png"
        pixmap = load_image(icon_path, size=(48, 48))
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
        if message == "":
            return
        self.input_field.clear()

        if message == "cls" or message == "clear":
            self.clear_chat()
            self.remove_image_thumbnail()
            return

        self.last_response = ""

        if self.dropped_image:
            self.process_image_with_prompt(self.dropped_image, message)
            self.dropped_image = None
            self.remove_image_thumbnail()
        else:
            QTimer.singleShot(100, lambda: self.process_text(message))

    def process_text(self, message, task="chat"):
        self.show_chat_box()
        if task == "chat":
            prompt = message + " \n" + "Generate a short and simple response."
        elif task == "summarize":
            prompt = f"Summarize the following text: {message}"
        elif task == "rephrase":
            prompt = f"Rephrase the following text {message}"
        elif task == "fix grammar":
            prompt = f"Fix the grammar in the following text:\n {message}"
        elif task == "brainstorm":
            prompt = f"Brainstorm ideas related to: {message}"
        elif task == "write email":
            prompt = f"Write an email about: {message}"

        self.chat_box.append(f'<span style="color: #aaa;"><b>You:</b></span> {message}')
        self.chat_box.append(f'<span style="color: #aaa;"><b>AI ({task}):</b></span> ')

        self.processing_thread = ProcessingThread(self.current_text_model, prompt)
        self.processing_thread.update_signal.connect(self.update_chat_box)
        self.processing_thread.finished_signal.connect(self.on_processing_finished)
        self.processing_thread.start()

    def process_image_with_prompt(self, image_path, prompt):
        self.show_chat_box()
        self.chat_box.append(
            '<span style="color: #aaa;"><b>You:</b></span> [Uploaded an image: {image_path}]'
        )
        self.chat_box.append(f'<span style="color: #aaa;"><b>You:</b></span> {prompt}')
        self.chat_box.append('<span style="color: #aaa;"><b>AI:</b></span> ')

        image = image_to_base64_data_uri(image_path)
        self.processing_thread = ProcessingThread(
            self.current_multimodal_model, prompt, image=image
        )
        self.processing_thread.update_signal.connect(self.update_chat_box)
        self.processing_thread.finished_signal.connect(self.on_processing_finished)
        self.processing_thread.start()

    def update_chat_box(self, text):
        cursor = self.chat_box.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.chat_box.setTextCursor(cursor)
        cursor.insertText(text)
        self.chat_box.verticalScrollBar().setValue(self.chat_box.verticalScrollBar().maximum())
        self.last_response += text

    def on_processing_finished(self):
        self.response_start_position = 0
        self.chat_box.append("")

    def show_chat_box(self):
        if self.scroll_area.isHidden():
            self.scroll_area.show()
            self.copy_button.show()
            self.clear_button.show()
            self.setFixedHeight(500)  # Increase this value if needed
        self.chat_box.verticalScrollBar().setValue(self.chat_box.verticalScrollBar().maximum())

    def copy_result(self):
        self.hide()
        if self.last_response:
            clipboard = QApplication.clipboard()
            clipboard.setText(self.last_response)

    def clear_chat(self):
        self.chat_box.clear()
        self.last_response = ""
        self.scroll_area.hide()
        self.input_field.clear()
        self.input_field.setFocus()
        self.copy_button.hide()
        self.clear_button.hide()
        self.setFixedHeight(200)  # Reset to default height

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
                self.show_image_thumbnail(file_path)
                break

    def show_image_thumbnail(self, image_path):
        if self.image_label is None:
            self.image_label = QLabel(self)
            self.image_label.setFixedSize(80, 80)
            self.image_label.setStyleSheet(
                """
                background-color: transparent;
                """
            )

            remove_button = QPushButton("×", self.image_label)
            remove_button.setStyleSheet(
                """
                QPushButton {
                    background-color: rgba(50, 50, 50, 200);
                    color: white;
                    border: none;
                    border-radius: 8px;
                    font-size: 12px;
                    padding: 2px;
                    width: 16px;
                    height: 16px;
                }
                QPushButton:hover {
                    background-color: rgba(50, 50, 50, 230);
                }
                """
            )
            remove_button.move(60, 0)
            remove_button.clicked.connect(self.remove_image_thumbnail)

        pixmap = QPixmap(image_path)
        scaled_pixmap = pixmap.scaled(
            80,
            80,
            Qt.AspectRatioMode.KeepAspectRatio,
            Qt.TransformationMode.SmoothTransformation,
        )

        # Create a rounded mask
        mask = QBitmap(scaled_pixmap.size())
        mask.fill(Qt.GlobalColor.color0)
        painter = QPainter(mask)
        painter.setBrush(Qt.GlobalColor.color1)
        painter.setPen(Qt.PenStyle.NoPen)
        painter.drawRoundedRect(mask.rect(), 20, 20)
        painter.end()

        # Apply the mask to the pixmap
        rounded_pixmap = scaled_pixmap.copy()
        rounded_pixmap.setMask(mask)

        self.image_label.setPixmap(rounded_pixmap)

        # Clear previous image if any
        for i in reversed(range(self.image_layout.count())):
            self.image_layout.itemAt(i).widget().setParent(None)

        # Add new image to layout
        self.image_layout.addWidget(self.image_label)
        self.setFixedHeight(self.height() + 110)  # Increase height to accommodate larger image

    def remove_image_thumbnail(self):
        if self.image_label:
            self.image_label.setParent(None)
            self.image_label = None
            self.dropped_image = None
            self.input_field.setPlaceholderText("Ask me anything...")
            self.setFixedHeight(self.height() - 110)  # Decrease height after removing image

    def mousePressEvent(self, event):
        self.oldPos = event.globalPosition().toPoint()

    def mouseMoveEvent(self, event):
        delta = QPoint(event.globalPosition().toPoint() - self.oldPos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPosition().toPoint()

    def on_wake_word_detected(self, model_name):
        self.show()
        self.activateWindow()
        self.raise_()
        if self.settings.get("hey_llama_mic", False):
            self.start_voice_input()

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
                    background-color: rgba(255, 0, 0, 0.5);
                    border: none;
                    border-radius: 20px;
                }
                QPushButton:hover {
                    background-color: rgba(255, 0, 0, 0.6);
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
                    background-color: rgba(255, 255, 255, 0.5);
                    border: none;
                    border-radius: 20px;
                }
                QPushButton:hover {
                    background-color: rgba(255, 255, 255, 0.6);
                }
            """
            )

    def on_speech_recognized(self, text):
        current_text = self.input_field.toPlainText()
        if current_text:
            self.input_field.setPlainText(f"{current_text}\n{text}")
        else:
            self.input_field.setPlainText(text)
        self.stop_voice_input()

    def on_speech_error(self, error_message):
        print(f"Speech recognition error: {error_message}")
        self.stop_voice_input()

    def closeEvent(self, event):
        if self.wake_word_detector is not None:
            self.wake_word_detector.stop()
        super().closeEvent(event)
