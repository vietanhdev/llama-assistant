import json
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog,
    QFormLayout,
    QPushButton,
    QSlider,
    QComboBox,
    QColorDialog,
    QLabel,
    QVBoxLayout,
    QHBoxLayout,
    QWidget,
)
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from llama_assistant.shortcut_recorder import ShortcutRecorder
from llama_assistant.config import models


class SettingsDialog(QDialog):
    settingsSaved = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.main_layout = QVBoxLayout(self)

        # Create a form layout for the settings
        form_widget = QWidget()
        self.layout = QFormLayout(form_widget)
        self.layout.setFormAlignment(Qt.AlignmentFlag.AlignLeft)
        self.layout.setLabelAlignment(Qt.AlignmentFlag.AlignLeft)

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

        # Text-only model selection
        self.text_model_combo = QComboBox()
        self.text_model_combo.addItems(self.get_model_names_by_type("text"))
        self.layout.addRow("Text-only Model:", self.text_model_combo)

        # Multimodal model selection
        self.multimodal_model_combo = QComboBox()
        self.multimodal_model_combo.addItems(self.get_model_names_by_type("image"))
        self.layout.addRow("Multimodal Model:", self.multimodal_model_combo)

        # Add the form widget to the main layout
        self.main_layout.addWidget(form_widget)

        # Create a horizontal layout for the save button
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.accept)
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)

        # Add the button layout to the main layout
        self.main_layout.addLayout(button_layout)

        self.load_settings()

    def accept(self):
        self.save_settings()
        self.settingsSaved.emit()
        super().accept()

    def get_model_names_by_type(self, model_type):
        return [model["model_id"] for model in models if model["model_type"] == model_type]

    def choose_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.color = color

    def reset_shortcut(self):
        self.shortcut_recorder.setText("<cmd>+<shift>+<space>")

    def load_settings(self):
        home_dir = Path.home()
        settings_file = home_dir / "llama_assistant" / "settings.json"

        if settings_file.exists():
            with open(settings_file, "r") as f:
                settings = json.load(f)
            self.shortcut_recorder.setText(settings.get("shortcut", "<cmd>+<shift>+<space>"))
            self.color = QColor(settings.get("color", "#1E1E1E"))
            self.transparency_slider.setValue(int(settings.get("transparency", 90)))

            text_model = settings.get("text_model")
            if text_model in self.get_model_names_by_type("text"):
                self.text_model_combo.setCurrentText(text_model)

            multimodal_model = settings.get("multimodal_model")
            if multimodal_model in self.get_model_names_by_type("image"):
                self.multimodal_model_combo.setCurrentText(multimodal_model)
        else:
            self.color = QColor("#1E1E1E")
            self.shortcut_recorder.setText("<cmd>+<shift>+<space>")

    def get_settings(self):
        return {
            "shortcut": self.shortcut_recorder.text(),
            "color": self.color.name(),
            "transparency": self.transparency_slider.value(),
            "text_model": self.text_model_combo.currentText(),
            "multimodal_model": self.multimodal_model_combo.currentText(),
        }

    def save_settings(self):
        home_dir = Path.home()
        settings_dir = home_dir / "llama_assistant"
        settings_file = settings_dir / "settings.json"

        if not settings_dir.exists():
            settings_dir.mkdir(parents=True)

        settings = self.get_settings()
        with open(settings_file, "w") as f:
            json.dump(settings, f)
