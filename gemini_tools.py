import json, re
from io import BytesIO
from PIL import Image
from google import genai
from google.genai import types
from .image_utils import resize_for_api, pil_to_png_bytes


def extract_json(text: str) -> dict:
    text = text.strip().replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(text)
    except Exception:
        pass
    m = re.search(r"\{[\s\S]*\}", text)
    if m:
        return json.loads(m.group(0))
    raise ValueError("Gemini 응답에서 JSON을 읽지 못했습니다.")


def get_client(api_key: str):
    return genai.Client(api_key=api_key)


def analyze_image(api_key: str, model: str, image: Image.Image, prompt: str) -> dict:
    client = get_client(api_key)
    part = types.Part.from_bytes(data=pil_to_png_bytes(resize_for_api(image)), mime_type="image/png")
    response = client.models.generate_content(
        model=model,
        contents=[prompt, part],
        config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.35),
    )
    return extract_json(response.text)


def generate_edited_image(api_key: str, model: str, image: Image.Image, prompt: str) -> Image.Image:
    client = get_client(api_key)
    part = types.Part.from_bytes(data=pil_to_png_bytes(resize_for_api(image)), mime_type="image/png")
    response = client.models.generate_content(
        model=model,
        contents=[prompt, part],
        config=types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"], temperature=0.7),
    )
    if not response.candidates:
        raise ValueError("Gemini 이미지 생성 응답이 비어 있습니다.")
    for part in response.candidates[0].content.parts:
        if getattr(part, "inline_data", None) is not None:
            return Image.open(BytesIO(part.inline_data.data)).convert("RGB")
    raise ValueError("Gemini 응답에서 생성 이미지를 찾지 못했습니다.")
