import base64, json, re
from io import BytesIO
from PIL import Image
from openai import OpenAI
from .image_utils import resize_for_api, pil_to_base64_jpeg, pil_to_png_file


def extract_json(text: str) -> dict:
    text = text.strip().replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(text)
    except Exception:
        pass
    m = re.search(r"\{[\s\S]*\}", text)
    if m:
        return json.loads(m.group(0))
    raise ValueError("AI 응답에서 JSON을 읽지 못했습니다.")


def get_client(api_key: str):
    return OpenAI(api_key=api_key)


def analyze_image(api_key: str, model: str, image: Image.Image, prompt: str) -> dict:
    client = get_client(api_key)
    img = resize_for_api(image)
    b64 = pil_to_base64_jpeg(img)
    response = client.responses.create(
        model=model,
        input=[{"role":"user","content":[
            {"type":"input_text","text":prompt},
            {"type":"input_image","image_url":f"data:image/jpeg;base64,{b64}"}
        ]}],
    )
    return extract_json(response.output_text)


def palm_reading(api_key: str, model: str, left: Image.Image, right: Image.Image, prompt: str) -> str:
    client = get_client(api_key)
    left_b64 = pil_to_base64_jpeg(resize_for_api(left))
    right_b64 = pil_to_base64_jpeg(resize_for_api(right))
    response = client.responses.create(
        model=model,
        input=[{"role":"user","content":[
            {"type":"input_text","text":prompt},
            {"type":"input_image","image_url":f"data:image/jpeg;base64,{left_b64}"},
            {"type":"input_image","image_url":f"data:image/jpeg;base64,{right_b64}"},
        ]}],
    )
    return response.output_text


def generate_edited_image(api_key: str, model: str, image: Image.Image, prompt: str) -> Image.Image:
    client = get_client(api_key)
    image_file = pil_to_png_file(resize_for_api(image), "base_scene.png")
    # 우선 편집 API. 지원되지 않거나 권한이 없으면 생성 API fallback.
    try:
        result = client.images.edit(model=model, image=image_file, prompt=prompt, size="1024x1024")
    except Exception:
        result = client.images.generate(model=model, prompt=prompt, size="1024x1024")
    b64 = result.data[0].b64_json
    return Image.open(BytesIO(base64.b64decode(b64))).convert("RGB")
