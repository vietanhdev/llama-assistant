from PyQt6.QtCore import QObject, pyqtSignal
from pynput import keyboard


class GlobalHotkey(QObject):
    activated = pyqtSignal()

    def __init__(self, hotkey):
        super().__init__()
        self.hotkey = keyboard.HotKey(keyboard.HotKey.parse(hotkey), self.on_activate)
        self.listener = keyboard.Listener(
            on_press=self.for_canonical(self.hotkey.press),
            on_release=self.for_canonical(self.hotkey.release),
        )
        self.listener.start()

    def on_activate(self):
        self.activated.emit()

    def for_canonical(self, f):
        return lambda k: f(self.listener.canonical(k))

    def stop(self):
        if self.listener:
            self.listener.stop()
