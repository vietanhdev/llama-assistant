import sys
import multiprocessing
from PyQt5.QtWidgets import QApplication
from PyQt5.QtCore import Qt
from llama_assistant.llama_assistant_app import LlamaAssistant


def main():
    # Enable high DPI scaling
    QApplication.setAttribute(Qt.AA_EnableHighDpiScaling, True)
    QApplication.setAttribute(Qt.AA_UseHighDpiPixmaps, True)

    app = QApplication(sys.argv)
    ex = LlamaAssistant()
    ex.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    multiprocessing.freeze_support()
    main()
