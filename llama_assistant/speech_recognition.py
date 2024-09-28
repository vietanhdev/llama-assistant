from PyQt6.QtCore import QThread, pyqtSignal
import speech_recognition as sr


class SpeechRecognitionThread(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)

    def __init__(self):
        super().__init__()
        self.recognizer = sr.Recognizer()
        self.microphone = sr.Microphone()
        self.stop_listening = False

    def run(self):
        with self.microphone as source:
            self.recognizer.adjust_for_ambient_noise(source)
            while not self.stop_listening:
                try:
                    audio = self.recognizer.listen(source, timeout=1, phrase_time_limit=10)
                    text = self.recognizer.recognize_google(audio)
                    self.finished.emit(text)
                except sr.WaitTimeoutError:
                    continue
                except sr.UnknownValueError:
                    self.error.emit("Could not understand audio")
                except sr.RequestError as e:
                    self.error.emit(f"Could not request results; {e}")

    def stop(self):
        self.stop_listening = True
