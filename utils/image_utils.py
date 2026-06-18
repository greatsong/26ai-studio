from io import BytesIO
import base64
from PIL import Image, ImageDraw, ImageFont


def resize_for_api(image: Image.Image, max_side: int = 1600) -> Image.Image:
    img = image.convert("RGB")
    w, h = img.size
    if max(w, h) <= max_side:
        return img
    ratio = max_side / max(w, h)
    return img.resize((int(w * ratio), int(h * ratio)))


def pil_to_base64_jpeg(image: Image.Image) -> str:
    buf = BytesIO()
    image.convert("RGB").save(buf, format="JPEG", quality=92)
    return base64.b64encode(buf.getvalue()).decode("utf-8")


def pil_to_png_bytes(image: Image.Image) -> bytes:
    buf = BytesIO()
    image.convert("RGB").save(buf, format="PNG")
    return buf.getvalue()


def pil_to_png_file(image: Image.Image, name="image.png") -> BytesIO:
    buf = BytesIO()
    image.convert("RGB").save(buf, format="PNG")
    buf.seek(0)
    buf.name = name
    return buf


def image_to_buffer(image: Image.Image, fmt="PNG") -> BytesIO:
    buf = BytesIO()
    image.save(buf, format=fmt)
    buf.seek(0)
    return buf


def get_font(size: int, bold: bool = False):
    candidates = [
        "/usr/share/fonts/truetype/dejavu/DejaVuSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf",
        "/usr/share/fonts/truetype/liberation/LiberationSans-Bold.ttf" if bold else "/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf",
    ]
    for path in candidates:
        try:
            return ImageFont.truetype(path, size)
        except Exception:
            pass
    return ImageFont.load_default()


def _clamp(v, lo, hi):
    return max(lo, min(hi, v))


def normalize_crop_box(box, width, height):
    left, top, right, bottom = box
    left = _clamp(int(left), 0, width - 2)
    top = _clamp(int(top), 0, height - 2)
    right = _clamp(int(right), left + 1, width)
    bottom = _clamp(int(bottom), top + 1, height)
    return (left, top, right, bottom)


def get_crop_box_from_analysis(image: Image.Image, data: dict):
    w, h = image.size
    crop = data.get("recommended_crop") or {}
    if crop:
        try:
            left = w * float(crop.get("left_percent", 0)) / 100.0
            top = h * float(crop.get("top_percent", 0)) / 100.0
            right = w * float(crop.get("right_percent", 100)) / 100.0
            bottom = h * float(crop.get("bottom_percent", 100)) / 100.0
            return normalize_crop_box((left, top, right, bottom), w, h)
        except Exception:
            pass

    best = (data.get("best_positions") or [{}])[0]
    cx = w * float(best.get("x_percent", 50)) / 100.0
    cy = h * float(best.get("y_percent", 62)) / 100.0
    crop_w = int(w * 0.72)
    crop_h = int(h * 0.82)
    left = cx - crop_w / 2
    top = cy - crop_h * 0.45
    right = left + crop_w
    bottom = top + crop_h
    return normalize_crop_box((left, top, right, bottom), w, h)


def crop_image_by_analysis(image: Image.Image, data: dict):
    box = get_crop_box_from_analysis(image, data)
    return image.crop(box), box


def adjust_analysis_for_crop(data: dict, crop_box, original_size):
    left, top, right, bottom = crop_box
    crop_w = max(1, right - left)
    crop_h = max(1, bottom - top)
    new_data = dict(data)
    new_positions = []
    for pos in data.get("best_positions", []):
        try:
            ox = original_size[0] * float(pos.get("x_percent", 50)) / 100.0
            oy = original_size[1] * float(pos.get("y_percent", 62)) / 100.0
            nx = (ox - left) / crop_w * 100.0
            ny = (oy - top) / crop_h * 100.0
            cloned = dict(pos)
            cloned["x_percent"] = round(_clamp(nx, 3, 97), 1)
            cloned["y_percent"] = round(_clamp(ny, 3, 97), 1)
            new_positions.append(cloned)
        except Exception:
            new_positions.append(dict(pos))
    new_data["best_positions"] = new_positions
    new_data["crop_context"] = {
        "left": left, "top": top, "right": right, "bottom": bottom,
        "width": crop_w, "height": crop_h
    }
    return new_data


def draw_position_overlay(image: Image.Image, data: dict, title="AI PHOTO DIRECTION MAP") -> Image.Image:
    img = image.convert("RGB").copy()
    draw = ImageDraw.Draw(img, "RGBA")
    w, h = img.size

    # recommended crop box
    try:
        left, top, right, bottom = get_crop_box_from_analysis(img, data)
        draw.rounded_rectangle([left, top, right, bottom], radius=18, outline=(184,155,94,235), width=max(3, int(min(w,h) * 0.005)))
        crop_label_font = get_font(max(14, int(w * 0.016)), True)
        crop_label = "BEST CROP"
        lb = draw.textbbox((0,0), crop_label, font=crop_label_font)
        lw, lh = lb[2]-lb[0], lb[3]-lb[1]
        bx, by = left + 8, max(10, top - lh - 18)
        draw.rounded_rectangle([bx, by, bx + lw + 20, by + lh + 10], radius=12, fill=(184,155,94,235), outline=(255,255,255,220), width=1)
        draw.text((bx + 10, by + 5), crop_label, font=crop_label_font, fill=(255,255,255,255))
    except Exception:
        pass

    font_title = get_font(max(20, int(w * 0.025)), True)
    font_big = get_font(max(24, int(w * 0.034)), True)
    font_small = get_font(max(15, int(w * 0.018)), True)

    positions = data.get("best_positions", [])
    colors = [(184,155,94,238), (34,34,34,230), (116,96,66,225)]

    for idx, pos in enumerate(positions[:3]):
        try:
            x = int(w * float(pos.get("x_percent", 50)) / 100)
            y = int(h * float(pos.get("y_percent", 62)) / 100)
        except Exception:
            x, y = int(w * .5), int(h * .62)
        rank = str(pos.get("rank", idx + 1))
        radius = max(18, int(min(w, h) * .035))
        color = colors[idx % len(colors)]
        draw.ellipse([x-radius, y-radius, x+radius, y+radius], fill=color, outline=(255,255,255,255), width=max(3, int(radius*.15)))
        bbox = draw.textbbox((0,0), rank, font=font_big)
        tw, th = bbox[2]-bbox[0], bbox[3]-bbox[1]
        draw.text((x-tw/2, y-th/2-2), rank, font=font_big, fill=(255,255,255,255))

        label = f"{rank}. {pos.get('short_label', '추천 위치')}"
        lb = draw.textbbox((0,0), label, font=font_small)
        lw, lh = lb[2]-lb[0], lb[3]-lb[1]
        pad = 10
        label_x = min(max(x + radius + 10, 12), w - lw - pad * 2 - 12)
        label_y = min(max(y - lh/2 - pad, 12), h - lh - pad * 2 - 12)
        draw.rounded_rectangle([label_x,label_y,label_x+lw+pad*2,label_y+lh+pad*2], radius=14, fill=(255,255,255,232), outline=(216,210,200,238), width=2)
        draw.text((label_x+pad,label_y+pad), label, font=font_small, fill=(34,34,34,255))

    tb = draw.textbbox((0,0), title, font=font_title)
    tw, th = tb[2]-tb[0], tb[3]-tb[1]
    draw.rounded_rectangle([18,18,18+tw+30,18+th+22], radius=16, fill=(248,245,239,235), outline=(216,210,200,235), width=2)
    draw.text((33,29), title, font=font_title, fill=(34,34,34,255))
    return img
