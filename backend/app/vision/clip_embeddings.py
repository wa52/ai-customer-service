from pathlib import Path


class ClipEmbedder:
    """Lazy CPU CLIP adapter; keeps model loading out of app startup until needed."""

    def __init__(self, model_name: str = "openai/clip-vit-base-patch32") -> None:
        self.model_name = model_name
        self._processor = None
        self._model = None

    def _load(self) -> None:
        if self._model is not None:
            return
        import torch
        from transformers import CLIPModel, CLIPProcessor

        self._processor = CLIPProcessor.from_pretrained(self.model_name)
        self._model = CLIPModel.from_pretrained(self.model_name)
        self._model.eval()
        self._torch = torch

    def image(self, path: Path) -> list[float]:
        from PIL import Image

        self._load()
        image = Image.open(path).convert("RGB")
        inputs = self._processor(images=image, return_tensors="pt")
        with self._torch.no_grad():
            vector = self._model.get_image_features(**inputs)[0]
        vector = vector / vector.norm(p=2)
        return vector.cpu().tolist()

    def text(self, value: str) -> list[float]:
        self._load()
        inputs = self._processor(text=[value], return_tensors="pt", padding=True, truncation=True)
        with self._torch.no_grad():
            vector = self._model.get_text_features(**inputs)[0]
        vector = vector / vector.norm(p=2)
        return vector.cpu().tolist()
