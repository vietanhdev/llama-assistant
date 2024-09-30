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
    QLineEdit,
    QMessageBox,
    QListWidget,
    QLabel,
)
from PyQt6.QtCore import pyqtSignal, Qt
from PyQt6.QtGui import QColor
from pynput import keyboard

from llama_assistant.shortcut_recorder import ShortcutRecorder
from llama_assistant import config


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
        layout = QVBoxLayout()

        shortcut_layout = QHBoxLayout()
        shortcut_label = QLabel("Shortcut:")
        self.shortcut_recorder = ShortcutRecorder()
        shortcut_layout.addWidget(shortcut_label)
        shortcut_layout.addWidget(self.shortcut_recorder)
        shortcut_layout.addStretch()
        layout.addLayout(shortcut_layout)

        self.reset_shortcut_button = QPushButton("Reset Shortcut")
        self.reset_shortcut_button.clicked.connect(self.reset_shortcut)
        layout.addWidget(self.reset_shortcut_button)

        group_box.setLayout(layout)
        self.main_layout.addWidget(group_box)

    def create_appearance_settings_group(self):
        group_box = QGroupBox("Appearance Settings")
        layout = QVBoxLayout()

        color_layout = QHBoxLayout()
        color_label = QLabel("Background Color:")
        self.color_button = QPushButton("Choose Color")
        self.color_button.clicked.connect(self.choose_color)
        color_layout.addWidget(color_label)
        color_layout.addWidget(self.color_button)
        color_layout.addStretch()
        layout.addLayout(color_layout)

        transparency_layout = QHBoxLayout()
        transparency_label = QLabel("Transparency:")
        self.transparency_slider = QSlider(Qt.Orientation.Horizontal)
        self.transparency_slider.setRange(10, 100)
        self.transparency_slider.setValue(90)
        transparency_layout.addWidget(transparency_label)
        transparency_layout.addWidget(self.transparency_slider)
        layout.addLayout(transparency_layout)

        group_box.setLayout(layout)
        self.main_layout.addWidget(group_box)

    def create_model_settings_group(self):
        group_box = QGroupBox("Model Settings")
        layout = QVBoxLayout()

        text_model_layout = QHBoxLayout()
        text_model_label = QLabel("Text-only Model:")
        self.text_model_combo = QComboBox()
        self.text_model_combo.addItems(self.get_model_names_by_type("text"))
        text_model_layout.addWidget(text_model_label)
        text_model_layout.addWidget(self.text_model_combo)
        text_model_layout.addStretch()
        layout.addLayout(text_model_layout)

        multimodal_model_layout = QHBoxLayout()
        multimodal_model_label = QLabel("Multimodal Model:")
        self.multimodal_model_combo = QComboBox()
        self.multimodal_model_combo.addItems(self.get_model_names_by_type("image"))
        multimodal_model_layout.addWidget(multimodal_model_label)
        multimodal_model_layout.addWidget(self.multimodal_model_combo)
        multimodal_model_layout.addStretch()
        layout.addLayout(multimodal_model_layout)

        self.manage_custom_models_button = QPushButton("Manage Custom Models")
        self.manage_custom_models_button.clicked.connect(self.open_custom_models_dialog)
        layout.addWidget(self.manage_custom_models_button)

        group_box.setLayout(layout)
        self.main_layout.addWidget(group_box)

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

    def get_model_names_by_type(self, model_type):
        return [model["model_id"] for model in config.models if model["model_type"] == model_type]

    def choose_color(self):
        color = QColorDialog.getColor()
        if color.isValid():
            self.color = color

    def reset_shortcut(self):
        self.shortcut_recorder.setText(config.DEFAULT_LAUNCH_SHORTCUT)

    def update_hey_llama_mic_state(self, state):
        self.hey_llama_mic_checkbox.setEnabled(state == Qt.CheckState.Checked.value)

    def load_settings(self):
        home_dir = Path.home()
        settings_file = home_dir / "llama_assistant" / "settings.json"

        if settings_file.exists():
            with open(settings_file, "r") as f:
                settings = json.load(f)
            try:
                keyboard.HotKey(keyboard.HotKey.parse(settings["shortcut"]), lambda: None)
            except ValueError:
                settings["shortcut"] = config.DEFAULT_LAUNCH_SHORTCUT
                self.save_settings(settings)
            self.shortcut_recorder.setText(settings.get("shortcut", config.DEFAULT_LAUNCH_SHORTCUT))
            self.color = QColor(settings.get("color", "#1E1E1E"))
            self.transparency_slider.setValue(int(settings.get("transparency", 90)))

            text_model = settings.get("text_model")
            if text_model in self.get_model_names_by_type("text"):
                self.text_model_combo.setCurrentText(text_model)

            multimodal_model = settings.get("multimodal_model")
            if multimodal_model in self.get_model_names_by_type("image"):
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
            "text_model": self.text_model_combo.currentText(),
            "multimodal_model": self.multimodal_model_combo.currentText(),
            "hey_llama_chat": self.hey_llama_chat_checkbox.isChecked(),
            "hey_llama_mic": self.hey_llama_mic_checkbox.isChecked(),
        }

    def save_settings(self, settings=None):
        if settings is None:
            home_dir = Path.home()
            settings_dir = home_dir / "llama_assistant"
            settings_file = settings_dir / "settings.json"

            if not settings_dir.exists():
                settings_dir.mkdir(parents=True)

            settings = self.get_settings()

        with open(settings_file, "w") as f:
            json.dump(settings, f)

    def open_custom_models_dialog(self):
        dialog = CustomModelsDialog(self)
        if dialog.exec():
            # Refresh the model combos after managing custom models
            self.refresh_model_combos()

    def refresh_model_combos(self):
        current_text_model = self.text_model_combo.currentText()
        current_multimodal_model = self.multimodal_model_combo.currentText()

        self.text_model_combo.clear()
        self.text_model_combo.addItems(self.get_model_names_by_type("text"))
        self.multimodal_model_combo.clear()
        self.multimodal_model_combo.addItems(self.get_model_names_by_type("image"))

        # Restore previously selected models if they still exist
        if current_text_model in self.get_model_names_by_type("text"):
            self.text_model_combo.setCurrentText(current_text_model)
        if current_multimodal_model in self.get_model_names_by_type("image"):
            self.multimodal_model_combo.setCurrentText(current_multimodal_model)


class CustomModelsDialog(QDialog):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setWindowTitle("Manage Custom Models")
        self.layout = QVBoxLayout(self)

        self.model_list = QListWidget()
        self.model_list.itemSelectionChanged.connect(self.load_selected_model)
        self.layout.addWidget(self.model_list)

        form_layout = QFormLayout()
        self.model_name_input = QLineEdit()
        self.model_id_input = QLineEdit()
        self.model_type_input = QComboBox()
        self.model_type_input.addItems(["text", "image"])
        self.repo_id_input = QLineEdit()
        self.filename_input = QLineEdit()

        form_layout.addRow("Model Name:", self.model_name_input)
        form_layout.addRow("Model ID:", self.model_id_input)
        form_layout.addRow("Model Type:", self.model_type_input)
        form_layout.addRow("Repo ID:", self.repo_id_input)
        form_layout.addRow("Filename:", self.filename_input)

        self.layout.addLayout(form_layout)

        button_layout = QHBoxLayout()
        self.add_button = QPushButton("Add Model")
        self.add_button.clicked.connect(self.add_model)
        self.update_button = QPushButton("Update Model")
        self.update_button.clicked.connect(self.update_model)
        self.remove_button = QPushButton("Remove Model")
        self.remove_button.clicked.connect(self.remove_model)
        button_layout.addWidget(self.add_button)
        button_layout.addWidget(self.update_button)
        button_layout.addWidget(self.remove_button)

        self.layout.addLayout(button_layout)

        self.refresh_model_list()

    def refresh_model_list(self):
        self.model_list.clear()
        for model in config.custom_models:
            self.model_list.addItem(f"{model['model_name']} ({model['model_type']})")

    def load_selected_model(self):
        selected_items = self.model_list.selectedItems()
        if selected_items:
            selected_index = self.model_list.row(selected_items[0])
            model = config.custom_models[selected_index]
            self.model_name_input.setText(model["model_name"])
            self.model_id_input.setText(model["model_id"])
            self.model_type_input.setCurrentText(model["model_type"])
            self.repo_id_input.setText(model["repo_id"])
            self.filename_input.setText(model["filename"])

    def add_model(self):
        model_name = self.model_name_input.text()
        model_id = self.model_id_input.text()
        model_type = self.model_type_input.currentText()
        repo_id = self.repo_id_input.text()
        filename = self.filename_input.text()

        if not all([model_name, model_id, model_type, repo_id, filename]):
            QMessageBox.warning(self, "Missing Information", "Please fill in all fields.")
            return

        new_model = {
            "model_name": model_name,
            "model_id": model_id,
            "model_type": model_type,
            "model_path": None,
            "repo_id": repo_id,
            "filename": filename,
        }

        config.custom_models.append(new_model)
        config.models = config.DEFAULT_MODELS + config.custom_models
        config.save_custom_models()
        self.refresh_model_list()
        self.clear_inputs()
        QMessageBox.information(
            self, "Model Added", f"Model '{model_name}' has been added successfully."
        )

    def update_model(self):
        selected_items = self.model_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a model to update.")
            return

        selected_index = self.model_list.row(selected_items[0])
        model_name = self.model_name_input.text()
        model_id = self.model_id_input.text()
        model_type = self.model_type_input.currentText()
        repo_id = self.repo_id_input.text()
        filename = self.filename_input.text()

        if not all([model_name, model_id, model_type, repo_id, filename]):
            QMessageBox.warning(self, "Missing Information", "Please fill in all fields.")
            return

        updated_model = {
            "model_name": model_name,
            "model_id": model_id,
            "model_type": model_type,
            "model_path": None,
            "repo_id": repo_id,
            "filename": filename,
        }

        config.custom_models[selected_index] = updated_model
        config.models = config.DEFAULT_MODELS + config.custom_models
        config.save_custom_models()
        self.refresh_model_list()
        self.clear_inputs()
        QMessageBox.information(
            self, "Model Updated", f"Model '{model_name}' has been updated successfully."
        )

    def remove_model(self):
        selected_items = self.model_list.selectedItems()
        if not selected_items:
            QMessageBox.warning(self, "No Selection", "Please select a model to remove.")
            return

        selected_index = self.model_list.row(selected_items[0])
        model_name = config.custom_models[selected_index]["model_name"]
        del config.custom_models[selected_index]
        config.models = config.DEFAULT_MODELS + config.custom_models
        config.save_custom_models()
        self.refresh_model_list()
        self.clear_inputs()
        QMessageBox.information(
            self, "Model Removed", f"Model '{model_name}' has been removed successfully."
        )

    def clear_inputs(self):
        self.model_name_input.clear()
        self.model_id_input.clear()
        self.model_type_input.setCurrentIndex(0)
        self.repo_id_input.clear()
        self.filename_input.clear()
