import json
from pathlib import Path

DEFAULT_LAUNCH_SHORTCUT = "<cmd>+<shift>+<space>"
DEFAULT_SETTINGS = {
    "shortcut": DEFAULT_LAUNCH_SHORTCUT,
    "color": "#1E1E1E",
    "transparency": 95,
    "text_model": "hugging-quants/Llama-3.2-1B-Instruct-Q4_K_M-GGUF",
    "multimodal_model": "vikhyatk/moondream2",
    "hey_llama_chat": False,
    "hey_llama_mic": False,
}
DEFAULT_MODELS = [
    {
        "model_name": "Llama-3.2-1B-Instruct-Q4_K_M-GGUF",
        "model_id": "hugging-quants/Llama-3.2-1B-Instruct-Q4_K_M-GGUF",
        "model_type": "text",
        "model_path": None,
        "repo_id": "hugging-quants/Llama-3.2-1B-Instruct-Q4_K_M-GGUF",
        "filename": "*q4_k_m.gguf",
    },
    {
        "model_name": "Llama-3.2-1B-Instruct-Q8_0-GGUF",
        "model_id": "hugging-quants/Llama-3.2-1B-Instruct-Q8_0-GGUF",
        "model_type": "text",
        "model_path": None,
        "repo_id": "hugging-quants/Llama-3.2-1B-Instruct-Q8_0-GGUF",
        "filename": "*q8_0.gguf",
    },
    {
        "model_name": "Llama-3.2-3B-Instruct-Q4_K_M-GGUF",
        "model_id": "hugging-quants/Llama-3.2-3B-Instruct-Q4_K_M-GGUF",
        "model_type": "text",
        "model_path": None,
        "repo_id": "hugging-quants/Llama-3.2-3B-Instruct-Q4_K_M-GGUF",
        "filename": "*q4_k_m.gguf",
    },
    {
        "model_name": "Llama-3.2-3B-Instruct-Q8_0-GGUF",
        "model_id": "hugging-quants/Llama-3.2-3B-Instruct-Q8_0-GGUF",
        "model_type": "text",
        "model_path": None,
        "repo_id": "hugging-quants/Llama-3.2-3B-Instruct-Q8_0-GGUF",
        "filename": "*q8_0.gguf",
    },
    {
        "model_name": "Qwen2.5-0.5B-Instruct-GGUF",
        "model_id": "Qwen/Qwen2.5-0.5B-Instruct-GGUF-q4_k_m",
        "model_type": "text",
        "model_path": None,
        "repo_id": "Qwen/Qwen2.5-0.5B-Instruct-GGUF",
        "filename": "*q4_k_m.gguf",
    },
    {
        "model_name": "Moondream2",
        "model_id": "vikhyatk/moondream2",
        "model_type": "image",
        "model_path": None,
        "repo_id": "vikhyatk/moondream2",
        "filename": "*text-model*",
    },
    {
        "model_name": "Llava-1.5",
        "model_id": "mys/ggml_llava-v1.5-7b/q4_k",
        "model_type": "image",
        "model_path": None,
        "repo_id": "mys/ggml_llava-v1.5-7b",
        "filename": "*q4_k.gguf",
    },
    {
        "model_name": "Llava-1.5",
        "model_id": "mys/ggml_llava-v1.5-7b/f16",
        "model_type": "image",
        "model_path": None,
        "repo_id": "mys/ggml_llava-v1.5-7b",
        "filename": "*f16.gguf",
    },
    {
        "model_name": "MiniCPM-V-2_6-gguf",
        "model_id": "openbmb/MiniCPM-V-2_6-gguf-Q4_K_M",
        "model_type": "image",
        "model_path": None,
        "repo_id": "openbmb/MiniCPM-V-2_6-gguf",
        "filename": "*Q4_K_M.gguf",
    },
    {
        "model_name": "MiniCPM-V-2_6-gguf",
        "model_id": "openbmb/MiniCPM-V-2_6-gguf-Q8_0",
        "model_type": "image",
        "model_path": None,
        "repo_id": "openbmb/MiniCPM-V-2_6-gguf",
        "filename": "*Q8_0.gguf",
    },
]


home_dir = Path.home()
config_file = home_dir / "llama_assistant" / "config.json"

if config_file.exists():
    with open(config_file, "r") as f:
        config_data = json.load(f)
    custom_models = config_data.get("custom_models", [])
else:
    custom_models = []

models = DEFAULT_MODELS + custom_models

# Save the initial configuration if it doesn't exist
if not config_file.exists():
    config_dir = config_file.parent
    if not config_dir.exists():
        config_dir.mkdir(parents=True)
    with open(config_file, "w") as f:
        json.dump({"custom_models": custom_models}, f, indent=2)


def save_custom_models():
    with open(config_file, "w") as f:
        json.dump({"custom_models": custom_models}, f, indent=2)
