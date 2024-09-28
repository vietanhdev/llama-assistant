import sys
from PyQt6.QtWidgets import QApplication
from llama_assistant.llama_assistant import LlamaAssistant


def main():
    app = QApplication(sys.argv)
    ex = LlamaAssistant()
    ex.show()
    sys.exit(app.exec())


if __name__ == "__main__":
    main()
