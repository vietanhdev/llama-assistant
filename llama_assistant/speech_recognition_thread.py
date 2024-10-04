from pathlib import Path
import time
import os
import re

from PyQt6.QtCore import QThread, pyqtSignal
import speech_recognition as sr

from pywhispercpp.model import Model

class SpeechRecognitionThread(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    WHISPER_THREADS = 4
    WHISPER_LANGUAGE = "en"

    def __init__(self):
        super().__init__()
        self.stop_listening = False

        # Initialize Whisper model
        self.whisper = Model(
            "base.en", n_threads=self.WHISPER_THREADS
        )

        # Create temporary folder for audio files
        self.tmp_audio_folder = Path.home() / "llama-assistant" / "tmp_audio"
        self.tmp_audio_folder.mkdir(parents=True, exist_ok=True)

    def run(self):
        recognizer = sr.Recognizer()
        microphone = sr.Microphone()
        try:
            with microphone as source:
                recognizer.adjust_for_ambient_noise(source)
                while not self.stop_listening:
                    try:
                        recognizer.pause_threshold = 1
                        audio_data = recognizer.listen(source, timeout=1, phrase_time_limit=5)

                        # Save audio data to temporary file
                        tmp_filepath = (
                            self.tmp_audio_folder / f"temp_audio_{time.time()}.wav"
                        )
                        with open(tmp_filepath, "wb") as f:
                            f.write(audio_data.get_wav_data())

                        # Transcribe audio
                        res = self.whisper.transcribe(
                            str(tmp_filepath)
                        )
                        transcription = ""
                        for r in res:
                            transcription += r.text

                        # Clean up transcription
                        transcription = re.sub(r"\[.*\]", "", transcription)
                        transcription = re.sub(r"\(.*\)", "", transcription)

                        print(f"Transcription: {transcription}")
                        os.remove(tmp_filepath)

                        self.finished.emit(transcription)
                    except sr.WaitTimeoutError:
                        print("timeout")
                        continue
                    except sr.UnknownValueError:
                        print("Could not understand audio")
                        self.error.emit("Could not understand audio")
                    except sr.RequestError as e:
                        print(f"Could not request results; {e}")
                        self.error.emit(f"Could not request results; {e}")
        except KeyboardInterrupt:
            print("Keyboard interrupt detected. Stopping speech recognition.")
            self.stop()

    def stop(self):
        self.stop_listening = True


# Demo code
if __name__ == "__main__":
    from PyQt6.QtWidgets import QApplication
    import sys

    app = QApplication(sys.argv)

    def on_finished(text):
        print(f"Transcription: {text}")
        thread.stop()
        app.quit()

    def on_error(error_message):
        print(f"Error: {error_message}")
        thread.stop()
        app.quit()

    thread = SpeechRecognitionThread()
    thread.finished.connect(on_finished)
    thread.error.connect(on_error)

    print("Starting speech recognition. Speak into your microphone...")
    thread.start()

    sys.exit(app.exec())
