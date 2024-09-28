from PyQt6.QtWidgets import QPlainTextEdit
from PyQt6.QtGui import QKeyEvent
from PyQt6.QtCore import Qt, pyqtSignal


class CustomPlainTextEdit(QPlainTextEdit):
    submit = pyqtSignal()

    def __init__(self, submit_callback, parent=None):
        super().__init__(parent)
        self.submit.connect(submit_callback)
        self.setStyleSheet(
            """
            QPlainTextEdit {
                border: none;
                border-radius: 20px;
                padding: 10px 15px;
            }
            """
        )

    def keyPressEvent(self, event: QKeyEvent):
        if (
            event.key() == Qt.Key.Key_Return
            and not event.modifiers() & Qt.KeyboardModifier.ShiftModifier
        ):
            self.submit.emit()
        else:
            super().keyPressEvent(event)
