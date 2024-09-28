from typing import List, Dict, Optional
import time
from threading import Timer
from llama_cpp import Llama
from llama_cpp.llama_chat_format import MoondreamChatHandler


class Model:
    def __init__(
        self,
        model_type: str,
        model_id: str,
        model_name: str,
        model_path: Optional[str] = None,
        repo_id: Optional[str] = None,
        filename: Optional[str] = None,
    ):
        self.model_type = model_type
        self.model_id = model_id
        self.model_name = model_name
        self.model_path = model_path
        self.repo_id = repo_id
        self.filename = filename

    def is_online(self) -> bool:
        return self.repo_id is not None and self.filename is not None


class ModelHandler:
    def __init__(self):
        self.supported_models: List[Model] = []
        self.loaded_models: Dict[str, Dict] = {}
        self.model_timers: Dict[str, Timer] = {}

    def list_supported_models(self) -> List[Model]:
        return self.supported_models

    def add_supported_model(self, model: Model):
        self.supported_models.append(model)

    def remove_supported_model(self, model_id: str):
        self.supported_models = [
            m for m in self.supported_models if m.model_id != model_id
        ]
        if model_id in self.loaded_models:
            self.unload_model(model_id)

    def load_model(self, model_id: str) -> Optional[Dict]:
        model = next(
            (m for m in self.supported_models if m.model_id == model_id), None
        )
        if not model:
            print(f"Model with ID {model_id} not found.")
            return None

        if model_id not in self.loaded_models:
            print(f"Loading model: {model.model_name}")
            if model.is_online():
                if model.model_type == "text":
                    loaded_model = Llama.from_pretrained(
                        repo_id=model.repo_id,
                        filename=model.filename,
                    )
                elif model.model_type == "image":
                    chat_handler = MoondreamChatHandler.from_pretrained(
                        repo_id="vikhyatk/moondream2",
                        filename="*mmproj*",
                    )
                    loaded_model = Llama.from_pretrained(
                        repo_id=model.repo_id,
                        filename=model.filename,
                        chat_handler=chat_handler,
                        n_ctx=2048,
                    )
                else:
                    print(f"Unsupported model type: {model.model_type}")
                    return None
            else:
                # Load model from local path
                loaded_model = Llama(model_path=model.model_path)

            self.loaded_models[model_id] = {
                "model": loaded_model,
                "last_used": time.time(),
            }
            self._schedule_unload(model_id)

        return self.loaded_models[model_id]

    def unload_model(self, model_id: str):
        if model_id in self.loaded_models:
            print(f"Unloading model: {model_id}")
            del self.loaded_models[model_id]
            if model_id in self.model_timers:
                self.model_timers[model_id].cancel()
                del self.model_timers[model_id]

    def chat_completion(
        self,
        model_id: str,
        message: str,
        image: Optional[str] = None,
        n_ctx: int = 2048,
    ) -> str:
        model_data = self.load_model(model_id)
        if not model_data:
            return "Failed to load model"

        model = model_data["model"]
        model_data["last_used"] = time.time()
        self._schedule_unload(model_id)

        if image:
            response = model.create_chat_completion(
                messages=[
                    {
                        "role": "user",
                        "content": [
                            {"type": "text", "text": message},
                            {"type": "image_url", "image_url": {"url": image}},
                        ],
                    }
                ]
            )
        else:
            response = model.create_chat_completion(
                messages=[{"role": "user", "content": message}]
            )

        return response["choices"][0]["message"]["content"]

    def _schedule_unload(self, model_id: str):
        if model_id in self.model_timers:
            self.model_timers[model_id].cancel()

        timer = Timer(3600, self.unload_model, args=[model_id])
        timer.start()
        self.model_timers[model_id] = timer


# Example usage
handler = ModelHandler()

# Add supported models
handler.add_supported_model(
    Model(
        model_type="text",
        model_id="llama_text",
        model_name="Llama 3.2 1B Instruct",
        repo_id="hugging-quants/Llama-3.2-1B-Instruct-Q4_K_M-GGUF",
        filename="*q4_k_m.gguf",
    )
)
handler.add_supported_model(
    Model(
        model_type="image",
        model_id="moondream",
        model_name="Moondream2",
        repo_id="vikhyatk/moondream2",
        filename="*text-model*",
    )
)
# handler.add_supported_model(
#     Model(
#         model_type="text",
#         model_id="local_model",
#         model_name="Local Text Model",
#         model_path="/path/to/local/model.gguf",
#     )
# )

# List supported models
print("Supported models:")
for model in handler.list_supported_models():
    print(f"- {model.model_name} (ID: {model.model_id})")

if __name__ == "__main__":
    # Use text model
    result = handler.chat_completion("llama_text", "Tell me a joke")
    print(result)

    # Use image model
    image_url = "https://upload.wikimedia.org/wikipedia/commons/thumb/d/dd/Gfp-wisconsin-madison-the-nature-boardwalk.jpg/2560px-Gfp-wisconsin-madison-the-nature-boardwalk.jpg"
    result = handler.chat_completion(
        "moondream", "What's in this image?", image=image_url
    )
    print(result)

    # Use local model
    result = handler.chat_completion("local_model", "Hello, local model!")
    print(result)
