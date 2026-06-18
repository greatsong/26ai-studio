import streamlit as st
from utils.ui import inject_css, hero, BRAND, sidebar_info

st.set_page_config(page_title=BRAND, page_icon="✨", layout="wide", initial_sidebar_state="expanded")
inject_css()
sidebar_info()

hero(
    "MULTIMODAL AI LAB",
    BRAND,
    "손금 분석, OpenAI 사진 구도 분석, Gemini 사진 구도 분석을 하나의 멀티페이지 Streamlit 앱으로 통합했습니다. 따뜻한 아이보리 톤, 라운드 카드, 얇은 라인, 넉넉한 여백의 에디토리얼 스타일로 구성했습니다."
)

c1, c2, c3 = st.columns(3, gap="large")
with c1:
    st.markdown('''<div class="nav-card"><div class="section-label">PALM READING</div><div class="card-title">손금 분석</div><div class="body-text">왼손과 오른손 사진을 업로드하면 OpenAI Vision이 손금의 흐름을 읽고 친절한 한국어 리포트를 생성합니다.</div></div>''', unsafe_allow_html=True)
with c2:
    st.markdown('''<div class="nav-card"><div class="section-label">OPENAI PHOTO</div><div class="card-title">OpenAI 사진 앱</div><div class="body-text">사진 속 여백, 빛, 시선 흐름을 분석하고 인물 또는 피사체가 있을 위치를 추천합니다. 예시 이미지 생성까지 지원합니다.</div></div>''', unsafe_allow_html=True)
with c3:
    st.markdown('''<div class="nav-card"><div class="section-label">GEMINI PHOTO</div><div class="card-title">Gemini 사진 앱</div><div class="body-text">같은 구도 분석 기능을 Gemini API로 실행합니다. OpenAI 결과와 비교하기 좋습니다.</div></div>''', unsafe_allow_html=True)

st.markdown('<div class="lux-card"><div class="section-label">GET STARTED</div><div class="card-title">왼쪽 사이드바에서 페이지를 선택하세요</div><div class="body-text">먼저 손금 분석 또는 사진 구도 분석 페이지로 이동해 사진을 업로드하세요. 생성된 결과는 리포트 다운로드 페이지에서 PDF로 저장할 수 있습니다.</div></div>', unsafe_allow_html=True)
