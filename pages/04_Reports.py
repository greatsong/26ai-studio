import streamlit as st
from utils.ui import inject_css, hero, card_start, card_end, sidebar_info
from utils.image_utils import image_to_buffer
from utils.report_utils import palm_pdf, photo_pdf, comparison_pdf

st.set_page_config(page_title="리포트 다운로드 | DangGok AI Vision Studio", page_icon="📄", layout="wide")
inject_css(); sidebar_info()

hero("DOWNLOAD CENTER", "리포트 다운로드", "손금 분석, OpenAI 사진 구도, Gemini 사진 구도 결과를 한 곳에서 확인하고 PDF와 PNG로 다운로드합니다. PDF는 한글 깨짐을 줄이기 위해 ReportLab 내장 한글 CID 폰트를 사용합니다.")

cols = st.columns(3, gap="large")
with cols[0]:
    card_start("PALM", "손금 리포트")
    if "palm_report" in st.session_state:
        st.markdown('<div class="body-text">손금 리포트가 준비되었습니다.</div>', unsafe_allow_html=True)
        pdf = palm_pdf(st.session_state["palm_report"], st.session_state.get("palm_report_name", "손금 분석 리포트"))
        st.download_button("손금 PDF 다운로드", data=pdf, file_name="palm_reading_report.pdf", mime="application/pdf", key="dl_palm_pdf")
        st.download_button("손금 TXT 다운로드", data=st.session_state["palm_report"].encode("utf-8"), file_name="palm_reading_report.txt", mime="text/plain", key="dl_palm_txt")
    else:
        st.info("손금 분석 결과가 없습니다.")
    card_end()

with cols[1]:
    card_start("OPENAI", "OpenAI 사진 리포트")
    if "openai_photo_analysis" in st.session_state and "openai_overlay_image" in st.session_state:
        pdf = photo_pdf(st.session_state["openai_photo_analysis"], st.session_state["openai_overlay_image"], st.session_state.get("openai_generated_image"), "OpenAI 사진 구도 리포트")
        st.download_button("OpenAI PDF 다운로드", data=pdf, file_name="openai_photo_report.pdf", mime="application/pdf", key="dl_openai_pdf")
        st.download_button("OpenAI 위치 PNG", data=image_to_buffer(st.session_state["openai_overlay_image"]), file_name="openai_direction_map.png", mime="image/png", key="dl_openai_overlay")
        if st.session_state.get("openai_generated_image") is not None:
            st.download_button("OpenAI 예시 PNG", data=image_to_buffer(st.session_state["openai_generated_image"]), file_name="openai_generated_example.png", mime="image/png", key="dl_openai_gen")
    else:
        st.info("OpenAI 사진 분석 결과가 없습니다.")
    card_end()

with cols[2]:
    card_start("GEMINI", "Gemini 사진 리포트")
    if "gemini_photo_analysis" in st.session_state and "gemini_overlay_image" in st.session_state:
        pdf = photo_pdf(st.session_state["gemini_photo_analysis"], st.session_state["gemini_overlay_image"], st.session_state.get("gemini_generated_image"), "Gemini 사진 구도 리포트")
        st.download_button("Gemini PDF 다운로드", data=pdf, file_name="gemini_photo_report.pdf", mime="application/pdf", key="dl_gemini_pdf")
        st.download_button("Gemini 위치 PNG", data=image_to_buffer(st.session_state["gemini_overlay_image"]), file_name="gemini_direction_map.png", mime="image/png", key="dl_gemini_overlay")
        if st.session_state.get("gemini_generated_image") is not None:
            st.download_button("Gemini 예시 PNG", data=image_to_buffer(st.session_state["gemini_generated_image"]), file_name="gemini_generated_example.png", mime="image/png", key="dl_gemini_gen")
    else:
        st.info("Gemini 사진 분석 결과가 없습니다.")
    card_end()

card_start("COMPARE", "OpenAI · Gemini 비교 리포트")
if "openai_photo_analysis" in st.session_state or "gemini_photo_analysis" in st.session_state:
    c1, c2 = st.columns(2, gap="large")
    with c1:
        if "openai_overlay_image" in st.session_state:
            st.image(st.session_state["openai_overlay_image"], caption="OpenAI 추천 위치", use_container_width=True)
        else:
            st.info("OpenAI 결과 없음")
    with c2:
        if "gemini_overlay_image" in st.session_state:
            st.image(st.session_state["gemini_overlay_image"], caption="Gemini 추천 위치", use_container_width=True)
        else:
            st.info("Gemini 결과 없음")
    pdf = comparison_pdf(
        st.session_state.get("openai_photo_analysis"),
        st.session_state.get("gemini_photo_analysis"),
        st.session_state.get("openai_overlay_image"),
        st.session_state.get("gemini_overlay_image"),
    )
    st.download_button("비교 PDF 다운로드", data=pdf, file_name="openai_gemini_comparison_report.pdf", mime="application/pdf")
else:
    st.info("비교할 사진 분석 결과가 없습니다.")
card_end()
