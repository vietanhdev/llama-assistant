from pathlib import Path
import time
import os
import re

from PyQt5.QtCore import QThread, pyqtSignal
import pyaudio
import wave

from whispercpp import Whisper
from llama_assistant.config import llama_assistant_dir

class SpeechRecognitionThread(QThread):
    finished = pyqtSignal(str)
    error = pyqtSignal(str)
    WHISPER_THREADS = 1

    def __init__(self):
        super().__init__()
        self.stop_listening = False

        # Initialize Whisper model
        self.whisper = Whisper("tiny")

        # Create temporary folder for audio files
        self.tmp_audio_folder = llama_assistant_dir / "tmp_audio"
        self.tmp_audio_folder.mkdir(parents=True, exist_ok=True)

        # Audio recording parameters
        self.FORMAT = pyaudio.paInt16
        self.CHANNELS = 1
        self.RATE = 16000
        self.CHUNK = 1024
        self.RECORD_SECONDS = 2  # Reduced to 2 seconds for more frequent transcription

    def run(self):
        self.stop_listening = False
        audio = pyaudio.PyAudio()

        try:
            stream = audio.open(format=self.FORMAT, channels=self.CHANNELS,
                                rate=self.RATE, input=True,
                                frames_per_buffer=self.CHUNK)

            print("Always-on microphone activated. Listening...")

            while not self.stop_listening:
                frames = []
                for _ in range(0, int(self.RATE / self.CHUNK * self.RECORD_SECONDS)):
                    data = stream.read(self.CHUNK)
                    frames.append(data)

                # Save audio data to temporary file
                tmp_filepath = self.tmp_audio_folder / f"temp_audio_{time.time()}.wav"
                wf = wave.open(str(tmp_filepath), 'wb')
                wf.setnchannels(self.CHANNELS)
                wf.setsampwidth(audio.get_sample_size(self.FORMAT))
                wf.setframerate(self.RATE)
                wf.writeframes(b''.join(frames))
                wf.close()

                # Transcribe audio
                res = self.whisper.transcribe(str(tmp_filepath))
                transcription = self.whisper.extract_text(res)
                os.remove(tmp_filepath)
                
                if isinstance(transcription, list):
                    # Remove all "[BLANK_AUDIO]" from the transcription
                    transcription = " ".join(transcription)
                    transcription = re.sub(r"\[BLANK_AUDIO\]", "", transcription)

                if transcription.strip():  # Only emit if there's non-empty transcription
                    self.finished.emit(transcription)

        except Exception as e:
            self.error.emit(f"An error occurred: {str(e)}")
        finally:
            stream.stop_stream()
            stream.close()
            audio.terminate()

    def stop(self):
        self.stop_listening = True
        print("Stopping always-on microphone...")

# Updated demo code
if __name__ == "__main__":
    from PyQt5.QtWidgets import QApplication, QWidget, QVBoxLayout, QLabel, QPushButton
    import sys

    class DemoWidget(QWidget):
        def __init__(self):
            super().__init__()
            self.init_ui()
            self.thread = SpeechRecognitionThread()
            self.thread.finished.connect(self.on_finished)
            self.thread.error.connect(self.on_error)

        def init_ui(self):
            layout = QVBoxLayout()
            self.status_label = QLabel("Click 'Start' to begin always-on speech recognition")
            self.transcription_label = QLabel("Transcription will appear here")
            self.start_button = QPushButton("Start")
            self.stop_button = QPushButton("Stop")
            self.stop_button.setEnabled(False)

            layout.addWidget(self.status_label)
            layout.addWidget(self.transcription_label)
            layout.addWidget(self.start_button)
            layout.addWidget(self.stop_button)

            self.setLayout(layout)
            self.setWindowTitle("Always-On Speech Recognition Demo")

            self.start_button.clicked.connect(self.start_recognition)
            self.stop_button.clicked.connect(self.stop_recognition)

        def start_recognition(self):
            self.status_label.setText("Always-on microphone activated. Listening...")
            self.start_button.setEnabled(False)
            self.stop_button.setEnabled(True)
            self.thread.start()

        def stop_recognition(self):
            self.thread.stop()
            self.status_label.setText("Always-on speech recognition stopped")
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)

        def on_finished(self, text):
            self.transcription_label.setText(f"Transcription: {text}")

        def on_error(self, error_message):
            self.status_label.setText(f"Error: {error_message}")
            self.start_button.setEnabled(True)
            self.stop_button.setEnabled(False)

    app = QApplication(sys.argv)
    demo = DemoWidget()
    demo.show()
    sys.exit(app.exec_())
