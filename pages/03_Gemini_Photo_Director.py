import streamlit as st
from PIL import Image
from utils.ui import inject_css, hero, card_start, card_end, sidebar_info
from utils.prompts import photo_analysis_prompt, image_edit_prompt
from utils.gemini_tools import analyze_image, generate_edited_image
from utils.image_utils import draw_position_overlay, image_to_buffer, crop_image_by_analysis, adjust_analysis_for_crop
from utils.report_utils import photo_pdf

st.set_page_config(page_title="Gemini 사진 앱 | DangGok AI Vision Studio", page_icon="🍌", layout="wide")
inject_css(); sidebar_info()

hero("GEMINI VISION + IMAGE GENERATION", "Gemini 사진 구도 분석", "Gemini API로 같은 사진 구도 분석을 실행합니다. 필요하면 전체 사진 대신 일부만 잘라 더 좋은 구도를 먼저 만든 뒤, 그 안에 모델이 실제로 있었던 것처럼 예시 이미지를 만듭니다.")

if "GEMINI_API_KEY" not in st.secrets:
    st.error("Streamlit Secrets에 GEMINI_API_KEY가 없습니다."); st.stop()

left, right = st.columns([0.9, 1.1], gap="large")
with left:
    card_start("INPUT", "사진과 생성 조건")
    mode = st.selectbox("분석 모드", ["인물 위치 잡아주기", "여행 사진 포즈 추천", "제품/소품 배치 추천", "교실/행사 사진 구도 추천", "썸네일·홍보 이미지 구도 추천"], key="gemini_mode_widget")
    subject = st.text_input("배치할 대상", value="a natural person", key="gemini_subject_widget", help="이전 오류 방지: 이 key는 절대 코드에서 직접 수정하지 않습니다.")
    style = st.selectbox("원하는 분위기", ["natural realistic editorial photography", "warm cinematic family photo", "clean minimal premium look", "bright school activity photo", "travel magazine style", "soft emotional portrait style"], key="gemini_style_widget")
    output_use = st.selectbox("결과물 용도", ["SNS 사진", "학교 홍보물", "여행 사진", "PPT 표지", "카드뉴스", "제품/소품 촬영", "개인 기록"], key="gemini_output_widget")
    extra = st.text_area("추가 요청", placeholder="예: 모델은 자연스럽게 웃고, 원본 배경과 조명은 최대한 유지해주세요.", height=100, key="gemini_extra_widget")
    vision_model = st.text_input("Gemini Vision 모델", value=st.secrets.get("GEMINI_VISION_MODEL", "gemini-2.5-flash"), key="gemini_vision_model_widget")
    image_model = st.text_input("Gemini Image 모델", value=st.secrets.get("GEMINI_IMAGE_MODEL", "gemini-2.5-flash-image"), key="gemini_image_model_widget")
    uploaded = st.file_uploader("분석할 사진 업로드", type=["jpg","jpeg","png","webp"], key="gemini_photo_widget")
    crop_first = st.checkbox("최적 구도로 크롭해서 예시 만들기", value=True, key="gemini_crop_widget")
    gen_example = st.checkbox("분석 후 예시 이미지도 생성", value=True, key="gemini_gen_widget")
    run = st.button("Gemini 구도 분석 실행", key="gemini_run_button")
    st.markdown('<p class="small-note">전체 사진을 꼭 다 쓰지 않아도 됩니다. Gemini가 추천한 크롭 구도를 먼저 적용해, 더 집중도 높은 예시 이미지를 만들 수 있습니다.</p>', unsafe_allow_html=True)
    card_end()
    if uploaded:
        st.image(uploaded, caption="원본 사진", use_container_width=True)

with right:
    card_start("RESULT", "Gemini 분석 결과")
    if run:
        if not uploaded:
            st.warning("먼저 사진을 업로드해주세요.")
        else:
            image = Image.open(uploaded).convert("RGB")
            prompt = photo_analysis_prompt(mode, subject, style, output_use, extra)
            try:
                with st.spinner("Gemini가 사진 구도를 분석하고 있습니다..."):
                    data = analyze_image(st.secrets["GEMINI_API_KEY"], vision_model, image, prompt)
                    overlay = draw_position_overlay(image, data, "GEMINI PHOTO DIRECTION MAP")
                    crop_preview, crop_box = crop_image_by_analysis(image, data)
                    crop_adjusted = adjust_analysis_for_crop(data, crop_box, image.size)
                    st.session_state["gemini_photo_analysis"] = data
                    st.session_state["gemini_original_image"] = image
                    st.session_state["gemini_overlay_image"] = overlay
                    st.session_state["gemini_crop_image"] = crop_preview
                    st.session_state["gemini_crop_adjusted_analysis"] = crop_adjusted
                    st.session_state["gemini_subject_value"] = subject
                    st.session_state["gemini_style_value"] = style
                    st.session_state["gemini_extra_value"] = extra
                    st.session_state["gemini_image_model_value"] = image_model
                    st.session_state["gemini_generated_image"] = None
                if gen_example:
                    with st.spinner("Gemini Image API가 최적 구도 장면 안에 모델이 실제로 있었던 것 같은 예시 이미지를 생성하고 있습니다..."):
                        base_for_gen = crop_preview if crop_first else image
                        prompt_data = crop_adjusted if crop_first else data
                        prompt2 = image_edit_prompt(prompt_data, subject, style, extra)
                        generated = generate_edited_image(st.secrets["GEMINI_API_KEY"], image_model, base_for_gen, prompt2)
                        st.session_state["gemini_generated_image"] = generated
                        st.session_state["gemini_used_crop_for_generation"] = crop_first
            except Exception as e:
                st.error(f"분석 오류: {e}")

    if "gemini_photo_analysis" not in st.session_state:
        st.markdown('<div class="body-text">아직 분석 결과가 없습니다. 왼쪽에서 사진을 업로드하고 실행해주세요.</div>', unsafe_allow_html=True)
    else:
        data = st.session_state["gemini_photo_analysis"]
        crop = data.get("recommended_crop", {})
        crop_text = f"왼쪽 {crop.get('left_percent','?')}% · 위 {crop.get('top_percent','?')}% · 오른쪽 {crop.get('right_percent','?')}% · 아래 {crop.get('bottom_percent','?')}%" if crop else "-"
        st.markdown(f'<div class="body-text"><b>장면 요약</b><br>{data.get("scene_summary","")}<br><br><b>구도 유형</b><br>{data.get("composition_type","")}<br><br><b>시선 흐름</b><br>{data.get("visual_flow","")}<br><br><b>빛 방향</b><br>{data.get("light_direction","")}<br><br><b>추천 크롭</b><br>{crop_text}<br>{crop.get("reason","")}</div>', unsafe_allow_html=True)
        st.divider()
        for pos in data.get("best_positions", []):
            st.markdown(f'<div class="pos-card"><div class="pos-rank">POSITION {pos.get("rank","-")}</div><div class="pos-title">{pos.get("short_label","추천 위치")}</div><div class="body-text"><b>좌표</b>: x {pos.get("x_percent")}% · y {pos.get("y_percent")}%<br><b>포즈</b>: {pos.get("pose","")}<br><b>카메라 팁</b>: {pos.get("camera_tip","")}<br><b>이유</b>: {pos.get("reason","")}</div></div>', unsafe_allow_html=True)
        st.markdown(f'<div class="body-text"><b>한 줄 디렉팅</b><br>{data.get("one_line_direction","")}</div>', unsafe_allow_html=True)
    card_end()

if "gemini_overlay_image" in st.session_state:
    card_start("VISUAL OUTPUT", "추천 위치 지도 · 최적 크롭 · 생성 예시")
    c1, c2, c3 = st.columns(3, gap="large")
    with c1:
        st.image(st.session_state["gemini_overlay_image"], caption="원본 위 추천 위치 지도", use_container_width=True)
        st.download_button("추천 위치 PNG 다운로드", data=image_to_buffer(st.session_state["gemini_overlay_image"]), file_name="gemini_direction_map.png", mime="image/png")
    with c2:
        crop_img = st.session_state.get("gemini_crop_image")
        if crop_img is not None:
            st.image(crop_img, caption="AI 추천 최적 크롭", use_container_width=True)
            st.download_button("크롭 예시 PNG 다운로드", data=image_to_buffer(crop_img), file_name="gemini_best_crop.png", mime="image/png")
    with c3:
        gen = st.session_state.get("gemini_generated_image")
        if gen is not None:
            caption = "Gemini 생성 예시 이미지"
            if st.session_state.get("gemini_used_crop_for_generation"):
                caption += " (크롭 구도 사용)"
            st.image(gen, caption=caption, use_container_width=True)
            st.download_button("생성 예시 PNG 다운로드", data=image_to_buffer(gen), file_name="gemini_generated_example.png", mime="image/png")
        else:
            st.info("예시 이미지가 아직 없습니다. 체크박스를 켜고 다시 실행하거나 모델 권한을 확인하세요.")
    pdf = photo_pdf(st.session_state["gemini_photo_analysis"], st.session_state["gemini_overlay_image"], st.session_state.get("gemini_generated_image"), "Gemini 사진 구도 리포트", crop_preview=st.session_state.get("gemini_crop_image"))
    st.download_button("Gemini PDF 리포트 다운로드", data=pdf, file_name="gemini_photo_report.pdf", mime="application/pdf")
    with st.expander("분석 JSON 보기"):
        st.json(st.session_state["gemini_photo_analysis"])
    card_end()
