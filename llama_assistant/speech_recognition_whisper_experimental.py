import threading
import queue
import pyaudio
import wave
import os
from pathlib import Path
import datetime
from whisper_cpp_python import Whisper
import re
import requests


class SpeechRecognition:
    def __init__(self):
        # Audio settings
        self.RATE = 16000
        self.CHUNK = self.RATE
        self.NB_CHANNELS = 1
        self.RECORD_SECONDS = 1

        # Whisper settings
        self.WHISPER_LANGUAGE = "en"
        self.WHISPER_THREADS = 1

        # Initialize queues
        self.audio_queue = queue.Queue()
        self.text_queue = queue.Queue()

        # Set up model path and download if necessary
        self.model_dir = Path.home() / "llama-assistant" / "models" / "whisper-cpp"
        self.model_path = self.model_dir / "ggml-tiny-fp16.bin"
        self.download_model_if_needed()

        # Initialize Whisper model
        self.whisper = Whisper(model_path=str(self.model_path), n_threads=self.WHISPER_THREADS)

        # Initialize PyAudio
        self.audio = pyaudio.PyAudio()
        self.stream = self.audio.open(
            format=pyaudio.paInt16,
            channels=self.NB_CHANNELS,
            rate=self.RATE,
            input=True,
            frames_per_buffer=self.CHUNK,
        )

        # Create temporary folder for audio files
        self.tmp_audio_folder = Path("./tmp_audio")
        if not self.tmp_audio_folder.exists():
            self.tmp_audio_folder.mkdir()

        self.stop_listening = False

    def download_model_if_needed(self):
        if not self.model_path.exists():
            print("Downloading Whisper model...")
            self.model_dir.mkdir(parents=True, exist_ok=True)
            url = "https://huggingface.co/danielus/ggml-whisper-models/resolve/main/ggml-tiny-fp16.bin"
            response = requests.get(url)
            with open(self.model_path, "wb") as f:
                f.write(response.content)
            print("Model downloaded successfully.")

    def listen(self):
        while not self.stop_listening:
            audio_data = self.stream.read(self.CHUNK)
            self.audio_queue.put(audio_data)

    def transcribe(self):
        while not self.stop_listening:
            if not self.audio_queue.empty():
                audio_data = self.audio_queue.get()

                # Save audio data to temporary file
                tmp_filepath = f"./tmp_audio/output_{datetime.datetime.now()}.wav"
                with wave.open(tmp_filepath, "wb") as wf:
                    wf.setnchannels(self.NB_CHANNELS)
                    wf.setsampwidth(2)  # 16-bit audio
                    wf.setframerate(self.RATE)
                    wf.writeframes(audio_data)

                # Transcribe audio
                res = self.whisper.transcribe(file=tmp_filepath, language=self.WHISPER_LANGUAGE)
                transcription = res["text"]

                # Clean up transcription
                transcription = re.sub(r"\[.*\]", "", transcription)
                transcription = re.sub(r"\(.*\)", "", transcription)

                # Add transcription to text queue
                self.text_queue.put(transcription)

                # Cleanup
                os.remove(tmp_filepath)

    def start(self):
        self.stop_listening = False
        threading.Thread(target=self.listen, daemon=True).start()
        threading.Thread(target=self.transcribe, daemon=True).start()

    def stop(self):
        self.stop_listening = True
        self.stream.stop_stream()
        self.stream.close()
        self.audio.terminate()

    def get_transcription(self):
        if not self.text_queue.empty():
            return self.text_queue.get()
        return None


# Example usage
if __name__ == "__main__":
    recognizer = SpeechRecognition()
    recognizer.start()

    print("Speech recognition started. Press Ctrl+C to stop.")
    try:
        while True:
            transcription = recognizer.get_transcription()
            if transcription:
                print(f"Transcription: {transcription}")
    except KeyboardInterrupt:
        print("Stopping speech recognition...")
        recognizer.stop()
