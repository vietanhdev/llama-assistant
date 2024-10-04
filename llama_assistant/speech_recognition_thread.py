import pkgutil
from pathlib import Path
import datetime
import os
import re
import requests

from PyQt6.QtCore import QThread, pyqtSignal
import speech_recognition as sr

# patch whisper on file not find error
# https://github.com/carloscdias/whisper-cpp-python/pull/12
try:
    import whisper_cpp_python
except FileNotFoundError:
    regex = r"(\"darwin\":\n\s*lib_ext = \")\.so(\")"
    subst = "\\1.dylib\\2"

    print("fixing and re-importing whisper_cpp_python...")
    # load whisper_cpp_python and substitute .so with .dylib for darwin
    package = pkgutil.get_loader("whisper_cpp_python")
    whisper_path = Path(package.path)
    whisper_cpp_py = whisper_path.parent.joinpath("whisper_cpp.py")
    content = whisper_cpp_py.read_text()
    result = re.sub(regex, subst, content, 0, re.MULTILINE)
    whisper_cpp_py.write_text(result)

    import whisper_cpp_python


class SpeechRecognitionThread(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    WHISPER_THREADS = 4
    WHISPER_LANGUAGE = "en"

    def __init__(self):
        super().__init__()
        self.stop_listening = False

        # Set up model path and download if necessary
        self.model_dir = Path.home() / "llama-assistant" / "models" / "whisper-cpp"
        self.model_path = self.model_dir / "ggml-base-fp16.bin"
        self.download_model_if_needed()

        # Initialize Whisper model
        self.whisper = whisper_cpp_python.Whisper(
            model_path=str(self.model_path), n_threads=self.WHISPER_THREADS
        )

        # Create temporary folder for audio files
        self.tmp_audio_folder = Path.home() / "llama-assistant" / "tmp_audio"
        self.tmp_audio_folder.mkdir(parents=True, exist_ok=True)

    def download_model_if_needed(self):
        if not self.model_path.exists():
            print("Downloading Whisper model...")
            self.model_dir.mkdir(parents=True, exist_ok=True)
            url = "https://huggingface.co/danielus/ggml-whisper-models/resolve/main/ggml-base-fp16.bin"
            response = requests.get(url)
            with open(self.model_path, "wb") as f:
                f.write(response.content)
            print("Model downloaded successfully.")

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
                            self.tmp_audio_folder / f"temp_audio_{datetime.datetime.now()}.wav"
                        )
                        with open(tmp_filepath, "wb") as f:
                            f.write(audio_data.get_wav_data())

                        # Transcribe audio
                        res = self.whisper.transcribe(
                            file=tmp_filepath, language=self.WHISPER_LANGUAGE
                        )
                        transcription = res["text"]

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
