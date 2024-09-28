import math

from PyQt6.QtWidgets import (
    QWidget,
)
from PyQt6.QtCore import (
    Qt,
    QPointF,
    QPropertyAnimation,
    QEasingCurve,
)
from PyQt6.QtGui import (
    QColor,
    QPainter,
)


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
