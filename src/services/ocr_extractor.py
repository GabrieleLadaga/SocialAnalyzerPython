import io
from typing import Optional
import pytesseract
from PIL import Image
from google.cloud import vision

class OCRExtractor:

    def __init__(self, use_vision_api: bool = True):
        self.use_vision_api = use_vision_api
        if use_vision_api:
            self.vision_client = vision.ImageAnnotatorClient()

    def extract_from_url(self, image_url: str) -> Optional[str]:
        try:
            image = vision.Image()
            image.source.image_uri = image_url
            response = self.vision_client.text_detection(image=image)

            if response.error.message:
                print(f"Errore Vision: {response.error.message}")
                return None

            texts = response.text_annotations
            if texts:
                text = texts[0].description
                return text
            return None
        except Exception as e:
            print(f"Errore OCR: {e}")
            return None

    @staticmethod
    def extract_from_bytes(image_bytes: bytes) -> Optional[str]:
        try:
            image = Image.open(io.BytesIO(image_bytes))
            text = pytesseract.image_to_string(image)
            return text if text.strip() else None
        except Exception as e:
            print(f"Errore Tesseract: {e}")
            return None
