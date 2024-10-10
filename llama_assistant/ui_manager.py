from PyQt5.QtWidgets import (
    QWidget,
    QVBoxLayout,
    QHBoxLayout,
    QTextBrowser,
    QPushButton,
    QScrollArea,
    QShortcut,
    QSizePolicy,
    QSpacerItem,
)
from PyQt5.QtCore import (
    Qt,
    QSize,
)
from PyQt5.QtGui import (
    QColor,
    QKeySequence,
)

from llama_assistant.custom_plaintext_editor import CustomPlainTextEdit
from llama_assistant.icons import (
    create_icon_from_svg,
    copy_icon_svg,
    clear_icon_svg,
    microphone_icon_svg,
)


class UIManager:
    def __init__(self, parent):
        self.parent = parent
        self.init_ui()
        self.update_styles()  # Call update_styles after initializing UI

    def init_ui(self):
        self.parent.setWindowTitle("AI Assistant")
        self.parent.setMinimumSize(600, 500)
        self.parent.setWindowFlags(
            Qt.WindowType.FramelessWindowHint | Qt.WindowType.WindowStaysOnTopHint
        )
        self.parent.setAttribute(Qt.WidgetAttribute.WA_TranslucentBackground)

        central_widget = QWidget(self.parent)
        self.parent.setCentralWidget(central_widget)

        main_layout = QVBoxLayout(central_widget)
        main_layout.setContentsMargins(10, 10, 10, 10)

        top_layout = QVBoxLayout()  # Changed to QVBoxLayout

        input_layout = QHBoxLayout()
        self.input_field = CustomPlainTextEdit(self.parent.on_submit, self.parent)
        self.input_field.setPlaceholderText("Ask me anything...")
        self.input_field.setAcceptDrops(True)
        self.input_field.setFixedHeight(100)
        self.input_field.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Fixed)
        self.input_field.dragEnterEvent = self.parent.dragEnterEvent
        self.input_field.dropEvent = self.parent.dropEvent
        input_layout.addWidget(self.input_field)

        self.mic_button = QPushButton(self.parent)
        self.mic_button.setIcon(create_icon_from_svg(microphone_icon_svg))
        self.mic_button.setIconSize(QSize(24, 24))
        self.mic_button.setFixedSize(40, 40)
        self.mic_button.clicked.connect(self.parent.toggle_voice_input)
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
        input_layout.addWidget(self.mic_button)

        close_button = QPushButton("×", self.parent)
        close_button.clicked.connect(self.parent.hide)
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
        input_layout.addWidget(close_button)

        top_layout.addLayout(input_layout)

        self.image_layout = QHBoxLayout()
        self.image_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        top_layout.addLayout(self.image_layout)

        button_layout = QHBoxLayout()
        button_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)
        self.summarize_button = QPushButton("Summarize", self.parent)
        self.rephrase_button = QPushButton("Rephrase", self.parent)
        self.fix_grammar_button = QPushButton("Fix Grammar", self.parent)
        self.brainstorm_button = QPushButton("Brainstorm", self.parent)
        self.write_email_button = QPushButton("Write Email", self.parent)

        for button in [
            self.summarize_button,
            self.rephrase_button,
            self.fix_grammar_button,
            self.brainstorm_button,
            self.write_email_button,
        ]:
            button.clicked.connect(self.parent.on_task_button_clicked)
            button_layout.addWidget(button)

        top_layout.addLayout(button_layout)
        main_layout.addLayout(top_layout)

        result_layout = QHBoxLayout()
        result_layout.setAlignment(Qt.AlignmentFlag.AlignLeft)

        self.copy_button = QPushButton("Copy Result", self.parent)
        self.copy_button.setIcon(create_icon_from_svg(copy_icon_svg))
        self.copy_button.setIconSize(QSize(18, 18))
        self.copy_button.clicked.connect(self.parent.copy_result)
        self.copy_button.hide()

        self.clear_button = QPushButton("Clear", self.parent)
        self.clear_button.setIcon(create_icon_from_svg(clear_icon_svg))
        self.clear_button.setIconSize(QSize(18, 18))
        self.clear_button.clicked.connect(self.parent.clear_chat)
        self.clear_button.hide()

        result_layout.addWidget(self.copy_button)
        result_layout.addWidget(self.clear_button)

        main_layout.addLayout(result_layout)

        self.scroll_area = QScrollArea(self.parent)
        self.scroll_area.setWidgetResizable(True)
        self.scroll_area.setHorizontalScrollBarPolicy(Qt.ScrollBarPolicy.ScrollBarAlwaysOff)
        self.scroll_area.setMinimumHeight(400)
        self.scroll_area.setStyleSheet(
            """
            QScrollArea {
                border: none;
                background-color: transparent;
                border-radius: 20px;
                min-height: 400px;
            }
            QScrollBar:vertical {
                border: none;
                background: rgba(255, 255, 255, 200);
                width: 10px;
                margin: 0px 0px 0px 0px;
                border-radius: 5px;
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
        self.scroll_area.hide()

        self.chat_box = QTextBrowser(self.scroll_area)
        self.chat_box.setOpenExternalLinks(True)
        self.chat_box.setStyleSheet(
            """
            QTextBrowser {
                border: none;
                background-color: transparent;
                border-radius: 15px;
                padding: 10px;
            }
            QTextBrowser::viewport {
                border-radius: 15px;
            }
        """
        )
        self.scroll_area.setWidget(self.chat_box)
        self.scroll_area.setSizePolicy(QSizePolicy.Expanding, QSizePolicy.Expanding)
        main_layout.addWidget(self.scroll_area)

        self.parent.esc_shortcut = QShortcut(QKeySequence("Esc"), self.parent)
        self.parent.esc_shortcut.activated.connect(self.parent.hide)

        # Add an expanding spacer
        spacer = QSpacerItem(20, 40, QSizePolicy.Minimum, QSizePolicy.Expanding)
        main_layout.addItem(spacer)

    def update_styles(self):
        opacity = self.parent.settings.get("transparency", 90) / 100
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
                background-color: rgba{QColor(self.parent.settings["color"]).getRgb()[:3] + (opacity,)};
                {base_style}
            }}
            """
        )
        self.chat_box.setStyleSheet(
            f"""QTextBrowser {{ {base_style}
                                    background-color: rgba{QColor(self.parent.settings["color"]).lighter(120).getRgb()[:3] + (opacity,)};
                                    border-radius: 10px;
                                    }}"""
        )
        button_style = f"""
            QPushButton {{
                {base_style}
                padding: 2.5px 5px;
                border-radius: 5px;
                background-color: rgba{QColor(self.parent.settings["color"]).getRgb()[:3] + (opacity,)};
            }}
            QPushButton:hover {{
                background-color: rgba{QColor(self.parent.settings["color"]).lighter(120).getRgb()[:3] + (opacity,)};
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
                background-color: rgba{QColor(self.parent.settings["color"]).lighter(120).getRgb()[:3] + (opacity,)};
            }}
            QPushButton:hover {{
                background-color: rgba{QColor(self.parent.settings["color"]).lighter(150).getRgb()[:3] + (opacity,)};
            }}
        """
        for button in [self.copy_button, self.clear_button]:
            button.setStyleSheet(button_style)
