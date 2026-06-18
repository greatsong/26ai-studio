import streamlit as st

BRAND = "DangGok AI Vision Studio"


def inject_css():
    st.markdown(
        """
        <style>
        :root{
          --ivory:#F8F5EF; --paper:#FFFFFF; --ink:#222222; --muted:#6F6A62;
          --line:#DDD5C9; --gold:#B89B5E; --soft:#FBF8F2;
        }
        .stApp{background:linear-gradient(180deg,#F8F5EF 0%,#FFFFFF 76%);color:#222222;}
        section[data-testid="stSidebar"]{background:#F8F5EF;border-right:1px solid #DDD5C9;}
        .hero{padding:44px 36px 32px;border:1px solid var(--line);border-radius:34px;background:rgba(255,255,255,.84);box-shadow:0 22px 64px rgba(70,55,35,.08);margin-bottom:26px;}
        .eyebrow{color:var(--gold);font-size:12px;letter-spacing:.23em;font-weight:900;text-transform:uppercase;margin-bottom:10px;}
        .main-title{font-size:50px;line-height:1.04;letter-spacing:-.045em;font-weight:950;color:var(--ink);margin-bottom:12px;}
        .subtitle{color:var(--muted);font-size:17px;line-height:1.75;max-width:980px;}
        .lux-card{background:rgba(255,255,255,.94);border:1px solid var(--line);border-radius:28px;padding:26px 28px;box-shadow:0 18px 50px rgba(70,55,35,.07);margin-bottom:22px;}
        .section-label{font-size:12px;color:var(--gold);letter-spacing:.18em;font-weight:900;text-transform:uppercase;margin-bottom:8px;}
        .card-title{font-size:25px;font-weight:900;margin-bottom:12px;color:var(--ink);}
        .body-text{font-size:16px;line-height:1.9;color:#34302B;}
        .small-note{font-size:13px;color:#817B72;line-height:1.7;}
        .pos-card{border:1px solid var(--line);border-radius:22px;padding:18px;background:#FBF8F2;margin-bottom:14px;}
        .pos-rank{color:var(--gold);font-size:12px;font-weight:900;letter-spacing:.16em;}
        .pos-title{font-size:20px;font-weight:900;color:var(--ink);margin-top:4px;margin-bottom:8px;}
        .pill{display:inline-block;border:1px solid var(--line);border-radius:999px;padding:7px 12px;background:#FBF8F2;color:#5B4A2E;font-size:13px;margin:0 6px 6px 0;}
        .nav-card{border:1px solid var(--line);border-radius:26px;background:rgba(255,255,255,.9);padding:24px;min-height:190px;box-shadow:0 16px 42px rgba(70,55,35,.06);}
        div[data-testid="stDownloadButton"] button, div[data-testid="stButton"] button{border-radius:999px;border:1px solid var(--gold);background:#222;color:white;padding:.65rem 1.3rem;font-weight:850;}
        .stTextInput input,.stTextArea textarea,.stSelectbox div[data-baseweb="select"]{border-radius:16px;}
        </style>
        """,
        unsafe_allow_html=True,
    )


def hero(kicker: str, title: str, subtitle: str):
    st.markdown(
        f"""
        <div class="hero">
          <div class="eyebrow">{kicker}</div>
          <div class="main-title">{title}</div>
          <div class="subtitle">{subtitle}</div>
        </div>
        """,
        unsafe_allow_html=True,
    )


def card_start(label: str, title: str):
    st.markdown(
        f"""<div class="lux-card"><div class="section-label">{label}</div><div class="card-title">{title}</div>""",
        unsafe_allow_html=True,
    )


def card_end():
    st.markdown("</div>", unsafe_allow_html=True)


def sidebar_info():
    st.sidebar.markdown(f"## {BRAND}")
    st.sidebar.caption("Vision API + Image Generation API")
    st.sidebar.divider()
    st.sidebar.markdown("**구성**")
    st.sidebar.markdown("- 손금 분석\n- OpenAI 사진 구도\n- Gemini 사진 구도\n- 리포트 다운로드")
