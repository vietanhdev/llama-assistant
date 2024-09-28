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
)
from PyQt6.QtCore import Qt
from PyQt6.QtGui import QColor
from llama_assistant.shortcut_recorder import ShortcutRecorder


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
        self.ai_model_combo.addItems(["Llama 1B + Moondream2"])
        self.layout.addRow("AI Model:", self.ai_model_combo)

        self.label = QLabel(
            "Note: Changing AI model will be supported in the future."
        )
        self.layout.addRow(self.label)

        self.save_button = QPushButton("Save")
        self.save_button.clicked.connect(self.accept)
        self.layout.addRow(self.save_button)

        self.load_settings()

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
            self.shortcut_recorder.setText(
                settings.get("shortcut", "<cmd>+<shift>+<space>")
            )
            self.color = QColor(settings.get("color", "#1E1E1E"))
            self.transparency_slider.setValue(
                int(settings.get("transparency", 90))
            )
            # self.ai_model_combo.setCurrentText(
            #     settings.get("ai_model", "Llama 1B")
            # ) # TODO: Implement this feature
            self.ai_model_combo.setCurrentText("Llama 1B + Moondream2")
        else:
            self.color = QColor("#1E1E1E")
            self.shortcut_recorder.setText("<cmd>+<shift>+<space>")

    def get_settings(self):
        return {
            "shortcut": self.shortcut_recorder.text(),
            "color": self.color.name(),
            "transparency": self.transparency_slider.value(),
            "ai_model": self.ai_model_combo.currentText(),
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
