import json
import copy
import time
import traceback
import markdown

from PyQt5.QtWidgets import (
    QApplication,
    QMainWindow,
    QPushButton,
    QLabel,
    QMessageBox,
    QSystemTrayIcon,
)
from PyQt5.QtCore import (
    Qt,
    QPoint,
    QTimer,
)
from PyQt5.QtGui import (
    QPixmap,
    QPainter,
    QDragEnterEvent,
    QDropEvent,
    QBitmap,
    QTextCursor,
)

from llama_assistant import config
from llama_assistant.wake_word_detector import WakeWordDetector
from llama_assistant.global_hotkey import GlobalHotkey
from llama_assistant.setting_dialog import SettingsDialog
from llama_assistant.speech_recognition_thread import SpeechRecognitionThread
from llama_assistant.utils import image_to_base64_data_uri
from llama_assistant.processing_thread import ProcessingThread
from llama_assistant.ui_manager import UIManager
from llama_assistant.tray_manager import TrayManager


class LlamaAssistant(QMainWindow):
    def __init__(self):
        super().__init__()
        self.wake_word_detector = None
        self.load_settings()
        self.ui_manager = UIManager(self)
        self.tray_manager = TrayManager(self)
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

    def tray_icon_activated(self, reason):
        if reason == QSystemTrayIcon.ActivationReason.Trigger:
            self.show()
            self.activateWindow()
            self.raise_()

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
        if config.settings_file.exists():
            with open(config.settings_file, "r") as f:
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
            self.ui_manager.update_styles()

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
        with open(config.settings_file, "w") as f:
            json.dump(self.settings, f)

    def toggle_visibility(self):
        if self.isVisible():
            self.hide()
        else:
            self.show()
            self.activateWindow()
            self.raise_()
            self.ui_manager.input_field.setFocus()

    def on_submit(self):
        message = self.ui_manager.input_field.toPlainText()
        if message == "":
            return
        self.ui_manager.input_field.clear()

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
            QTimer.singleShot(100, lambda: self.process_text(message, "chat"))

    def on_task_button_clicked(self):
        button = self.sender()
        task = button.text()
        if message == "":
            return
        message = self.ui_manager.input_field.toPlainText()
        self.process_text(message, task)

    def process_text(self, message, task="chat"):
        if task != "chat":
            self.clear_chat()
        self.show_chat_box()
        if task == "chat":
            prompt = message + " \n" + "Generate a short and simple response."
        elif task == "Summarize":
            prompt = f"Summarize the following text: {message}"
        elif task == "Rephrase":
            prompt = f"Rephrase the following text {message}"
        elif task == "Fix Grammar":
            prompt = f"Fix the grammar in the following text:\n {message}"
        elif task == "Brainstorm":
            prompt = f"Brainstorm ideas related to: {message}"
        elif task == "Write Email":
            prompt = f"Write an email about: {message}"

        self.ui_manager.chat_box.append(f'<span style="color: #aaa;"><b>You:</b></span> {message}')
        self.ui_manager.chat_box.append(f'<span style="color: #aaa;"><b>AI ({task}):</b></span> ')

        self.processing_thread = ProcessingThread(self.current_text_model, prompt)
        self.processing_thread.update_signal.connect(self.update_chat_box)
        self.processing_thread.finished_signal.connect(self.on_processing_finished)
        self.processing_thread.start()

    def process_image_with_prompt(self, image_path, prompt):
        self.show_chat_box()
        self.ui_manager.chat_box.append(
            f'<span style="color: #aaa;"><b>You:</b></span> [Uploaded an image: {image_path}]'
        )
        self.ui_manager.chat_box.append(f'<span style="color: #aaa;"><b>You:</b></span> {prompt}')
        self.ui_manager.chat_box.append('<span style="color: #aaa;"><b>AI:</b></span> ')

        image = image_to_base64_data_uri(image_path)
        self.processing_thread = ProcessingThread(
            self.current_multimodal_model, prompt, image=image
        )
        self.processing_thread.update_signal.connect(self.update_chat_box)
        self.processing_thread.finished_signal.connect(self.on_processing_finished)
        self.processing_thread.start()

    def update_chat_box(self, text):
        cursor = self.ui_manager.chat_box.textCursor()
        cursor.movePosition(QTextCursor.MoveOperation.End)
        self.ui_manager.chat_box.setTextCursor(cursor)
        cursor.insertText(text)
        self.ui_manager.chat_box.verticalScrollBar().setValue(
            self.ui_manager.chat_box.verticalScrollBar().maximum()
        )
        self.last_response += text

    def on_processing_finished(self):
        self.response_start_position = 0
        self.ui_manager.chat_box.append("")

    def show_chat_box(self):
        if self.ui_manager.scroll_area.isHidden():
            self.ui_manager.scroll_area.show()
            self.ui_manager.copy_button.show()
            self.ui_manager.clear_button.show()
            self.setFixedHeight(500)  # Increase this value if needed
        self.ui_manager.chat_box.verticalScrollBar().setValue(
            self.ui_manager.chat_box.verticalScrollBar().maximum()
        )

    def copy_result(self):
        self.hide()
        if self.last_response:
            clipboard = QApplication.clipboard()
            clipboard.setText(self.last_response)

    def clear_chat(self):
        self.ui_manager.chat_box.clear()
        self.last_response = ""
        self.ui_manager.scroll_area.hide()
        self.ui_manager.input_field.clear()
        self.ui_manager.input_field.setFocus()
        self.ui_manager.copy_button.hide()
        self.ui_manager.clear_button.hide()
        self.setFixedHeight(400)  # Reset to default height

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
                self.ui_manager.input_field.setPlaceholderText("Enter a prompt for the image...")
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
        for i in reversed(range(self.ui_manager.image_layout.count())):
            self.ui_manager.image_layout.itemAt(i).widget().setParent(None)

        # Add new image to layout
        self.ui_manager.image_layout.addWidget(self.image_label)
        self.setFixedHeight(self.height() + 110)  # Increase height to accommodate larger image

    def remove_image_thumbnail(self):
        if self.image_label:
            self.image_label.setParent(None)
            self.image_label = None
            self.dropped_image = None
            self.ui_manager.input_field.setPlaceholderText("Ask me anything...")
            self.setFixedHeight(self.height() - 110)  # Decrease height after removing image

    def mousePressEvent(self, event):
        self.oldPos = event.globalPos()

    def mouseMoveEvent(self, event):
        delta = QPoint(event.globalPos() - self.oldPos)
        self.move(self.x() + delta.x(), self.y() + delta.y())
        self.oldPos = event.globalPos()

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
            self.ui_manager.mic_button.setStyleSheet(
                """
                QPushButton {
                    background-color: rgba(240, 150, 20, 0.5);
                    border: none;
                    border-radius: 20px;
                }
                QPushButton:hover {
                    background-color: rgba(240, 150, 20, 0.6);
                }
            """
            )
            self.speech_thread = SpeechRecognitionThread()
            self.speech_thread.finished.connect(self.on_speech_recognized)
            self.speech_thread.error.connect(self.on_speech_error)
            self.speech_thread.start()

            # Use QTimer to delay the application of the second style
            QTimer.singleShot(500, self.update_mic_button_style)

    def update_mic_button_style(self):
        self.ui_manager.mic_button.setStyleSheet(
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

    def stop_voice_input(self):
        if self.speech_thread and self.speech_thread.isRunning():
            self.is_listening = False
            self.speech_thread.stop()
            self.ui_manager.mic_button.setStyleSheet(
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
        current_text = self.ui_manager.input_field.toPlainText()
        if current_text:
            self.ui_manager.input_field.setPlainText(f"{current_text}\n{text}")
        else:
            self.ui_manager.input_field.setPlainText(text)
        self.stop_voice_input()

    def on_speech_error(self, error_message):
        print(f"Speech recognition error: {error_message}")
        self.stop_voice_input()

    def closeEvent(self, event):
        if self.wake_word_detector is not None:
            self.wake_word_detector.stop()
        super().closeEvent(event)
