<p align="center">
  <img alt="Llama Assistant" style="width: 128px; max-width: 100%; height: auto;" src="https://raw.githubusercontent.com/vietanhdev/llama-assistant/refs/heads/main/logo.png"/>
  <h1 align="center">🌟 Llama Assistant 🌟</h1>
  <p align="center">Your Local AI Assistant with Llama Models</p>
</p>

![](https://user-images.githubusercontent.com/18329471/234640541-a6a65fbc-d7a5-4ec3-9b65-55305b01a7aa.png)

![Python](https://img.shields.io/badge/python-3.8%2B-blue.svg)
![Llama 3](https://img.shields.io/badge/Llama-3-green.svg)
![License](https://img.shields.io/badge/license-MIT-orange.svg)
![Version](https://img.shields.io/badge/version-0.1.0-red.svg)
![Stars](https://img.shields.io/github/stars/vietanhdev/llama-assistant.svg)
![Forks](https://img.shields.io/github/forks/vietanhdev/llama-assistant.svg)
![Issues](https://img.shields.io/github/issues/vietanhdev/llama-assistant.svg)

A simple AI-powered assistant to help you with your daily tasks, powered by Llama 3.2. It can recognize your voice, process natural language, and perform various actions based on your commands: summarizing text, rephasing sentences, answering questions, writing emails, and more.

This assistant can run offline on your local machine, and it respects your privacy by not sending any data to external servers.

![Screenshot](https://raw.githubusercontent.com/vietanhdev/llama-assistant/refs/heads/main/screenshot.png)

## TODO

- [x] Support multimodal model: [moondream2](https://huggingface.co/vikhyatk/moondream2).
- [ ] Add offline STT support: WhisperCPP.
- [ ] Add wake word detection: "Hey Llama!".
- [ ] Support 5 other text models.
- [ ] Support 5 other multimodal models.
- [ ] Knowledge database: Langchain or LlamaIndex?.
- [ ] Plugin system for extensibility.
- [ ] Package for Windows, Linux, and macOS.

## Features

- 🎙️ Voice recognition for hands-free interaction
- 💬 Natural language processing with Llama 3.2
- 🖼️ Image analysis capabilities (TODO)
- ⚡ Global hotkey for quick access (Cmd+Shift+Space on macOS)
- 🎨 Customizable UI with adjustable transparency

**Note:** This project is a work in progress, and new features are being added regularly.

## Technologies Used

- ![Python](https://img.shields.io/badge/Python-3.8%2B-blue?style=flat-square&logo=python&logoColor=white)
- ![Llama](https://img.shields.io/badge/Llama-3.2-yellow?style=flat-square&logo=meta&logoColor=white)
- ![SpeechRecognition](https://img.shields.io/badge/SpeechRecognition-3.8-green?style=flat-square&logo=google&logoColor=white)
- ![PyQt](https://img.shields.io/badge/PyQt-6-41CD52?style=flat-square&logo=qt&logoColor=white)

## Installation

**Install from PyPI:**

```bash
pip install llama-assistant
pip install pyaudio
```

**Or install from source:**

1. Clone the repository:

   ```bash
   git clone https://github.com/vietanhdev/llama-assistant.git
   cd llama-assistant
   ```

2. Install the required dependencies:

   ```bash
   pip install -r requirements.txt
   pip install pyaudio
   ```

**Speed Hack for Apple Silicon (M1, M2, M3) users:** 🔥🔥🔥

- Install Xcode:

```bash
# check the path of your xcode install 
xcode-select -p

# xcode installed returns
# /Applications/Xcode-beta.app/Contents/Developer

# if xcode is missing then install it... it takes ages;
xcode-select --install
```

- Build `llama-cpp-python` with METAL support:

```bash
pip uninstall llama-cpp-python -y
CMAKE_ARGS="-DGGML_METAL=on" pip install -U llama-cpp-python --no-cache-dir
pip install 'llama-cpp-python[server]'

# you should now have llama-cpp-python v0.1.62 or higher installed
llama-cpp-python         0.1.68
```

## Usage

Run the assistant using the following command:

```bash
llama-assistant

# Or with a
python -m llama_assistant.main
```

Use the global hotkey (default: `Cmd+Shift+Space`) to quickly access the assistant from anywhere on your system.

## Configuration

The assistant's settings can be customized by editing the `settings.json` file located in your home directory: `~/llama_assistant/settings.json`.

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgements

- [Radio icons created by Freepik - Flaticon](https://www.flaticon.com/free-icons/radio)
- [Llama 3.2](https://github.com/facebookresearch/llama) by Meta AI Research

## Contact

- Viet-Anh Nguyen - [vietanhdev](https://github.com/vietanhdev), [contact form](https://www.vietanh.dev/contact).
- Project Link: [https://github.com/vietanhdev/llama-assistant](https://github.com/vietanhdev/llama-assistant)
