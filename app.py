import base64
import json
import re
import textwrap
from datetime import datetime
from io import BytesIO
from typing import Optional, Dict, Any, List

import streamlit as st
from PIL import Image, ImageDraw, ImageFont
from reportlab.lib.pagesizes import A4
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.pdfgen import canvas
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

# Optional API imports are handled after checking secrets
from openai import OpenAI
from google import genai
from google.genai import types


# =========================================================
# App config
# =========================================================
st.set_page_config(
    page_title="AI Vision Studio",
    page_icon="✨",
    layout="wide",
    initial_sidebar_state="expanded",
)

APP_BG = "#F8F5EF"
CARD = "#FFFFFF"
INK = "#222222"
MUTED = "#6F6A62"
LINE = "#DDD5C9"
GOLD = "#B89B5E"

st.markdown(
    f"""
    <style>
    .stApp {{
        background: linear-gradient(180deg, {APP_BG} 0%, #FFFFFF 78%);
        color: {INK};
    }}
    .hero {{
        padding: 46px 34px 30px 34px;
        border: 1px solid {LINE};
        border-radius: 32px;
        background: rgba(255,255,255,0.84);
        box-shadow: 0 20px 60px rgba(70, 55, 35, 0.08);
        margin-bottom: 26px;
    }}
    .eyebrow {{
        color: {GOLD}; font-size: 13px; letter-spacing: .22em;
        font-weight: 900; margin-bottom: 10px;
    }}
    .main-title {{
        font-size: 52px; line-height: 1.04; letter-spacing: -.045em;
        font-weight: 900; color: {INK}; margin-bottom: 14px;
    }}
    .subtitle {{ color: {MUTED}; font-size: 17px; line-height: 1.75; max-width: 980px; }}
    .lux-card {{
        background: rgba(255,255,255,0.94); border: 1px solid {LINE};
        border-radius: 28px; padding: 26px 28px;
        box-shadow: 0 18px 50px rgba(70, 55, 35, 0.07);
        margin-bottom: 22px;
    }}
    .section-label {{
        font-size: 12px; color: {GOLD}; letter-spacing: .18em;
        font-weight: 900; text-transform: uppercase; margin-bottom: 8px;
    }}
    .card-title {{ font-size: 25px; font-weight: 900; margin-bottom: 12px; color: {INK}; }}
    .body-text {{ font-size: 16px; line-height: 1.9; color: #34302B; white-space: pre-wrap; }}
    .small-note {{ font-size: 13px; color: #817B72; line-height: 1.7; }}
    .pos-card {{
        border: 1px solid {LINE}; border-radius: 22px; padding: 18px;
        background: #FBF8F2; margin-bottom: 14px;
    }}
    .pos-rank {{ color: {GOLD}; font-size: 12px; font-weight: 900; letter-spacing: .16em; }}
    .pos-title {{ font-size: 20px; font-weight: 900; color: {INK}; margin-top: 4px; margin-bottom: 8px; }}
    div[data-testid="stDownloadButton"] button, div[data-testid="stButton"] button {{
        border-radius: 999px; border: 1px solid {GOLD};
        background: {INK}; color: white; padding: .65rem 1.3rem; font-weight: 800;
    }}
    section[data-testid="stSidebar"] {{ background: {APP_BG}; border-right: 1px solid {LINE}; }}
    </style>
    """,
    unsafe_allow_html=True,
)


# =========================================================
# Helpers
# =========================================================
def get_secret(name: str, default: Optional[str] = None) -> Optional[str]:
    try:
        return st.secrets.get(name, default)
    except Exception:
        return default


def get_openai_client() -> OpenAI:
    key = get_secret("OPENAI_API_KEY")
    if not key:
        raise RuntimeError("OPENAI_API_KEY가 Streamlit Secrets에 없습니다.")
    return OpenAI(api_key=key)


def get_gemini_client() -> genai.Client:
    key = get_secret("GEMINI_API_KEY")
    if not key:
        raise RuntimeError("GEMINI_API_KEY가 Streamlit Secrets에 없습니다.")
    return genai.Client(api_key=key)


def resize_for_api(image: Image.Image, max_side: int = 1600) -> Image.Image:
    img = image.convert("RGB")
    w, h = img.size
    if max(w, h) <= max_side:
        return img
    r = max_side / max(w, h)
    return img.resize((int(w * r), int(h * r)))


def pil_to_base64_jpeg(image: Image.Image) -> str:
    buffer = BytesIO()
    resize_for_api(image).save(buffer, format="JPEG", quality=92)
    return base64.b64encode(buffer.getvalue()).decode("utf-8")


def pil_to_png_bytes(image: Image.Image) -> bytes:
    buffer = BytesIO()
    resize_for_api(image).save(buffer, format="PNG")
    return buffer.getvalue()


def pil_to_png_file(image: Image.Image, name: str = "image.png") -> BytesIO:
    buffer = BytesIO()
    resize_for_api(image).save(buffer, format="PNG")
    buffer.seek(0)
    buffer.name = name
    return buffer


def image_buffer(image: Image.Image, fmt: str = "PNG") -> BytesIO:
    buffer = BytesIO()
    image.save(buffer, format=fmt)
    buffer.seek(0)
    return buffer


def extract_json(text: str) -> Dict[str, Any]:
    text = (text or "").strip()
    text = text.replace("```json", "").replace("```", "").strip()
    try:
        return json.loads(text)
    except Exception:
        pass
    m = re.search(r"\{[\s\S]*\}", text)
    if not m:
        raise ValueError("응답에서 JSON을 찾지 못했습니다.")
    return json.loads(m.group(0))


def safe(data: Dict[str, Any], key: str, default: str = "") -> str:
    v = data.get(key, default)
    return default if v is None else str(v)


def get_latin_font(size: int, bold: bool = False):
    paths = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for p in paths:
        try:
            return ImageFont.truetype(p, size)
        except Exception:
            continue
    return ImageFont.load_default()


def draw_overlay(image: Image.Image, data: Dict[str, Any], title: str = "AI DIRECTION MAP") -> Image.Image:
    """Draw only numbers and English title to avoid Korean font issues in PIL."""
    img = image.convert("RGB").copy()
    draw = ImageDraw.Draw(img, "RGBA")
    w, h = img.size
    font_title = get_latin_font(max(18, int(w * 0.023)), True)
    font_big = get_latin_font(max(24, int(w * 0.034)), True)
    colors = [(184, 155, 94, 238), (34, 34, 34, 230), (116, 96, 66, 225)]

    for idx, pos in enumerate(data.get("best_positions", [])[:3]):
        try:
            x = int(w * float(pos.get("x_percent", 50)) / 100)
            y = int(h * float(pos.get("y_percent", 60)) / 100)
        except Exception:
            x, y = int(w * 0.5), int(h * 0.6)
        radius = max(18, int(min(w, h) * 0.037))
        color = colors[idx % len(colors)]
        rank = str(pos.get("rank", idx + 1))
        draw.ellipse([x - radius, y - radius, x + radius, y + radius], fill=color, outline=(255, 255, 255, 255), width=max(3, int(radius * .15)))
        box = draw.textbbox((0, 0), rank, font=font_big)
        tw, th = box[2] - box[0], box[3] - box[1]
        draw.text((x - tw / 2, y - th / 2 - 2), rank, font=font_big, fill=(255, 255, 255, 255))

    box = draw.textbbox((0, 0), title, font=font_title)
    tw, th = box[2] - box[0], box[3] - box[1]
    draw.rounded_rectangle([18, 18, 18 + tw + 30, 18 + th + 22], radius=16, fill=(248, 245, 239, 235), outline=(216, 210, 200, 235), width=2)
    draw.text((33, 29), title, font=font_title, fill=(34, 34, 34, 255))
    return img


def init_pdf_font():
    # Korean CID font supported by ReportLab without bundling font files
    try:
        pdfmetrics.registerFont(UnicodeCIDFont("HYGoThic-Medium"))
        return "HYGoThic-Medium", "HYGoThic-Medium"
    except Exception:
        return "Helvetica", "Helvetica-Bold"


def wrap_for_pdf(text: str, width: int = 82) -> List[str]:
    lines: List[str] = []
    for p in (text or "").split("\n"):
        if not p.strip():
            lines.append("")
        else:
            lines.extend(textwrap.wrap(p, width=width, replace_whitespace=False, break_long_words=False))
    return lines


def make_text_pdf(title: str, body: str, images: Optional[List[tuple]] = None) -> BytesIO:
    buf = BytesIO()
    c = canvas.Canvas(buf, pagesize=A4)
    W, H = A4
    font, font_bold = init_pdf_font()
    margin = 36

    def new_page():
        c.setFillColor(HexColor(APP_BG))
        c.rect(0, 0, W, H, stroke=0, fill=1)

    new_page()
    c.setFillColor(HexColor(CARD))
    c.roundRect(margin, H - 132, W - margin * 2, 96, 18, stroke=0, fill=1)
    c.setFillColor(HexColor(GOLD)); c.setFont(font_bold, 10); c.drawString(margin + 22, H - 70, "AI VISION STUDIO")
    c.setFillColor(HexColor(INK)); c.setFont(font_bold, 22); c.drawString(margin + 22, H - 99, title[:48])
    c.setFillColor(HexColor(MUTED)); c.setFont(font, 8.5); c.drawString(margin + 22, H - 116, datetime.now().strftime("%Y-%m-%d %H:%M"))
    y = H - 160

    if images:
        for img_title, img in images:
            if y < 260:
                c.showPage(); new_page(); y = H - 54
            c.setFillColor(HexColor(INK)); c.setFont(font_bold, 12); c.drawString(margin, y, img_title)
            y -= 12
            temp = BytesIO(); thumb = img.copy(); thumb.thumbnail((900, 520)); thumb.save(temp, format="PNG"); temp.seek(0)
            iw, ih = thumb.size; max_w, max_h = W - margin * 2, 190
            ratio = min(max_w / iw, max_h / ih)
            dw, dh = iw * ratio, ih * ratio
            c.drawImage(ImageReader(temp), (W - dw) / 2, y - dh, width=dw, height=dh, mask="auto")
            y = y - dh - 24

    c.setFillColor(HexColor(INK)); c.setFont(font_bold, 14); c.drawString(margin, y, "Report")
    y -= 24
    c.setFont(font, 9.5); c.setFillColor(HexColor("#34302B"))
    for line in wrap_for_pdf(body):
        if y < 48:
            c.showPage(); new_page(); y = H - 54
            c.setFont(font, 9.5); c.setFillColor(HexColor("#34302B"))
        if not line.strip():
            y -= 8
        else:
            c.drawString(margin, y, line)
            y -= 14
    c.save(); buf.seek(0)
    return buf


# =========================================================
# Prompts
# =========================================================
def palm_prompt(dominant_hand: str, report_name: str, tone: str) -> str:
    return f"""
너는 손금 해석 전문가이자 고급 에디토리얼 리포트 작가이다.
업로드된 왼손, 오른손 사진을 실제로 관찰해 손금 리포트를 작성하라.

중요 원칙:
- 손금 해석은 과학적 진단이나 확정적 예언이 아니라 상징적 성향 분석이라고 명시하라.
- 건강, 수명, 질병, 사고, 사망, 임신, 재산 확정 등은 단정하지 마라.
- 사진에서 보이는 손금 특징만 근거로 분석하라.
- 주로 사용하는 손: {dominant_hand}
- 리포트 이름: {report_name}
- 문체: {tone}
- 한국어로 작성하라.

구성:
1. 제목
2. 주의 문구
3. 전체 인상
4. 왼손 분석: 생명선, 두뇌선, 감정선, 운명선, 태양선
5. 오른손 분석: 생명선, 두뇌선, 감정선, 운명선, 태양선
6. 양손 비교
7. 핵심 성향 카드: LIFE, MIND, HEART, WORK, TALENT
8. 종합 리딩
9. 한 줄 리딩
"""


def photo_analysis_prompt(mode: str, subject_type: str, style: str, output_use: str, extra: str) -> str:
    return f"""
너는 전문 사진 디렉터이자 구도 분석가이다.
업로드한 사진을 실제로 관찰하여 인물 또는 피사체가 어디에 배치되면 가장 자연스럽고 아름다운지 분석하라.

중요:
- 하드코딩된 일반 조언 금지. 반드시 사진 속 실제 장면을 근거로 분석하라.
- 공간, 선, 여백, 빛 방향, 배경 요소, 시선 흐름을 관찰하라.
- 특정 인물의 신원, 나이, 성별, 민감한 속성은 추정하지 마라.
- 추천 위치는 이미지 전체 기준 비율 좌표로 제시하라.
- x_percent: 왼쪽 0, 오른쪽 100 / y_percent: 위쪽 0, 아래쪽 100
- 결과는 JSON만 반환하라.

사용자 설정:
- 분석 모드: {mode}
- 배치할 대상: {subject_type}
- 원하는 분위기: {style}
- 결과물 용도: {output_use}
- 추가 요청: {extra}

반환 JSON 스키마:
{{
  "scene_summary": "사진 속 실제 장면 요약",
  "composition_type": "사진의 구도 유형",
  "visual_flow": "시선 흐름 설명",
  "light_direction": "빛의 방향과 활용 방법",
  "background_notes": "배경에서 주의할 요소",
  "best_positions": [
    {{"rank": 1, "short_label": "짧은 위치 이름", "x_percent": 68, "y_percent": 64, "pose": "추천 포즈 또는 배치", "camera_tip": "촬영 팁", "reason": "사진 속 요소를 근거로 한 이유"}},
    {{"rank": 2, "short_label": "짧은 위치 이름", "x_percent": 42, "y_percent": 62, "pose": "추천 포즈 또는 배치", "camera_tip": "촬영 팁", "reason": "사진 속 요소를 근거로 한 이유"}},
    {{"rank": 3, "short_label": "짧은 위치 이름", "x_percent": 55, "y_percent": 70, "pose": "추천 포즈 또는 배치", "camera_tip": "촬영 팁", "reason": "사진 속 요소를 근거로 한 이유"}}
  ],
  "avoid_positions": [{{"x_percent": 50, "y_percent": 42, "reason": "피해야 하는 이유"}}],
  "shooting_tips": ["팁 1", "팁 2", "팁 3"],
  "one_line_direction": "촬영자가 바로 말해줄 수 있는 한 줄 디렉팅"
}}
"""


def image_prompt_from_analysis(data: Dict[str, Any], subject_type: str, style: str, extra: str) -> str:
    best = (data.get("best_positions") or [{}])[0]
    return f"""
Use the uploaded image as the base scene.
Add one natural realistic {subject_type} into the scene.
Place the subject around x={best.get('x_percent', 50)}%, y={best.get('y_percent', 60)}% of the image.
Recommended location: {best.get('short_label', '')}.
Pose: {best.get('pose', '')}.
Reason for placement: {best.get('reason', '')}.
Preserve the original background, camera angle, perspective, lighting, and overall composition.
Lighting note: {data.get('light_direction', '')}.
Style: {style}. Natural realistic premium editorial photography.
Do not add text, labels, arrows, UI, or graphic markers.
Extra request: {extra}
"""


def photo_report_text(data: Dict[str, Any], engine: str) -> str:
    lines = [f"{engine} PHOTO DIRECTOR REPORT", ""]
    for k, label in [("scene_summary", "장면 요약"), ("composition_type", "구도 유형"), ("visual_flow", "시선 흐름"), ("light_direction", "빛 방향"), ("background_notes", "배경 메모")]:
        lines.append(f"{label}: {safe(data, k)}")
    lines.append("\n추천 위치 TOP 3")
    for p in data.get("best_positions", []):
        lines += ["", f"{p.get('rank', '-')}. {p.get('short_label', '추천 위치')}", f"- 좌표: x {p.get('x_percent')}%, y {p.get('y_percent')}%", f"- 포즈: {p.get('pose', '')}", f"- 카메라 팁: {p.get('camera_tip', '')}", f"- 이유: {p.get('reason', '')}"]
    lines.append("\n피해야 할 위치")
    for a in data.get("avoid_positions", []):
        lines.append(f"- x {a.get('x_percent')}%, y {a.get('y_percent')}%: {a.get('reason', '')}")
    lines.append("\n촬영 팁")
    for t in data.get("shooting_tips", []):
        lines.append(f"- {t}")
    lines.append(f"\n한 줄 디렉팅: {safe(data, 'one_line_direction')}")
    return "\n".join(lines)


# =========================================================
# API calls
# =========================================================
def openai_vision_text(images: List[Image.Image], prompt: str, model: Optional[str] = None) -> str:
    client = get_openai_client()
    model = model or get_secret("OPENAI_VISION_MODEL", "gpt-4.1-mini")
    content = [{"type": "input_text", "text": prompt}]
    for im in images:
        content.append({"type": "input_image", "image_url": f"data:image/jpeg;base64,{pil_to_base64_jpeg(im)}"})
    resp = client.responses.create(model=model, input=[{"role": "user", "content": content}])
    return resp.output_text


def openai_analyze_photo(image: Image.Image, prompt: str) -> Dict[str, Any]:
    return extract_json(openai_vision_text([image], prompt))


def openai_generate_image(base_image: Image.Image, prompt: str) -> Image.Image:
    client = get_openai_client()
    model = get_secret("OPENAI_IMAGE_MODEL", "gpt-image-1")
    img_file = pil_to_png_file(base_image, "base_scene.png")
    try:
        resp = client.images.edit(model=model, image=img_file, prompt=prompt, size="1024x1024")
    except Exception:
        resp = client.images.generate(model=model, prompt=prompt, size="1024x1024")
    b64 = resp.data[0].b64_json
    return Image.open(BytesIO(base64.b64decode(b64))).convert("RGB")


def gemini_analyze_photo(image: Image.Image, prompt: str) -> Dict[str, Any]:
    client = get_gemini_client()
    model = get_secret("GEMINI_VISION_MODEL", "gemini-2.5-flash")
    image_part = types.Part.from_bytes(data=pil_to_png_bytes(image), mime_type="image/png")
    resp = client.models.generate_content(
        model=model,
        contents=[prompt, image_part],
        config=types.GenerateContentConfig(response_mime_type="application/json", temperature=0.35),
    )
    return extract_json(resp.text)


def gemini_generate_image(base_image: Image.Image, prompt: str) -> Image.Image:
    client = get_gemini_client()
    model = get_secret("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image")
    image_part = types.Part.from_bytes(data=pil_to_png_bytes(base_image), mime_type="image/png")
    resp = client.models.generate_content(
        model=model,
        contents=[prompt, image_part],
        config=types.GenerateContentConfig(response_modalities=["TEXT", "IMAGE"], temperature=0.7),
    )
    for part in resp.candidates[0].content.parts:
        if getattr(part, "inline_data", None):
            return Image.open(BytesIO(part.inline_data.data)).convert("RGB")
    raise RuntimeError("Gemini 응답에서 생성 이미지를 찾지 못했습니다.")


# =========================================================
# UI components
# =========================================================
def hero(eyebrow: str, title: str, subtitle: str):
    st.markdown(f"""
    <div class="hero">
      <div class="eyebrow">{eyebrow}</div>
      <div class="main-title">{title}</div>
      <div class="subtitle">{subtitle}</div>
    </div>
    """, unsafe_allow_html=True)


def card_start(label: str, title: str):
    st.markdown(f'<div class="lux-card"><div class="section-label">{label}</div><div class="card-title">{title}</div>', unsafe_allow_html=True)


def card_end():
    st.markdown('</div>', unsafe_allow_html=True)


def show_photo_analysis(data: Dict[str, Any]):
    st.markdown(f"""
    <div class="body-text"><b>장면 요약</b><br>{safe(data,'scene_summary')}<br><br>
    <b>구도 유형</b><br>{safe(data,'composition_type')}<br><br>
    <b>시선 흐름</b><br>{safe(data,'visual_flow')}<br><br>
    <b>빛 방향</b><br>{safe(data,'light_direction')}<br><br>
    <b>배경 메모</b><br>{safe(data,'background_notes')}</div>
    """, unsafe_allow_html=True)
    st.divider()
    for p in data.get("best_positions", []):
        st.markdown(f"""
        <div class="pos-card"><div class="pos-rank">POSITION {p.get('rank','-')}</div>
        <div class="pos-title">{p.get('short_label','추천 위치')}</div>
        <div class="body-text"><b>좌표</b>: x {p.get('x_percent')}%, y {p.get('y_percent')}%<br>
        <b>포즈</b>: {p.get('pose','')}<br><b>카메라 팁</b>: {p.get('camera_tip','')}<br>
        <b>이유</b>: {p.get('reason','')}</div></div>
        """, unsafe_allow_html=True)
    st.markdown(f"<div class='body-text'><b>한 줄 디렉팅</b><br>{safe(data, 'one_line_direction')}</div>", unsafe_allow_html=True)


def photo_settings(prefix: str):
    mode = st.selectbox("분석 모드", ["인물 위치 잡아주기", "여행 사진 포즈 추천", "제품/소품 배치 추천", "교실/행사 사진 구도 추천", "썸네일·홍보 이미지 구도 추천"], key=f"{prefix}_mode")
    subject = st.text_input("배치할 대상", value="person", key=f"{prefix}_subject", help="예: person, student, teacher, child, product 등 영어 권장")
    style = st.selectbox("원하는 분위기", ["natural realistic editorial photography", "warm cinematic family photo", "clean minimal premium look", "bright school activity photo", "travel magazine style", "soft emotional portrait style"], key=f"{prefix}_style")
    use = st.selectbox("결과물 용도", ["SNS 사진", "학교 홍보물", "여행 사진", "PPT 표지", "카드뉴스", "제품/소품 촬영", "개인 기록"], key=f"{prefix}_use")
    extra = st.text_area("추가 요청", placeholder="예: 인물은 자연스럽게 웃고, 배경은 최대한 유지해주세요.", height=90, key=f"{prefix}_extra")
    uploaded = st.file_uploader("사진 업로드", type=["jpg", "jpeg", "png", "webp"], key=f"{prefix}_file")
    return mode, subject, style, use, extra, uploaded


def clear_keys(keys: List[str]):
    for k in keys:
        st.session_state.pop(k, None)


# =========================================================
# Pages
# =========================================================
st.sidebar.markdown("## AI Vision Studio")
page = st.sidebar.radio("페이지", ["0. Home", "1. 손금 분석", "2. OpenAI 사진 앱", "3. Gemini 사진 앱", "4. 비교·다운로드", "5. 사용 가이드"])
st.sidebar.divider()
st.sidebar.caption("필요 Secrets")
st.sidebar.code("OPENAI_API_KEY\nGEMINI_API_KEY", language="toml")

if page == "0. Home":
    hero("MULTIMODAL AI WEB APP", "AI Vision Studio", "손금 분석, OpenAI 사진 구도 분석, Gemini 사진 구도 분석을 하나로 묶은 Streamlit Cloud용 멀티페이지 앱입니다.")
    c1, c2, c3 = st.columns(3)
    with c1:
        card_start("PALM", "손금 분석")
        st.markdown("<div class='body-text'>양손 사진을 업로드하면 OpenAI Vision이 생명선, 두뇌선, 감정선, 운명선, 태양선 중심으로 고급 리포트를 작성합니다.</div>", unsafe_allow_html=True)
        card_end()
    with c2:
        card_start("OPENAI", "사진 구도 앱")
        st.markdown("<div class='body-text'>사진을 분석해 추천 위치 TOP 3을 좌표로 만들고, 원본 위에 마커를 표시하며, OpenAI 이미지 API로 예시 이미지를 생성합니다.</div>", unsafe_allow_html=True)
        card_end()
    with c3:
        card_start("GEMINI", "사진 구도 앱")
        st.markdown("<div class='body-text'>같은 흐름을 Gemini Vision과 Gemini Image Generation으로 구현하여 모델별 결과를 비교할 수 있습니다.</div>", unsafe_allow_html=True)
        card_end()

elif page == "1. 손금 분석":
    hero("OPENAI VISION", "Palm Reading Report", "왼손과 오른손 사진을 업로드하면 손금 기반의 상징적 성향 리포트를 생성합니다. 과학적 진단이나 확정적 예언이 아닌 자기이해용 콘텐츠입니다.")
    left, right = st.columns([0.9, 1.1], gap="large")
    with left:
        card_start("INPUT", "손 사진 업로드")
        report_name = st.text_input("리포트 이름", value="나의 손금 리포트")
        dominant = st.radio("주로 사용하는 손", ["오른손", "왼손"], horizontal=True)
        tone = st.selectbox("문체", ["차분하고 고급스러운 에디토리얼", "따뜻하고 다정한 상담가", "간결하고 전문적인 분석가", "신비롭지만 과장 없는 매거진"])
        left_file = st.file_uploader("왼손 사진", type=["jpg", "jpeg", "png", "webp"], key="palm_left")
        right_file = st.file_uploader("오른손 사진", type=["jpg", "jpeg", "png", "webp"], key="palm_right")
        run = st.button("손금 리포트 생성")
        if st.button("손금 결과 초기화"):
            clear_keys(["palm_report", "palm_left_img", "palm_right_img"]); st.rerun()
        card_end()
        if left_file and right_file:
            pc1, pc2 = st.columns(2)
            pc1.image(left_file, caption="왼손", use_container_width=True)
            pc2.image(right_file, caption="오른손", use_container_width=True)
    with right:
        card_start("REPORT", "분석 결과")
        if run:
            if not left_file or not right_file:
                st.warning("왼손과 오른손 사진을 모두 업로드해주세요.")
            else:
                left_img = Image.open(left_file).convert("RGB")
                right_img = Image.open(right_file).convert("RGB")
                with st.spinner("OpenAI Vision이 손금을 분석하고 있습니다..."):
                    try:
                        report = openai_vision_text([left_img, right_img], palm_prompt(dominant, report_name, tone))
                        st.session_state["palm_report"] = report
                        st.session_state["palm_left_img"] = left_img
                        st.session_state["palm_right_img"] = right_img
                    except Exception as e:
                        st.error(f"오류: {e}")
        if "palm_report" in st.session_state:
            st.markdown(f"<div class='body-text'>{st.session_state['palm_report']}</div>", unsafe_allow_html=True)
            pdf = make_text_pdf(report_name, st.session_state["palm_report"], [("Left Hand", st.session_state["palm_left_img"]), ("Right Hand", st.session_state["palm_right_img"])])
            st.download_button("손금 PDF 다운로드", data=pdf, file_name="palm_reading_report.pdf", mime="application/pdf")
            st.download_button("손금 TXT 다운로드", data=st.session_state["palm_report"].encode("utf-8"), file_name="palm_reading_report.txt", mime="text/plain")
        else:
            st.markdown("<div class='body-text'>아직 생성된 손금 리포트가 없습니다.</div>", unsafe_allow_html=True)
        card_end()

elif page == "2. OpenAI 사진 앱":
    hero("OPENAI VISION + IMAGE API", "OpenAI Photo Director", "사진 속 구도와 여백, 시선 흐름을 분석하고 추천 위치 마커와 AI 예시 이미지를 생성합니다.")
    left, right = st.columns([0.9, 1.1], gap="large")
    with left:
        card_start("INPUT", "사진과 설정")
        mode, subject, style, use, extra, uploaded = photo_settings("openai")
        gen_image = st.checkbox("예시 이미지까지 생성", value=False, key="openai_gen_check")
        run = st.button("OpenAI 구도 분석 실행")
        if st.button("OpenAI 결과 초기화"):
            clear_keys(["openai_data", "openai_original", "openai_overlay", "openai_generated", "openai_subject", "openai_style", "openai_extra"]); st.rerun()
        card_end()
        if uploaded:
            st.image(uploaded, caption="원본", use_container_width=True)
    with right:
        card_start("RESULT", "분석 결과")
        if run:
            if not uploaded:
                st.warning("사진을 업로드해주세요.")
            else:
                img = Image.open(uploaded).convert("RGB")
                with st.spinner("OpenAI Vision이 사진을 분석하고 있습니다..."):
                    try:
                        data = openai_analyze_photo(img, photo_analysis_prompt(mode, subject, style, use, extra))
                        overlay = draw_overlay(img, data, "OPENAI DIRECTION MAP")
                        st.session_state["openai_data"] = data
                        st.session_state["openai_original"] = img
                        st.session_state["openai_overlay"] = overlay
                        st.session_state["openai_subject"] = subject
                        st.session_state["openai_style"] = style
                        st.session_state["openai_extra"] = extra
                    except Exception as e:
                        st.error(f"분석 오류: {e}")
                if gen_image and "openai_data" in st.session_state:
                    with st.spinner("OpenAI 이미지 API가 예시 이미지를 생성하고 있습니다..."):
                        try:
                            prompt = image_prompt_from_analysis(st.session_state["openai_data"], subject, style, extra)
                            st.session_state["openai_generated"] = openai_generate_image(img, prompt)
                        except Exception as e:
                            st.warning(f"이미지 생성 실패: {e}")
        if "openai_data" in st.session_state:
            data = st.session_state["openai_data"]
            show_photo_analysis(data)
            st.image(st.session_state["openai_overlay"], caption="추천 위치 마커", use_container_width=True)
            st.download_button("OpenAI 위치 마커 PNG", image_buffer(st.session_state["openai_overlay"]), "openai_direction_map.png", "image/png")
            if "openai_generated" in st.session_state:
                st.image(st.session_state["openai_generated"], caption="OpenAI 생성 예시", use_container_width=True)
                st.download_button("OpenAI 예시 PNG", image_buffer(st.session_state["openai_generated"]), "openai_generated_example.png", "image/png")
            pdf = make_text_pdf("OpenAI Photo Director", photo_report_text(data, "OpenAI"), [("OpenAI Direction Map", st.session_state["openai_overlay"])] + ([ ("OpenAI Generated Example", st.session_state["openai_generated"]) ] if "openai_generated" in st.session_state else []))
            st.download_button("OpenAI PDF 리포트", pdf, "openai_photo_report.pdf", "application/pdf")
            with st.expander("분석 JSON"):
                st.json(data)
        else:
            st.markdown("<div class='body-text'>아직 OpenAI 분석 결과가 없습니다.</div>", unsafe_allow_html=True)
        card_end()

elif page == "3. Gemini 사진 앱":
    hero("GEMINI VISION + IMAGE GENERATION", "Gemini Photo Director", "같은 사진 구도 분석 흐름을 Gemini API로 실행합니다. OpenAI 결과와 비교하기 좋습니다.")
    left, right = st.columns([0.9, 1.1], gap="large")
    with left:
        card_start("INPUT", "사진과 설정")
        mode, subject, style, use, extra, uploaded = photo_settings("gemini")
        gen_image = st.checkbox("예시 이미지까지 생성", value=False, key="gemini_gen_check")
        run = st.button("Gemini 구도 분석 실행")
        if st.button("Gemini 결과 초기화"):
            clear_keys(["gemini_data", "gemini_original", "gemini_overlay", "gemini_generated", "gemini_subject", "gemini_style", "gemini_extra"]); st.rerun()
        card_end()
        if uploaded:
            st.image(uploaded, caption="원본", use_container_width=True)
    with right:
        card_start("RESULT", "분석 결과")
        if run:
            if not uploaded:
                st.warning("사진을 업로드해주세요.")
            else:
                img = Image.open(uploaded).convert("RGB")
                with st.spinner("Gemini가 사진을 분석하고 있습니다..."):
                    try:
                        data = gemini_analyze_photo(img, photo_analysis_prompt(mode, subject, style, use, extra))
                        overlay = draw_overlay(img, data, "GEMINI DIRECTION MAP")
                        st.session_state["gemini_data"] = data
                        st.session_state["gemini_original"] = img
                        st.session_state["gemini_overlay"] = overlay
                        st.session_state["gemini_subject"] = subject
                        st.session_state["gemini_style"] = style
                        st.session_state["gemini_extra"] = extra
                    except Exception as e:
                        st.error(f"분석 오류: {e}")
                if gen_image and "gemini_data" in st.session_state:
                    with st.spinner("Gemini가 예시 이미지를 생성하고 있습니다..."):
                        try:
                            prompt = image_prompt_from_analysis(st.session_state["gemini_data"], subject, style, extra)
                            st.session_state["gemini_generated"] = gemini_generate_image(img, prompt)
                        except Exception as e:
                            st.warning(f"이미지 생성 실패: {e}")
        if "gemini_data" in st.session_state:
            data = st.session_state["gemini_data"]
            show_photo_analysis(data)
            st.image(st.session_state["gemini_overlay"], caption="추천 위치 마커", use_container_width=True)
            st.download_button("Gemini 위치 마커 PNG", image_buffer(st.session_state["gemini_overlay"]), "gemini_direction_map.png", "image/png")
            if "gemini_generated" in st.session_state:
                st.image(st.session_state["gemini_generated"], caption="Gemini 생성 예시", use_container_width=True)
                st.download_button("Gemini 예시 PNG", image_buffer(st.session_state["gemini_generated"]), "gemini_generated_example.png", "image/png")
            pdf = make_text_pdf("Gemini Photo Director", photo_report_text(data, "Gemini"), [("Gemini Direction Map", st.session_state["gemini_overlay"])] + ([ ("Gemini Generated Example", st.session_state["gemini_generated"]) ] if "gemini_generated" in st.session_state else []))
            st.download_button("Gemini PDF 리포트", pdf, "gemini_photo_report.pdf", "application/pdf")
            with st.expander("분석 JSON"):
                st.json(data)
        else:
            st.markdown("<div class='body-text'>아직 Gemini 분석 결과가 없습니다.</div>", unsafe_allow_html=True)
        card_end()

elif page == "4. 비교·다운로드":
    hero("COMPARE", "OpenAI vs Gemini", "두 모델의 구도 분석 결과를 나란히 비교하고, 생성된 모든 결과물을 다운로드합니다.")
    has_o = "openai_data" in st.session_state
    has_g = "gemini_data" in st.session_state
    if not has_o and not has_g:
        st.warning("먼저 OpenAI 사진 앱 또는 Gemini 사진 앱에서 분석을 실행해주세요.")
    else:
        cols = st.columns(2)
        if has_o:
            with cols[0]:
                card_start("OPENAI", "OpenAI 결과")
                st.image(st.session_state["openai_overlay"], use_container_width=True)
                show_photo_analysis(st.session_state["openai_data"])
                card_end()
        if has_g:
            with cols[1]:
                card_start("GEMINI", "Gemini 결과")
                st.image(st.session_state["gemini_overlay"], use_container_width=True)
                show_photo_analysis(st.session_state["gemini_data"])
                card_end()
        body = ""
        images = []
        if has_o:
            body += photo_report_text(st.session_state["openai_data"], "OpenAI") + "\n\n"
            images.append(("OpenAI Direction Map", st.session_state["openai_overlay"]))
            if "openai_generated" in st.session_state: images.append(("OpenAI Generated Example", st.session_state["openai_generated"]))
        if has_g:
            body += photo_report_text(st.session_state["gemini_data"], "Gemini") + "\n\n"
            images.append(("Gemini Direction Map", st.session_state["gemini_overlay"]))
            if "gemini_generated" in st.session_state: images.append(("Gemini Generated Example", st.session_state["gemini_generated"]))
        st.download_button("통합 비교 PDF 다운로드", make_text_pdf("OpenAI vs Gemini Report", body, images), "ai_vision_comparison_report.pdf", "application/pdf")

elif page == "5. 사용 가이드":
    hero("GUIDE", "Streamlit Cloud 배포 가이드", "GitHub에 app.py와 requirements.txt를 올리고, Streamlit Cloud Secrets에 API 키를 넣으면 바로 실행할 수 있습니다.")
    card_start("FILES", "필요 파일")
    st.code("""ai-vision-studio/
├── app.py
└── requirements.txt""", language="text")
    card_end()
    card_start("SECRETS", "Streamlit Secrets")
    st.code("""OPENAI_API_KEY = "sk-..."
OPENAI_VISION_MODEL = "gpt-4.1-mini"
OPENAI_IMAGE_MODEL = "gpt-image-1"

GEMINI_API_KEY = "..."
GEMINI_VISION_MODEL = "gemini-2.5-flash"
GEMINI_IMAGE_MODEL = "gemini-2.5-flash-image""", language="toml")
    st.markdown("<div class='body-text'>이미지 생성 모델은 계정 권한이나 지역, 모델 공개 상태에 따라 실패할 수 있습니다. 이 경우에도 Vision 분석과 위치 마커, PDF 다운로드는 작동합니다.</div>", unsafe_allow_html=True)
    card_end()
