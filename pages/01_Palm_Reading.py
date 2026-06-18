import streamlit as st
from PIL import Image
from utils.ui import inject_css, hero, card_start, card_end, sidebar_info
from utils.prompts import palm_prompt
from utils.openai_tools import palm_reading
from utils.report_utils import palm_pdf

st.set_page_config(page_title="손금 분석 | DangGok AI Vision Studio", page_icon="✋", layout="wide")
inject_css(); sidebar_info()

hero("PALM READING", "손금 분석", "왼손과 오른손 사진을 업로드하면 AI가 사진에서 보이는 손금 흐름을 바탕으로 친절한 한국어 리포트를 작성합니다. 예언이 아니라 자기이해를 위한 상징적 분석으로 설계했습니다.")

if "OPENAI_API_KEY" not in st.secrets:
    st.error("Streamlit Secrets에 OPENAI_API_KEY가 없습니다.")
    st.stop()

left_col, right_col = st.columns([0.9, 1.1], gap="large")

with left_col:
    card_start("INPUT", "손 사진 업로드")
    report_name = st.text_input("리포트 이름", value="나의 손금 리포트", key="palm_report_name_widget")
    dominant = st.radio("주로 사용하는 손", ["오른손", "왼손"], horizontal=True, key="palm_dominant_widget")
    tone = st.selectbox("리포트 문체", ["차분하고 고급스러운 에디토리얼", "따뜻하고 다정한 상담가", "쉽고 친절한 선생님", "간결하고 전문적인 분석가"], key="palm_tone_widget")
    model = st.text_input("OpenAI Vision 모델", value=st.secrets.get("OPENAI_VISION_MODEL", "gpt-4.1-mini"), key="palm_model_widget")
    left_file = st.file_uploader("왼손 사진", type=["jpg","jpeg","png","webp"], key="palm_left_widget")
    right_file = st.file_uploader("오른손 사진", type=["jpg","jpeg","png","webp"], key="palm_right_widget")
    run = st.button("손금 리포트 생성", key="palm_run_button")
    st.markdown('<p class="small-note">손가락 끝과 손목선까지 보이고, 손바닥 선이 밝게 보이는 사진일수록 결과가 좋아집니다.</p>', unsafe_allow_html=True)
    card_end()
    if left_file and right_file:
        p1, p2 = st.columns(2)
        p1.image(left_file, caption="왼손", use_container_width=True)
        p2.image(right_file, caption="오른손", use_container_width=True)

with right_col:
    card_start("REPORT", "분석 결과")
    if run:
        if not left_file or not right_file:
            st.warning("왼손과 오른손 사진을 모두 업로드해주세요.")
        else:
            with st.spinner("AI가 손금 흐름을 읽고 친절한 리포트를 작성하고 있습니다..."):
                try:
                    left_img = Image.open(left_file).convert("RGB")
                    right_img = Image.open(right_file).convert("RGB")
                    prompt = palm_prompt(dominant, report_name, tone)
                    report = palm_reading(st.secrets["OPENAI_API_KEY"], model, left_img, right_img, prompt)
                    st.session_state["palm_report"] = report
                    st.session_state["palm_report_name"] = report_name
                    st.session_state["palm_left_image"] = left_img
                    st.session_state["palm_right_image"] = right_img
                except Exception as e:
                    st.error(f"분석 오류: {e}")

    if "palm_report" in st.session_state:
        report = st.session_state["palm_report"]
        st.markdown(f'<div class="body-text">{report.replace(chr(10), "<br>")}</div>', unsafe_allow_html=True)
        st.divider()
        pdf = palm_pdf(report, st.session_state.get("palm_report_name", "손금 분석 리포트"))
        st.download_button("PDF 리포트 다운로드", data=pdf, file_name="palm_reading_report.pdf", mime="application/pdf")
        st.download_button("TXT 다운로드", data=report.encode("utf-8"), file_name="palm_reading_report.txt", mime="text/plain")
    else:
        st.markdown('<div class="body-text">아직 생성된 손금 리포트가 없습니다. 왼쪽에서 사진을 업로드하고 생성 버튼을 눌러주세요.</div>', unsafe_allow_html=True)
    card_end()

