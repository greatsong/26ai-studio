from io import BytesIO
from datetime import datetime
import textwrap
from PIL import Image
from reportlab.lib.pagesizes import A4
from reportlab.pdfgen import canvas
from reportlab.lib.colors import HexColor
from reportlab.lib.utils import ImageReader
from reportlab.pdfbase import pdfmetrics
from reportlab.pdfbase.cidfonts import UnicodeCIDFont

BRAND = "DangGok AI Vision Studio"


def register_korean_fonts():
    """ReportLab 내장 CID 한글 폰트 사용. Streamlit Cloud에서도 별도 폰트 파일 없이 한글 깨짐을 피한다."""
    try:
        pdfmetrics.registerFont(UnicodeCIDFont("HYGoThic-Medium"))
        pdfmetrics.registerFont(UnicodeCIDFont("HYSMyeongJo-Medium"))
        return "HYGoThic-Medium", "HYGoThic-Medium"
    except Exception:
        return "Helvetica", "Helvetica-Bold"


def _draw_header(c, width, height, title, subtitle=""):
    font, font_bold = register_korean_fonts()
    margin = 34
    c.setFillColor(HexColor("#F8F5EF"))
    c.rect(0, 0, width, height, stroke=0, fill=1)
    c.setFillColor(HexColor("#FFFFFF"))
    c.roundRect(margin, height - 132, width - margin * 2, 98, 20, stroke=0, fill=1)
    c.setStrokeColor(HexColor("#DDD5C9"))
    c.roundRect(margin, height - 132, width - margin * 2, 98, 20, stroke=1, fill=0)
    c.setFillColor(HexColor("#B89B5E"))
    c.setFont(font_bold, 10)
    c.drawString(margin + 24, height - 66, BRAND.upper())
    c.setFillColor(HexColor("#222222"))
    c.setFont(font_bold, 23)
    c.drawString(margin + 24, height - 96, title[:38])
    c.setFillColor(HexColor("#6F6A62"))
    c.setFont(font, 8.5)
    if subtitle:
        c.drawString(margin + 24, height - 115, subtitle[:72])
    else:
        c.drawString(margin + 24, height - 115, datetime.now().strftime("%Y-%m-%d %H:%M"))
    return height - 158


def _new_page(c, width, height):
    c.showPage()
    c.setFillColor(HexColor("#F8F5EF"))
    c.rect(0, 0, width, height, stroke=0, fill=1)
    return height - 46


def _draw_wrapped_text(c, text, x, y, width, height, font, font_bold, size=10.5):
    lines = []
    for para in str(text).split("\n"):
        if not para.strip():
            lines.append("")
        else:
            # Korean-aware rough wrapping by character count
            max_chars = max(24, int(width / (size * 0.55)))
            lines.extend(textwrap.wrap(para, width=max_chars, break_long_words=True, replace_whitespace=False))
    c.setFont(font, size)
    c.setFillColor(HexColor("#34302B"))
    for line in lines:
        if y < 44:
            y = _new_page(c, A4[0], A4[1])
            c.setFont(font, size)
            c.setFillColor(HexColor("#34302B"))
        if not line:
            y -= size * .85
        elif line.strip().endswith(":") or line.startswith("#") or (len(line) < 24 and any(k in line for k in ["분석", "리딩", "추천", "비교", "생명선", "두뇌선", "감정선", "운명선", "태양선", "LIFE", "MIND", "HEART", "WORK", "TALENT"])):
            c.setFont(font_bold, size + 2)
            c.setFillColor(HexColor("#222222"))
            c.drawString(x, y, line.replace("#", "").strip())
            y -= size + 7
            c.setFont(font, size)
            c.setFillColor(HexColor("#34302B"))
        else:
            c.drawString(x, y, line)
            y -= size + 4
    return y


def _draw_image(c, img: Image.Image, title: str, y: float, width, height):
    font, font_bold = register_korean_fonts()
    margin = 34
    if y < 250:
        y = _new_page(c, width, height)
    c.setFillColor(HexColor("#222222"))
    c.setFont(font_bold, 12)
    c.drawString(margin, y, title)
    y -= 12
    temp = BytesIO()
    thumb = img.convert("RGB").copy()
    thumb.thumbnail((900, 560))
    thumb.save(temp, format="PNG")
    temp.seek(0)
    reader = ImageReader(temp)
    iw, ih = thumb.size
    max_w = width - margin * 2
    max_h = 220
    ratio = min(max_w / iw, max_h / ih)
    dw, dh = iw * ratio, ih * ratio
    x = (width - dw) / 2
    c.setFillColor(HexColor("#FFFFFF"))
    c.roundRect(x - 8, y - dh - 8, dw + 16, dh + 16, 14, stroke=0, fill=1)
    c.drawImage(reader, x, y - dh, width=dw, height=dh, mask="auto")
    return y - dh - 30


def palm_pdf(report_text: str, title="손금 분석 리포트") -> BytesIO:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    font, font_bold = register_korean_fonts()
    y = _draw_header(c, width, height, title, "사진 기반 상징적 손금 리포트")
    margin = 34
    c.setFillColor(HexColor("#FFFFFF"))
    c.roundRect(margin, 34, width - margin * 2, y - 34, 18, stroke=0, fill=1)
    c.setStrokeColor(HexColor("#DDD5C9"))
    c.roundRect(margin, 34, width - margin * 2, y - 34, 18, stroke=1, fill=0)
    y -= 24
    y = _draw_wrapped_text(c, report_text, margin + 22, y, width - (margin + 22) * 2, height, font, font_bold, 10.2)
    c.save()
    buffer.seek(0)
    return buffer


def photo_report_text(data: dict) -> str:
    lines = ["사진 구도 분석 리포트", ""]
    lines.append(f"장면 요약: {data.get('scene_summary','')}")
    lines.append(f"구도 유형: {data.get('composition_type','')}")
    lines.append(f"시선 흐름: {data.get('visual_flow','')}")
    lines.append(f"빛 방향: {data.get('light_direction','')}")
    lines.append(f"배경 메모: {data.get('background_notes','')}")
    crop = data.get('recommended_crop', {})
    if crop:
        lines.append("추천 크롭")
        lines.append(f"영역: 왼쪽 {crop.get('left_percent')}%, 위 {crop.get('top_percent')}%, 오른쪽 {crop.get('right_percent')}%, 아래 {crop.get('bottom_percent')}%")
        lines.append(f"이유: {crop.get('reason','')}")
        lines.append('')
    lines.append("추천 위치 TOP 3")
    for p in data.get("best_positions", []):
        lines.append(f"\n{p.get('rank','-')}. {p.get('short_label','추천 위치')}")
        lines.append(f"좌표: x {p.get('x_percent')}%, y {p.get('y_percent')}%")
        lines.append(f"포즈: {p.get('pose','')}")
        lines.append(f"카메라 팁: {p.get('camera_tip','')}")
        lines.append(f"이유: {p.get('reason','')}")
    lines.append("\n피해야 할 위치")
    for p in data.get("avoid_positions", []):
        lines.append(f"- x {p.get('x_percent')}%, y {p.get('y_percent')}%: {p.get('reason','')}")
    lines.append("\n촬영 팁")
    for tip in data.get("shooting_tips", []):
        lines.append(f"- {tip}")
    lines.append(f"\n한 줄 디렉팅: {data.get('one_line_direction','')}")
    return "\n".join(lines)


def photo_pdf(data: dict, overlay: Image.Image, generated: Image.Image | None, title="사진 구도 리포트", crop_preview: Image.Image | None = None) -> BytesIO:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    font, font_bold = register_korean_fonts()
    y = _draw_header(c, width, height, title, "구도 분석 · 위치 마커 · 생성 예시")
    y = _draw_image(c, overlay, "추천 위치 지도", y, width, height)
    if crop_preview is not None:
        y = _draw_image(c, crop_preview, "AI 추천 최적 크롭", y, width, height)
    if generated is not None:
        y = _draw_image(c, generated, "AI 생성 예시 이미지", y, width, height)
    if y < 180:
        y = _new_page(c, width, height)
    margin = 34
    c.setFillColor(HexColor("#FFFFFF"))
    c.roundRect(margin, 34, width - margin * 2, max(40, y - 34), 18, stroke=0, fill=1)
    c.setStrokeColor(HexColor("#DDD5C9"))
    c.roundRect(margin, 34, width - margin * 2, max(40, y - 34), 18, stroke=1, fill=0)
    y -= 22
    _draw_wrapped_text(c, photo_report_text(data), margin + 20, y, width - (margin + 20) * 2, height, font, font_bold, 9.8)
    c.save()
    buffer.seek(0)
    return buffer


def comparison_pdf(openai_data: dict | None, gemini_data: dict | None, openai_overlay=None, gemini_overlay=None) -> BytesIO:
    buffer = BytesIO()
    c = canvas.Canvas(buffer, pagesize=A4)
    width, height = A4
    font, font_bold = register_korean_fonts()
    y = _draw_header(c, width, height, "OpenAI · Gemini 비교 리포트", "같은 사진에 대한 모델별 구도 해석 비교")
    if openai_overlay is not None:
        y = _draw_image(c, openai_overlay, "OpenAI 추천 위치 지도", y, width, height)
    if gemini_overlay is not None:
        y = _draw_image(c, gemini_overlay, "Gemini 추천 위치 지도", y, width, height)
    text = ""
    if openai_data:
        text += "OpenAI 분석 요약\n" + photo_report_text(openai_data) + "\n\n"
    if gemini_data:
        text += "Gemini 분석 요약\n" + photo_report_text(gemini_data)
    if not text:
        text = "아직 비교할 분석 결과가 없습니다."
    if y < 160:
        y = _new_page(c, width, height)
    _draw_wrapped_text(c, text, 40, y, width - 80, height, font, font_bold, 9.4)
    c.save()
    buffer.seek(0)
    return buffer
