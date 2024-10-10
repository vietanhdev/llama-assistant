from PyQt5.QtCore import (
    QThread,
    pyqtSignal,
)
from llama_assistant.model_handler import handler as model_handler


class ProcessingThread(QThread):
    update_signal = pyqtSignal(str)
    finished_signal = pyqtSignal()

    def __init__(self, model, prompt, image=None):
        super().__init__()
        self.model = model
        self.prompt = prompt
        self.image = image

    def run(self):
        output = model_handler.chat_completion(
            self.model, self.prompt, image=self.image, stream=True
        )
        for chunk in output:
            delta = chunk["choices"][0]["delta"]
            if "role" in delta:
                print(delta["role"], end=": ")
            elif "content" in delta:
                print(delta["content"], end="")
                self.update_signal.emit(delta["content"])
        self.finished_signal.emit()
