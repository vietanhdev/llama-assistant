import json
from pathlib import Path
from PyQt6.QtWidgets import (
    QDialog,
    QFormLayout,
    QPushButton,
    QSlider,
    QComboBox,
    QColorDialog,
    QVBoxLayout,
    QHBoxLayout,
    QCheckBox,
    QGroupBox,
    QLabel,
)
from PyQt6.QtCore import pyqtSignal
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor

from llama_assistant import config
from llama_assistant.shortcut_recorder import ShortcutRecorder
from llama_assistant.config import models


class SettingsDialog(QDialog):
    settingsSaved = pyqtSignal()

    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Settings")
        self.main_layout = QVBoxLayout(self)

        # General Settings Group
        self.create_general_settings_group()

        # Appearance Settings Group
        self.create_appearance_settings_group()

        # Model Settings Group
        self.create_model_settings_group()

        # Voice Activation Settings Group
        self.create_voice_activation_settings_group()

        # Create a horizontal layout for the save button
        button_layout = QHBoxLayout()
        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.accept)
        button_layout.addStretch()
        button_layout.addWidget(self.save_button)

        # Add the button layout to the main layout
        self.main_layout.addLayout(button_layout)

        self.load_settings()

    def create_general_settings_group(self):
        group_box = QGroupBox("General Settings")
        layout = QFormLayout()

        self.shortcut_recorder = ShortcutRecorder()
        layout.addRow("Shortcut:", self.shortcut_recorder)

        self.reset_shortcut_button = QPushButton("Reset Shortcut")
        self.reset_shortcut_button.clicked.connect(self.reset_shortcut)
        layout.addRow(self.reset_shortcut_button)

        group_box.setLayout(layout)
        self.main_layout.addWidget(group_box)

    def create_appearance_settings_group(self):
        group_box = QGroupBox("Appearance Settings")
        layout = QFormLayout()

        self.color_button = QPushButton("Choose Color")
        self.color_button.clicked.connect(self.choose_color)
        layout.addRow("Background Color:", self.color_button)

        self.transparency_slider = QSlider(Qt.Orientation.Horizontal)
        self.transparency_slider.setRange(10, 100)
        self.transparency_slider.setValue(90)
        layout.addRow("Transparency:", self.transparency_slider)

        group_box.setLayout(layout)
        self.main_layout.addWidget(group_box)

    def create_model_settings_group(self):
        group_box = QGroupBox("Model Settings")
        layout = QFormLayout()

        if not config.is_mlx_supported:
            note_label = QLabel(
                "Install mlx-lm to run mlx engine models (pip install mlx-lm). This is supposed to be faster on Apple Sillicon chips."
            )
            note_label.setWordWrap(True)
            # Smaller font size for the note
            font = note_label.font()
            font.setPointSize(10)
            note_label.setFont(font)
            layout.addRow(note_label)

        # Engine selector for text model
        self.text_engine_combo = QComboBox()
        self.text_engine_combo.addItems(self.get_unique_engines())
        self.text_engine_combo.currentTextChanged.connect(self.update_text_model_combo)
        layout.addRow("Text Model Engine:", self.text_engine_combo)

        # Text model selector
        self.text_model_combo = QComboBox()
        layout.addRow("Text-only Model:", self.text_model_combo)

        # Multimodal model selector (LlamaCpp only)
        self.multimodal_model_combo = QComboBox()
        self.multimodal_model_combo.addItems(
            self.get_model_names_by_type_and_engine("image", "llamacpp")
        )
        layout.addRow("Multimodal Model:", self.multimodal_model_combo)

        # Add a note about the multimodal model
        note_label = QLabel("Note: Multimodal models are limited to LlamaCpp engine.")
        note_label.setWordWrap(True)
        layout.addRow(note_label)

        group_box.setLayout(layout)
        self.main_layout.addWidget(group_box)

        # Initialize text model combo
        self.update_text_model_combo(self.text_engine_combo.currentText())

    def create_voice_activation_settings_group(self):
        group_box = QGroupBox("Voice Activation Settings")
        layout = QVBoxLayout()

        self.hey_llama_chat_checkbox = QCheckBox('Say "Hey Llama" to open chat form')
        self.hey_llama_chat_checkbox.stateChanged.connect(self.update_hey_llama_mic_state)
        layout.addWidget(self.hey_llama_chat_checkbox)

        self.hey_llama_mic_checkbox = QCheckBox('Say "Hey Llama" to activate microphone')
        layout.addWidget(self.hey_llama_mic_checkbox)

        group_box.setLayout(layout)
        self.main_layout.addWidget(group_box)

    def accept(self):
        self.save_settings()
        self.settingsSaved.emit()
        super().accept()

    def get_unique_engines(self):
        return sorted(set(model["engine"] for model in models))

    def get_model_names_by_type_and_engine(self, model_type, engine):
        return [
            model["model_id"]
            for model in models
            if model["model_type"] == model_type and model["engine"] == engine
        ]

    def update_text_model_combo(self, engine):
        self.text_model_combo.clear()
        text_models = self.get_model_names_by_type_and_engine("text", engine)
        self.text_model_combo.addItems(text_models)

    def choose_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.color = color

    def reset_shortcut(self):
        self.shortcut_recorder.setText("<cmd>+<shift>+<space>")

    def update_hey_llama_mic_state(self, state):
        self.hey_llama_mic_checkbox.setEnabled(state == Qt.CheckState.Checked.value)

    def load_settings(self):
        home_dir = Path.home()
        settings_file = home_dir / "llama_assistant" / "settings.json"

        if settings_file.exists():
            with open(settings_file, "r") as f:
                settings = json.load(f)
            self.shortcut_recorder.setText(settings.get("shortcut", "<cmd>+<shift>+<space>"))
            self.color = QColor(settings.get("color", "#1E1E1E"))
            self.transparency_slider.setValue(int(settings.get("transparency", 90)))

            text_engine = settings.get("text_engine")
            if text_engine in self.get_unique_engines():
                self.text_engine_combo.setCurrentText(text_engine)

            text_model = settings.get("text_model")
            if text_model in self.get_model_names_by_type_and_engine("text", text_engine):
                self.text_model_combo.setCurrentText(text_model)

            multimodal_model = settings.get("multimodal_model")
            if multimodal_model in self.get_model_names_by_type_and_engine("image", "llamacpp"):
                self.multimodal_model_combo.setCurrentText(multimodal_model)

            self.hey_llama_chat_checkbox.setChecked(settings.get("hey_llama_chat", False))
            self.hey_llama_mic_checkbox.setChecked(settings.get("hey_llama_mic", False))
            self.update_hey_llama_mic_state(settings.get("hey_llama_chat", False))
        else:
            self.color = QColor("#1E1E1E")
            self.shortcut_recorder.setText("<cmd>+<shift>+<space>")

    def get_settings(self):
        return {
            "shortcut": self.shortcut_recorder.text(),
            "color": self.color.name(),
            "transparency": self.transparency_slider.value(),
            "text_engine": self.text_engine_combo.currentText(),
            "text_model": self.text_model_combo.currentText(),
            "multimodal_model": self.multimodal_model_combo.currentText(),
            "hey_llama_chat": self.hey_llama_chat_checkbox.isChecked(),
            "hey_llama_mic": self.hey_llama_mic_checkbox.isChecked(),
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
