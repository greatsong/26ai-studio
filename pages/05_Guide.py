import streamlit as st
from utils.ui import inject_css, hero, card_start, card_end, sidebar_info

st.set_page_config(page_title="사용 가이드 | DangGok AI Vision Studio", page_icon="🛠️", layout="wide")
inject_css(); sidebar_info()

hero("GUIDE", "사용 가이드", "배포 전 확인해야 할 API 키, 모델명, 오류 해결, 이미지 생성 프롬프트 방향을 정리했습니다.")

card_start("SECRETS", "Streamlit Cloud Secrets")
st.code('''OPENAI_API_KEY = "sk-..."
OPENAI_VISION_MODEL = "gpt-4.1-mini"
OPENAI_IMAGE_MODEL = "gpt-image-1"

GEMINI_API_KEY = "..."
GEMINI_VISION_MODEL = "gemini-2.5-flash"
GEMINI_IMAGE_MODEL = "gemini-2.5-flash-image"''', language="toml")
st.markdown('<div class="body-text">모델명은 계정 권한과 지역에 따라 달라질 수 있습니다. 앱 안에서 모델명을 직접 입력할 수 있게 했으므로, 사용 가능한 최신 모델명으로 바꿔 테스트하면 됩니다.</div>', unsafe_allow_html=True)
card_end()

card_start("FIXED", "이번 수정에서 해결한 문제")
st.markdown('''<div class="body-text">
<span class="pill">한글 PDF 깨짐 완화</span>
<span class="pill">ReportLab 내장 한글 CID 폰트 적용</span>
<span class="pill">pages/ 멀티페이지 구조</span>
<span class="pill">DangGok AI Vision Studio 리브랜딩</span>
<span class="pill">손금 분석 프롬프트 친절화</span>
<span class="pill">세션 상태 key 충돌 수정</span>
<span class="pill">모델이 실제 그 자리에 있는 듯한 이미지 편집 프롬프트 강화</span>
<br><br>
특히 <b>st.session_state.gemini_subject cannot be modified...</b> 오류는 위젯 key인 <code>gemini_subject_widget</code>을 코드에서 직접 수정하지 않고, 저장용 key인 <code>gemini_subject_value</code>를 따로 사용하도록 고쳤습니다.
</div>''', unsafe_allow_html=True)
card_end()

card_start("IMAGE GENERATION", "그 자리에 모델이 있는 것처럼 만들기")
st.markdown('''<div class="body-text">
이미지 생성 프롬프트는 단순히 “사람을 추가”가 아니라 다음 조건을 강하게 줍니다.<br><br>
1. 원본 사진을 다른 장면으로 바꾸지 않기<br>
2. 추천 좌표에 모델의 몸 중심 배치<br>
3. 원본 조명, 렌즈, 원근, 배경 유지<br>
4. 발이 바닥면에 닿도록 배치<br>
5. 자연스러운 그림자와 주변광 추가<br>
6. 스티커처럼 보이지 않게 실제 촬영 컷처럼 합성<br>
7. 텍스트, 화살표, 라벨 금지
</div>''', unsafe_allow_html=True)
card_end()
